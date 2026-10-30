"""Markdown to HTML for the subset this repository uses.

Adapted from the renderer in the other project sites: headings, paragraphs,
nested lists, tables, fenced code, block quotes, code spans, links, images,
and bold or italic text. Task list items (`- [ ]`, `- [x]`) become
checkboxes carrying their source line number, so a click can name the line
it changes. A code span that names a file or folder in the repository links
to it.
"""
from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import quote

LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
TASK = re.compile(r"^\[([ xX])\]\s+(.*)$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"[`*]", "", text).lower()).strip("-")


class Renderer:
    def __init__(self, repo_root: Path, rel: str):
        self.root = repo_root
        self.rel = rel

    def known_path(self, text: str) -> str | None:
        """A code span naming a repo file or folder, as a site URL; else None."""
        if not re.fullmatch(r"[\w .'/-]+", text) or text.startswith(("/", ".")):
            return None
        for base in (Path(), Path(self.rel).parent):
            candidate = (self.root / base / text).resolve()
            if candidate.exists() and candidate.is_relative_to(self.root):
                rel = candidate.relative_to(self.root).as_posix()
                return "/" + quote(rel) + ("/" if candidate.is_dir() else "")
        return None

    def inline(self, text: str) -> str:
        # Code spans become \0N\0 placeholders first, so bold, italics, and
        # links can wrap them without touching what is inside them.
        codes: list[str] = []

        def stash(match: re.Match[str]) -> str:
            code = match.group(1)
            url = self.known_path(code)
            tag = f"<code>{esc(code)}</code>"
            codes.append(f'<a href="{esc(url)}">{tag}</a>' if url else tag)
            return f"\0{len(codes) - 1}\0"

        def link(match: re.Match[str]) -> str:
            bang, label, target = match.group(1), match.group(2), html.unescape(match.group(3))
            if bang:
                return f'<img src="{esc(target)}" alt="{label}">'
            return f'<a href="{esc(target)}">{label}</a>'

        t = esc(re.sub(r"`([^`]+)`", stash, text))
        t = re.sub(r"(!?)\[([^\]]+)\]\(([^)\s]+)\)", link, t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<![\w*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\w*])", r"<em>\1</em>", t)
        return re.sub(r"\0(\d+)\0", lambda m: codes[int(m.group(1))], t)

    def item(self, text: str, line_no: int, source: str) -> str:
        task = TASK.match(text)
        if not task:
            return self.inline(text)
        checked = " checked" if task.group(1) != " " else ""
        return (
            f'<label class="task"><input type="checkbox" data-path="{esc(self.rel)}" data-line="{line_no}" '
            f'data-text="{esc(source)}"{checked}> <span>{self.inline(task.group(2))}</span></label>'
        )

    def render_list(self, block: list[tuple[int, str]]) -> str:
        """Nested lists by indentation. Indented text that is not a list item
        continues the deepest item it is indented under."""
        root: dict = {"indent": -1, "children": []}
        stack = [root]
        for line_no, line in block:
            if not line.strip():
                continue
            ind = indent_of(line)
            match = LIST_ITEM.match(line)
            if match:
                ordered = match.group(2)[0].isdigit()
                while len(stack) > 1 and stack[-1]["indent"] > ind:
                    stack.pop()
                top = stack[-1]
                if top is not root and top["indent"] == ind and top["ordered"] == ordered:
                    lst = top
                else:
                    if top is not root and top["indent"] == ind:
                        stack.pop()
                    parent = stack[-1]
                    start = int(match.group(2)[:-1]) if ordered else 1
                    lst = {"indent": ind, "ordered": ordered, "start": start, "items": []}
                    if parent is root:
                        root["children"].append(lst)
                    else:
                        parent["items"][-1].append(("list", lst))
                    stack.append(lst)
                lst["items"].append([("text", (match.group(3), line_no, line))])
            elif len(stack) > 1:
                while len(stack) > 2 and stack[-1]["indent"] >= ind:
                    stack.pop()
                stack[-1]["items"][-1].append(("para", line.strip()))

        def draw(lst: dict) -> str:
            tag = "ol" if lst["ordered"] else "ul"
            start = f' start="{lst["start"]}"' if lst["ordered"] and lst["start"] != 1 else ""
            items = []
            for item in lst["items"]:
                parts = []
                is_task = False
                for kind, value in item:
                    if kind == "text":
                        is_task = bool(TASK.match(value[0]))
                        parts.append(self.item(*value))
                    elif kind == "para":
                        parts.append(f"<p>{self.inline(value)}</p>")
                    else:
                        parts.append(draw(value))
                cls = ' class="task-item"' if is_task else ""
                items.append(f"<li{cls}>" + "".join(parts) + "</li>")
            return f"<{tag}{start}>" + "".join(items) + f"</{tag}>"

        return "".join(draw(lst) for lst in root["children"])

    def render(self, text: str) -> str:
        lines = text.splitlines()
        out = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if line.lstrip().startswith(("```", "~~~")):
                fence = line.lstrip()[:3]
                j = i + 1
                while j < len(lines) and not lines[j].lstrip().startswith(fence):
                    j += 1
                out.append("<pre><code>" + esc("\n".join(lines[i + 1 : j])) + "</code></pre>")
                i = j + 1
                continue
            match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                out.append(f'<h{level} id="{slug(title)}">{self.inline(title)}</h{level}>')
                i += 1
                continue
            if line.startswith(">"):
                j = i
                quoted = []
                while j < len(lines) and lines[j].startswith(">"):
                    quoted.append(lines[j][1:].strip())
                    j += 1
                out.append(f"<blockquote><p>{self.inline(' '.join(quoted))}</p></blockquote>")
                i = j
                continue
            if line.lstrip().startswith("|") and i + 1 < len(lines) and TABLE_RULE.match(lines[i + 1]):
                head = cells(line)
                j = i + 2
                body = []
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    body.append(cells(lines[j]))
                    j += 1
                th = "".join(f"<th>{self.inline(c)}</th>" for c in head)
                rows = "".join(
                    "<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in row) + "</tr>\n"
                    for row in body
                )
                out.append(
                    f'<div class="table-wrap"><table>\n<thead><tr>{th}</tr></thead>\n'
                    f"<tbody>\n{rows}</tbody>\n</table></div>"
                )
                i = j
                continue
            if LIST_ITEM.match(line):
                j = i
                block = []
                while j < len(lines):
                    cur = lines[j]
                    if LIST_ITEM.match(cur) or (cur.strip() and indent_of(cur) > 0):
                        block.append((j + 1, cur))
                        j += 1
                    elif not cur.strip():
                        k = j + 1
                        while k < len(lines) and not lines[k].strip():
                            k += 1
                        if k < len(lines) and (LIST_ITEM.match(lines[k]) or indent_of(lines[k]) > 0):
                            j = k
                        else:
                            break
                    else:
                        break
                out.append(self.render_list(block))
                i = j
                continue
            para = [line.strip()]
            i += 1
            while (
                i < len(lines)
                and lines[i].strip()
                and not re.match(r"^(#{1,6}\s|\s*\||\s*```|\s*~~~|>)", lines[i])
                and not LIST_ITEM.match(lines[i])
            ):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{self.inline(' '.join(para))}</p>")
        return "\n".join(out)


def indent_of(line: str) -> int:
    return len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())


def cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def render_markdown(repo_root: Path, rel: str, text: str) -> str:
    return Renderer(repo_root, rel).render(text)
