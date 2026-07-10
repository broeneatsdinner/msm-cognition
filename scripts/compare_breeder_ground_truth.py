#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Box:
	x: int
	y: int
	w: int
	h: int

	@property
	def right(self) -> int:
		return self.x + self.w

	@property
	def bottom(self) -> int:
		return self.y + self.h

	def as_pillow_box(self) -> tuple[int, int, int, int]:
		return (self.x, self.y, self.right, self.bottom)

	def as_text(self) -> str:
		return f"x={self.x}, y={self.y}, w={self.w}, h={self.h}"


def display_path(path: Path) -> str:
	try:
		return path.relative_to(REPO_ROOT).as_posix()
	except ValueError:
		return str(path)


def parse_box(value: object) -> Box | None:
	if not isinstance(value, dict):
		return None
	try:
		box = Box(
			x=int(value["x"]),
			y=int(value["y"]),
			w=int(value["w"]),
			h=int(value["h"]),
		)
	except (KeyError, TypeError, ValueError):
		return None
	return box if box.w > 0 and box.h > 0 else None


def box_iou(left: Box, right: Box) -> float:
	x1 = max(left.x, right.x)
	y1 = max(left.y, right.y)
	x2 = min(left.right, right.right)
	y2 = min(left.bottom, right.bottom)
	if x2 <= x1 or y2 <= y1:
		return 0.0
	intersection = (x2 - x1) * (y2 - y1)
	union = (left.w * left.h) + (right.w * right.h) - intersection
	return intersection / union if union else 0.0


def clamp_box(box: Box, image: Image.Image) -> Box:
	x = max(0, min(box.x, image.width - 1))
	y = max(0, min(box.y, image.height - 1))
	right = max(x + 1, min(box.right, image.width))
	bottom = max(y + 1, min(box.bottom, image.height))
	return Box(x=x, y=y, w=right - x, h=bottom - y)


def resolve_image(image_value: object) -> Path:
	if not isinstance(image_value, str) or not image_value:
		raise RuntimeError("Annotation is missing a string image path")
	path = Path(image_value)
	return path if path.is_absolute() else REPO_ROOT / path


def score_value(candidate: dict) -> float:
	value = candidate.get("breeder_likeness_score")
	try:
		return float(value)
	except (TypeError, ValueError):
		return -1.0


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
	name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
	try:
		return ImageFont.truetype(name, size=size)
	except OSError:
		return ImageFont.load_default(size=size)


def crop_box(image: Image.Image, box: Box) -> Image.Image:
	return image.crop(clamp_box(box, image).as_pillow_box()).convert("RGB")


def selected_comparison_candidates(candidates: list[dict], limit: int = 5) -> list[dict]:
	selected: list[dict] = []
	for ordered in (
		sorted(candidates, key=lambda item: (item["iou"], score_value(item)), reverse=True),
		sorted(candidates, key=lambda item: (score_value(item), item["iou"]), reverse=True),
		sorted(candidates, key=lambda item: (item["iou"], -score_value(item))),
	):
		for candidate in ordered:
			if candidate not in selected:
				selected.append(candidate)
			if len(selected) >= limit:
				return selected
	return selected


def draw_crop_card(
	sheet: Image.Image,
	position: tuple[int, int],
	crop: Image.Image,
	title: str,
	details: list[str],
	card_width: int,
	card_height: int,
) -> None:
	x, y = position
	draw = ImageDraw.Draw(sheet)
	draw.rounded_rectangle(
		(x, y, x + card_width, y + card_height),
		radius=14,
		fill=(244, 247, 251),
		outline=(83, 99, 126),
		width=2,
	)
	draw.text((x + 18, y + 14), title, font=load_font(22, bold=True), fill=(24, 36, 54))
	for line_index, line in enumerate(details):
		draw.text((x + 18, y + 47 + (line_index * 21)), line, font=load_font(15), fill=(65, 80, 104))
	image_top = y + 102
	image_width = card_width - 36
	image_height = card_height - 120
	canvas = Image.new("RGB", (image_width, image_height), (34, 42, 57))
	contained = crop.copy()
	contained.thumbnail((image_width - 20, image_height - 20), Image.Resampling.LANCZOS)
	paste_x = (image_width - contained.width) // 2
	paste_y = (image_height - contained.height) // 2
	canvas.paste(contained, (paste_x, paste_y))
	sheet.paste(canvas, (x + 18, image_top))


def save_comparison_sheet(
	path: Path,
	image: Image.Image,
	ground_truth: Box,
	candidates: list[dict],
) -> None:
	selected = selected_comparison_candidates(candidates)
	items: list[tuple[Image.Image, str, list[str]]] = [
		(crop_box(image, ground_truth), "Ground truth", [ground_truth.as_text()]),
	]
	for candidate in selected:
		box = candidate["parsed_box"]
		items.append(
			(
				crop_box(image, box),
				candidate.get("id", "candidate"),
				[
					f"IoU {candidate['iou']:.3f} · IoU rank {candidate['iou_rank']}",
					f"breeder {score_value(candidate):.3f} · score rank {candidate['likeness_rank']}",
				],
			)
		)

	columns = 3
	card_width = 440
	card_height = 390
	margin = 26
	gap = 20
	rows = max(1, math.ceil(len(items) / columns))
	width = (2 * margin) + (columns * card_width) + ((columns - 1) * gap)
	height = (2 * margin) + (rows * card_height) + ((rows - 1) * gap)
	sheet = Image.new("RGB", (width, height), (24, 30, 42))
	for index, (crop, title, details) in enumerate(items):
		row, column = divmod(index, columns)
		draw_crop_card(
			sheet,
			(margin + column * (card_width + gap), margin + row * (card_height + gap)),
			crop,
			title,
			details,
			card_width,
			card_height,
		)
	path.parent.mkdir(parents=True, exist_ok=True)
	sheet.save(path, optimize=True)


def failure_mode(best_iou: float) -> str:
	if best_iou >= 0.50:
		return "reasonable_hit"
	if best_iou < 0.20:
		return "missed_proposal"
	return "poor_ranking"


def compare_annotation(annotation_path: Path, out_dir: Path) -> dict | None:
	try:
		annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
	except (json.JSONDecodeError, OSError) as exc:
		raise RuntimeError(f"Could not read annotation {annotation_path}: {exc}") from exc
	ground_truth_data = annotation.get("ground_truth", {})
	ground_truth = parse_box(ground_truth_data.get("box"))
	if ground_truth_data.get("status") != "confirmed" or ground_truth is None:
		return None

	image_path = resolve_image(annotation.get("image"))
	if not image_path.is_file():
		raise RuntimeError(f"Annotated image does not exist: {image_path}")
	with Image.open(image_path) as image_file:
		image = image_file.convert("RGBA")
	ground_truth = clamp_box(ground_truth, image)
	candidates: list[dict] = []
	for candidate_data in annotation.get("detector_candidates", []):
		candidate_box = parse_box(candidate_data.get("box"))
		if candidate_box is None:
			continue
		candidate = dict(candidate_data)
		candidate["parsed_box"] = clamp_box(candidate_box, image)
		candidate["iou"] = box_iou(ground_truth, candidate["parsed_box"])
		candidates.append(candidate)

	iou_order = sorted(candidates, key=lambda item: (item["iou"], score_value(item)), reverse=True)
	likeness_order = sorted(candidates, key=lambda item: (score_value(item), item["iou"]), reverse=True)
	for rank, candidate in enumerate(iou_order, start=1):
		candidate["iou_rank"] = rank
	for rank, candidate in enumerate(likeness_order, start=1):
		candidate["likeness_rank"] = rank
	best_iou_candidate = iou_order[0] if iou_order else None
	best_likeness_candidate = likeness_order[0] if likeness_order else None
	best_iou = best_iou_candidate["iou"] if best_iou_candidate else 0.0

	image_out = out_dir / image_path.stem
	image_out.mkdir(parents=True, exist_ok=True)
	ground_truth_crop_path = image_out / "ground-truth-crop.png"
	crop_box(image, ground_truth).save(ground_truth_crop_path)
	for candidate in selected_comparison_candidates(candidates):
		crop_box(image, candidate["parsed_box"]).save(image_out / f"{candidate['id']}-crop.png")
	contact_sheet_path = image_out / "comparison.png"
	save_comparison_sheet(contact_sheet_path, image, ground_truth, candidates)

	return {
		"annotation_path": annotation_path,
		"image_path": image_path,
		"ground_truth": ground_truth,
		"candidates": iou_order,
		"best_iou_candidate": best_iou_candidate,
		"best_likeness_candidate": best_likeness_candidate,
		"best_iou": best_iou,
		"any_overlap": any(candidate["iou"] > 0.0 for candidate in candidates),
		"failure_mode": failure_mode(best_iou),
		"ground_truth_crop_path": ground_truth_crop_path,
		"contact_sheet_path": contact_sheet_path,
	}


def relative_link(path: Path, base: Path) -> str:
	return path.relative_to(base).as_posix()


def write_report(path: Path, results: list[dict], scanned: int) -> None:
	lines = [
		"# Breeding Structure Ground-Truth Comparison",
		"",
		f"Annotation files scanned: **{scanned}**  ",
		f"Confirmed ground-truth boxes compared: **{len(results)}**  ",
		f"Skipped pending/unboxed annotations: **{scanned - len(results)}**",
		"",
		"Ground-truth coordinates identify the true object in one image. They are supervision for measuring proposal and ranking failures, not future location rules.",
		"",
	]
	if not results:
		lines.extend(
			[
				"No annotations have both `ground_truth.status: confirmed` and a non-null box yet.",
				"",
			]
		)
	else:
		lines.extend(
			[
				"| Image | Ground-truth box | Best IoU | Best breeder-likeness candidate | Any overlap | Failure mode | Comparison |",
				"|---|---|---:|---|---|---|---|",
			]
		)
		for result in results:
			best_likeness = result["best_likeness_candidate"]
			best_likeness_text = (
				f"{best_likeness['id']} ({score_value(best_likeness):.3f})"
				if best_likeness
				else "none"
			)
			lines.append(
				f"| {result['image_path'].name} | `{result['ground_truth'].as_text()}` | "
				f"{result['best_iou']:.3f} | {best_likeness_text} | "
				f"{'yes' if result['any_overlap'] else 'no'} | `{result['failure_mode']}` | "
				f"[contact sheet]({relative_link(result['contact_sheet_path'], path.parent)}) |"
			)
		lines.append("")

		for result in results:
			lines.extend(
				[
					f"## {result['image_path'].name}",
					"",
					f"Ground truth: `{result['ground_truth'].as_text()}`  ",
					f"Best IoU: **{result['best_iou']:.3f}**  ",
					f"Any detector overlap: **{'yes' if result['any_overlap'] else 'no'}**  ",
					f"Failure mode: **{result['failure_mode']}**",
					"",
					f"![Ground-truth and detector comparison]({relative_link(result['contact_sheet_path'], path.parent)})",
					"",
					"| IoU rank | Candidate | IoU | Breeder-likeness | Likeness rank | Box |",
					"|---:|---|---:|---:|---:|---|",
				]
			)
			for candidate in result["candidates"]:
				lines.append(
					f"| {candidate['iou_rank']} | {candidate.get('id', 'candidate')} | "
					f"{candidate['iou']:.3f} | {score_value(candidate):.3f} | "
					f"{candidate['likeness_rank']} | `{candidate['parsed_box'].as_text()}` |"
				)
			lines.append("")

	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Compare confirmed Breeding Structure boxes with detector candidates."
	)
	parser.add_argument("--annotations-dir", required=True, type=Path)
	parser.add_argument("--out-dir", required=True, type=Path)
	args = parser.parse_args()
	args.annotations_dir = (
		args.annotations_dir if args.annotations_dir.is_absolute() else REPO_ROOT / args.annotations_dir
	)
	args.out_dir = args.out_dir if args.out_dir.is_absolute() else REPO_ROOT / args.out_dir
	if not args.annotations_dir.is_dir():
		parser.error(f"--annotations-dir is not a directory: {args.annotations_dir}")
	return args


def main() -> int:
	args = parse_args()
	annotation_paths = sorted(args.annotations_dir.rglob("annotation.json"))
	results: list[dict] = []
	for annotation_path in annotation_paths:
		result = compare_annotation(annotation_path, args.out_dir)
		if result:
			results.append(result)
	report_path = args.out_dir / "comparison-report.md"
	write_report(report_path, results, len(annotation_paths))
	print(f"Scanned annotations: {len(annotation_paths)}")
	print(f"Compared confirmed boxes: {len(results)}")
	print(f"Wrote {display_path(report_path)}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
