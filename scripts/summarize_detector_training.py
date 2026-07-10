#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPO_ROOT / "training" / "evidence"


@dataclass
class CandidateSummary:
	index: str
	template: str
	score: str
	box: str = ""


@dataclass
class EvidenceReport:
	path: Path
	evidence_dir: Path
	island: str = ""
	detection_mode: str = ""
	detector_classification: str = "unresolved"
	detector_candidate_correct: str = ""
	confirmed_left_parent: str = ""
	confirmed_right_parent: str = ""
	confirmed_result: str = ""
	notes: str = ""
	active_filters: str = ""
	active_templates: str = ""
	candidates: list[CandidateSummary] = field(default_factory=list)


def strip_md_value(value: str) -> str:
	value = value.strip()
	value = value.removesuffix("  ").strip()
	if value.startswith("**") and value.endswith("**"):
		value = value[2:-2]
	if value.startswith("`") and value.endswith("`"):
		value = value[1:-1]
	return value.strip()


def parse_training_review(text: str) -> dict[str, str]:
	match = re.search(r"```yaml\s+training_review:\s*(.*?)```", text, re.DOTALL)
	if not match:
		return {}

	values: dict[str, str] = {}
	for raw_line in match.group(1).splitlines():
		line = raw_line.strip()
		if not line or ":" not in line:
			continue
		key, value = line.split(":", 1)
		value = value.strip()
		values[key.strip()] = "" if value == "null" else value
	return values


def parse_candidate_rows(text: str) -> list[CandidateSummary]:
	candidates: list[CandidateSummary] = []
	seen: set[tuple[str, str, str]] = set()
	for line in text.splitlines():
		if not line.startswith("|"):
			continue
		cells = [cell.strip() for cell in line.strip("|").split("|")]
		if len(cells) < 3:
			continue
		if not cells[0].isdigit():
			continue
		template = cells[1]
		score = cells[2]
		if not template.endswith(".webp"):
			continue
		box = cells[-1].strip("`") if cells else ""
		key = (template, score, box)
		if key in seen:
			continue
		seen.add(key)
		candidates.append(CandidateSummary(index=cells[0], template=template, score=score, box=box))
	return candidates


def parse_report(path: Path) -> EvidenceReport:
	text = path.read_text(encoding="utf-8")
	report = EvidenceReport(path=path, evidence_dir=path.parent)

	for line in text.splitlines():
		if line.startswith("Island:"):
			report.island = strip_md_value(line.split(":", 1)[1])
		elif line.startswith("Detection mode:"):
			report.detection_mode = strip_md_value(line.split(":", 1)[1])
		elif line.startswith("Active filters:"):
			report.active_filters = line.strip()
		elif line.startswith("Active templates:"):
			report.active_templates = strip_md_value(line.split(":", 1)[1])

	review = parse_training_review(text)
	report.detector_classification = review.get("detector_classification") or "unresolved"
	report.detector_candidate_correct = review.get("detector_candidate_correct", "")
	report.confirmed_left_parent = review.get("confirmed_left_parent", "")
	report.confirmed_right_parent = review.get("confirmed_right_parent", "")
	report.confirmed_result = review.get("confirmed_result", "")
	report.notes = review.get("notes", "")
	report.candidates = parse_candidate_rows(text)
	return report


def report_label(report: EvidenceReport) -> str:
	return report.evidence_dir.relative_to(REPO_ROOT).as_posix()


def markdown_table_row(values: list[str]) -> str:
	return "| " + " | ".join(value.replace("\n", " ") for value in values) + " |"


def candidate_text(report: EvidenceReport) -> str:
	if not report.candidates:
		return "none"
	return ", ".join(f"{item.template} ({item.score})" for item in report.candidates)


def section_for_classification(title: str, reports: list[EvidenceReport]) -> list[str]:
	lines = [f"## {title}", ""]
	if not reports:
		lines.append("_None._")
		lines.append("")
		return lines

	for report in reports:
		lines.append(f"### {report_label(report)}")
		lines.append("")
		lines.append(f"- Island: {report.island or 'unknown'}")
		lines.append(f"- Candidates: {candidate_text(report)}")
		lines.append(f"- Confirmed parents: {report.confirmed_left_parent or 'unknown'} + {report.confirmed_right_parent or 'unknown'}")
		lines.append(f"- Confirmed result: {report.confirmed_result or 'unknown'}")
		if report.notes:
			lines.append(f"- Notes: {report.notes}")
		lines.append("")
	return lines


def improvement_hints(reports: list[EvidenceReport]) -> list[str]:
	classifications = Counter(report.detector_classification for report in reports)
	lines = ["## Detector improvement hints", ""]

	if classifications.get("false_positive"):
		lines.append("- False positives are present; keep conservative template thresholds and review low-confidence candidate crops before trusting parent crops.")
	if classifications.get("missed_detection"):
		lines.append("- Missed detections are present; use confirmed missed screenshots to tune template scale coverage, template assets, or candidate size guards.")
	if any(report.confirmed_left_parent or report.confirmed_right_parent for report in reports):
		lines.append("- Confirmed parent labels exist; use them to evaluate parent crop regions separately from Breeding Structure detection.")
	if any("threshold" in report.active_filters.lower() for report in reports if report.active_filters):
		lines.append("- Active filter lines are available; compare threshold and template-family settings against each report outcome.")
	if not lines[2:]:
		lines.append("- No reviewed detector outcomes yet; annotate report `training_review` blocks before tuning detector behavior.")

	lines.append("")
	return lines


def build_summary(reports: list[EvidenceReport]) -> str:
	reports = sorted(reports, key=lambda item: report_label(item))
	counts = Counter(report.detector_classification for report in reports)

	lines: list[str] = ["# Breeder Detector Training Summary", ""]
	lines.append(f"Reports scanned: **{len(reports)}**")
	lines.append("")
	lines.append("## Counts by detector_classification")
	lines.append("")
	lines.append("| Classification | Count |")
	lines.append("|---|---:|")
	for classification, count in sorted(counts.items()):
		lines.append(markdown_table_row([classification, str(count)]))
	lines.append("")

	lines.append("## Evidence reports")
	lines.append("")
	lines.append("| Evidence directory | Island | Mode | Classification | Candidate correct | Confirmed parents | Confirmed result | Candidates |")
	lines.append("|---|---|---|---|---|---|---|---|")
	for report in reports:
		lines.append(
			markdown_table_row(
				[
					report_label(report),
					report.island or "unknown",
					report.detection_mode or "unknown",
					report.detector_classification,
					report.detector_candidate_correct or "unknown",
					f"{report.confirmed_left_parent or 'unknown'} + {report.confirmed_right_parent or 'unknown'}",
					report.confirmed_result or "unknown",
					candidate_text(report),
				]
			)
		)
	lines.append("")

	lines.extend(section_for_classification("False positives", [r for r in reports if r.detector_classification == "false_positive"]))
	lines.extend(section_for_classification("Missed detections", [r for r in reports if r.detector_classification == "missed_detection"]))
	lines.extend(section_for_classification("Unresolved", [r for r in reports if r.detector_classification == "unresolved"]))
	lines.extend(improvement_hints(reports))
	return "\n".join(lines)


def find_reports() -> list[Path]:
	return sorted(EVIDENCE_ROOT.glob("**/report.md"))


def main() -> int:
	parser = argparse.ArgumentParser(description="Summarize breeder detector training evidence.")
	parser.add_argument("--out", type=Path, help="Optional path to write the Markdown summary")
	args = parser.parse_args()

	reports = [parse_report(path) for path in find_reports()]
	summary = build_summary(reports)

	if args.out:
		out_path = args.out
		if not out_path.is_absolute():
			out_path = REPO_ROOT / out_path
		out_path.parent.mkdir(parents=True, exist_ok=True)
		out_path.write_text(summary + "\n", encoding="utf-8")
	else:
		print(summary)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
