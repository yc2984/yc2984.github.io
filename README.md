# yc2984.github.io

Personal blog. Hugo, deployed to GitHub Pages by
[`.github/workflows/hugo.yaml`](.github/workflows/hugo.yaml) on every push to `main`.

Theme: **Cobalt Grid**, in [`themes/cobalt/`](themes/cobalt/) — cream paper, one
cobalt ink, a graph-paper ground. Newsreader for display, Hanken Grotesk for
body, DM Mono for chrome.

Switching the look is one line in `hugo.toml`: `theme = 'cobalt'` for the cobalt
grid, or `theme = ['quiet', 'cobalt']` for [`themes/quiet/`](themes/quiet/), one
ink on warm paper. `quiet` overrides only the stylesheet, the font link and the
home page and inherits every other layout from `cobalt`, so it must be listed
first. Both build from the same content; run `hugo --theme quiet,cobalt` to
check the other one without editing the config.

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
| `comments`   | `true` (default under `/posts/`) shows the giscus thread. Set `false` to close one. |
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

## Comments

Comments are GitHub Discussions, drawn by [giscus](https://giscus.app). There is
no server and no database. The first time someone comments on a page the giscus
app opens a discussion in the **Announcements** category keyed on the page's
pathname; the widget is an iframe reading and writing that discussion through
the GitHub API. Commenting needs a GitHub account.

Two things have to be true on the GitHub side before any of this renders:
Discussions enabled on the repo, and the [giscus app](https://github.com/apps/giscus)
installed and granted access to it. The app is the part that is easy to miss,
because everything looks configured without it and the widget just reports
`giscus is not installed on this repository`. You can check from the command
line: anything other than that message means the app is on.

```bash
curl -s "https://giscus.app/api/discussions?repo=yc2984%2Fyc2984.github.io&category=Announcements&number=0&strict=false&first=1"
```

Configured in [`hugo.toml`](hugo.toml) under `[params.giscus]`. The two IDs
there are GraphQL node IDs, not the names sitting next to them:

```bash
gh api repos/yc2984/yc2984.github.io --jq .node_id
```

Two choices worth keeping: **Announcements**, because only maintainers can open
a thread in it, so the category cannot fill up with discussions that match no
page; and `mapping = pathname` rather than `title`, because titles here carry
italic markup in `title_html` and posts get renamed, while pathnames hold still.

On by default everywhere under `/posts/`, off everywhere else — so `/about/`
stays quiet without being told to. `comments = false` in a post closes its
thread; `comments = true` on a page outside `/posts/` opens one. Delete the
`[params.giscus]` table and comments vanish site-wide, which is also what makes
a fork of this theme render nothing.

### Styling it

Giscus ships a fixed set of themes and none of them are cream-and-cobalt, so
`data-theme` points at [`static/giscus.css`](static/giscus.css) instead. In
custom mode giscus loads that file and nothing else, so it opens by importing
giscus's own `light.css` for the couple of hundred Primer variables that don't
need changing, then remaps the ones that show: ground to the cream, text and
rules to the cobalt, the primary button off GitHub green and onto the ink, and
code to tonal cobalt with the rust and the jade doing the two distinctions that
genuinely need separating. Avatars are greyed and squared so a colour photo
can't break the two inks, and radii are flattened because nothing else on this
site has a rounded corner.

Two things that will catch you out:

- The iframe is a separate document. Nothing in
  [`themes/cobalt/assets/css/main.css`](themes/cobalt/assets/css/main.css)
  reaches it, so the tokens are restated at the top of `static/giscus.css` and
  have to be kept in step by hand.
- The theme is fetched from `https://yc2984.github.io/giscus.css`, so **it does
  not apply on localhost**: giscus cannot reach a URL on your machine. Under
  `hugo server` the widget renders in giscus's default light theme. The styling
  only shows up on the deployed site.

## Layout notes

Body text holds a 33em measure; figures, code blocks and tables are allowed to
run wider. The first paragraph of a post gets a drop cap, so make it a real
paragraph rather than one short sentence.

The theme is committed to light. There is no dark mode — adding one means
choosing a second ground colour, which is a design decision rather than a CSS
toggle.


## Not done yet

- **Dark mode.** Deliberately absent — it needs a second ground colour chosen,
  not a CSS toggle.
- **OG images.** No per-post social card yet.
