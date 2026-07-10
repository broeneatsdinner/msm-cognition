#!/usr/bin/env python3

from __future__ import annotations

import argparse
import itertools
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import guess_breeder_result as breeder


REPO_ROOT = Path(__file__).resolve().parents[1]
STRUCTURE_THRESHOLDS = (0.68, 0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.82)
MIN_SIZES = ((96, 96), (112, 112), (120, 120), (132, 132), (144, 144))
MAX_CANDIDATES = (1, 2, 3)


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


def append_contexts_to_report(report_path: Path, contexts: list[CandidateContext]) -> None:
	if not contexts:
		return
	lines = [
		"",
		"## Candidate source context",
		"",
		"These wider screenshot crops show where each isolated detector crop came from. The yellow rectangle is the exact candidate box.",
		"",
	]
	for context in contexts:
		lines.extend(
			[
				f"### Candidate {context.candidate_index} context",
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
	results: list[ExperimentResult] = []
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
		append_contexts_to_report(report_path, candidate_contexts)
		results.append(
			ExperimentResult(
				number=number,
				config=config,
				out_dir=experiment_dir,
				candidates=candidate_evidence,
				contexts=candidate_contexts,
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
		for candidate, context in zip(result.candidates, result.contexts, strict=True):
			if candidate.detection is None:
				continue
			observation = CandidateObservation(
				experiment_number=result.number,
				candidate_index=candidate.index,
				detection=candidate.detection,
				boxed_context_path=context.boxed_path,
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
		"## Candidate box clusters",
		"",
		"Candidate boxes are grouped when their intersection-over-union is at least 0.85. Repeated detections at one location are one review target, not independent evidence that the detection is correct.",
		"",
		"| Cluster | Representative box | Occurrences | Experiments | Score range | Templates | Annotation | Status | Example context |",
		"|---:|---|---:|---|---|---|---|---|---|",
	]
	for cluster in clusters:
		box = cluster.representative_box
		annotation = annotation_for_box(annotations, box) or {}
		scores = [observation.detection.match_score for observation in cluster.observations]
		templates = sorted({observation.detection.template_name for observation in cluster.observations})
		experiments = sorted({observation.experiment_number for observation in cluster.observations})
		example = cluster.observations[0]
		lines.append(
			f"| {cluster.number} | `{box.as_report_text()}` | {len(cluster.observations)} | "
			f"{', '.join(f'{number:03d}' for number in experiments)} | "
			f"{min(scores):.3f}–{max(scores):.3f} | {', '.join(templates)} | "
			f"{annotation.get('label', 'unannotated')} | {annotation.get('status', 'needs_review')} | "
			f"{markdown_link('boxed context', example.boxed_context_path, args.out)} |"
		)
	lines.extend(
		[
			"",
			"## Experiments",
			"",
		"| Experiment | Threshold | Min size | Template set | Template flags | Max candidates | Candidates | Top score | Top template | Top box | No candidates | Evidence |",
		"|---:|---:|---:|---|---|---:|---:|---:|---|---|---|---|",
		]
	)
	for result in results:
		config = result.config
		top = result.top_candidate
		detection = top.detection if top else None
		experiment_link = markdown_link(
			f"{result.number:03d}",
			result.out_dir / "report.md",
			args.out,
		)
		lines.append(
			f"| {experiment_link} | {config.threshold:.2f} | {config.min_width}x{config.min_height} | "
			f"{config.template_set.name} | `{config.template_set.flags}` | {config.max_candidates} | "
			f"{len(result.candidates)} | "
			f"{f'{detection.match_score:.3f}' if detection else '—'} | "
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
	cell_height = 450
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
		image_top = y + 112
		image_width = cell_width - 44
		image_height = cell_height - 134
		draw.rounded_rectangle(
			(image_left, image_top, image_left + image_width, image_top + image_height),
			radius=10,
			fill=(38, 46, 62),
		)

		if detection:
			draw.text(
				(x + 22, y + 78),
				f"{detection.match_score:.3f} · {detection.template_name} · ({detection.box.x}, {detection.box.y}, {detection.box.w}, {detection.box.h})",
				font=card_font,
				fill=(38, 113, 89),
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
