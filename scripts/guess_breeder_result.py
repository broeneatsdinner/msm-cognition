#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2
from PIL import Image, ImageChops, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[1]
BREEDING_DATA = REPO_ROOT / "reference" / "breeding" / "common-natural-breeding.json"
EGG_DIR = REPO_ROOT / "assets" / "eggs"
STRUCTURE_DIR = REPO_ROOT / "assets" / "structures" / "breeding-structure"

# These boxes are deliberately heuristic. They are relative positions within a
# detected Breeding Structure crop and preserve the current report workflow while
# the detector is still being tuned against real island screenshots.
LEFT_PARENT_EGG_REL = (0.20, 0.06, 0.22, 0.22)
RIGHT_PARENT_EGG_REL = (0.58, 0.06, 0.22, 0.22)

# TODO: Improve automatic Breeding Structure detection from evidence reports:
# 1. tune template scales and thresholds against full island screenshots
# 2. locate one or two Breeding Structure candidates in each screenshot
# 3. crop each candidate structure
# 4. crop top-left and top-right parent eggs inside each in-progress candidate
# 5. for finished structures, crop the bottom-center resulting egg
# 6. compare egg crops against assets/eggs/
# 7. run island-scoped breeding lookup for recognized parent pairs
# Manual crop mode remains as a fallback/debug path when detection misses.


@dataclass(frozen=True)
class CropBox:
	x: int
	y: int
	w: int
	h: int

	def as_pillow_box(self) -> tuple[int, int, int, int]:
		return (self.x, self.y, self.x + self.w, self.y + self.h)

	def as_report_text(self) -> str:
		return f"x={self.x}, y={self.y}, w={self.w}, h={self.h}"


@dataclass(frozen=True)
class RelativeCropBox:
	x: float
	y: float
	w: float
	h: float

	def as_report_text(self) -> str:
		return f"x={self.x:g}, y={self.y:g}, w={self.w:g}, h={self.h:g}"


@dataclass(frozen=True)
class DetectorCandidate:
	box: CropBox
	template_name: str
	match_score: float
	template_scale: float


@dataclass(frozen=True)
class CropArtifact:
	label: str
	box: CropBox
	path: Path
	upscaled_path: Path


@dataclass(frozen=True)
class ParentEvidence:
	side: str
	crop: CropArtifact
	relative_crop: RelativeCropBox | None
	crop_was_clamped: bool
	manual_parent: str | None
	manual_reference_path: Path | None
	auto_parent: str | None
	auto_matches: list[dict]

	@property
	def chosen_parent(self) -> str | None:
		return self.manual_parent or self.auto_parent

	@property
	def chosen_source(self) -> str:
		if self.manual_parent:
			return "manual_parent_recognition"
		if self.auto_parent:
			return "automated_egg_reference_match"
		return "unknown"


@dataclass(frozen=True)
class CandidateEvidence:
	index: int
	detection: DetectorCandidate | None
	breeder_crop: CropArtifact
	left_parent: ParentEvidence
	right_parent: ParentEvidence
	guesses: list[dict]


@dataclass(frozen=True)
class DetectorDebug:
	rejected_counts: dict[str, int]
	paironormal_templates_allowed: bool
	locked_templates_allowed: bool
	active_templates: list[str]
	min_width: int
	min_height: int
	threshold: float


def parse_crop(value: str) -> CropBox:
	parts = [part.strip() for part in value.split(",")]
	if len(parts) != 4:
		raise argparse.ArgumentTypeError("crop boxes must be x,y,w,h")
	try:
		x, y, w, h = [int(part) for part in parts]
	except ValueError as exc:
		raise argparse.ArgumentTypeError("crop box values must be integers") from exc

	if w <= 0 or h <= 0:
		raise argparse.ArgumentTypeError("crop width and height must be positive")

	return CropBox(x=x, y=y, w=w, h=h)


def parse_relative_crop(value: str) -> RelativeCropBox:
	parts = [part.strip() for part in value.split(",")]
	if len(parts) != 4:
		raise argparse.ArgumentTypeError("relative crop boxes must be x,y,w,h")
	try:
		x, y, w, h = [float(part) for part in parts]
	except ValueError as exc:
		raise argparse.ArgumentTypeError("relative crop box values must be floats") from exc

	if not 0.0 <= x <= 1.0:
		raise argparse.ArgumentTypeError("relative crop x must be between 0 and 1")
	if not 0.0 <= y <= 1.0:
		raise argparse.ArgumentTypeError("relative crop y must be between 0 and 1")
	if not 0.0 < w <= 1.0:
		raise argparse.ArgumentTypeError("relative crop w must be greater than 0 and no more than 1")
	if not 0.0 < h <= 1.0:
		raise argparse.ArgumentTypeError("relative crop h must be greater than 0 and no more than 1")

	return RelativeCropBox(x=x, y=y, w=w, h=h)


def normalize_name(value: str) -> str:
	return " ".join(value.strip().split()).lower()


def slugify(value: str) -> str:
	value = normalize_name(value)
	value = re.sub(r"[^a-z0-9]+", "-", value)
	return value.strip("-")


def load_breeding_data() -> dict:
	with BREEDING_DATA.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def canonical_island(data: dict, island: str) -> tuple[str, str | None]:
	normalized = normalize_name(island)

	for alias, original in data.get("mirror_aliases", {}).items():
		if normalize_name(alias) == normalized:
			return original, alias

	return island, None


def egg_name_from_path(path: Path) -> str:
	name = path.stem
	return name.removesuffix("-egg").replace("_", " ")


def egg_asset_for_monster(monster: str) -> Path | None:
	normalized = normalize_name(monster)

	for egg_path in sorted(EGG_DIR.glob("*-egg.*")):
		if normalize_name(egg_name_from_path(egg_path)) == normalized:
			return egg_path

	return None


def load_image(path: Path) -> Image.Image:
	return Image.open(path).convert("RGBA")


def crop_image(source: Image.Image, crop: CropBox) -> Image.Image:
	return source.crop(crop.as_pillow_box())


def save_png(image: Image.Image, path: Path) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	image.save(path)


def upscale(image: Image.Image, factor: int = 4) -> Image.Image:
	return image.resize((image.width * factor, image.height * factor), Image.Resampling.LANCZOS)


def fit_on_square(image: Image.Image, size: int = 128) -> Image.Image:
	"""
	Normalize images for crude visual comparison.

	This is intentionally simple. It is not a trained recognizer. It creates a
	square thumbnail on a neutral background so cropped eggs can be compared
	against transparent egg reference assets.
	"""
	background = Image.new("RGBA", (size, size), (116, 103, 137, 255))
	contained = ImageOps.contain(image, (size, size), Image.Resampling.LANCZOS)
	x = (size - contained.width) // 2
	y = (size - contained.height) // 2
	background.alpha_composite(contained, (x, y))
	return background.convert("RGB")


def rms_distance(a: Image.Image, b: Image.Image) -> float:
	diff = ImageChops.difference(a, b)
	histogram = diff.histogram()
	squares = (value * ((index % 256) ** 2) for index, value in enumerate(histogram))
	sum_of_squares = sum(squares)
	return math.sqrt(sum_of_squares / float(a.size[0] * a.size[1] * 3))


def score_from_rms(rms: float) -> float:
	# 0 is perfect. 441.67 is max RGB distance. This is a rough readability score.
	return max(0.0, min(100.0, 100.0 * (1.0 - (rms / 441.67295593))))


def compare_to_egg_assets(crop: Image.Image, top_n: int = 5) -> list[dict]:
	crop_norm = fit_on_square(crop)
	results: list[dict] = []

	for egg_path in sorted(EGG_DIR.glob("*-egg.*")):
		try:
			ref = load_image(egg_path)
		except Exception:
			continue

		ref_norm = fit_on_square(ref)
		rms = rms_distance(crop_norm, ref_norm)
		results.append(
			{
				"monster": egg_name_from_path(egg_path),
				"path": egg_path,
				"rms": rms,
				"score": score_from_rms(rms),
			}
		)

	return sorted(results, key=lambda item: item["rms"])[:top_n]


def unordered_pair_key(parents: list[str]) -> tuple[str, str]:
	normalized = sorted(normalize_name(parent) for parent in parents)
	return (normalized[0], normalized[1])


def guess_results(data: dict, island: str, parents: list[str]) -> list[dict]:
	canonical, alias = canonical_island(data, island)
	parent_key = unordered_pair_key(parents)
	results: list[dict] = []

	for monster, record in data.get("monsters", {}).items():
		record_islands = [normalize_name(item) for item in record.get("islands", [])]
		if normalize_name(canonical) not in record_islands:
			continue

		if unordered_pair_key(record.get("parents", [])) == parent_key:
			results.append(
				{
					"monster": monster,
					"record": record,
					"canonical_island": canonical,
					"alias": alias,
				}
			)

	return results


def copy_reference_images(matches: list[dict], out_dir: Path, prefix: str) -> list[dict]:
	copied: list[dict] = []

	for index, match in enumerate(matches, start=1):
		source = match["path"]
		destination = out_dir / f"{prefix}-match-{index}-{slugify(match['monster'])}{source.suffix.lower()}"
		shutil.copy2(source, destination)
		copied.append({**match, "copied_path": destination})

	return copied


def copy_manual_reference_image(monster: str | None, out_dir: Path, prefix: str) -> Path | None:
	if not monster:
		return None

	source = egg_asset_for_monster(monster)
	if not source:
		return None

	destination = out_dir / f"{prefix}-manual-{slugify(monster)}{source.suffix.lower()}"
	shutil.copy2(source, destination)
	return destination


def md_rel(path: Path, base: Path) -> str:
	return path.relative_to(base).as_posix()


def relative_box(parent: CropBox, rel_box: RelativeCropBox) -> CropBox:
	return CropBox(
		x=parent.x + round(parent.w * rel_box.x),
		y=parent.y + round(parent.h * rel_box.y),
		w=max(1, round(parent.w * rel_box.w)),
		h=max(1, round(parent.h * rel_box.h)),
	)


def clamp_box(box: CropBox, image: Image.Image) -> CropBox:
	x = max(0, min(box.x, image.width - 1))
	y = max(0, min(box.y, image.height - 1))
	right = max(x + 1, min(box.x + box.w, image.width))
	bottom = max(y + 1, min(box.y + box.h, image.height))
	return CropBox(x=x, y=y, w=right - x, h=bottom - y)


def box_iou(a: CropBox, b: CropBox) -> float:
	a_right = a.x + a.w
	a_bottom = a.y + a.h
	b_right = b.x + b.w
	b_bottom = b.y + b.h
	x1 = max(a.x, b.x)
	y1 = max(a.y, b.y)
	x2 = min(a_right, b_right)
	y2 = min(a_bottom, b_bottom)

	if x2 <= x1 or y2 <= y1:
		return 0.0

	intersection = (x2 - x1) * (y2 - y1)
	union = (a.w * a.h) + (b.w * b.h) - intersection
	return intersection / union if union else 0.0


def template_scales(template_shape: tuple[int, int], source_shape: tuple[int, int]) -> list[float]:
	template_h, template_w = template_shape
	source_h, source_w = source_shape
	base_scales = [0.08, 0.10, 0.125, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.65, 0.80, 1.00]
	scales: set[float] = set()

	for scale in base_scales:
		if template_w * scale <= source_w and template_h * scale <= source_h:
			scales.add(scale)

	max_fit = min(source_w / template_w, source_h / template_h)
	for factor in (0.25, 0.33, 0.50, 0.67, 0.80):
		scale = max_fit * factor
		if 0.03 <= scale <= 1.25:
			scales.add(round(scale, 4))

	return sorted(scales)


def paironormal_templates_allowed(args: argparse.Namespace) -> bool:
	return args.allow_paironormal_templates or "paironormal" in normalize_name(args.island)


def detector_confidence_label(score: float) -> str:
	if score >= 0.90:
		return "high"
	if score >= 0.82:
		return "medium"
	return "low"


def template_allowed(template_name: str, allow_paironormal: bool, allow_locked: bool) -> tuple[bool, str | None]:
	is_paironormal = "paironormal" in template_name
	is_locked = "locked" in template_name

	if is_paironormal and not allow_paironormal:
		return False, "paironormal_template_excluded"
	if is_locked and not allow_locked:
		return False, "locked_template_excluded"

	return True, None


def detect_breeding_structures(
	source_path: Path,
	max_candidates: int,
	threshold: float,
	min_width: int,
	min_height: int,
	allow_paironormal_templates: bool,
	allow_locked_templates: bool,
	debug_candidates: bool,
) -> tuple[list[DetectorCandidate], list[DetectorCandidate], DetectorDebug]:
	source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
	if source is None:
		raise RuntimeError(f"Could not read source image with OpenCV: {source_path}")

	source_gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
	raw_candidates: list[DetectorCandidate] = []
	rejected_counts = {
		"paironormal_template_excluded": 0,
		"locked_template_excluded": 0,
		"below_min_size": 0,
		"below_threshold": 0,
	}
	active_templates: list[str] = []

	for template_path in sorted(STRUCTURE_DIR.glob("*.webp")):
		template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
		if template is None:
			continue

		template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
		scales = template_scales(template_gray.shape, source_gray.shape)
		allowed, rejected_reason = template_allowed(
			template_path.name,
			allow_paironormal=allow_paironormal_templates,
			allow_locked=allow_locked_templates,
		)
		if not allowed:
			assert rejected_reason is not None
			rejected_counts[rejected_reason] += len(scales)
			continue

		active_templates.append(template_path.name)
		for scale in scales:
			width = max(8, round(template_gray.shape[1] * scale))
			height = max(8, round(template_gray.shape[0] * scale))
			if width > source_gray.shape[1] or height > source_gray.shape[0]:
				continue
			if width < min_width or height < min_height:
				rejected_counts["below_min_size"] += 1
				continue

			resized = cv2.resize(template_gray, (width, height), interpolation=cv2.INTER_AREA)
			result = cv2.matchTemplate(source_gray, resized, cv2.TM_CCOEFF_NORMED)
			_, max_value, _, max_location = cv2.minMaxLoc(result)
			if max_value < threshold:
				rejected_counts["below_threshold"] += 1
				continue

			raw_candidates.append(
				DetectorCandidate(
					box=CropBox(x=max_location[0], y=max_location[1], w=width, h=height),
					template_name=template_path.name,
					match_score=float(max_value),
					template_scale=scale,
				)
			)

	raw_candidates.sort(key=lambda item: item.match_score, reverse=True)
	selected: list[DetectorCandidate] = []
	for candidate in raw_candidates:
		if all(box_iou(candidate.box, selected_candidate.box) < 0.35 for selected_candidate in selected):
			selected.append(candidate)
		if len(selected) >= max_candidates:
			break

	debug = raw_candidates[:25] if debug_candidates else []
	return selected, debug, DetectorDebug(
		rejected_counts=rejected_counts,
		paironormal_templates_allowed=allow_paironormal_templates,
		locked_templates_allowed=allow_locked_templates,
		active_templates=active_templates,
		min_width=min_width,
		min_height=min_height,
		threshold=threshold,
	)


def append_crop(lines: list[str], artifact: CropArtifact, out_dir: Path) -> None:
	lines.append(f"Crop coordinates: `{artifact.box.as_report_text()}`")
	lines.append("")
	lines.append(f"![{artifact.label}]({md_rel(artifact.path, out_dir)})")
	lines.append("")
	lines.append("Upscaled evidence crop:")
	lines.append("")
	lines.append(f"![{artifact.label} 4x]({md_rel(artifact.upscaled_path, out_dir)})")


def append_parent_evidence(lines: list[str], parent: ParentEvidence, out_dir: Path) -> None:
	lines.append(f"### {parent.side.title()} parent egg crop")
	lines.append("")
	if parent.relative_crop:
		lines.append(f"Relative crop inside detected Breeding Structure: `{parent.relative_crop.as_report_text()}`")
		lines.append("")
		lines.append(f"Resulting absolute crop box: `{parent.crop.box.as_report_text()}`")
		lines.append("")
		if parent.crop_was_clamped:
			lines.append("Crop clamping: **yes**")
		else:
			lines.append("Crop clamping: **no**")
		lines.append("")
	append_crop(lines, parent.crop, out_dir)
	lines.append("")
	lines.append(f"Manual parent: **{parent.manual_parent or 'not supplied'}**  ")
	if parent.manual_reference_path:
		lines.append("")
		lines.append("Manual parent reference egg:")
		lines.append("")
		lines.append(f"![{parent.manual_parent}]({md_rel(parent.manual_reference_path, out_dir)})")
	elif parent.manual_parent:
		lines.append("")
		lines.append(f"Manual parent reference egg: **missing from `{EGG_DIR.relative_to(REPO_ROOT)}`**")
	lines.append("")
	lines.append(f"Top automated match: **{parent.auto_parent or 'unknown'}**")
	lines.append("")
	lines.append("Automated egg-reference matches:")
	lines.append("")
	lines.append("| Rank | Monster | Score | RMS | Reference |")
	lines.append("|---:|---|---:|---:|---|")
	for index, match in enumerate(parent.auto_matches, start=1):
		lines.append(
			f"| {index} | {match['monster']} | {match['score']:.1f} | {match['rms']:.2f} | "
			f"![{match['monster']}]({md_rel(match['copied_path'], out_dir)}) |"
		)


def parent_disagrees(parent: ParentEvidence) -> bool:
	if not parent.manual_parent or not parent.auto_parent:
		return False
	return normalize_name(parent.manual_parent) != normalize_name(parent.auto_parent)


def append_warning_notes(lines: list[str], candidate: CandidateEvidence) -> None:
	manual_supplied = bool(candidate.left_parent.manual_parent or candidate.right_parent.manual_parent)
	manual_used = (
		candidate.left_parent.chosen_source == "manual_parent_recognition"
		or candidate.right_parent.chosen_source == "manual_parent_recognition"
	)
	low_detector_confidence = (
		candidate.detection is not None
		and detector_confidence_label(candidate.detection.match_score) == "low"
	)
	disagreements = [
		parent.side
		for parent in (candidate.left_parent, candidate.right_parent)
		if parent_disagrees(parent)
	]

	if not manual_supplied and not manual_used and not low_detector_confidence and not disagreements:
		return

	lines.append("### Warnings")
	lines.append("")
	if low_detector_confidence:
		lines.append("- The Breeding Structure detector confidence is low; candidate crop requires manual review.")
	if manual_supplied:
		lines.append("- Manual `--parents` were supplied for this candidate.")
	if manual_used:
		lines.append("- The final guess depends on manual parent recognition.")
	for side in disagreements:
		parent = candidate.left_parent if side == "left" else candidate.right_parent
		lines.append(
			f"- The {side} automated egg-reference match disagrees with manual recognition: "
			f"manual `{parent.manual_parent}`, automated `{parent.auto_parent}`."
		)
	lines.append("")


def append_lookup_and_guess(
	lines: list[str],
	args: argparse.Namespace,
	data: dict,
	left_parent: ParentEvidence,
	right_parent: ParentEvidence,
	guesses: list[dict],
) -> None:
	canonical, alias = canonical_island(data, args.island)

	lines.append("## Structured breeding lookup")
	lines.append("")
	lines.append("```text")
	lines.append(f"Island: {args.island}")
	if alias:
		lines.append(f"Alias: {alias} -> {canonical}")
	lines.append(f"Parents used: {left_parent.chosen_parent or 'unknown'} + {right_parent.chosen_parent or 'unknown'}")
	lines.append(f"Left parent source: {left_parent.chosen_source}")
	lines.append(f"Right parent source: {right_parent.chosen_source}")
	lines.append("```")
	lines.append("")
	lines.append("## Final guess")
	lines.append("")

	if not left_parent.chosen_parent or not right_parent.chosen_parent:
		lines.append("Likely result: **unknown**")
		lines.append("")
		lines.append("Confidence: **manual_review**")
		lines.append("")
		lines.append("Reason:")
		lines.append("")
		lines.append("- One or both parent eggs could not be recognized.")
	elif not guesses:
		lines.append("Likely result: **no match in current breeding data**")
		lines.append("")
		lines.append("Confidence: **manual_review**")
		lines.append("")
		lines.append("Reason:")
		lines.append("")
		lines.append("- The parent pair was recognized, but no island-scoped result matched the current structured breeding data.")
		lines.append("- This may mean the data is incomplete, the crop was misread, or the monster is outside the current data scope.")
	elif len(guesses) == 1:
		guess = guesses[0]
		record = guess["record"]
		lines.append(f"Likely result: **{guess['monster']}**")
		lines.append("")
		confidence = (
			"high"
			if left_parent.chosen_source == "manual_parent_recognition"
			and right_parent.chosen_source == "manual_parent_recognition"
			else "medium"
		)
		lines.append(f"Confidence: **{confidence}**")
		lines.append("")
		lines.append("Reason:")
		lines.append("")
		if alias:
			lines.append(f"- {alias} aliases to {canonical}.")
		lines.append(f"- {guess['monster']} is listed for {canonical}.")
		lines.append(f"- {guess['monster']}'s listed parent pair is {' + '.join(record['parents'])}.")
		lines.append(f"- Standard time: {record['time']}.")
		lines.append(f"- Enhanced time: {record['enhanced_time']}.")
	else:
		lines.append("Likely result: **multiple matches**")
		lines.append("")
		lines.append("Confidence: **manual_review**")
		lines.append("")
		lines.append("Possible results:")
		lines.append("")
		for guess in guesses:
			lines.append(f"- {guess['monster']}")


def write_report(
	report_path: Path,
	args: argparse.Namespace,
	source_copy: Path,
	candidates: list[CandidateEvidence],
	data: dict,
	debug_candidates: list[DetectorCandidate],
	detector_debug: DetectorDebug,
) -> None:
	out_dir = report_path.parent
	canonical, alias = canonical_island(data, args.island)

	lines: list[str] = []
	lines.append("# Breeder Result Guess")
	lines.append("")
	lines.append("## Source")
	lines.append("")
	lines.append(f"Island: **{args.island}**  ")
	if alias:
		lines.append(f"Island alias: **{alias} -> {canonical}**  ")
	lines.append(f"Detection mode: **{args.mode}**  ")
	lines.append("")
	lines.append(f"Source image: `{args.source}`")
	lines.append("")
	lines.append(f"![Source screenshot]({md_rel(source_copy, out_dir)})")
	lines.append("")
	lines.append("## Detector candidates")
	lines.append("")
	if args.mode == "manual-crops":
		lines.append("Manual/debug crop mode uses the provided crop boxes instead of OpenCV detector candidates.")
	else:
		lines.append(
			f"Active filters: locked templates "
			f"{'allowed' if detector_debug.locked_templates_allowed else 'excluded'}, Paironormal templates "
			f"{'allowed' if detector_debug.paironormal_templates_allowed else 'excluded'}, "
			f"minimum size `{detector_debug.min_width}x{detector_debug.min_height}`, "
			f"match threshold `{detector_debug.threshold:.3f}`."
		)
		lines.append("")
		lines.append(f"Active templates: `{', '.join(detector_debug.active_templates) or 'none'}`")
		lines.append("")
		lines.append("Rejected detector checks:")
		lines.append("")
		lines.append("| Reason | Count |")
		lines.append("|---|---:|")
		for reason in ("paironormal_template_excluded", "locked_template_excluded", "below_min_size", "below_threshold"):
			lines.append(f"| {reason} | {detector_debug.rejected_counts.get(reason, 0)} |")
		lines.append("")
		if not candidates:
			lines.append("No Breeding Structure candidates met the current template filters, size guards, and threshold.")
		else:
			lines.append("| Candidate | Template | Match score | Detector confidence | Template scale | Bounding box |")
			lines.append("|---:|---|---:|---|---:|---|")
			for candidate in candidates:
				detection = candidate.detection
				if detection:
					lines.append(
						f"| {candidate.index} | {detection.template_name} | {detection.match_score:.3f} | "
						f"{detector_confidence_label(detection.match_score)} | {detection.template_scale:.4g} | "
						f"`{detection.box.as_report_text()}` |"
					)
	if debug_candidates:
		lines.append("")
		lines.append("Debug candidate shortlist:")
		lines.append("")
		lines.append("| Rank | Template | Match score | Template scale | Bounding box |")
		lines.append("|---:|---|---:|---:|---|")
		for index, candidate in enumerate(debug_candidates, start=1):
			lines.append(
				f"| {index} | {candidate.template_name} | {candidate.match_score:.3f} | "
				f"{candidate.template_scale:.4g} | `{candidate.box.as_report_text()}` |"
			)
	lines.append("")
	lines.append("## Recognition notes")
	lines.append("")
	lines.append("- When a Breeding Structure is in progress, the top-left and top-right eggs are the parent eggs.")
	lines.append("- When a Breeding Structure is finished, the bottom-center egg is the resulting egg.")
	lines.append("- Parent egg crop regions are currently heuristic and should be tuned from confirmed training examples.")
	lines.append("- Automated egg-reference matching is a simple helper, not a trained recognizer and not authoritative.")
	lines.append("- Manual parent recognition, when supplied, is displayed separately from automated matches.")
	lines.append("")

	for candidate in candidates:
		lines.append(f"## Candidate {candidate.index}")
		lines.append("")
		if candidate.detection:
			lines.append(
				f"Detector: `{candidate.detection.template_name}`, score `{candidate.detection.match_score:.3f}`, "
				f"confidence `{detector_confidence_label(candidate.detection.match_score)}`, "
				f"scale `{candidate.detection.template_scale:.4g}`"
			)
			lines.append("")
		append_warning_notes(lines, candidate)
		lines.append("### Breeding Structure crop")
		lines.append("")
		append_crop(lines, candidate.breeder_crop, out_dir)
		lines.append("")
		lines.append("## Manual parent recognition")
		lines.append("")
		lines.append("Manual parent recognition comes only from `--parents LEFT RIGHT` and currently applies to candidate 1 only.")
		lines.append("")
		lines.append(f"Left manual parent: **{candidate.left_parent.manual_parent or 'not supplied'}**  ")
		lines.append(f"Right manual parent: **{candidate.right_parent.manual_parent or 'not supplied'}**")
		lines.append("")
		lines.append("## Automated egg-reference matches")
		lines.append("")
		lines.append("Automated matching is non-authoritative evidence for review.")
		lines.append("")
		lines.append(f"Left automated parent: **{candidate.left_parent.auto_parent or 'unknown'}**  ")
		lines.append(f"Right automated parent: **{candidate.right_parent.auto_parent or 'unknown'}**")
		lines.append("")
		lines.append("### Parent egg evidence")
		lines.append("")
		if args.mode == "detect-breeders":
			lines.append(f"Left parent relative crop setting: `{args.left_parent_rel.as_report_text()}`  ")
			lines.append(f"Right parent relative crop setting: `{args.right_parent_rel.as_report_text()}`")
			lines.append("")
		append_parent_evidence(lines, candidate.left_parent, out_dir)
		lines.append("")
		append_parent_evidence(lines, candidate.right_parent, out_dir)
		lines.append("")
		append_lookup_and_guess(lines, args, data, candidate.left_parent, candidate.right_parent, candidate.guesses)
		lines.append("")

	lines.append("## Training review")
	lines.append("")
	lines.append("Suggested `detector_classification` values: `confirmed_positive`, `false_positive`, `missed_detection`, `parent_crop_incorrect`, `parent_crop_correct`, `unresolved`.")
	lines.append("")
	lines.append("```yaml")
	lines.append("training_review:")
	lines.append("  status: unresolved")
	lines.append("  detector_candidate_correct: null")
	lines.append("  detector_classification: null")
	lines.append("  breeder_box_correction: null")
	lines.append("  left_parent_crop_correct: null")
	lines.append("  left_parent_box_correction: null")
	lines.append("  right_parent_crop_correct: null")
	lines.append("  right_parent_box_correction: null")
	lines.append("  confirmed_left_parent: null")
	lines.append("  confirmed_right_parent: null")
	lines.append("  confirmed_result: null")
	lines.append("  notes: null")
	lines.append("```")
	lines.append("")

	report_path.write_text("\n".join(lines), encoding="utf-8")


def build_candidate_evidence(
	source_image: Image.Image,
	out_dir: Path,
	data: dict,
	args: argparse.Namespace,
	index: int,
	breeder_box: CropBox,
	detection: DetectorCandidate | None,
	manual_parents: tuple[str | None, str | None],
) -> CandidateEvidence:
	prefix = f"candidate-{index}"
	breeder_box = clamp_box(breeder_box, source_image)
	left_unclamped_box = relative_box(breeder_box, args.left_parent_rel)
	right_unclamped_box = relative_box(breeder_box, args.right_parent_rel)
	left_box = clamp_box(left_unclamped_box, source_image)
	right_box = clamp_box(right_unclamped_box, source_image)

	breeder = crop_image(source_image, breeder_box)
	left = crop_image(source_image, left_box)
	right = crop_image(source_image, right_box)

	breeder_path = out_dir / f"{prefix}-crop-breeder.png"
	breeder_4x_path = out_dir / f"{prefix}-crop-breeder-4x.png"
	left_path = out_dir / f"{prefix}-crop-left-parent-egg.png"
	left_4x_path = out_dir / f"{prefix}-crop-left-parent-egg-4x.png"
	right_path = out_dir / f"{prefix}-crop-right-parent-egg.png"
	right_4x_path = out_dir / f"{prefix}-crop-right-parent-egg-4x.png"

	save_png(breeder, breeder_path)
	save_png(upscale(breeder), breeder_4x_path)
	save_png(left, left_path)
	save_png(upscale(left), left_4x_path)
	save_png(right, right_path)
	save_png(upscale(right), right_4x_path)

	left_matches = copy_reference_images(
		compare_to_egg_assets(left, top_n=args.top_matches),
		out_dir,
		f"{prefix}-reference-left",
	)
	right_matches = copy_reference_images(
		compare_to_egg_assets(right, top_n=args.top_matches),
		out_dir,
		f"{prefix}-reference-right",
	)

	left_manual, right_manual = manual_parents
	breeder_artifact = CropArtifact(
		label=f"Candidate {index} Breeding Structure crop",
		box=breeder_box,
		path=breeder_path,
		upscaled_path=breeder_4x_path,
	)
	left_artifact = CropArtifact(
		label=f"Candidate {index} left parent egg crop",
		box=left_box,
		path=left_path,
		upscaled_path=left_4x_path,
	)
	right_artifact = CropArtifact(
		label=f"Candidate {index} right parent egg crop",
		box=right_box,
		path=right_path,
		upscaled_path=right_4x_path,
	)

	left_parent = ParentEvidence(
		side="left",
		crop=left_artifact,
		relative_crop=args.left_parent_rel,
		crop_was_clamped=left_box != left_unclamped_box,
		manual_parent=left_manual,
		manual_reference_path=copy_manual_reference_image(left_manual, out_dir, f"{prefix}-left"),
		auto_parent=left_matches[0]["monster"] if left_matches else None,
		auto_matches=left_matches,
	)
	right_parent = ParentEvidence(
		side="right",
		crop=right_artifact,
		relative_crop=args.right_parent_rel,
		crop_was_clamped=right_box != right_unclamped_box,
		manual_parent=right_manual,
		manual_reference_path=copy_manual_reference_image(right_manual, out_dir, f"{prefix}-right"),
		auto_parent=right_matches[0]["monster"] if right_matches else None,
		auto_matches=right_matches,
	)

	guesses: list[dict] = []
	if left_parent.chosen_parent and right_parent.chosen_parent:
		guesses = guess_results(data, args.island, [left_parent.chosen_parent, right_parent.chosen_parent])

	return CandidateEvidence(
		index=index,
		detection=detection,
		breeder_crop=breeder_artifact,
		left_parent=left_parent,
		right_parent=right_parent,
		guesses=guesses,
	)


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
	if args.max_candidates < 1:
		parser.error("--max-candidates must be at least 1")
	if not 0.0 <= args.structure_match_threshold <= 1.0:
		parser.error("--structure-match-threshold must be between 0 and 1")
	if args.structure_min_width < 1:
		parser.error("--structure-min-width must be at least 1")
	if args.structure_min_height < 1:
		parser.error("--structure-min-height must be at least 1")

	if args.mode == "manual-crops":
		missing = [
			name
			for name, value in (
				("--crop-breeder", args.crop_breeder),
				("--crop-left-egg", args.crop_left_egg),
				("--crop-right-egg", args.crop_right_egg),
			)
			if value is None
		]
		if missing:
			parser.error(f"--mode manual-crops requires {', '.join(missing)}")


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Generate a Markdown evidence report for an MSM breeder result."
	)
	parser.add_argument(
		"--mode",
		choices=("manual-crops", "detect-breeders"),
		default="manual-crops",
		help="Use manual/debug crop boxes or detect Breeding Structure candidates from the full screenshot.",
	)
	parser.add_argument("--source", required=True, type=Path, help="Source island screenshot")
	parser.add_argument("--island", required=True, help="Island name")
	parser.add_argument("--crop-breeder", type=parse_crop, help="Manual mode breeder crop as x,y,w,h")
	parser.add_argument("--crop-left-egg", type=parse_crop, help="Manual mode left parent egg crop as x,y,w,h")
	parser.add_argument("--crop-right-egg", type=parse_crop, help="Manual mode right parent egg crop as x,y,w,h")
	parser.add_argument(
		"--left-parent-rel",
		type=parse_relative_crop,
		default=RelativeCropBox(*LEFT_PARENT_EGG_REL),
		help="Detected mode left parent egg crop as relative x,y,w,h inside the Breeding Structure candidate",
	)
	parser.add_argument(
		"--right-parent-rel",
		type=parse_relative_crop,
		default=RelativeCropBox(*RIGHT_PARENT_EGG_REL),
		help="Detected mode right parent egg crop as relative x,y,w,h inside the Breeding Structure candidate",
	)
	parser.add_argument("--parents", nargs=2, metavar=("LEFT", "RIGHT"), help="Optional manual parent names for candidate 1")
	parser.add_argument("--out", required=True, type=Path, help="Output evidence directory")
	parser.add_argument("--top-matches", type=int, default=5, help="Number of egg reference matches to show")
	parser.add_argument("--max-candidates", type=int, default=2, help="Maximum Breeding Structure candidates to report")
	parser.add_argument(
		"--structure-match-threshold",
		type=float,
		default=0.80,
		help="OpenCV template-match threshold for Breeding Structure candidates",
	)
	parser.add_argument(
		"--structure-min-width",
		type=int,
		default=120,
		help="Reject scaled Breeding Structure candidates narrower than this many pixels",
	)
	parser.add_argument(
		"--structure-min-height",
		type=int,
		default=120,
		help="Reject scaled Breeding Structure candidates shorter than this many pixels",
	)
	parser.add_argument(
		"--allow-paironormal-templates",
		action="store_true",
		help="Allow Paironormal Breeding Structure templates on non-Paironormal islands",
	)
	parser.add_argument(
		"--allow-locked-templates",
		action="store_true",
		help="Allow locked Breeding Structure templates",
	)
	parser.add_argument(
		"--debug-candidates",
		action="store_true",
		help="Include the raw detector shortlist in the Markdown report",
	)
	args = parser.parse_args()
	validate_args(parser, args)

	source_path = args.source
	if not source_path.is_absolute():
		source_path = REPO_ROOT / source_path

	out_dir = args.out
	if not out_dir.is_absolute():
		out_dir = REPO_ROOT / out_dir
	out_dir.mkdir(parents=True, exist_ok=True)

	data = load_breeding_data()
	source_image = load_image(source_path)

	source_copy = out_dir / "source.png"
	shutil.copy2(source_path, source_copy)

	left_manual = args.parents[0] if args.parents else None
	right_manual = args.parents[1] if args.parents else None

	candidates: list[CandidateEvidence] = []
	debug_candidates: list[DetectorCandidate] = []
	detector_debug = DetectorDebug(
		rejected_counts={
			"paironormal_template_excluded": 0,
			"locked_template_excluded": 0,
			"below_min_size": 0,
			"below_threshold": 0,
		},
		paironormal_templates_allowed=paironormal_templates_allowed(args),
		locked_templates_allowed=args.allow_locked_templates,
		active_templates=[],
		min_width=args.structure_min_width,
		min_height=args.structure_min_height,
		threshold=args.structure_match_threshold,
	)
	if args.mode == "manual-crops":
		assert args.crop_breeder is not None
		assert args.crop_left_egg is not None
		assert args.crop_right_egg is not None
		manual_detection = DetectorCandidate(
			box=args.crop_breeder,
			template_name="manual-crops",
			match_score=1.0,
			template_scale=1.0,
		)
		candidates.append(
			build_candidate_evidence_from_boxes(
				source_image=source_image,
				out_dir=out_dir,
				data=data,
				args=args,
				index=1,
				breeder_box=args.crop_breeder,
				left_box=args.crop_left_egg,
				right_box=args.crop_right_egg,
				detection=manual_detection,
				manual_parents=(left_manual, right_manual),
			)
		)
	else:
		detected, debug_candidates, detector_debug = detect_breeding_structures(
			source_path=source_path,
			max_candidates=args.max_candidates,
			threshold=args.structure_match_threshold,
			min_width=args.structure_min_width,
			min_height=args.structure_min_height,
			allow_paironormal_templates=paironormal_templates_allowed(args),
			allow_locked_templates=args.allow_locked_templates,
			debug_candidates=args.debug_candidates,
		)
		for index, detection in enumerate(detected, start=1):
			manual_parents = (left_manual, right_manual) if index == 1 else (None, None)
			candidates.append(
				build_candidate_evidence(
					source_image=source_image,
					out_dir=out_dir,
					data=data,
					args=args,
					index=index,
					breeder_box=detection.box,
					detection=detection,
					manual_parents=manual_parents,
				)
			)

	report_path = out_dir / "report.md"
	write_report(
		report_path=report_path,
		args=args,
		source_copy=source_copy,
		candidates=candidates,
		data=data,
		debug_candidates=debug_candidates,
		detector_debug=detector_debug,
	)

	print(f"Wrote {report_path.relative_to(REPO_ROOT)}")
	if not candidates:
		print("Detected candidates: 0")
	for candidate in candidates:
		if candidate.guesses:
			for guess in candidate.guesses:
				print(f"Candidate {candidate.index} likely result: {guess['monster']}")
		else:
			print(f"Candidate {candidate.index} likely result: <no match or manual review>")

	return 0


def build_candidate_evidence_from_boxes(
	source_image: Image.Image,
	out_dir: Path,
	data: dict,
	args: argparse.Namespace,
	index: int,
	breeder_box: CropBox,
	left_box: CropBox,
	right_box: CropBox,
	detection: DetectorCandidate | None,
	manual_parents: tuple[str | None, str | None],
) -> CandidateEvidence:
	prefix = f"candidate-{index}"
	breeder_box = clamp_box(breeder_box, source_image)
	left_unclamped_box = left_box
	right_unclamped_box = right_box
	left_box = clamp_box(left_unclamped_box, source_image)
	right_box = clamp_box(right_unclamped_box, source_image)

	breeder = crop_image(source_image, breeder_box)
	left = crop_image(source_image, left_box)
	right = crop_image(source_image, right_box)

	breeder_path = out_dir / f"{prefix}-crop-breeder.png"
	breeder_4x_path = out_dir / f"{prefix}-crop-breeder-4x.png"
	left_path = out_dir / f"{prefix}-crop-left-parent-egg.png"
	left_4x_path = out_dir / f"{prefix}-crop-left-parent-egg-4x.png"
	right_path = out_dir / f"{prefix}-crop-right-parent-egg.png"
	right_4x_path = out_dir / f"{prefix}-crop-right-parent-egg-4x.png"

	save_png(breeder, breeder_path)
	save_png(upscale(breeder), breeder_4x_path)
	save_png(left, left_path)
	save_png(upscale(left), left_4x_path)
	save_png(right, right_path)
	save_png(upscale(right), right_4x_path)

	left_matches = copy_reference_images(
		compare_to_egg_assets(left, top_n=args.top_matches),
		out_dir,
		f"{prefix}-reference-left",
	)
	right_matches = copy_reference_images(
		compare_to_egg_assets(right, top_n=args.top_matches),
		out_dir,
		f"{prefix}-reference-right",
	)

	left_manual, right_manual = manual_parents
	left_parent = ParentEvidence(
		side="left",
		crop=CropArtifact(
			label=f"Candidate {index} left parent egg crop",
			box=left_box,
			path=left_path,
			upscaled_path=left_4x_path,
		),
		relative_crop=None,
		crop_was_clamped=left_box != left_unclamped_box,
		manual_parent=left_manual,
		manual_reference_path=copy_manual_reference_image(left_manual, out_dir, f"{prefix}-left"),
		auto_parent=left_matches[0]["monster"] if left_matches else None,
		auto_matches=left_matches,
	)
	right_parent = ParentEvidence(
		side="right",
		crop=CropArtifact(
			label=f"Candidate {index} right parent egg crop",
			box=right_box,
			path=right_path,
			upscaled_path=right_4x_path,
		),
		relative_crop=None,
		crop_was_clamped=right_box != right_unclamped_box,
		manual_parent=right_manual,
		manual_reference_path=copy_manual_reference_image(right_manual, out_dir, f"{prefix}-right"),
		auto_parent=right_matches[0]["monster"] if right_matches else None,
		auto_matches=right_matches,
	)

	guesses: list[dict] = []
	if left_parent.chosen_parent and right_parent.chosen_parent:
		guesses = guess_results(data, args.island, [left_parent.chosen_parent, right_parent.chosen_parent])

	return CandidateEvidence(
		index=index,
		detection=detection,
		breeder_crop=CropArtifact(
			label=f"Candidate {index} Breeding Structure crop",
			box=breeder_box,
			path=breeder_path,
			upscaled_path=breeder_4x_path,
		),
		left_parent=left_parent,
		right_parent=right_parent,
		guesses=guesses,
	)


if __name__ == "__main__":
	raise SystemExit(main())
