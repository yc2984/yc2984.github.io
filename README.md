# yc2984.github.io

Personal blog. Hugo, deployed to GitHub Pages by
[`.github/workflows/hugo.yaml`](.github/workflows/hugo.yaml) on every push to `main`.

Theme: **Cobalt Grid**, in [`themes/cobalt/`](themes/cobalt/) — cream paper, one
cobalt ink, a graph-paper ground. Newsreader for display, Hanken Grotesk for
body, DM Mono for chrome.

## Running it

```bash
hugo server -D          # drafts included, live reload on :1313
hugo --gc --minify      # production build into public/
```

`public/` and `resources/` are build output and are not tracked.

## Writing a post

```bash
hugo new content posts/my-post.md
```

The archetype scaffolds the front matter this theme uses:

| Field        | What it does |
|--------------|--------------|
| `title`      | The real title. Used in `<title>`, RSS and OG tags — keep it plain. |
| `title_html` | Optional. Same title with an italic accent (`with <em>KServe</em>`), used for display only. |
| `summary`    | The standfirst under the title, the line in the index, and the RSS description. |
| `tags`       | Lowercase, hyphenated. They render as mono chips. |
| `toc`        | `true` (default) shows the sticky contents rail. Set `false` for short posts. |
| `aliases`    | Old URLs to redirect from, if you rename a post. |

## The figure vocabulary

This is a two-ink system, so it leans on drawn figures rather than photographs.

**Diagrams** — inline SVG, straight in the markdown. Use `currentColor` for
strokes and it picks up the ink automatically; `var(--paper)` for knocked-out
text on a filled shape.

```
{{< diagram caption="Fig. 1 — what the thing actually does" >}}
<svg viewBox="0 0 700 300" role="img" aria-label="Describe it here.">…</svg>
{{< /diagram >}}
```

**Notes** — the labelled aside, for gotchas and corrections.

```
{{< note "Where I lost an hour" >}}
Markdown goes here.
{{< /note >}}
```

**Headline numbers** — a row of figures with a caption.

```
{{< figures caption="ghz, step load 10→20 rps"
           items="p50=1.70 s|p99=2.70 s|succeeded=57 %" >}}
```

**Pull quote** — a plain markdown `>` blockquote. One per post at most.

**Images** — any markdown image is wrapped in the duotone treatment
automatically (`layouts/_default/_markup/render-image.html`), so a colour
screenshot can't slip through. The alt text becomes the caption.

## Charts

Charts are inline SVG too, drawn by hand, using the tokens in
`themes/cobalt/assets/css/main.css`:

- One series → one colour, no legend, label only the extreme.
- Ordered categories → tonal steps of cobalt.
- Genuinely independent series → the validated three-colour extension:
  `--series-1` cobalt `#1F2BE0`, `--series-2` rust `#9D4616`, `--series-3` jade
  `#0E9977`. Colour-blind separation deutan ΔE 12.8; all three clear 3:1 on the
  paper background.

Every chart should have a table below it carrying the same numbers.

## Layout notes

Body text holds a 33em measure; figures, code blocks and tables are allowed to
run wider. The first paragraph of a post gets a drop cap, so make it a real
paragraph rather than one short sentence.

The theme is committed to light. There is no dark mode — adding one means
choosing a second ground colour, which is a design decision rather than a CSS
toggle.
