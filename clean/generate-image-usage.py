#!/usr/bin/env python3
"""Generate CSV of image usage for files under content/."""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
OUTPUT_DIR = ROOT / "sandbox"
LIST_PATH = OUTPUT_DIR / "images-all.txt"
CSV_PATH = OUTPUT_DIR / "images-all.csv"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif"}


def iter_images() -> list[Path]:
    images: list[Path] = []
    for path in CONTENT_DIR.rglob("*"):
        if path.suffix.lower() in IMAGE_EXTS:
            images.append(path.relative_to(ROOT))
    images.sort()
    return images


def search_usage(basename: str) -> list[str]:
    # Exclude sandbox/ to avoid spurious matches in generated artifacts
    cmd = [
        "rg",
        "-l",
        "-F",
        basename,
        ".",
        "--glob",
        "!sandbox/**",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"rg failed for {basename}: {proc.stderr}")
    if proc.returncode == 1:
        return []
    files = [line.strip().lstrip("./") for line in proc.stdout.splitlines() if line.strip()]
    return files


def main() -> None:
    images = iter_images()
    with LIST_PATH.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(str(path) for path in images))
        handle.write("\n")

    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["image", "used", "files"])
        for idx, image in enumerate(images, 1):
            basename = image.name
            files = search_usage(basename)
            used = "y" if files else "n"
            writer.writerow([str(image), used, " :: ".join(files)])
            if idx % 100 == 0:
                print(f"Processed {idx}/{len(images)}", file=sys.stderr)


if __name__ == "__main__":
    main()
