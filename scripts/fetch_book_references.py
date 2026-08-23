#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "reference/book/book-reference-manifest.json"
OUTPUT_DIR = REPO_ROOT / "reference/book/images"
API_URL = "https://mysingingmonsters.fandom.com/api.php"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    return data


def api_query(params: dict[str, str]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "msm-cognition-reference-fetcher/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("Expected API object response")
    return data


def image_info(file_title: str) -> tuple[str, int | None]:
    data = api_query(
        {
            "action": "query",
            "format": "json",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url|size",
        }
    )
    pages = data.get("query", {}).get("pages", {})
    if not isinstance(pages, dict):
        raise ValueError(f"Unexpected API response for {file_title}")
    for page in pages.values():
        infos = page.get("imageinfo", [])
        if infos:
            info = infos[0]
            return str(info["url"]), info.get("size")
    raise ValueError(f"No imageinfo returned for {file_title}")


def download(url: str, output: Path) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "msm-cognition-reference-fetcher/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()
    output.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Book of Monsters reference images.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    output_dir = args.out if args.out.is_absolute() else REPO_ROOT / args.out
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for reference in manifest.get("references", []):
        island = reference["island"]
        variant = reference["variant"]
        file_title = reference["file_title"]
        url, source_size = image_info(file_title)
        suffix = Path(urllib.parse.urlparse(url).path).suffix or ".png"
        output = output_dir / f"{slug(island)}-{slug(variant)}{suffix}"
        digest = download(url, output)
        records.append(
            {
                "island": island,
                "variant": variant,
                "file_title": file_title,
                "source_url": url,
                "source_size": source_size,
                "local_path": str(output.relative_to(REPO_ROOT)),
                "sha256": digest,
            }
        )
        print(f"Fetched {island} {variant}: {output}")

    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps({"images": records}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
