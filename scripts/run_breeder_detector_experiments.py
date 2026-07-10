#!/usr/bin/env python3

from __future__ import annotations

import argparse
import itertools
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import guess_breeder_result as breeder


REPO_ROOT = Path(__file__).resolve().parents[1]
STRUCTURE_THRESHOLDS = (0.68, 0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.82)
MIN_SIZES = ((96, 96), (112, 112), (120, 120), (132, 132), (144, 144))
MAX_CANDIDATES = (1, 2, 3)
SCORE_IMAGE_SIZE = 128
REFERENCE_SCALES = (0.85, 1.0, 1.15)
ANNOTATED_REFERENCE_TOKENS = (
	"annotated",
	"annotation",
	"note",
	"notes",
	"human",
	"markup",
	"marked",
	"guide",
	"guidance",
)


@dataclass(frozen=True)
class TemplateSet:
	name: str
	allow_locked: bool = False
	allow_paironormal: bool = False

	@property
	def flags(self) -> str:
		flags: list[str] = []
		if self.allow_locked:
			flags.append("--allow-locked-templates")
		if self.allow_paironormal:
			flags.append("--allow-paironormal-templates")
		return " ".join(flags) or "none"


@dataclass(frozen=True)
class ExperimentConfig:
	threshold: float
	min_width: int
	min_height: int
	template_set: TemplateSet
	max_candidates: int


@dataclass(frozen=True)
class ExperimentResult:
	number: int
	config: ExperimentConfig
	out_dir: Path
	candidates: list[breeder.CandidateEvidence]
	contexts: list[CandidateContext]
	scores: list[CandidateScore]

	@property
	def top_candidate(self) -> breeder.CandidateEvidence | None:
		return self.candidates[0] if self.candidates else None


@dataclass(frozen=True)
class CandidateContext:
	candidate_index: int
	context_box: breeder.CropBox
	path: Path
	boxed_path: Path


@dataclass(frozen=True)
class CandidateObservation:
	experiment_number: int
	candidate_index: int
	detection: breeder.DetectorCandidate
	boxed_context_path: Path
	score: CandidateScore


@dataclass(frozen=True)
class CandidateScore:
	raw_template_score: float
	color_score: float
	edge_score: float
	shape_or_mask_score: float
	local_context_score: float
	negative_similarity_penalty: float
	layout_score: float
	breeder_likeness_score: float
	best_reference: str


@dataclass(frozen=True)
class ReferenceVariant:
	name: str
	scale: float
	rgb: np.ndarray
	gray: np.ndarray
	mask: np.ndarray
	edges: np.ndarray
	color_hist: np.ndarray
	value_hist: np.ndarray


@dataclass(frozen=True)
class FalsePositiveExample:
	box: breeder.CropBox
	rgb: np.ndarray
	color_hist: np.ndarray
	value_hist: np.ndarray
	gray: np.ndarray
	edge_grid: np.ndarray


@dataclass(frozen=True)
class ScoringModel:
	references: list[ReferenceVariant]
	false_positives: list[FalsePositiveExample]
	source_width: int
	source_height: int


@dataclass
class CandidateCluster:
	number: int
	observations: list[CandidateObservation]

	@property
	def representative_box(self) -> breeder.CropBox:
		box_counts: dict[breeder.CropBox, int] = {}
		for observation in self.observations:
			box = observation.detection.box
			box_counts[box] = box_counts.get(box, 0) + 1
		return max(box_counts, key=lambda box: (box_counts[box], observation_box_area(box)))


def observation_box_area(box: breeder.CropBox) -> int:
	return box.w * box.h


def clamp_score(value: float) -> float:
	return max(0.0, min(1.0, float(value)))


def pil_to_rgb(image: Image.Image) -> np.ndarray:
	return np.asarray(image.convert("RGB"), dtype=np.uint8)


def resize_rgb(rgb: np.ndarray, size: int = SCORE_IMAGE_SIZE) -> np.ndarray:
	return cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA)


def hsv_histograms(rgb: np.ndarray, mask: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
	hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
	mask_u8 = None if mask is None else np.where(mask, 255, 0).astype(np.uint8)
	color_hist = cv2.calcHist([hsv], [0, 1], mask_u8, [24, 16], [0, 180, 0, 256])
	value_hist = cv2.calcHist([hsv], [2], mask_u8, [32], [0, 256])
	cv2.normalize(color_hist, color_hist, alpha=1.0, norm_type=cv2.NORM_L1)
	cv2.normalize(value_hist, value_hist, alpha=1.0, norm_type=cv2.NORM_L1)
	return color_hist, value_hist


def histogram_similarity(
	left_color: np.ndarray,
	left_value: np.ndarray,
	right_color: np.ndarray,
	right_value: np.ndarray,
) -> float:
	color = 1.0 - cv2.compareHist(left_color, right_color, cv2.HISTCMP_BHATTACHARYYA)
	value = 1.0 - cv2.compareHist(left_value, right_value, cv2.HISTCMP_BHATTACHARYYA)
	return clamp_score((0.75 * color) + (0.25 * value))


def canny_edges(gray: np.ndarray) -> np.ndarray:
	blurred = cv2.GaussianBlur(gray, (5, 5), 0)
	median = float(np.median(blurred))
	lower = max(20, round(0.66 * median))
	upper = max(lower + 20, min(240, round(1.33 * median)))
	return cv2.Canny(blurred, lower, upper) > 0


def grid_density(values: np.ndarray, mask: np.ndarray | None = None, grid_size: int = 4) -> np.ndarray:
	height, width = values.shape
	descriptor: list[float] = []
	for row in range(grid_size):
		for column in range(grid_size):
			y1 = round(row * height / grid_size)
			y2 = round((row + 1) * height / grid_size)
			x1 = round(column * width / grid_size)
			x2 = round((column + 1) * width / grid_size)
			cell = values[y1:y2, x1:x2]
			if mask is None:
				descriptor.append(float(cell.mean()))
				continue
			cell_mask = mask[y1:y2, x1:x2]
			descriptor.append(float(cell[cell_mask].mean()) if cell_mask.any() else 0.0)
	return np.asarray(descriptor, dtype=np.float32)


def descriptor_similarity(left: np.ndarray, right: np.ndarray) -> float:
	difference = float(np.abs(left - right).sum())
	scale = float(np.abs(left).sum() + np.abs(right).sum())
	return clamp_score(1.0 - (difference / max(scale, 1e-6)))


def masked_correlation(left: np.ndarray, right: np.ndarray, mask: np.ndarray) -> float:
	left_values = left[mask].astype(np.float32)
	right_values = right[mask].astype(np.float32)
	if left_values.size < 16 or left_values.std() < 1e-6 or right_values.std() < 1e-6:
		return 0.0
	correlation = float(np.corrcoef(left_values, right_values)[0, 1])
	if not math.isfinite(correlation):
		return 0.0
	return clamp_score((correlation + 1.0) / 2.0)


def candidate_foreground_mask(rgb: np.ndarray) -> np.ndarray:
	lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
	border_width = max(3, round(min(rgb.shape[:2]) * 0.07))
	border = np.concatenate(
		(
			lab[:border_width, :, :].reshape(-1, 3),
			lab[-border_width:, :, :].reshape(-1, 3),
			lab[:, :border_width, :].reshape(-1, 3),
			lab[:, -border_width:, :].reshape(-1, 3),
		),
		axis=0,
	)
	background = np.median(border, axis=0)
	distance = np.linalg.norm(lab - background, axis=2)
	distance_u8 = cv2.normalize(distance, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
	_, foreground = cv2.threshold(distance_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	kernel = np.ones((5, 5), dtype=np.uint8)
	foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel)
	foreground = cv2.morphologyEx(foreground, cv2.MORPH_OPEN, np.ones((3, 3), dtype=np.uint8))
	return foreground > 0


def render_reference_variant(path: Path, scale: float) -> ReferenceVariant:
	with Image.open(path) as image_file:
		rgba = np.asarray(image_file.convert("RGBA"), dtype=np.uint8)
	alpha = rgba[:, :, 3]
	y_values, x_values = np.where(alpha > 16)
	if not len(x_values):
		raise RuntimeError(f"Reference has no visible pixels: {path}")
	tight = rgba[y_values.min() : y_values.max() + 1, x_values.min() : x_values.max() + 1]
	target_extent = round(SCORE_IMAGE_SIZE * 0.82 * scale)
	resize_scale = min(target_extent / tight.shape[1], target_extent / tight.shape[0])
	width = max(1, round(tight.shape[1] * resize_scale))
	height = max(1, round(tight.shape[0] * resize_scale))
	resized = cv2.resize(tight, (width, height), interpolation=cv2.INTER_AREA)
	canvas = np.zeros((SCORE_IMAGE_SIZE, SCORE_IMAGE_SIZE, 4), dtype=np.uint8)
	x = (SCORE_IMAGE_SIZE - width) // 2
	y = SCORE_IMAGE_SIZE - height - 4
	canvas[y : y + height, x : x + width] = resized
	mask = canvas[:, :, 3] > 32
	rgb = canvas[:, :, :3]
	gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
	edges = canny_edges(gray)
	color_hist, value_hist = hsv_histograms(rgb, mask)
	return ReferenceVariant(
		name=path.name,
		scale=scale,
		rgb=rgb,
		gray=gray,
		mask=mask,
		edges=edges,
		color_hist=color_hist,
		value_hist=value_hist,
	)


def reference_paths_for_island(island: str) -> list[Path]:
	is_paironormal = "paironormal" in breeder.normalize_name(island)
	paths: list[Path] = []
	for path in sorted(breeder.STRUCTURE_DIR.glob("*.webp")):
		if any(token in path.name.lower() for token in ANNOTATED_REFERENCE_TOKENS):
			continue
		if ("paironormal" in path.name) == is_paironormal:
			paths.append(path)
	return paths


def confirmed_false_positive_boxes(annotation_path: Path, source: Path) -> list[breeder.CropBox]:
	if not annotation_path.exists():
		return []
	try:
		data = json.loads(annotation_path.read_text(encoding="utf-8"))
	except (json.JSONDecodeError, OSError) as exc:
		raise RuntimeError(f"Could not load negative examples from {annotation_path}: {exc}") from exc
	if data.get("source") != source_display_path(source):
		return []
	boxes: list[breeder.CropBox] = []
	for annotation in data.get("annotations", []):
		if annotation.get("label") != "false_positive" or annotation.get("status") != "confirmed":
			continue
		box = box_from_json(annotation.get("box"))
		if box:
			boxes.append(box)
	return boxes


def false_positive_example(source_image: Image.Image, box: breeder.CropBox) -> FalsePositiveExample:
	rgb = resize_rgb(pil_to_rgb(breeder.crop_image(source_image, breeder.clamp_box(box, source_image))))
	gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
	edges = canny_edges(gray)
	color_hist, value_hist = hsv_histograms(rgb)
	return FalsePositiveExample(
		box=box,
		rgb=rgb,
		color_hist=color_hist,
		value_hist=value_hist,
		gray=gray,
		edge_grid=grid_density(edges),
	)


def build_scoring_model(args: argparse.Namespace, source_image: Image.Image) -> ScoringModel:
	references = [
		render_reference_variant(path, scale)
		for path in reference_paths_for_island(args.island)
		for scale in REFERENCE_SCALES
	]
	false_positives = [
		false_positive_example(source_image, box)
		for box in confirmed_false_positive_boxes(args.out / "annotations.json", args.source)
	]
	return ScoringModel(
		references=references,
		false_positives=false_positives,
		source_width=source_image.width,
		source_height=source_image.height,
	)


def reference_signal_scores(candidate_rgb: np.ndarray, reference: ReferenceVariant) -> tuple[float, float, float]:
	candidate_gray = cv2.cvtColor(candidate_rgb, cv2.COLOR_RGB2GRAY)
	candidate_edges = canny_edges(candidate_gray)
	candidate_color, candidate_value = hsv_histograms(candidate_rgb, reference.mask)
	color_score = histogram_similarity(
		candidate_color,
		candidate_value,
		reference.color_hist,
		reference.value_hist,
	)

	comparison_mask = cv2.dilate(reference.mask.astype(np.uint8), np.ones((3, 3), dtype=np.uint8)) > 0
	candidate_edge_grid = grid_density(candidate_edges, comparison_mask)
	reference_edge_grid = grid_density(reference.edges, comparison_mask)
	edge_score = descriptor_similarity(candidate_edge_grid, reference_edge_grid)

	foreground = candidate_foreground_mask(candidate_rgb)
	intersection = float(np.logical_and(foreground, reference.mask).sum())
	dice = (2.0 * intersection) / max(float(foreground.sum() + reference.mask.sum()), 1.0)
	correlation = masked_correlation(candidate_gray, reference.gray, reference.mask)
	shape_score = clamp_score((0.65 * dice) + (0.35 * correlation))
	return color_score, edge_score, shape_score


def crop_visual_similarity(candidate_rgb: np.ndarray, example: FalsePositiveExample) -> float:
	candidate_color, candidate_value = hsv_histograms(candidate_rgb)
	color = histogram_similarity(candidate_color, candidate_value, example.color_hist, example.value_hist)
	candidate_gray = cv2.cvtColor(candidate_rgb, cv2.COLOR_RGB2GRAY)
	gray = masked_correlation(
		candidate_gray,
		example.gray,
		np.ones(candidate_gray.shape, dtype=bool),
	)
	edges = descriptor_similarity(grid_density(canny_edges(candidate_gray)), example.edge_grid)
	return clamp_score((0.45 * color) + (0.35 * gray) + (0.20 * edges))


def local_context_score(source_image: Image.Image, box: breeder.CropBox) -> float:
	padding = max(24, round(max(box.w, box.h) * 0.35))
	context_box = breeder.clamp_box(
		breeder.CropBox(
			x=box.x - padding,
			y=box.y - padding,
			w=box.w + (2 * padding),
			h=box.h + (2 * padding),
		),
		source_image,
	)
	context_rgb = pil_to_rgb(breeder.crop_image(source_image, context_box))
	candidate_mask = np.zeros(context_rgb.shape[:2], dtype=bool)
	left = box.x - context_box.x
	top = box.y - context_box.y
	right = min(context_rgb.shape[1], left + box.w)
	bottom = min(context_rgb.shape[0], top + box.h)
	candidate_mask[max(0, top) : bottom, max(0, left) : right] = True
	ring_mask = np.logical_not(candidate_mask)
	if not candidate_mask.any() or not ring_mask.any():
		return 0.0

	candidate_color, candidate_value = hsv_histograms(context_rgb, candidate_mask)
	ring_color, ring_value = hsv_histograms(context_rgb, ring_mask)
	color_similarity = histogram_similarity(candidate_color, candidate_value, ring_color, ring_value)
	color_separation = 1.0 - color_similarity
	edges = canny_edges(cv2.cvtColor(context_rgb, cv2.COLOR_RGB2GRAY))
	inside_density = float(edges[candidate_mask].mean())
	ring_density = float(edges[ring_mask].mean())
	edge_enrichment = clamp_score(0.5 + ((inside_density - ring_density) * 3.0))
	return clamp_score((0.65 * color_separation) + (0.35 * edge_enrichment))


def box_layout_score(box: breeder.CropBox, model: ScoringModel) -> float:
	object_scale = math.sqrt(box.w * box.h) / min(model.source_width, model.source_height)
	if object_scale < 0.035:
		size_score = object_scale / 0.035
	elif object_scale <= 0.20:
		size_score = 1.0
	else:
		size_score = max(0.0, 1.0 - ((object_scale - 0.20) / 0.20))
	aspect_score = math.exp(-1.5 * abs(math.log(box.w / box.h)))
	margin = min(
		box.x,
		box.y,
		model.source_width - (box.x + box.w),
		model.source_height - (box.y + box.h),
	)
	clearance_score = clamp_score(margin / max(box.w, box.h, 1) / 0.5)
	return clamp_score((0.55 * size_score) + (0.25 * aspect_score) + (0.20 * clearance_score))


def score_candidate(
	source_image: Image.Image,
	detection: breeder.DetectorCandidate,
	model: ScoringModel,
) -> CandidateScore:
	crop = breeder.crop_image(source_image, breeder.clamp_box(detection.box, source_image))
	candidate_rgb = resize_rgb(pil_to_rgb(crop))
	variant_scores: list[tuple[float, float, float, ReferenceVariant]] = []
	for reference in model.references:
		color, edge, shape = reference_signal_scores(candidate_rgb, reference)
		variant_scores.append((color, edge, shape, reference))
	color_score, edge_score, shape_score, best_reference = max(
		variant_scores,
		key=lambda item: (0.34 * item[0]) + (0.31 * item[1]) + (0.35 * item[2]),
	)

	max_overlap = max(
		(breeder.box_iou(detection.box, example.box) for example in model.false_positives),
		default=0.0,
	)
	max_negative_similarity = max(
		(crop_visual_similarity(candidate_rgb, example) for example in model.false_positives),
		default=0.0,
	)
	negative_penalty = clamp_score((0.55 * max_overlap) + (0.25 * max_negative_similarity))
	context_score = local_context_score(source_image, detection.box)
	layout_score = box_layout_score(detection.box, model)
	positive_score = (
		(0.15 * detection.match_score)
		+ (0.23 * color_score)
		+ (0.20 * edge_score)
		+ (0.24 * shape_score)
		+ (0.10 * context_score)
		+ (0.08 * layout_score)
	)
	breeder_likeness = clamp_score(positive_score - negative_penalty)
	return CandidateScore(
		raw_template_score=detection.match_score,
		color_score=color_score,
		edge_score=edge_score,
		shape_or_mask_score=shape_score,
		local_context_score=context_score,
		negative_similarity_penalty=negative_penalty,
		layout_score=layout_score,
		breeder_likeness_score=breeder_likeness,
		best_reference=f"{best_reference.name} @ {best_reference.scale:.2f}x",
	)


def template_sets_for_island(island: str) -> tuple[TemplateSet, ...]:
	sets = (
		TemplateSet(name="normal/enhanced"),
		TemplateSet(name="normal/enhanced/locked", allow_locked=True),
	)
	if "paironormal" in breeder.normalize_name(island):
		sets += (
			TemplateSet(
				name="normal/enhanced/paironormal",
				allow_paironormal=True,
			),
		)
	return sets


def balanced_base_configs(template_sets: tuple[TemplateSet, ...]) -> list[tuple[float, tuple[int, int], TemplateSet]]:
	"""Order the full product so small --limit values still cover every dimension."""
	remaining = list(itertools.product(STRUCTURE_THRESHOLDS, MIN_SIZES, template_sets))
	threshold_counts = {value: 0 for value in STRUCTURE_THRESHOLDS}
	size_counts = {value: 0 for value in MIN_SIZES}
	template_counts = {value: 0 for value in template_sets}
	ordered: list[tuple[float, tuple[int, int], TemplateSet]] = []

	while remaining:
		best_index = min(
			range(len(remaining)),
			key=lambda index: (
				threshold_counts[remaining[index][0]]
				+ size_counts[remaining[index][1]]
				+ template_counts[remaining[index][2]],
				max(
					threshold_counts[remaining[index][0]],
					size_counts[remaining[index][1]],
					template_counts[remaining[index][2]],
				),
				index,
			),
		)
		threshold, min_size, template_set = remaining.pop(best_index)
		ordered.append((threshold, min_size, template_set))
		threshold_counts[threshold] += 1
		size_counts[min_size] += 1
		template_counts[template_set] += 1

	return ordered


def experiment_configs(island: str) -> list[ExperimentConfig]:
	configs: list[ExperimentConfig] = []
	for threshold, (min_width, min_height), template_set in balanced_base_configs(
		template_sets_for_island(island)
	):
		for max_candidates in MAX_CANDIDATES:
			configs.append(
				ExperimentConfig(
					threshold=threshold,
					min_width=min_width,
					min_height=min_height,
					template_set=template_set,
					max_candidates=max_candidates,
				)
			)
	return configs


def detector_args(
	args: argparse.Namespace,
	config: ExperimentConfig,
	experiment_dir: Path,
) -> argparse.Namespace:
	return argparse.Namespace(
		mode="detect-breeders",
		source=args.source,
		island=args.island,
		parents=args.parents,
		out=experiment_dir,
		top_matches=5,
		max_candidates=config.max_candidates,
		structure_match_threshold=config.threshold,
		structure_min_width=config.min_width,
		structure_min_height=config.min_height,
		allow_paironormal_templates=config.template_set.allow_paironormal,
		allow_locked_templates=config.template_set.allow_locked,
		debug_candidates=True,
		left_parent_rel=breeder.RelativeCropBox(*breeder.LEFT_PARENT_EGG_REL),
		right_parent_rel=breeder.RelativeCropBox(*breeder.RIGHT_PARENT_EGG_REL),
	)


def save_candidate_context(
	source_image: Image.Image,
	experiment_dir: Path,
	candidate_index: int,
	candidate_box: breeder.CropBox,
) -> CandidateContext:
	padding = max(96, round(max(candidate_box.w, candidate_box.h) * 1.25))
	unclamped_context_box = breeder.CropBox(
		x=candidate_box.x - padding,
		y=candidate_box.y - padding,
		w=candidate_box.w + (padding * 2),
		h=candidate_box.h + (padding * 2),
	)
	context_box = breeder.clamp_box(unclamped_context_box, source_image)
	context = breeder.crop_image(source_image, context_box).convert("RGB")
	context_path = experiment_dir / f"candidate-{candidate_index}-source-context.png"
	boxed_path = experiment_dir / f"candidate-{candidate_index}-source-context-boxed.png"
	breeder.save_png(context, context_path)

	boxed = context.copy()
	draw = ImageDraw.Draw(boxed)
	left = candidate_box.x - context_box.x
	top = candidate_box.y - context_box.y
	right = left + candidate_box.w - 1
	bottom = top + candidate_box.h - 1
	draw.rectangle((left, top, right, bottom), outline=(8, 12, 18), width=10)
	draw.rectangle((left, top, right, bottom), outline=(255, 216, 64), width=5)

	font = load_font(20, bold=True)
	label = f"Candidate {candidate_index} · {candidate_box.x},{candidate_box.y},{candidate_box.w},{candidate_box.h}"
	label_box = draw.textbbox((0, 0), label, font=font)
	label_width = label_box[2] - label_box[0]
	label_height = label_box[3] - label_box[1]
	label_x = max(0, min(left, boxed.width - label_width - 12))
	label_y = top - label_height - 14
	if label_y < 0:
		label_y = min(boxed.height - label_height - 12, bottom + 8)
	draw.rounded_rectangle(
		(label_x, label_y, label_x + label_width + 12, label_y + label_height + 10),
		radius=5,
		fill=(8, 12, 18),
	)
	draw.text((label_x + 6, label_y + 4), label, font=font, fill=(255, 226, 94))
	breeder.save_png(boxed, boxed_path)

	return CandidateContext(
		candidate_index=candidate_index,
		context_box=context_box,
		path=context_path,
		boxed_path=boxed_path,
	)


def append_contexts_to_report(
	report_path: Path,
	contexts: list[CandidateContext],
	scores: list[CandidateScore],
) -> None:
	if not contexts:
		return
	lines = [
		"",
		"## Candidate source context and breeder-likeness scoring",
		"",
		"These wider screenshot crops show where each isolated detector crop came from. The yellow rectangle is the exact candidate box.",
		"",
		"The breeder-likeness score is an explainable ranking aid, not a definitive classification. It preserves the raw template score and combines reference color, edge layout, masked shape, size/layout sanity, and confirmed-false-positive evidence.",
		"",
	]
	for context, score in zip(contexts, scores, strict=True):
		lines.extend(
			[
				f"### Candidate {context.candidate_index} context",
				"",
				"| Raw template | Color | Edge | Shape/mask | Local context | Negative penalty | Layout sanity | Breeder-likeness | Best reference |",
				"|---:|---:|---:|---:|---:|---:|---:|---:|---|",
				f"| {score.raw_template_score:.3f} | {score.color_score:.3f} | {score.edge_score:.3f} | "
				f"{score.shape_or_mask_score:.3f} | {score.local_context_score:.3f} | "
				f"{score.negative_similarity_penalty:.3f} | "
				f"{score.layout_score:.3f} | **{score.breeder_likeness_score:.3f}** | {score.best_reference} |",
				"",
				f"Context box: `{context.context_box.as_report_text()}`",
				"",
				f"![Candidate {context.candidate_index} source context]({context.path.name})",
				"",
				f"![Candidate {context.candidate_index} source context with detector box]({context.boxed_path.name})",
				"",
			]
		)
	with report_path.open("a", encoding="utf-8") as report:
		report.write("\n".join(lines))


def run_experiments(args: argparse.Namespace, configs: list[ExperimentConfig]) -> list[ExperimentResult]:
	source_image = breeder.load_image(args.source)
	breeding_data = breeder.load_breeding_data()
	scoring_model = build_scoring_model(args, source_image)
	results: list[ExperimentResult] = []
	score_cache: dict[breeder.CropBox, CandidateScore] = {}
	detection_cache: dict[
		tuple[float, int, int, TemplateSet],
		tuple[list[breeder.DetectorCandidate], list[breeder.DetectorCandidate], breeder.DetectorDebug],
	] = {}

	for number, config in enumerate(configs, start=1):
		experiment_dir = args.out / f"experiment-{number:03d}"
		experiment_dir.mkdir(parents=True, exist_ok=True)
		config_args = detector_args(args, config, experiment_dir)
		cache_key = (
			config.threshold,
			config.min_width,
			config.min_height,
			config.template_set,
		)
		if cache_key not in detection_cache:
			detection_cache[cache_key] = breeder.detect_breeding_structures(
				source_path=args.source,
				max_candidates=max(MAX_CANDIDATES),
				threshold=config.threshold,
				min_width=config.min_width,
				min_height=config.min_height,
				allow_paironormal_templates=config.template_set.allow_paironormal,
				allow_locked_templates=config.template_set.allow_locked,
				debug_candidates=True,
			)
		detected, debug_candidates, detector_debug = detection_cache[cache_key]
		detected = detected[: config.max_candidates]

		shutil.copy2(args.source, experiment_dir / "source.png")
		candidate_evidence: list[breeder.CandidateEvidence] = []
		candidate_contexts: list[CandidateContext] = []
		candidate_scores: list[CandidateScore] = []
		for candidate_index, detection in enumerate(detected, start=1):
			manual_parents = tuple(args.parents) if candidate_index == 1 else (None, None)
			candidate_evidence.append(
				breeder.build_candidate_evidence(
					source_image=source_image,
					out_dir=experiment_dir,
					data=breeding_data,
					args=config_args,
					index=candidate_index,
					breeder_box=detection.box,
					detection=detection,
					manual_parents=manual_parents,
				)
			)
			candidate_contexts.append(
				save_candidate_context(
					source_image=source_image,
					experiment_dir=experiment_dir,
					candidate_index=candidate_index,
					candidate_box=detection.box,
				)
			)
			if detection.box not in score_cache:
				score_cache[detection.box] = score_candidate(source_image, detection, scoring_model)
			candidate_scores.append(score_cache[detection.box])

		report_path = experiment_dir / "report.md"
		breeder.write_report(
			report_path=report_path,
			args=config_args,
			source_copy=experiment_dir / "source.png",
			candidates=candidate_evidence,
			data=breeding_data,
			debug_candidates=debug_candidates,
			detector_debug=detector_debug,
		)
		append_contexts_to_report(report_path, candidate_contexts, candidate_scores)
		results.append(
			ExperimentResult(
				number=number,
				config=config,
				out_dir=experiment_dir,
				candidates=candidate_evidence,
				contexts=candidate_contexts,
				scores=candidate_scores,
			)
		)
		print(
			f"Experiment {number:03d}/{len(configs):03d}: "
			f"threshold={config.threshold:.2f}, min={config.min_width}x{config.min_height}, "
			f"templates={config.template_set.name}, max={config.max_candidates}, "
			f"candidates={len(candidate_evidence)}"
		)

	return results


def markdown_link(label: str, path: Path, base: Path) -> str:
	return f"[{label}]({path.relative_to(base).as_posix()})"


def cluster_candidate_boxes(results: list[ExperimentResult], iou_threshold: float = 0.85) -> list[CandidateCluster]:
	clusters: list[CandidateCluster] = []
	for result in results:
		for candidate, context, score in zip(result.candidates, result.contexts, result.scores, strict=True):
			if candidate.detection is None:
				continue
			observation = CandidateObservation(
				experiment_number=result.number,
				candidate_index=candidate.index,
				detection=candidate.detection,
				boxed_context_path=context.boxed_path,
				score=score,
			)
			matching_cluster = next(
				(
					cluster
					for cluster in clusters
					if breeder.box_iou(candidate.detection.box, cluster.representative_box) >= iou_threshold
				),
				None,
			)
			if matching_cluster:
				matching_cluster.observations.append(observation)
			else:
				clusters.append(CandidateCluster(number=len(clusters) + 1, observations=[observation]))

	clusters.sort(key=lambda cluster: len(cluster.observations), reverse=True)
	for number, cluster in enumerate(clusters, start=1):
		cluster.number = number
	return clusters


def box_as_json(box: breeder.CropBox) -> dict[str, int]:
	return {"x": box.x, "y": box.y, "w": box.w, "h": box.h}


def box_from_json(value: object) -> breeder.CropBox | None:
	if not isinstance(value, dict):
		return None
	try:
		return breeder.CropBox(
			x=int(value["x"]),
			y=int(value["y"]),
			w=int(value["w"]),
			h=int(value["h"]),
		)
	except (KeyError, TypeError, ValueError):
		return None


def annotation_for_box(annotations: list[dict], box: breeder.CropBox) -> dict | None:
	for annotation in annotations:
		annotation_box = box_from_json(annotation.get("box"))
		if annotation_box and breeder.box_iou(annotation_box, box) >= 0.85:
			return annotation
	return None


def source_display_path(source: Path) -> str:
	try:
		return source.relative_to(REPO_ROOT).as_posix()
	except ValueError:
		return str(source)


def write_annotation_file(
	args: argparse.Namespace,
	clusters: list[CandidateCluster],
) -> tuple[Path, dict]:
	path = args.out / "annotations.json"
	if path.exists():
		try:
			data = json.loads(path.read_text(encoding="utf-8"))
		except (json.JSONDecodeError, OSError) as exc:
			raise RuntimeError(f"Could not preserve existing annotation file {path}: {exc}") from exc
	else:
		data = {"schema_version": 1, "annotations": []}

	annotations = data.get("annotations")
	if not isinstance(annotations, list):
		raise RuntimeError(f"Expected an annotations list in {path}")
	data["schema_version"] = 1
	data["source"] = source_display_path(args.source)
	data["island"] = args.island

	if not any(annotation.get("label") == "breeding_structure" for annotation in annotations):
		annotations.append(
			{
				"id": "breeding-structure-manual-box",
				"label": "breeding_structure",
				"status": "needs_manual_box",
				"box": None,
				"notes": "Draw the real Breeding Structure box after reviewing source context crops.",
			}
		)

	for cluster in clusters:
		box = cluster.representative_box
		annotation = annotation_for_box(annotations, box)
		if annotation is None:
			annotation = {
				"id": f"detector-cluster-{box.x}-{box.y}-{box.w}-{box.h}",
				"label": "detector_candidate",
				"status": "needs_review",
				"box": box_as_json(box),
				"notes": "Review the boxed source context before assigning a label.",
			}
			annotations.append(annotation)
		annotation["cluster_occurrences"] = len(cluster.observations)
		annotation["observed_in_experiments"] = sorted(
			{observation.experiment_number for observation in cluster.observations}
		)

	path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
	return path, data


def crop_links(result: ExperimentResult, base: Path) -> str:
	if not result.top_candidate:
		return "—"
	prefix = result.out_dir / "candidate-1"
	paths = (
		("context", result.contexts[0].path),
		("boxed context", result.contexts[0].boxed_path),
		("crop", Path(f"{prefix}-crop-breeder.png")),
		("crop 4x", Path(f"{prefix}-crop-breeder-4x.png")),
		("left egg", Path(f"{prefix}-crop-left-parent-egg.png")),
		("left egg 4x", Path(f"{prefix}-crop-left-parent-egg-4x.png")),
		("right egg", Path(f"{prefix}-crop-right-parent-egg.png")),
		("right egg 4x", Path(f"{prefix}-crop-right-parent-egg-4x.png")),
	)
	return "<br>".join(markdown_link(label, path, base) for label, path in paths)


def write_summary(
	args: argparse.Namespace,
	results: list[ExperimentResult],
	total_configs: int,
	clusters: list[CandidateCluster],
	annotation_data: dict,
) -> Path:
	path = args.out / "experiment-summary.md"
	annotations = annotation_data["annotations"]
	lines = [
		"# Breeder Detector Experiment Summary",
		"",
		f"Source: `{args.source}`  ",
		f"Island: **{args.island}**  ",
		f"Manual parents: **{args.parents[0]} + {args.parents[1]}**  ",
		f"Experiments run: **{len(results)} of {total_configs}**",
		"",
		"The experiment order is balanced across thresholds, minimum sizes, and template sets so limited runs sample the full search space early.",
		"",
		"Candidate annotations: [annotations.json](annotations.json)",
		"",
		"## Breeder-likeness score",
		"",
		"This score is a ranking aid for human review, not a definitive recognition result. Every component is normalized to 0–1, and the raw OpenCV template score remains visible separately.",
		"",
		"Positive evidence is `0.15 × raw template + 0.23 × HSV color + 0.20 × edge layout + 0.24 × shape/mask + 0.10 × local context + 0.08 × layout sanity`. The final breeder-likeness score is that weighted sum minus the negative-similarity penalty, clamped to 0–1.",
		"",
		"- **Color** compares HSV histograms only under transparent reference-object masks, including brightness as a smaller component.",
		"- **Edge layout** compares Canny edge density across a 4×4 grid inside the masked object region.",
		"- **Shape/mask** combines a border-relative foreground silhouette overlap with masked grayscale structure correlation.",
		"- **Local context** rewards color separation and edge enrichment between the candidate box and its immediate surrounding ring; continuous texture patches tend to score lower.",
		"- **Multi-scale references** evaluate each applicable structure asset at 0.85×, 1.00×, and 1.15×; the best combined reference variant supplies the reported component scores.",
		"- **Layout sanity** softly checks world-view object scale, aspect ratio, and screen-edge clearance. It does not hard-code coordinates for this screenshot.",
		"- **Negative penalty** is `0.55 × box overlap + 0.25 × visual similarity` against confirmed false-positive annotations. Visual similarity combines color, grayscale correlation, and edge layout.",
		"",
		"## Candidate box clusters",
		"",
		"Candidate boxes are grouped when their intersection-over-union is at least 0.85. Repeated detections at one location are one review target, not independent evidence that the detection is correct.",
		"",
		"| Cluster | Representative box | Occurrences | Experiments | Raw score range | Breeder-likeness range | Templates | Annotation | Status | Example context |",
		"|---:|---|---:|---|---|---|---|---|---|---|",
	]
	for cluster in clusters:
		box = cluster.representative_box
		annotation = annotation_for_box(annotations, box) or {}
		scores = [observation.detection.match_score for observation in cluster.observations]
		likeness_scores = [observation.score.breeder_likeness_score for observation in cluster.observations]
		templates = sorted({observation.detection.template_name for observation in cluster.observations})
		experiments = sorted({observation.experiment_number for observation in cluster.observations})
		example = cluster.observations[0]
		lines.append(
			f"| {cluster.number} | `{box.as_report_text()}` | {len(cluster.observations)} | "
			f"{', '.join(f'{number:03d}' for number in experiments)} | "
			f"{min(scores):.3f}–{max(scores):.3f} | "
			f"{min(likeness_scores):.3f}–{max(likeness_scores):.3f} | {', '.join(templates)} | "
			f"{annotation.get('label', 'unannotated')} | {annotation.get('status', 'needs_review')} | "
			f"{markdown_link('boxed context', example.boxed_context_path, args.out)} |"
		)
	lines.extend(
		[
			"",
			"## Experiments",
			"",
		"| Experiment | Threshold | Min size | Template set | Max candidates | Candidates | Raw template | Color | Edge | Shape/mask | Local context | Negative penalty | Breeder-likeness | Best reference | Top template | Top box | No candidates | Evidence |",
		"|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|",
		]
	)
	for result in results:
		config = result.config
		top = result.top_candidate
		detection = top.detection if top else None
		score = result.scores[0] if result.scores else None
		experiment_link = markdown_link(
			f"{result.number:03d}",
			result.out_dir / "report.md",
			args.out,
		)
		lines.append(
			f"| {experiment_link} | {config.threshold:.2f} | {config.min_width}x{config.min_height} | "
			f"{config.template_set.name} (`{config.template_set.flags}`) | {config.max_candidates} | "
			f"{len(result.candidates)} | "
			f"{f'{score.raw_template_score:.3f}' if score else '—'} | "
			f"{f'{score.color_score:.3f}' if score else '—'} | "
			f"{f'{score.edge_score:.3f}' if score else '—'} | "
			f"{f'{score.shape_or_mask_score:.3f}' if score else '—'} | "
			f"{f'{score.local_context_score:.3f}' if score else '—'} | "
			f"{f'{score.negative_similarity_penalty:.3f}' if score else '—'} | "
			f"{f'**{score.breeder_likeness_score:.3f}**' if score else '—'} | "
			f"{score.best_reference if score else '—'} | "
			f"{detection.template_name if detection else '—'} | "
			f"{f'`{detection.box.as_report_text()}`' if detection else '—'} | "
			f"{'no' if detection else 'yes'} | {crop_links(result, args.out)} |"
		)

	path.write_text("\n".join(lines) + "\n", encoding="utf-8")
	return path


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
	font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
	try:
		return ImageFont.truetype(font_name, size=size)
	except OSError:
		return ImageFont.load_default(size=size)


def draw_contact_sheet(args: argparse.Namespace, results: list[ExperimentResult]) -> Path:
	columns = 4
	cell_width = 500
	cell_height = 520
	margin = 28
	gap = 22
	header_height = 104
	rows = max(1, math.ceil(len(results) / columns))
	sheet_width = (margin * 2) + (columns * cell_width) + ((columns - 1) * gap)
	sheet_height = header_height + margin + (rows * cell_height) + ((rows - 1) * gap) + margin
	sheet = Image.new("RGB", (sheet_width, sheet_height), (24, 30, 42))
	draw = ImageDraw.Draw(sheet)
	title_font = load_font(32, bold=True)
	subtitle_font = load_font(18)
	card_title_font = load_font(24, bold=True)
	card_font = load_font(17)
	card_small_font = load_font(14)
	no_candidate_font = load_font(28, bold=True)

	draw.text((margin, 20), "Breeder Detector Experiment Contact Sheet", font=title_font, fill=(246, 248, 252))
	draw.text(
		(margin, 64),
		f"{args.island} · {len(results)} experiments · boxed source context for each top candidate",
		font=subtitle_font,
		fill=(174, 187, 207),
	)

	for index, result in enumerate(results):
		row, column = divmod(index, columns)
		x = margin + column * (cell_width + gap)
		y = header_height + row * (cell_height + gap)
		draw.rounded_rectangle(
			(x, y, x + cell_width, y + cell_height),
			radius=16,
			fill=(245, 247, 250),
			outline=(91, 109, 139),
			width=2,
		)
		config = result.config
		top = result.top_candidate
		detection = top.detection if top else None
		score = result.scores[0] if result.scores else None
		draw.text(
			(x + 22, y + 16),
			f"Experiment {result.number:03d}",
			font=card_title_font,
			fill=(27, 38, 57),
		)
		draw.text(
			(x + 22, y + 51),
			f"threshold {config.threshold:.2f} · min {config.min_width}x{config.min_height} · max {config.max_candidates}",
			font=card_font,
			fill=(67, 80, 103),
		)

		image_left = x + 22
		image_top = y + 164
		image_width = cell_width - 44
		image_height = cell_height - 186
		draw.rounded_rectangle(
			(image_left, image_top, image_left + image_width, image_top + image_height),
			radius=10,
			fill=(38, 46, 62),
		)

		if detection and score:
			draw.text(
				(x + 22, y + 78),
				f"raw {score.raw_template_score:.3f} · breeder-likeness {score.breeder_likeness_score:.3f} · penalty {score.negative_similarity_penalty:.3f}",
				font=card_font,
				fill=(38, 113, 89) if score.breeder_likeness_score >= 0.50 else (164, 74, 65),
			)
			draw.text(
				(x + 22, y + 104),
				f"color {score.color_score:.3f} · edge {score.edge_score:.3f} · shape {score.shape_or_mask_score:.3f} · context {score.local_context_score:.3f}",
				font=card_small_font,
				fill=(67, 80, 103),
			)
			draw.text(
				(x + 22, y + 125),
				f"{detection.template_name} · box ({detection.box.x}, {detection.box.y}, {detection.box.w}, {detection.box.h})",
				font=card_small_font,
				fill=(67, 80, 103),
			)
			crop_path = result.contexts[0].boxed_path
			with Image.open(crop_path) as crop_file:
				crop = crop_file.convert("RGB")
				crop.thumbnail((image_width - 28, image_height - 28), Image.Resampling.LANCZOS)
				paste_x = image_left + (image_width - crop.width) // 2
				paste_y = image_top + (image_height - crop.height) // 2
				sheet.paste(crop, (paste_x, paste_y))
		else:
			draw.text(
				(x + 22, y + 78),
				f"{config.template_set.name} · {config.template_set.flags}",
				font=card_font,
				fill=(120, 82, 75),
			)
			label = "NO CANDIDATE"
			label_box = draw.textbbox((0, 0), label, font=no_candidate_font)
			label_width = label_box[2] - label_box[0]
			label_height = label_box[3] - label_box[1]
			draw.text(
				(
					image_left + (image_width - label_width) // 2,
					image_top + (image_height - label_height) // 2,
				),
				label,
				font=no_candidate_font,
				fill=(196, 204, 218),
			)

	path = args.out / "contact-sheet.png"
	sheet.save(path, optimize=True)
	return path


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Run a reviewable sweep of Breeding Structure detector configurations."
	)
	parser.add_argument("--source", required=True, type=Path, help="Source island screenshot")
	parser.add_argument("--island", required=True, help="Island name")
	parser.add_argument("--parents", required=True, nargs=2, metavar=("LEFT", "RIGHT"))
	parser.add_argument("--out", required=True, type=Path, help="Output experiment directory")
	parser.add_argument("--limit", type=int, help="Run only the first N balanced configurations")
	args = parser.parse_args()

	if args.limit is not None and args.limit < 1:
		parser.error("--limit must be at least 1")
	args.source = args.source if args.source.is_absolute() else REPO_ROOT / args.source
	args.out = args.out if args.out.is_absolute() else REPO_ROOT / args.out
	if not args.source.is_file():
		parser.error(f"--source is not a file: {args.source}")
	return args


def main() -> int:
	args = parse_args()
	all_configs = experiment_configs(args.island)
	configs = all_configs[: args.limit] if args.limit is not None else all_configs
	args.out.mkdir(parents=True, exist_ok=True)

	results = run_experiments(args, configs)
	clusters = cluster_candidate_boxes(results)
	annotation_path, annotation_data = write_annotation_file(args, clusters)
	summary_path = write_summary(args, results, len(all_configs), clusters, annotation_data)
	contact_sheet_path = draw_contact_sheet(args, results)
	print(f"Wrote {annotation_path.relative_to(REPO_ROOT)}")
	print(f"Wrote {summary_path.relative_to(REPO_ROOT)}")
	print(f"Wrote {contact_sheet_path.relative_to(REPO_ROOT)}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
