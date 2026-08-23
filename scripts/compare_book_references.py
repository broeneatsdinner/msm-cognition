#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml
from PIL import Image, ImageDraw


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_DIR = REPO_ROOT / "inventory/islands"
REFERENCE_INDEX = REPO_ROOT / "reference/book/images/index.json"
DEFAULT_OUT = REPO_ROOT / "training/evidence/book-reference-audit"
MAX_FEATURE_DIMENSION = 1400


@dataclass(frozen=True)
class ImageFeatures:
    path: Path
    original_shape: tuple[int, int]
    scale: float
    gray: np.ndarray
    keypoints: tuple[cv2.KeyPoint, ...]
    descriptors: np.ndarray | None


@dataclass(frozen=True)
class MatchResult:
    screenshot: Path
    reference: Path
    island: str
    variant: str
    good_matches: int
    inliers: int
    inlier_ratio: float
    variant_inliers: int
    variant_score: float
    title_similarity: float
    full_page_score: float
    score: float
    screenshot_keypoints: int
    reference_keypoints: int
    confidence: str
    best_matches: tuple[cv2.DMatch, ...]
    homography: np.ndarray | None


def feature_score(reference_gray: np.ndarray, screenshot_gray: np.ndarray) -> tuple[int, int, float]:
    orb = cv2.ORB_create(nfeatures=2500)
    reference_keypoints, reference_descriptors = orb.detectAndCompute(reference_gray, None)
    screenshot_keypoints, screenshot_descriptors = orb.detectAndCompute(screenshot_gray, None)
    if reference_descriptors is None or screenshot_descriptors is None:
        return 0, 0, 0.0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(reference_descriptors, screenshot_descriptors, k=2)
    good = []
    for pair in pairs:
        if len(pair) != 2:
            continue
        first, second = pair
        if first.distance < 0.74 * second.distance:
            good.append(first)

    inliers = 0
    if len(good) >= 8:
        reference_points = np.float32([reference_keypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        screenshot_points = np.float32([screenshot_keypoints[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        _, mask = cv2.findHomography(reference_points, screenshot_points, cv2.RANSAC, 5.0)
        if mask is not None:
            inliers = int(mask.ravel().sum())

    ratio = inliers / len(good) if good else 0.0
    score = float(inliers + (0.15 * len(good)) + (20.0 * ratio))
    return len(good), inliers, score


def variant_region(gray: np.ndarray) -> np.ndarray:
    height, width = gray.shape[:2]
    region = gray[
        int(height * 0.08) : int(height * 0.24),
        int(width * 0.18) : int(width * 0.82),
    ]
    mask = cv2.inRange(region, 180, 255)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    region_height, region_width = region.shape[:2]
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if 2 <= width <= 90 and 5 <= height <= 40 and y < region_height * 0.55:
            boxes.append((x, y, width, height))
    if not boxes:
        return region

    x1 = max(0, min(x for x, _, _, _ in boxes) - 10)
    y1 = max(0, min(y for _, y, _, _ in boxes) - 8)
    x2 = min(region_width, max(x + width for x, _, width, _ in boxes) + 10)
    y2 = min(region_height, max(y + height for _, y, _, height in boxes) + 8)
    return region[y1:y2, x1:x2]


def title_similarity(reference_gray: np.ndarray, screenshot_gray: np.ndarray) -> float:
    reference = cv2.resize(variant_region(reference_gray), (500, 80), interpolation=cv2.INTER_AREA)
    screenshot = cv2.resize(variant_region(screenshot_gray), (500, 80), interpolation=cv2.INTER_AREA)
    reference_edges = cv2.Canny(reference, 50, 150).astype("float32")
    screenshot_edges = cv2.Canny(screenshot, 50, 150).astype("float32")
    if reference_edges.std() == 0 or screenshot_edges.std() == 0:
        return 0.0
    normalized_reference = reference_edges - reference_edges.mean()
    normalized_screenshot = screenshot_edges - screenshot_edges.mean()
    return float(
        (normalized_reference * normalized_screenshot).mean()
        / (reference_edges.std() * screenshot_edges.std())
    )


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def repo_display(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML object: {path}")
    return data


def inventory_paths(selected_island: str | None) -> list[Path]:
    paths = sorted(INVENTORY_DIR.glob("*.yaml"))
    if selected_island is None:
        return paths
    matches = [path for path in paths if load_yaml(path).get("island") == selected_island]
    if not matches:
        raise SystemExit(f"No inventory YAML found for island: {selected_island}")
    return matches


def load_reference_index(path: Path) -> dict[tuple[str, str], Path]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    references: dict[tuple[str, str], Path] = {}
    for record in data.get("images", []):
        if not isinstance(record, dict):
            continue
        local_path = record.get("local_path")
        island = record.get("island")
        variant = record.get("variant")
        if not local_path or not island or not variant:
            continue
        references[(str(island), str(variant))] = REPO_ROOT / str(local_path)
    return references


def book_screenshots(island: dict[str, Any]) -> list[Path]:
    evidence = island.get("evidence", {})
    if not isinstance(evidence, dict):
        return []
    directory = evidence.get("screenshot_directory")
    filenames = evidence.get("book", [])
    if not directory or not isinstance(filenames, list):
        return []
    base = REPO_ROOT / str(directory)
    return [base / str(filename) for filename in filenames]


def load_features(path: Path, orb: cv2.ORB) -> ImageFeatures:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {path}")
    height, width = image.shape[:2]
    scale = min(1.0, MAX_FEATURE_DIMENSION / max(width, height))
    if scale < 1.0:
        image = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    keypoints, descriptors = orb.detectAndCompute(image, None)
    return ImageFeatures(
        path=path,
        original_shape=(height, width),
        scale=scale,
        gray=image,
        keypoints=tuple(keypoints or ()),
        descriptors=descriptors,
    )


def compare_features(
    screenshot: ImageFeatures,
    reference: ImageFeatures,
    island: str,
    variant: str,
) -> MatchResult:
    if screenshot.descriptors is None or reference.descriptors is None:
        good: list[cv2.DMatch] = []
    else:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        pairs = matcher.knnMatch(reference.descriptors, screenshot.descriptors, k=2)
        good = []
        for pair in pairs:
            if len(pair) != 2:
                continue
            first, second = pair
            if first.distance < 0.74 * second.distance:
                good.append(first)

    homography = None
    inliers = 0
    if len(good) >= 8:
        reference_points = np.float32([reference.keypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        screenshot_points = np.float32([screenshot.keypoints[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        homography, mask = cv2.findHomography(reference_points, screenshot_points, cv2.RANSAC, 5.0)
        if mask is not None:
            inliers = int(mask.ravel().sum())

    inlier_ratio = inliers / len(good) if good else 0.0
    full_page_score = float(inliers + (0.15 * len(good)) + (20.0 * inlier_ratio))
    title_score = max(0.0, title_similarity(reference.gray, screenshot.gray))
    variant_score = title_score * 1400.0
    score = float(variant_score + (0.20 * full_page_score))
    if title_score >= 0.10 and inliers >= 40:
        confidence = "high"
    elif title_score >= 0.07 and inliers >= 20:
        confidence = "medium"
    elif title_score >= 0.04 or inliers >= 12:
        confidence = "low"
    else:
        confidence = "none"

    return MatchResult(
        screenshot=screenshot.path,
        reference=reference.path,
        island=island,
        variant=variant,
        good_matches=len(good),
        inliers=inliers,
        inlier_ratio=inlier_ratio,
        variant_inliers=round(title_score * 1000),
        variant_score=variant_score,
        title_similarity=title_score,
        full_page_score=full_page_score,
        score=score,
        screenshot_keypoints=len(screenshot.keypoints),
        reference_keypoints=len(reference.keypoints),
        confidence=confidence,
        best_matches=tuple(sorted(good, key=lambda match: match.distance)[:60]),
        homography=homography,
    )


def render_match_image(
    result: MatchResult,
    screenshot_features: ImageFeatures,
    reference_features: ImageFeatures,
    output: Path,
) -> None:
    image = cv2.drawMatches(
        reference_features.gray,
        list(reference_features.keypoints),
        screenshot_features.gray,
        list(screenshot_features.keypoints),
        list(result.best_matches),
        None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), image)


def thumbnail(path: Path, label: str, max_width: int = 520) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = max_width / image.width
    size = (max_width, round(image.height * ratio))
    image = image.resize(size, Image.Resampling.LANCZOS)
    label_height = 44
    canvas = Image.new("RGB", (image.width, image.height + label_height), "white")
    canvas.paste(image, (0, label_height))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 12), label, fill=(20, 20, 20))
    return canvas


def render_contact_sheet(screenshots: list[Path], references: list[tuple[str, Path]], output: Path) -> None:
    cells = [thumbnail(path, path.name) for path in screenshots]
    cells.extend(thumbnail(path, f"{variant}: {path.name}") for variant, path in references)
    if not cells:
        return
    columns = 2
    gap = 20
    cell_width = max(cell.width for cell in cells)
    cell_height = max(cell.height for cell in cells)
    rows = (len(cells) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (columns * cell_width + (columns + 1) * gap, rows * cell_height + (rows + 1) * gap),
        (245, 245, 245),
    )
    for index, cell in enumerate(cells):
        row = index // columns
        col = index % columns
        x = gap + col * (cell_width + gap)
        y = gap + row * (cell_height + gap)
        canvas.paste(cell, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def result_row(result: MatchResult, best: bool) -> str:
    marker = "yes" if best else ""
    return (
        f"| `{result.screenshot.name}` | {result.variant} | {result.confidence} | "
        f"{result.score:.2f} | {result.title_similarity:.3f} | {result.inliers} | "
        f"{result.good_matches} | {result.inlier_ratio:.2f} | {marker} |"
    )


def audit_island(
    island_path: Path,
    references: dict[tuple[str, str], Path],
    out_root: Path,
    orb: cv2.ORB,
) -> tuple[str, list[str]]:
    island = load_yaml(island_path)
    island_name = str(island["island"])
    screenshots = [path for path in book_screenshots(island) if path.exists()]
    island_references = [
        (variant, path)
        for (name, variant), path in sorted(references.items())
        if name == island_name and path.exists()
    ]

    lines = [f"## {island_name}", ""]
    problems: list[str] = []
    if not screenshots:
        lines.append("- No Book screenshots recorded for this island.")
        problems.append(f"{island_name}: no Book screenshots recorded")
        return "\n".join(lines), problems
    if not island_references:
        lines.append("- No cached canonical Book references found for this island.")
        problems.append(f"{island_name}: no cached canonical Book references")
        return "\n".join(lines), problems

    island_out = out_root / slug(island_name)
    if island_out.exists():
        for generated_image in island_out.glob("*.jpg"):
            generated_image.unlink()
    contact_sheet = island_out / "contact-sheet.jpg"
    render_contact_sheet(screenshots, island_references, contact_sheet)

    screenshot_features = {path: load_features(path, orb) for path in screenshots}
    reference_features = {variant: load_features(path, orb) for variant, path in island_references}
    results: list[MatchResult] = []
    for screenshot in screenshots:
        for variant, _ in island_references:
            results.append(
                compare_features(
                    screenshot_features[screenshot],
                    reference_features[variant],
                    island_name,
                    variant,
                )
            )

    best_by_screenshot: dict[Path, MatchResult] = {}
    for screenshot in screenshots:
        candidates = [result for result in results if result.screenshot == screenshot]
        best_by_screenshot[screenshot] = max(candidates, key=lambda result: result.score)

    lines.append(f"- Inventory file: `{repo_display(island_path)}`")
    lines.append(f"- Contact sheet: `{repo_display(contact_sheet)}`")
    lines.append("")
    lines.append("| Screenshot | Best variant | Confidence | Score | Title similarity | Page inliers | Good matches | Page inlier ratio |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for screenshot in screenshots:
        best = best_by_screenshot[screenshot]
        lines.append(
            f"| `{screenshot.name}` | {best.variant} | {best.confidence} | "
            f"{best.score:.2f} | {best.title_similarity:.3f} | {best.inliers} | "
            f"{best.good_matches} | {best.inlier_ratio:.2f} |"
        )
        if best.confidence in {"none", "low"}:
            problems.append(f"{island_name} {screenshot.name}: weak Book reference match")

        match_image = island_out / f"{screenshot.stem}-best-{best.variant}-matches.jpg"
        render_match_image(
            best,
            screenshot_features[screenshot],
            reference_features[best.variant],
            match_image,
        )

    lines.extend(["", "### All Variant Scores", ""])
    lines.append("| Screenshot | Variant | Confidence | Score | Title similarity | Page inliers | Good matches | Page inlier ratio | Best |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for screenshot in screenshots:
        best = best_by_screenshot[screenshot]
        screenshot_results = sorted(
            [result for result in results if result.screenshot == screenshot],
            key=lambda result: result.score,
            reverse=True,
        )
        for result in screenshot_results:
            lines.append(result_row(result, result is best))

    expected = set(island.get("book", {}).keys()) & {"common", "rare", "epic"}
    observed = {result.variant for result in best_by_screenshot.values() if result.confidence != "none"}
    missing_variants = sorted(expected - observed)
    if missing_variants:
        problems.append(f"{island_name}: no best screenshot match for {', '.join(missing_variants)}")
        lines.extend(["", f"- Missing best-match variants: `{', '.join(missing_variants)}`"])

    return "\n".join(lines), problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare account Book screenshots against cached canonical Book references."
    )
    parser.add_argument("--island", help="Full island name, such as 'Water Island'. Omit for all indexed islands.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--features", type=int, default=5000, help="Maximum ORB features per image.")
    args = parser.parse_args()

    out_root = args.out if args.out.is_absolute() else REPO_ROOT / args.out
    references = load_reference_index(REFERENCE_INDEX)
    orb = cv2.ORB_create(nfeatures=args.features)

    lines = [
        "# Book reference comparison audit",
        "",
        "Generated by comparing account Book screenshots with cached canonical Book reference images.",
        "Scores are evidence for review; they do not update inventory YAML.",
        "",
    ]
    all_problems: list[str] = []
    for path in inventory_paths(args.island):
        report, problems = audit_island(path, references, out_root, orb)
        lines.append(report)
        lines.append("")
        all_problems.extend(problems)

    lines.extend(["## Summary", ""])
    if all_problems:
        lines.extend(f"- {problem}" for problem in all_problems)
    else:
        lines.append("- No weak or missing reference matches found.")

    out_root.mkdir(parents=True, exist_ok=True)
    report_path = out_root / ("report.md" if args.island is None else f"{slug(args.island)}.md")
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {repo_display(report_path)}")
    if all_problems:
        print("Summary:")
        for problem in all_problems:
            print(f"- {problem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
