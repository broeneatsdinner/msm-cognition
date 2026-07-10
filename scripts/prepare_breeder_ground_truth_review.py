#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

import guess_breeder_result as breeder
import run_breeder_detector_experiments as experiments


REPO_ROOT = Path(__file__).resolve().parents[1]
ISLAND = "Plant Island"
DETECTOR_THRESHOLD = 0.45
DETECTOR_MIN_SIZE = 64
DETECTOR_MAX_CANDIDATES = 12


def display_path(path: Path) -> str:
	try:
		return path.relative_to(REPO_ROOT).as_posix()
	except ValueError:
		return str(path)


def infer_state(path: Path) -> str:
	name = path.stem.lower()
	if "in-use" in name or "in_use" in name:
		return "in_use"
	if "idle" in name:
		return "idle"
	return "unknown"


def load_existing_ground_truth(annotation_path: Path) -> tuple[str, dict]:
	if not annotation_path.exists():
		return "unknown", {"status": "needs_manual_box", "box": None}
	try:
		data = json.loads(annotation_path.read_text(encoding="utf-8"))
	except (json.JSONDecodeError, OSError) as exc:
		raise RuntimeError(f"Could not preserve existing annotation {annotation_path}: {exc}") from exc
	state = data.get("state", "unknown")
	if state not in {"idle", "in_use", "unknown"}:
		state = "unknown"
	ground_truth = data.get("ground_truth")
	if not isinstance(ground_truth, dict):
		ground_truth = {"status": "needs_manual_box", "box": None}
	return state, ground_truth


def draw_candidate_overlay(
	source: Image.Image,
	candidates: list[breeder.DetectorCandidate],
	scores: list[experiments.CandidateScore],
) -> Image.Image:
	overlay = source.convert("RGB")
	draw = ImageDraw.Draw(overlay)
	font = experiments.load_font(30, bold=True)
	small_font = experiments.load_font(22, bold=True)

	for index, (candidate, score) in enumerate(zip(candidates, scores, strict=True), start=1):
		box = candidate.box
		left, top = box.x, box.y
		right, bottom = box.x + box.w - 1, box.y + box.h - 1
		draw.rectangle((left, top, right, bottom), outline=(8, 12, 18), width=12)
		draw.rectangle((left, top, right, bottom), outline=(54, 224, 255), width=6)
		label = f"#{index}"
		details = f"raw {score.raw_template_score:.3f}  breeder {score.breeder_likeness_score:.3f}"
		label_box = draw.textbbox((0, 0), label, font=font)
		details_box = draw.textbbox((0, 0), details, font=small_font)
		label_width = max(label_box[2] - label_box[0], details_box[2] - details_box[0]) + 20
		label_height = (label_box[3] - label_box[1]) + (details_box[3] - details_box[1]) + 24
		label_x = max(0, min(left, overlay.width - label_width))
		label_y = top - label_height - 8
		if label_y < 0:
			label_y = min(overlay.height - label_height, bottom + 8)
		draw.rounded_rectangle(
			(label_x, label_y, label_x + label_width, label_y + label_height),
			radius=7,
			fill=(8, 12, 18),
		)
		draw.text((label_x + 10, label_y + 4), label, font=font, fill=(92, 235, 255))
		draw.text((label_x + 10, label_y + 44), details, font=small_font, fill=(245, 248, 252))

	if not candidates:
		message = "NO DETECTOR CANDIDATES — manually annotate the true box"
		message_box = draw.textbbox((0, 0), message, font=font)
		width = message_box[2] - message_box[0]
		draw.rounded_rectangle((30, 30, 70 + width, 86), radius=8, fill=(8, 12, 18))
		draw.text((50, 39), message, font=font, fill=(255, 216, 64))

	return overlay


def review_html(image_name: str, candidates: list[dict]) -> str:
	template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Breeding Structure ground-truth review</title>
<style>
body { margin: 0; padding: 24px; background: #161c28; color: #eef2f8; font: 16px/1.5 system-ui, sans-serif; }
h1 { margin-top: 0; }
code, pre { background: #252d3d; border-radius: 6px; padding: 3px 7px; }
.stage { position: relative; display: inline-block; max-width: 100%; border: 2px solid #53627b; background: #0b0f16; }
.stage img { display: block; max-width: 100%; height: auto; user-select: none; }
.stage canvas { position: absolute; inset: 0; width: 100%; height: 100%; cursor: crosshair; touch-action: none; }
.output { margin: 18px 0; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
button { padding: 8px 14px; border: 0; border-radius: 6px; background: #38c6df; color: #071118; font-weight: 700; cursor: pointer; }
.warning { color: #ffdf68; font-weight: 700; }
</style>
</head>
<body>
<h1>Breeding Structure ground-truth review</h1>
<p class="warning">Manually enter the true Breeding Structure box into the JSON file.</p>
<p>Drag a rectangle around the complete Breeding Structure. Candidate boxes are cyan; your current drag is yellow. Coordinates are reported in original image pixels, even when the image is scaled in the browser.</p>
<p>Edit <code>annotation.json</code>, set <code>ground_truth.status</code> to <code>confirmed</code>, and paste the generated box into <code>ground_truth.box</code>. These coordinates identify the object only in this image; they are not a future location rule.</p>
<div class="output"><pre id="box">Drag on the image to create a box.</pre><button id="copy" type="button">Copy box JSON</button></div>
<div class="stage"><img id="source" src="__IMAGE__" alt="Source screenshot"><canvas id="overlay"></canvas></div>
<script>
const candidates = __CANDIDATES__;
const image = document.getElementById('source');
const canvas = document.getElementById('overlay');
const context = canvas.getContext('2d');
const output = document.getElementById('box');
let start = null;
let current = null;

function point(event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: Math.round((event.clientX - rect.left) * canvas.width / rect.width),
    y: Math.round((event.clientY - rect.top) * canvas.height / rect.height)
  };
}

function boxFromPoints(a, b) {
  const x = Math.min(a.x, b.x);
  const y = Math.min(a.y, b.y);
  return {x, y, w: Math.abs(a.x - b.x), h: Math.abs(a.y - b.y)};
}

function draw() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.font = 'bold 24px system-ui';
  context.lineWidth = 5;
  for (const candidate of candidates) {
    const b = candidate.box;
    context.strokeStyle = '#36e1ff';
    context.strokeRect(b.x, b.y, b.w, b.h);
    context.fillStyle = '#071118';
    context.fillRect(b.x, Math.max(0, b.y - 32), 76, 32);
    context.fillStyle = '#66ebff';
    context.fillText(candidate.id.replace('candidate-', '#'), b.x + 6, Math.max(25, b.y - 7));
  }
  if (start && current) {
    const b = boxFromPoints(start, current);
    context.strokeStyle = '#ffdc4e';
    context.lineWidth = 7;
    context.strokeRect(b.x, b.y, b.w, b.h);
  }
}

image.addEventListener('load', () => {
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  draw();
});
canvas.addEventListener('pointerdown', event => {
  canvas.setPointerCapture(event.pointerId);
  start = point(event);
  current = start;
  draw();
});
canvas.addEventListener('pointermove', event => {
  if (!start) return;
  current = point(event);
  draw();
});
canvas.addEventListener('pointerup', event => {
  if (!start) return;
  current = point(event);
  const box = boxFromPoints(start, current);
  output.textContent = JSON.stringify(box);
  start = null;
  current = null;
  draw();
});
document.getElementById('copy').addEventListener('click', async () => {
  if (!output.textContent.startsWith('{')) return;
  await navigator.clipboard.writeText(output.textContent);
});
</script>
</body>
</html>
"""
	return template.replace("__IMAGE__", html.escape(image_name)).replace(
		"__CANDIDATES__",
		json.dumps(candidates),
	)


def write_index(out_dir: Path, entries: list[tuple[str, Path]]) -> None:
	lines = [
		"<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">",
		"<title>Breeding Structure ground-truth reviews</title>",
		"<style>body{font:17px/1.5 system-ui,sans-serif;max-width:1000px;margin:40px auto;padding:0 20px}li{margin:10px 0}</style>",
		"<h1>Breeding Structure ground-truth reviews</h1>",
		"<p>Open a review, drag the true object box, then update that image's <code>annotation.json</code>.</p><ul>",
	]
	for label, path in entries:
		lines.append(f'<li><a href="{path.relative_to(out_dir).as_posix()}">{html.escape(label)}</a></li>')
	lines.append("</ul>")
	(out_dir / "index.html").write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_image(
	screenshot_path: Path,
	out_dir: Path,
	references: list[experiments.ReferenceVariant],
) -> Path:
	image_dir = out_dir / screenshot_path.stem
	image_dir.mkdir(parents=True, exist_ok=True)
	annotation_path = image_dir / "annotation.json"
	existing_state, ground_truth = load_existing_ground_truth(annotation_path)
	state = existing_state if annotation_path.exists() else infer_state(screenshot_path)

	source = breeder.load_image(screenshot_path)
	model = experiments.ScoringModel(
		references=references,
		false_positives=[],
		source_width=source.width,
		source_height=source.height,
	)
	candidates, _, _ = breeder.detect_breeding_structures(
		source_path=screenshot_path,
		max_candidates=DETECTOR_MAX_CANDIDATES,
		threshold=DETECTOR_THRESHOLD,
		min_width=DETECTOR_MIN_SIZE,
		min_height=DETECTOR_MIN_SIZE,
		allow_paironormal_templates=False,
		allow_locked_templates=True,
		debug_candidates=False,
	)
	scores = [experiments.score_candidate(source, candidate, model) for candidate in candidates]

	shutil.copy2(screenshot_path, image_dir / "source.png")
	detector_candidates: list[dict] = []
	for index, (candidate, score) in enumerate(zip(candidates, scores, strict=True), start=1):
		candidate_id = f"candidate-{index:03d}"
		crop_path = image_dir / f"{candidate_id}-crop.png"
		breeder.save_png(breeder.crop_image(source, candidate.box), crop_path)
		context = experiments.save_candidate_context(
			source_image=source,
			experiment_dir=image_dir,
			candidate_index=index,
			candidate_box=candidate.box,
		)
		detector_candidates.append(
			{
				"id": candidate_id,
				"box": experiments.box_as_json(candidate.box),
				"raw_template_score": round(score.raw_template_score, 6),
				"breeder_likeness_score": round(score.breeder_likeness_score, 6),
				"best_reference": score.best_reference,
				"template": candidate.template_name,
				"crop": crop_path.name,
				"boxed_context": context.boxed_path.name,
			}
		)

	review_path = image_dir / "review.png"
	draw_candidate_overlay(source, candidates, scores).save(review_path)
	annotation = {
		"schema_version": 1,
		"image": display_path(screenshot_path),
		"label": "breeding_structure",
		"island": ISLAND,
		"state": state,
		"ground_truth": ground_truth,
		"detector_settings": {
			"threshold": DETECTOR_THRESHOLD,
			"minimum_size": {"w": DETECTOR_MIN_SIZE, "h": DETECTOR_MIN_SIZE},
			"max_candidates": DETECTOR_MAX_CANDIDATES,
		},
		"detector_candidates": detector_candidates,
	}
	annotation_path.write_text(json.dumps(annotation, indent=2) + "\n", encoding="utf-8")
	(image_dir / "review.html").write_text(
		review_html("source.png", detector_candidates),
		encoding="utf-8",
	)
	return image_dir / "review.html"


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Prepare local Breeding Structure ground-truth review files."
	)
	parser.add_argument("--screenshots-dir", required=True, type=Path)
	parser.add_argument("--out-dir", required=True, type=Path)
	args = parser.parse_args()
	args.screenshots_dir = (
		args.screenshots_dir if args.screenshots_dir.is_absolute() else REPO_ROOT / args.screenshots_dir
	)
	args.out_dir = args.out_dir if args.out_dir.is_absolute() else REPO_ROOT / args.out_dir
	if not args.screenshots_dir.is_dir():
		parser.error(f"--screenshots-dir is not a directory: {args.screenshots_dir}")
	return args


def main() -> int:
	args = parse_args()
	screenshots = sorted(args.screenshots_dir.glob("*.png"))
	if not screenshots:
		raise RuntimeError(f"No PNG screenshots found in {args.screenshots_dir}")
	args.out_dir.mkdir(parents=True, exist_ok=True)
	references = [
		experiments.render_reference_variant(path, scale)
		for path in experiments.reference_paths_for_island(ISLAND)
		for scale in experiments.REFERENCE_SCALES
	]
	index_entries: list[tuple[str, Path]] = []
	for index, screenshot_path in enumerate(screenshots, start=1):
		review_path = prepare_image(screenshot_path, args.out_dir, references)
		index_entries.append((screenshot_path.name, review_path))
		print(f"Prepared {index:02d}/{len(screenshots):02d}: {display_path(review_path)}")
	write_index(args.out_dir, index_entries)
	print(f"Wrote {display_path(args.out_dir / 'index.html')}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
