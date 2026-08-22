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
| `labels`     | The top-level filter chips on the home page. Pick from `params.label_order` in `hugo.toml`: Tech, Data, AI, Thoughts, Music, Art & Science. One or two per post. |
| `tags`       | Finer-grained, lowercase, hyphenated. Listed at the foot of a post. |
| `toc`        | `true` (default) shows the sticky contents rail. Set `false` for short posts. |
| `aliases`    | Old URLs to redirect from, if you rename a post. |

## Labels and the filter

`labels` is the coarse cut — the chips above the index. `tags` are the fine cut,
at the foot of a post. Add a label to `params.label_order` in `hugo.toml` to
control where its chip appears; the order there is the order on the page.

A chip only appears once at least one post carries that label, so the row never
shows a filter that leads nowhere. Each chip is a real link to `/labels/<name>/`
and works with JavaScript off; the inline script in
`layouts/partials/filter.html` upgrades it to instant in-page filtering and
writes the label to the URL hash, so a filtered view can be shared.

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


## Not done yet

- **Comments.** Nothing is wired up. The realistic options, cheapest first:
  *Giscus* (comments as GitHub Discussions — one script tag, commenters need a
  GitHub account, free, no server); *Cusdis* or *Isso* (self-hosted, anyone can
  comment, needs somewhere to run); *Mastodon reply-thread embedding* (you post
  the link, the thread becomes the comments). Giscus is about half an hour of
  work including styling it to the two-ink palette; anything self-hosted is a
  service to run and moderate forever.
- **Dark mode.** Deliberately absent — it needs a second ground colour chosen,
  not a CSS toggle.
- **OG images.** No per-post social card yet.
