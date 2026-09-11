"""Render a post's link-preview image.

LinkedIn, Slack and X fetch og:image when a post URL is shared. They do not
render SVG, and LinkedIn crops to 1.91:1, so each post that wants a large card
gets a 1200x627 source page in scripts/og/<post-file-stem>.html, usually a
post figure plus a headline on the site's paper, and headless Chrome draws it.

    python3 scripts/og-image.py <post-file-stem>

writes static/og/<stem>.png; set `image = "og/<stem>.png"` in the post's front
matter so the head partial emits it.
"""

import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    stem = sys.argv[1]
    page = ROOT / "scripts" / "og" / f"{stem}.html"
    out = ROOT / "static" / "og" / f"{stem}.png"
    out.parent.mkdir(exist_ok=True)
    subprocess.run(
        [CHROME, "--headless=new", "--hide-scrollbars", "--virtual-time-budget=4000",
         "--window-size=1200,627", f"--screenshot={out}", page.as_uri()],
        check=True, capture_output=True,
    )
    sys.stdout.write(f"{out.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
