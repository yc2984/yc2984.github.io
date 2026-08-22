+++
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
# optional: same title with an italic accent, used for display only
# title_html = 'Serving models on Kubernetes with <em>KServe</em>'
date = {{ .Date }}
draft = true

# the standfirst under the title, and the line in the index and RSS
summary = ""

tags = []
toc = true
# comments are on for everything under /posts/; set false to close a thread
comments = true
+++

Opening paragraph. Make it a real paragraph — it gets the drop cap, so a single
short sentence looks odd.

## First section

Section headings are set in mono small-caps. Keep them to h2; h3 exists for
sub-points inside a section.

{{</* note "Where I lost an hour" */>}}
A labelled aside. Use it for gotchas, corrections and things that cost you time.
{{</* /note */>}}

{{</* figures caption="ghz, step load 10→20 rps" items="p50=1.70 s|p99=2.70 s|succeeded=57 %" */>}}

{{</* diagram caption="Fig. 1 — what the thing actually does" */>}}
<svg viewBox="0 0 700 300" role="img" aria-label="Describe the diagram here."> </svg>
{{</* /diagram */>}}

> A blockquote is the pull quote — big, italic, between double rules. One per
> post at most, or it stops meaning anything.
