"""Turn a checklist click into a file change.

A click names a Markdown file, a line number, the text that line held when
the page was drawn, and an action. Two kinds of file accept clicks:

- A generated island page (inventory/islands/<island>.md next to its
  <island>.yaml): the click changes the matching monster's `owned` count in
  the YAML, one line, and the caller regenerates the pages.
- Any other Markdown file: the click flips that line's `[ ]` or `[x]`.

The expected line text guards against a page drawn before the file changed:
if the line no longer matches, nothing is written.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from msm_cognition.inventory import CHECKLIST_HEADING, VARIANTS, normalize_name

TASK = re.compile(r"^(\s*[-*]\s+\[)([ xX])(\]\s+)(.*)$")
LABEL = re.compile(r"^(?P<name>.+?)(?: x(?P<count>\d+))?(?: \((?P<note>[^)]*)\))?$")
ACTIONS = {"check", "uncheck", "increment", "decrement"}


class EditError(ValueError):
    """A click that cannot be applied; the message is shown on the page."""


@dataclass
class Edit:
    path: Path
    text: str
    message: str


def task_line(lines: list[str], line_no: int, expected: str) -> re.Match[str]:
    if not 1 <= line_no <= len(lines):
        raise EditError("That line is no longer in the file. Reload the page.")
    if lines[line_no - 1] != expected:
        raise EditError("The file changed since the page loaded. Reload the page.")
    match = TASK.match(lines[line_no - 1])
    if not match:
        raise EditError("That line is not a checklist item.")
    return match


def toggle_markdown(path: Path, rel: str, line_no: int, expected: str, action: str) -> Edit:
    """Flip one `[ ]` / `[x]` in a hand-written Markdown file."""
    if action not in {"check", "uncheck"}:
        raise EditError("Counts can only change on generated island pages.")
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    match = task_line(lines, line_no, expected)
    box = "x" if action == "check" else " "
    lines[line_no - 1] = match.group(1) + box + match.group(3) + match.group(4)
    verb = "Check" if action == "check" else "Uncheck"
    return Edit(path, "\n".join(lines), f"{verb} '{match.group(4)}' in {rel}")


def checklist_entry(lines: list[str], line_no: int) -> tuple[str, str]:
    """The variant and monster label a generated checklist line belongs to."""
    variant = None
    in_checklist = False
    for line in lines[: line_no - 1]:
        if line.startswith("## "):
            in_checklist = line[3:].strip() == CHECKLIST_HEADING
            variant = None
        elif line.startswith("### ") and in_checklist:
            variant = line[4:].strip().lower()
    if not in_checklist or variant not in VARIANTS:
        raise EditError(f"Only the '{CHECKLIST_HEADING}' checklist can be ticked here.")
    label = TASK.match(lines[line_no - 1]).group(4)
    return variant, LABEL.match(label).group("name")


def monster_row(yaml_lines: list[str], variant: str, label: str) -> tuple[int, dict]:
    """The YAML line index and parsed row for one monster of one variant."""
    wanted = normalize_name(label)
    found = []
    for index, line in enumerate(yaml_lines):
        stripped = line.strip()
        if not stripped.startswith("- {"):
            continue
        row = yaml.safe_load(stripped[2:])
        if not isinstance(row, dict) or row.get("variant") != variant:
            continue
        names = {normalize_name(row.get("name", "")), normalize_name(row.get("display_name", ""))}
        if wanted in names:
            found.append((index, row))
    if len(found) != 1:
        raise EditError(f"Expected one {variant} {label} row in the YAML, found {len(found)}.")
    return found[0]


def bump_book_count(yaml_lines: list[str], variant: str) -> None:
    """Add one to book.<variant>.discovered, the Book total for that variant."""
    section = None
    for index, line in enumerate(yaml_lines):
        if re.match(r"^\S", line):
            section = line.split(":")[0]
            continue
        if section != "book":
            continue
        if re.match(rf"^  {variant}:\s*$", line):
            for inner in range(index + 1, len(yaml_lines)):
                match = re.match(r"^(    discovered: )(\d+)\s*$", yaml_lines[inner])
                if match:
                    yaml_lines[inner] = f"{match.group(1)}{int(match.group(2)) + 1}"
                    return
                if not yaml_lines[inner].startswith("    "):
                    break
    raise EditError(f"No book.{variant}.discovered count in the YAML to update.")


def set_owned(yaml_path: Path, md_lines: list[str], line_no: int, action: str) -> Edit:
    """Change one owned count in an island YAML from a generated page click."""
    variant, label = checklist_entry(md_lines, line_no)
    text = yaml_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    index, row = monster_row(lines, variant, label)
    owned = row["owned"]
    if action == "check":
        if owned:
            raise EditError(f"{label} is already ticked.")
        new = 1
    elif action == "uncheck":
        if owned > 1:
            raise EditError(f"{label} has {owned}; use the minus button to lower the count.")
        new = 0
    elif action == "increment":
        new = owned + 1
    else:
        if owned == 0:
            raise EditError(f"{label} is already at zero.")
        new = owned - 1
    if row.get("checked_in", 0) > new:
        raise EditError(f"{label} has {row['checked_in']} checked in; edit the YAML for that.")

    line = re.sub(r"\bowned: \d+", f"owned: {new}", lines[index], count=1)
    # A tick is the player's own confirmation, so it settles a less certain count.
    line = re.sub(r", confidence: \w+", "", line, count=1)
    discovered_now = new > 0 and not row.get("discovered")
    if discovered_now:
        line = line.replace("discovered: false", "discovered: true", 1)
    lines[index] = line
    if discovered_now:
        bump_book_count(lines, variant)

    new_text = "\n".join(lines)
    island = yaml.safe_load(new_text)
    _, check = monster_row(new_text.split("\n"), variant, label)
    if check["owned"] != new or (new and not check["discovered"]):
        raise EditError("The YAML edit did not come out as expected; nothing was written.")

    variant_label = "" if variant == "common" else variant.title() + " "
    name = row.get("display_name", row["name"])
    if name.lower().startswith(variant_label.lower()):
        variant_label = ""
    where = island["island"]
    if action == "check":
        message = f"Mark {variant_label}{name} owned on {where}"
    elif action == "uncheck":
        message = f"Mark {variant_label}{name} not owned on {where}"
    else:
        message = f"Set {variant_label}{name} owned count to {new} on {where}"
    return Edit(yaml_path, new_text, message)


def plan_edit(repo_root: Path, rel: str, line_no: int, expected: str, action: str) -> Edit:
    """Work out the edit a click asks for, without writing anything."""
    if action not in ACTIONS:
        raise EditError(f"Unknown action: {action}")
    repo_root = repo_root.resolve()
    path = (repo_root / rel).resolve()
    if path.suffix != ".md" or not path.is_file() or not path.is_relative_to(repo_root):
        raise EditError("Only Markdown files in the repository can be edited.")
    yaml_path = path.with_suffix(".yaml")
    if path.parent == (repo_root / "inventory/islands").resolve() and yaml_path.is_file():
        md_lines = path.read_text(encoding="utf-8").split("\n")
        task_line(md_lines, line_no, expected)
        return set_owned(yaml_path, md_lines, line_no, action)
    return toggle_markdown(path, rel, line_no, expected, action)
