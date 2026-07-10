#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[1]
BREEDING_DATA = REPO_ROOT / "reference" / "breeding" / "common-natural-breeding.json"
EGG_DIR = REPO_ROOT / "assets" / "eggs"


# TODO: Future automatic Breeding Structure detection should work from the full
# island screenshot instead of fixed crop boxes:
# 1. locate one or two Breeding Structure candidates in the screenshot
# 2. crop each candidate structure
# 3. crop top-left and top-right parent eggs inside each in-progress candidate
# 4. for finished structures, crop the bottom-center resulting egg
# 5. compare egg crops against assets/eggs/
# 6. run island-scoped breeding lookup for recognized parent pairs
# The current script intentionally keeps fixed crop boxes in manual/debug mode
# while preserving a report shape that can accept automatic candidates later.


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
class CropArtifact:
	label: str
	box: CropBox
	path: Path
	upscaled_path: Path


@dataclass(frozen=True)
class ParentEvidence:
	side: str
	crop: CropArtifact
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
	rms = math.sqrt(sum_of_squares / float(a.size[0] * a.size[1] * 3))
	return rms


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


def write_report(
	report_path: Path,
	args: argparse.Namespace,
	source_copy: Path,
	breeder_crop: CropArtifact,
	left_parent: ParentEvidence,
	right_parent: ParentEvidence,
	guesses: list[dict],
	data: dict,
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
	lines.append("Structure: **Breeding Structure**  ")
	lines.append("State: **breeding in progress**  ")
	lines.append("Detection mode: **manual/debug crop boxes**  ")
	lines.append("")
	lines.append(f"Source image: `{args.source}`")
	lines.append("")
	lines.append(f"![Source screenshot]({md_rel(source_copy, out_dir)})")
	lines.append("")
	lines.append("## Breeding Structure crop")
	lines.append("")
	append_crop(lines, breeder_crop, out_dir)
	lines.append("")
	lines.append("## Parent egg evidence")
	lines.append("")
	lines.append("When a Breeding Structure is in progress, the top-left and top-right eggs are the parent eggs.")
	lines.append("When a Breeding Structure is finished, the bottom-center egg is the resulting egg.")
	lines.append("")
	append_parent_evidence(lines, left_parent, out_dir)
	lines.append("")
	append_parent_evidence(lines, right_parent, out_dir)
	lines.append("")
	lines.append("## Manual parent recognition")
	lines.append("")
	lines.append("Manual parent recognition comes only from `--parents LEFT RIGHT`.")
	lines.append("")
	lines.append(f"Left manual parent: **{left_parent.manual_parent or 'not supplied'}**  ")
	lines.append(f"Right manual parent: **{right_parent.manual_parent or 'not supplied'}**")
	lines.append("")
	lines.append("## Automated egg-reference matches")
	lines.append("")
	lines.append("Automated matching is a simple image comparison helper. It is useful evidence, not an authoritative recognizer.")
	lines.append("")
	lines.append(f"Left automated parent: **{left_parent.auto_parent or 'unknown'}**  ")
	lines.append(f"Right automated parent: **{right_parent.auto_parent or 'unknown'}**")
	lines.append("")
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

	lines.append("")
	lines.append("## Confirmation")
	lines.append("")
	lines.append("```yaml")
	lines.append("user_confirmation:")
	lines.append("  status: pending")
	lines.append("  confirmed_result: null")
	lines.append("  correction: null")
	lines.append("```")
	lines.append("")
	lines.append("## Recognition notes")
	lines.append("")
	lines.append("- This report preserves the visual evidence used for the guess.")
	lines.append("- Automated egg-reference matching is a simple helper, not a trained recognizer and not authoritative.")
	lines.append("- Manual parent recognition, when supplied, is displayed separately from automated matches.")
	lines.append("- User confirmation or correction remains authoritative.")
	lines.append("")

	report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Generate a Markdown evidence report for an MSM breeder result."
	)
	parser.add_argument(
		"--mode",
		choices=("manual-crops",),
		default="manual-crops",
		help="Detection mode. Only manual/debug crop boxes are implemented today.",
	)
	parser.add_argument("--source", required=True, type=Path, help="Source island screenshot")
	parser.add_argument("--island", required=True, help="Island name")
	parser.add_argument("--crop-breeder", required=True, type=parse_crop, help="Breeder crop as x,y,w,h")
	parser.add_argument("--crop-left-egg", required=True, type=parse_crop, help="Left parent egg crop as x,y,w,h")
	parser.add_argument("--crop-right-egg", required=True, type=parse_crop, help="Right parent egg crop as x,y,w,h")
	parser.add_argument("--parents", nargs=2, metavar=("LEFT", "RIGHT"), help="Optional manual parent names")
	parser.add_argument("--out", required=True, type=Path, help="Output evidence directory")
	parser.add_argument("--top-matches", type=int, default=5, help="Number of egg reference matches to show")
	args = parser.parse_args()

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

	breeder = crop_image(source_image, args.crop_breeder)
	left = crop_image(source_image, args.crop_left_egg)
	right = crop_image(source_image, args.crop_right_egg)

	breeder_path = out_dir / "crop-breeder.png"
	breeder_4x_path = out_dir / "crop-breeder-4x.png"
	left_path = out_dir / "crop-left-parent-egg.png"
	left_4x_path = out_dir / "crop-left-parent-egg-4x.png"
	right_path = out_dir / "crop-right-parent-egg.png"
	right_4x_path = out_dir / "crop-right-parent-egg-4x.png"

	save_png(breeder, breeder_path)
	save_png(upscale(breeder), breeder_4x_path)
	save_png(left, left_path)
	save_png(upscale(left), left_4x_path)
	save_png(right, right_path)
	save_png(upscale(right), right_4x_path)

	left_matches = compare_to_egg_assets(left, top_n=args.top_matches)
	right_matches = compare_to_egg_assets(right, top_n=args.top_matches)

	left_matches = copy_reference_images(left_matches, out_dir, "reference-left")
	right_matches = copy_reference_images(right_matches, out_dir, "reference-right")

	left_manual = args.parents[0] if args.parents else None
	right_manual = args.parents[1] if args.parents else None

	breeder_artifact = CropArtifact(
		label="Breeding Structure crop",
		box=args.crop_breeder,
		path=breeder_path,
		upscaled_path=breeder_4x_path,
	)
	left_artifact = CropArtifact(
		label="Left parent egg crop",
		box=args.crop_left_egg,
		path=left_path,
		upscaled_path=left_4x_path,
	)
	right_artifact = CropArtifact(
		label="Right parent egg crop",
		box=args.crop_right_egg,
		path=right_path,
		upscaled_path=right_4x_path,
	)

	left_parent = ParentEvidence(
		side="left",
		crop=left_artifact,
		manual_parent=left_manual,
		manual_reference_path=copy_manual_reference_image(left_manual, out_dir, "left"),
		auto_parent=left_matches[0]["monster"] if left_matches else None,
		auto_matches=left_matches,
	)
	right_parent = ParentEvidence(
		side="right",
		crop=right_artifact,
		manual_parent=right_manual,
		manual_reference_path=copy_manual_reference_image(right_manual, out_dir, "right"),
		auto_parent=right_matches[0]["monster"] if right_matches else None,
		auto_matches=right_matches,
	)

	guesses: list[dict] = []
	if left_parent.chosen_parent and right_parent.chosen_parent:
		guesses = guess_results(
			data,
			args.island,
			[left_parent.chosen_parent, right_parent.chosen_parent],
		)

	report_path = out_dir / "report.md"
	write_report(
		report_path=report_path,
		args=args,
		source_copy=source_copy,
		breeder_crop=breeder_artifact,
		left_parent=left_parent,
		right_parent=right_parent,
		guesses=guesses,
		data=data,
	)

	print(f"Wrote {report_path.relative_to(REPO_ROOT)}")

	if guesses:
		for guess in guesses:
			print(f"Likely result: {guess['monster']}")
	else:
		print("Likely result: <no match or manual review>")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
