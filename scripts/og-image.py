"""Render one of a post's diagrams as its link-preview image.

LinkedIn, Slack and X fetch og:image when a post URL is shared. They do not
render SVG, and LinkedIn crops to 1.91:1, so the image is a 1200x627 PNG of the
chosen diagram on the site's paper, drawn by headless Chrome.

    python3 scripts/og-image.py <post-file-stem> <figure-number>

writes static/og/<stem>.png; set `image = "og/<stem>.png"` in the post's front
matter so the head partial emits it.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH, HEIGHT = 1200, 627
ROOT = Path(__file__).resolve().parent.parent

PAGE = """<!doctype html>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600&family=DM+Mono:wght@400;500&display=block">
<style>
  html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; }}
  body {{
    background-color: #F0EBDE;
    background-image:
      linear-gradient(rgba(31, 43, 224, 0.10) 1px, transparent 1px),
      linear-gradient(90deg, rgba(31, 43, 224, 0.10) 1px, transparent 1px);
    background-size: 36px 36px;
    color: #1F2BE0;
    font-family: "Hanken Grotesk", -apple-system, sans-serif;
    display: flex; align-items: center; justify-content: center;
  }}
  body > svg {{ width: {sw:.0f}px; height: {sh:.0f}px; }}
</style>
{svg}
"""


def diagram_svg(post: Path, number: int) -> str:
    blocks = re.findall(r"\{\{< diagram[^>]*>\}\}(.*?)\{\{< /diagram >\}\}", post.read_text(), re.S)
    if not 1 <= number <= len(blocks):
        sys.exit(f"{post.name} has {len(blocks)} diagrams; asked for {number}")
    return blocks[number - 1].strip()


def main() -> None:
    stem, number = sys.argv[1], int(sys.argv[2])
    svg = diagram_svg(ROOT / "content" / "posts" / f"{stem}.md", number)
    out = ROOT / "static" / "og" / f"{stem}.png"
    out.parent.mkdir(exist_ok=True)
    vw, vh = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    scale = min((WIDTH - 100) / vw, (HEIGHT - 60) / vh)
    html = PAGE.format(w=WIDTH, h=HEIGHT, sw=vw * scale, sh=vh * scale, svg=svg)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as page:
        page.write(html)
    subprocess.run(
        [CHROME, "--headless=new", "--hide-scrollbars", "--virtual-time-budget=3000",
         f"--window-size={WIDTH},{HEIGHT}", f"--screenshot={out}", f"file://{page.name}"],
        check=True, capture_output=True,
    )
    sys.stdout.write(f"{out.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
