+++
title = "The loop is free. Eight decisions behind a self-serve data agent."
title_html = "The loop is <em>free</em>. Eight decisions behind a self-serve data agent."
date = 2026-09-10T09:00:00+02:00
draft = true

summary = "A self-serve data agent whose answers are grounded in sources you can open. What powers it, the eight decisions that made the answers high quality, and what a thousand real questions revealed about the data underneath."

labels = ['AI', 'Data']
tags = ['ai-agents', 'llm', 'data-engineering', 'slack', 'tool-design', 'observability']
toc = true
comments = true
+++

"Only a single correct answer using a single correct source." Anthropic, on their data team's agent.
{.epigraph}

A coding agent works in an open space, and its documentation and tests catch it when it invents something.
A data agent gets one right answer, from one right source, and nothing downstream proves it got there.

And yet the loop that runs the self-serve data agent I maintain is seven lines: ask the model, run the tool it picks, hand the result back, ask again.
Nothing that makes its answers good is in those seven lines.
What makes them good is curated tools with rich descriptions, and grounding in sources we control.

The agent lives in Slack.
Since June it has answered 1,057 questions over 64 active days, from 57 people across 7 channels, and no onboarding doc exists.
87% of its answers point at a source you can open.

By the end of this post you will know three things.
What powers it.
The eight decisions that made the answers high quality.
And what the questions revealed about the data underneath.
Enough to build an agent like it yourself.

## What powers it

Ask. Run. Hand back. Ask again.

A question arrives in a Slack thread.
The model gets it, along with ten tools across four sources: the documentation, the application database, the source code, and the data warehouse.
It asks for a tool, the tool runs, the result is handed back, and the model asks again, 6.8 rounds on average.
When it stops asking, what it wrote is the answer, with its sources and a note of what it did not check.

{{< diagram caption="Fig. 1: one question in, one cited answer out. Four sources, ten tools, one loop, no router." >}}
<svg viewBox="0 0 960 560" role="img" aria-label="A question from a Slack thread enters the agent loop: the model asks for a tool, the tool runs, the result is handed back, 6.8 rounds on average. Out comes a cited answer plus what it did not check. Below, the four sources the ten tools reach: the documentation, the application database, the source code, and the data warehouse.">
  <g fill="none" stroke="currentColor" stroke-width="1.5">
    <rect x="10" y="118" width="170" height="70" rx="12"/>
    <rect x="780" y="118" width="170" height="70" rx="12"/>
  </g>
  <text x="95" y="148" text-anchor="middle" font-family="inherit" font-size="20" font-weight="600" fill="currentColor">Question</text>
  <text x="95" y="170" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">a Slack thread</text>
  <text x="865" y="148" text-anchor="middle" font-family="inherit" font-size="20" font-weight="600" fill="currentColor">Cited answer</text>
  <text x="865" y="170" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">+ what it did not check</text>
  <g fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M180 153 H236"/><path d="M230 153 l-9 -4 v8 z" fill="currentColor"/>
    <path d="M724 153 H780"/><path d="M774 153 l-9 -4 v8 z" fill="currentColor"/>
  </g>
  <svg x="245" y="5" width="470" height="296" viewBox="0 0 470 296">

        <defs>
          <marker id="f1-cy-ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
            <path d="M0 0 L10 5 L0 10 z" fill="#1F9D63"/>
          </marker>
        </defs>
        <rect x="105" y="8" width="260" height="72" rx="14" fill="currentColor"/>
        <text x="235" y="40" text-anchor="middle" font-family="inherit" font-size="25" font-weight="600" fill="#fff">Model</text>
        <text x="235" y="63" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11.5" fill="#9FE3BF">one frontier model</text>
        <rect x="130" y="216" width="210" height="66" rx="14" fill="#fff" stroke="currentColor" stroke-width="1.5"/>
        <text x="235" y="245" text-anchor="middle" font-family="inherit" font-size="22" font-weight="600" fill="currentColor">A tool runs</text>
        <text x="235" y="266" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">one of the ten below</text>
        <path d="M 360 86 C 425 122, 425 178, 348 212" fill="none" stroke="#1F9D63" stroke-width="4" marker-end="url(#f1-cy-ah)"/>
        <path d="M 110 212 C 45 178, 45 122, 110 86" fill="none" stroke="#1F9D63" stroke-width="4" marker-end="url(#f1-cy-ah)"/>
        <text x="418" y="140" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13.5" font-weight="700" fill="#157049">asks for</text>
        <text x="418" y="158" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13.5" font-weight="700" fill="#157049">a tool</text>
        <text x="55" y="140" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13.5" font-weight="700" fill="#157049">result</text>
        <text x="55" y="158" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13.5" font-weight="700" fill="#157049">handed back</text>
        <text x="235" y="156" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" font-weight="700" fill="#157049">&#8635; 6.8 rounds on average</text>
      
  </svg>
  <path d="M480 305 V330" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4"/>
  <path d="M115 330 H845 M115 330 V352 M358 330 V352 M602 330 V352 M845 330 V352" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4"/>
<rect x="10" y="352" width="210" height="150" rx="12" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="115.0" y="382" text-anchor="middle" font-family="inherit" font-size="20" font-weight="600" fill="currentColor">The docs</text>
<text x="115.0" y="402" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">the rule as written</text>
<text x="115.0" y="426" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">search_docs</text>
<text x="115.0" y="442" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">get_page</text>
<rect x="253" y="352" width="210" height="150" rx="12" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="358.0" y="382" text-anchor="middle" font-family="inherit" font-size="20" font-weight="600" fill="currentColor">App database</text>
<text x="358.0" y="402" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">the records, read-only</text>
<text x="358.0" y="426" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">query_db</text>
<text x="358.0" y="442" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">describe_table</text>
<rect x="497" y="352" width="210" height="150" rx="12" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="602.0" y="382" text-anchor="middle" font-family="inherit" font-size="20" font-weight="600" fill="currentColor">The code</text>
<text x="602.0" y="402" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">the rule as implemented</text>
<text x="602.0" y="426" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">grep_code</text>
<text x="602.0" y="442" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">read_file</text>
<text x="602.0" y="458" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">list_files</text>
<rect x="740" y="352" width="210" height="150" rx="12" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="845.0" y="382" text-anchor="middle" font-family="inherit" font-size="20" font-weight="600" fill="currentColor">Warehouse</text>
<text x="845.0" y="402" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">history and scale</text>
<text x="845.0" y="426" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">query_warehouse</text>
<text x="845.0" y="442" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">describe_table</text>
<text x="845.0" y="458" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">list_tables</text>
  <text x="480" y="540" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.6">nothing decides which box to reach for: the model reads all ten descriptions and picks</text>
</svg>
{{< /diagram >}}

That circle is the entire loop, and it is seven lines of code.
No framework, no knowledge base, no vector database.
The loop is free.
Everyone gets the same one.

## Eight decisions

### 1. Few questions, answered well

Wired in: the documentation, the application database, the source code, the data warehouse.
Deliberately left out: the internal wiki, free search over Slack, the open web, and anything I cannot vouch for.
One confidently wrong answer costs more than ten it declines to give.

### 2. Rich descriptions, not predefined routes

There is no router.
A router is a classifier in front of the tools, and a classifier is an if-else in disguise: every new scenario is another branch.
Instead, the model reads all ten tool descriptions and decides where to look.
Adding a source is writing one description.
Fixing routing is sharpening a sentence.
Descriptions scale.
A classifier degrades as the scenarios multiply.

{{< diagram caption="Fig. 2: a router is an if-else in disguise. Rich descriptions put every tool in view and let the model pick." >}}
<svg viewBox="0 0 980 260" role="img" aria-label="Left: a router. The question goes to a classifier that forwards it to one tool; a wrong guess strands it at the wrong tool. Right: rich descriptions. The question and all ten described tools go to one model, which reads every description and picks.">
  <text x="240" y="24" text-anchor="middle" font-family="inherit" font-size="18" font-weight="600" fill="currentColor">A router</text>
  <text x="740" y="24" text-anchor="middle" font-family="inherit" font-size="18" font-weight="600" fill="currentColor">Rich descriptions</text>
  <svg x="5" y="40" width="470" height="210" viewBox="0 0 470 210">

          <defs>
            <marker id="f2a-rt-c" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#C2632B"/>
            </marker>
            <marker id="f2a-rt-x" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#B3261E"/>
            </marker>
          </defs>
          <rect x="6" y="80" width="118" height="50" rx="11" fill="none" stroke="currentColor" stroke-width="1.5"/>
          <text x="65" y="110" text-anchor="middle" font-family="inherit" font-size="19" font-weight="600" fill="currentColor">Question</text>
          <path d="M124 105 H166" fill="none" stroke="#C2632B" stroke-width="2.5" marker-end="url(#f2a-rt-c)"/>
          <rect x="172" y="72" width="132" height="66" rx="11" fill="#fff" stroke="#C2632B" stroke-width="1.5"/>
          <text x="238" y="100" text-anchor="middle" font-family="inherit" font-size="19" font-weight="600" fill="currentColor">Classifier</text>
          <text x="238" y="122" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" fill="#C2632B">if-else in disguise</text>
          <g fill="none" stroke="currentColor" stroke-width="1.4">
            <rect x="386" y="14"  width="72" height="34" rx="8"/>
            <rect x="386" y="62"  width="72" height="34" rx="8"/>
            <rect x="386" y="110" width="72" height="34" rx="8"/>
            <rect x="386" y="158" width="72" height="34" rx="8"/>
          </g>
          <path d="M304 96 C 340 88, 352 84, 382 79" fill="none" stroke="#C2632B" stroke-width="2.5" marker-end="url(#f2a-rt-c)"/>
          <path d="M304 118 C 340 130, 352 152, 380 170" fill="none" stroke="#B3261E" stroke-width="2.5" stroke-dasharray="6 5" marker-end="url(#f2a-rt-x)"/>
          <text x="424" y="184" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" font-weight="700" fill="#B3261E">&#10007;</text>
          <text x="330" y="197" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" fill="#B3261E">wrong guess</text>
        
  </svg>
  <svg x="505" y="40" width="470" height="210" viewBox="0 0 470 210">

          <defs>
            <marker id="f2b-rd-g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#1F9D63"/>
            </marker>
          </defs>
          <rect x="6" y="80" width="118" height="50" rx="11" fill="none" stroke="currentColor" stroke-width="1.5"/>
          <text x="65" y="110" text-anchor="middle" font-family="inherit" font-size="19" font-weight="600" fill="currentColor">Question</text>
          <path d="M124 105 H166" fill="none" stroke="#1F9D63" stroke-width="2.5" marker-end="url(#f2b-rd-g)"/>
          <rect x="172" y="72" width="132" height="66" rx="11" fill="currentColor"/>
          <text x="238" y="100" text-anchor="middle" font-family="inherit" font-size="19" font-weight="600" fill="#fff">Model</text>
          <text x="238" y="122" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" fill="#9FE3BF">reads all ten, picks</text>
          <g fill="none" stroke="#1F9D63" stroke-width="1.4">
            <rect x="386" y="14"  width="72" height="34" rx="8"/>
            <rect x="386" y="62"  width="72" height="34" rx="8"/>
            <rect x="386" y="110" width="72" height="34" rx="8"/>
            <rect x="386" y="158" width="72" height="34" rx="8"/>
          </g>
          <g fill="none" stroke="#1F9D63" stroke-width="1.4" opacity=".45">
            <path d="M304 90 C 340 70, 352 44, 382 33"/>
            <path d="M304 112 C 340 122, 352 122, 382 127"/>
            <path d="M304 118 C 340 140, 352 160, 382 173"/>
          </g>
          <path d="M304 96 C 340 88, 352 84, 382 79" fill="none" stroke="#1F9D63" stroke-width="3.5" marker-end="url(#f2b-rd-g)"/>
          <text x="318" y="56" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="#157049">every description in view</text>
        
  </svg>
  <path d="M490 40 V250" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 4" opacity="0.5"/>
</svg>
{{< /diagram >}}

### 3. Grounded and reproducible

Every answer has to be checkable by the reader, and that is enforced by code, not requested in a prompt.
The sources are recorded by code: the loop logs every source it opens, and the model cannot edit that record.
No sources, and it says so: zero sources stamps the answer as from general knowledge, not verified.
The exact SQL, verbatim: a button on the answer replays every query exactly as it ran.
The references section is the model writing.
The recorded log is the control.

### 4. Clone the repo. Do not wrap it in a protocol

For code, the agent greps a local clone.
Nothing sits between the agent and the source.

A grep is a grep: a regular expression over the code exactly as it is on disk now, and a byte-range read of any file.
GitHub's code search API can do neither: it matches keywords only, against an index that is rebuilt after a push and lags behind the latest commit.
Nobody in the hot path: no rate limit, no auth, no third-party outage arriving in the middle of an investigation.
The tool list stays ours: an MCP passthrough once grew a write tool between deploys, and the agent used it, unprompted.
Nothing had changed on our side.
Ripgrep over a local clone is what makes Claude Code good at code.
Same mechanism here.

### 5. Guardrails, written as refusals

Its guardrails are its permissions: three identities of its own, and what each one is refused.
A cloud role with no stored key that rotates hourly, for the warehouse.
A read-only database role, for the application database.
A GitHub App whose token expires hourly, for three repositories and no others.

{{< diagram caption="Fig. 3: three identities of its own, and what each is refused. The red arrows are the product." >}}
<svg viewBox="0 0 960 320" role="img" aria-label="Three identities, one per lane. The cloud role can query and read the warehouse; INSERT and CTAS are refused. The database role can SELECT from the application database; any write is refused. The GitHub App can clone and read three repositories; push is refused.">
  <text x="10" y="40" font-family="inherit" font-size="19" font-weight="600" fill="currentColor">Cloud role</text>
  <text x="10" y="60" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">no stored key, rotates hourly</text>
  <svg x="300" y="10" width="360" height="89" viewBox="0 0 300 74">

          <defs>
            <marker id="f3a-l1g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#1F9D63"/></marker>
            <marker id="f3a-l1r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#B3261E"/></marker>
          </defs>
          <path d="M4 24 H274" fill="none" stroke="#1F9D63" stroke-width="3" marker-end="url(#f3a-l1g)"/>
          <text x="140" y="14" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12.5" font-weight="700" fill="#157049">query &middot; read</text>
          <path d="M4 58 H160" fill="none" stroke="#B3261E" stroke-width="3" marker-end="url(#f3a-l1r)"/>
          <rect x="170" y="44" width="5" height="28" rx="2" fill="#B3261E"/>
          <text x="188" y="63" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12.5" font-weight="700" fill="#B3261E">&#10007; INSERT, CTAS</text>
        
  </svg>
  <text x="690" y="50" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">the data warehouse</text>
  <path d="M10 98 H950" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 4" opacity="0.4"/>
  <text x="10" y="140" font-family="inherit" font-size="19" font-weight="600" fill="currentColor">Database role</text>
  <text x="10" y="160" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">read-only</text>
  <svg x="300" y="110" width="360" height="89" viewBox="0 0 300 74">

          <defs>
            <marker id="f3b-l2g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#1F9D63"/></marker>
            <marker id="f3b-l2r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#B3261E"/></marker>
          </defs>
          <path d="M4 24 H274" fill="none" stroke="#1F9D63" stroke-width="3" marker-end="url(#f3b-l2g)"/>
          <text x="140" y="14" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12.5" font-weight="700" fill="#157049">SELECT</text>
          <path d="M4 58 H160" fill="none" stroke="#B3261E" stroke-width="3" marker-end="url(#f3b-l2r)"/>
          <rect x="170" y="44" width="5" height="28" rx="2" fill="#B3261E"/>
          <text x="188" y="63" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12.5" font-weight="700" fill="#B3261E">&#10007; any write</text>
        
  </svg>
  <text x="690" y="150" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">the app database, read replica</text>
  <path d="M10 198 H950" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 4" opacity="0.4"/>
  <text x="10" y="240" font-family="inherit" font-size="19" font-weight="600" fill="currentColor">GitHub App</text>
  <text x="10" y="260" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">token expires hourly</text>
  <svg x="300" y="210" width="360" height="89" viewBox="0 0 300 74">

          <defs>
            <marker id="f3c-l3g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#1F9D63"/></marker>
            <marker id="f3c-l3r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0 L10 5 L0 10 z" fill="#B3261E"/></marker>
          </defs>
          <path d="M4 24 H274" fill="none" stroke="#1F9D63" stroke-width="3" marker-end="url(#f3c-l3g)"/>
          <text x="140" y="14" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12.5" font-weight="700" fill="#157049">clone &middot; read</text>
          <path d="M4 58 H160" fill="none" stroke="#B3261E" stroke-width="3" marker-end="url(#f3c-l3r)"/>
          <rect x="170" y="44" width="5" height="28" rx="2" fill="#B3261E"/>
          <text x="188" y="63" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12.5" font-weight="700" fill="#B3261E">&#10007; push</text>
        
  </svg>
  <text x="690" y="250" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.75">three repositories, no others</text>
  <text x="480" y="308" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.6">every red arrow is proven by a live check that runs the forbidden thing and records the denial</text>
</svg>
{{< /diagram >}}

Every blocked arrow is proven by a live check that runs the forbidden thing.

### 6. Safe to deploy, and fast to change

Read it as a timeline.
On commit, 433 tests, and a red suite cannot land.
On push, CI runs inside the image, the container the cluster runs.
After deploy, live checks run as the pod: capabilities, fences, identity, and every answer must name its sources.
On every start, a startup check: no grounding files, no start.

Answer quality has its own check, a question bank of real colleague questions with human-verified answers.
Each of these is one command: evaluate offline, test the live agent, verify a deploy.
Shipping rides the same GitOps path every other service uses.
Nothing bespoke.
Everything that proves the deployed agent runs in the image the cluster runs.
No works-on-my-machine.

### 7. Start simple: zero infrastructure

The agent is one pod that dials out to Slack over one websocket.
Nothing comes in: no endpoint, no webhook.
The thread is the memory, re-read on every mention, nothing stored.
Unchanged since the hackathon, and 0 outage mentions in roughly 400 questions since the cutover to the cluster.
Nothing to host.
Nothing to store.

### 8. Telemetry from day one

Every answer is recorded: the tools, the rounds, the exact SQL.
From that one record: what people actually ask, where the gaps are, what data is missing, which of our own words confuse us, and how to tune the agent's tools, rounds and cost.
Build the measuring before you need the measurement.

## The one line to leave with

Spend your time on the data foundation: the sources you ground in, and what they say about themselves.
Not on the loop.

Grounding means the answer comes from a live call against a source we own, not from the model's memory.
Anthropic's data team reached the same place with their own agent: the complexity lies in the ambiguity of the data, and once a question is mapped to the right entity in the data model, the SQL is the easy part.

## What people actually ask

The first 518 of the 1,057 questions, read and themed by hand.
The six biggest themes:

| Theme | Questions |
|---|---|
| Record lookups and exports | 123 |
| How a number is calculated | 75 |
| Ad-hoc statistics | 72 |
| Analysis for external partners | 45 |
| Support debugging | 44 |
| Live progress tracking | 44 |

Two of three questions ask it to query our databases directly.
The 45 partner-analysis questions have no product serving them today.
And 0 outage mentions in the roughly 400 questions since the cutover.

## The one gap

238 of those 518 questions needed somebody to say which source is the authority.

75 were answered by reading the source code.
Questions about how a number is calculated, from 20 colleagues, in all seven channels, and the rule is written down nowhere except the code itself.

171 needed the agent to reverse-engineer a table first.
On one request it gave five successive answers from five different "authoritative" tables before the right one, and every correction came from one colleague's memory.

We document our tables.
We never record which table is the authority for a given business question, or what its words mean.
One everyday term names three different things in our own database.

## Work waiting for an owner

The data foundation: column comments the agent can see, a description on every dataset, an authority per business question, an analytics layer.

Run it safely: per-user identity, disclosure rules as code, memory that survives restarts, real monitoring.

Product and knowledge: a reaction that files a ticket, the partner-analysis demand, knowledge on demand, evaluations per domain.

None of it is the loop.
All of it is the data foundation, and that is where the interesting work is.
