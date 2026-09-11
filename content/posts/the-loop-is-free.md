+++
title = "Eight decisions behind a self-serve data agent"
slug = "eight-decisions-behind-a-self-serve-data-agent"
title_html = "Eight decisions behind a <em>self-serve</em> data agent"
date = 2026-09-10T23:49:01+02:00
draft = false

summary = "A self-serve data agent whose answers are grounded in sources you can open. What powers it, the eight decisions that made the answers high quality, and what a thousand real questions revealed about the data underneath."

labels = ['AI', 'Data']
tags = ['ai-agents', 'llm', 'data-engineering', 'slack', 'tool-design', 'observability']
toc = true
comments = true
+++

“Coding is an open-ended solution space that rewards the models’ creativity, while documentation and tests provide natural guardrails against hallucination. In contrast, for analytics use cases, there’s often only a single correct answer using a single correct source in which there’s no deterministic way of proving the correctness.” Anthropic, on their own data team’s agent.
{.epigraph}

That is the whole difficulty in one place: nothing downstream tells a data agent it was wrong.

And yet the loop that runs the self-serve data agent my team and I built in a two-day hackathon, and that I have maintained since, is seven lines: ask the model, run the tool it picks, hand the result back, ask again.
Nothing that makes its answers good is in those seven lines.
What makes them good is curated tools with rich descriptions, and grounding in sources we control, and the rest of this post is that sentence taken apart.

First, the receipt.
The agent lives in Slack.
Since June it has answered 1,057 questions on 64 active days, from 57 people across seven channels, and no onboarding doc exists; people tagged it, it answered, and they told each other.
87% of its answers point at a source you can open, which is the property I care about most and the one the rest of this post is organised around.

By the end you should know three things: what powers it, the eight decisions that made the answers high quality, and what a thousand questions revealed about the data underneath.
That should be enough to build one like it yourself, and I would like you to, because the interesting problems turn out not to be in the agent at all.

## What powers it

Ask. Run. Hand back. Ask again.

A question arrives in a Slack thread.
The model receives it together with ten tools spread across four sources: the documentation, the application database, the source code, and the data warehouse.
It asks for one tool.
The code runs it, hands the result back, and the model asks again, 6.8 rounds on average, until it stops asking and whatever it has written is the answer, with its sources attached and a note of what it did not check.

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
There is no framework underneath it, no knowledge base, no vector database, and nothing that decides which of the four boxes to reach for.
I am not claiming any of this is clever.
The loop is free, and everyone gets the same one.
The months went into what the loop reads.

## Eight decisions

### Few questions, answered well {.decision}

Four sources are wired in: the documentation, the application database, the source code, the data warehouse.
Four are left out on purpose: the internal wiki, free search over Slack, the open web, and anything I cannot vouch for.
That is not a judgement on those sources.
It is that I cannot control what comes back from them, and the arithmetic of trust is lopsided: one confidently wrong answer costs more than ten questions the agent politely declines to answer.
So the wiring stays narrow.

### Rich descriptions, not predefined routes {.decision}

There is no router.
The obvious design puts a classifier in front of the tools to decide whether a question is about code or data or documentation, and the obvious design is an if-else in disguise: every new scenario becomes another branch, and it degrades exactly as the scenarios multiply.
Instead the model reads all ten tool descriptions and decides for itself where to look.
Adding a source means writing one description.
Fixing a routing mistake means sharpening a sentence.
Descriptions scale in a way a classifier never will, and they are where most of my writing time on this project has gone.

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

### Grounded and reproducible {.decision}

Every answer has to be checkable by the person reading it, and I mean enforced by code rather than requested in a prompt.
Three mechanisms do it.
The sources are recorded by code: the loop logs every source it opens, and the model cannot edit that record, so it cannot cite a page it never fetched.
If it finishes with no sources, the code says so and stamps the answer as from general knowledge, not verified.
And every query is kept verbatim as it ran, behind a button on the answer that replays the chain.
The References section you read in Slack is the model writing.
The recorded log underneath is the control, and the log is the thing I audit.

### Clone the repo. Do not wrap it in a protocol {.decision}

For code, the agent greps a local clone, and nothing sits between it and the source.
A grep is a grep: a regular expression over the files exactly as they are on disk, and a byte-range read of any of them.
GitHub's code search API can do neither; it matches keywords against an index rebuilt after each push, so it is both less precise and a little behind.
There is also nobody in the hot path: no rate limit, no auth, no third-party outage arriving halfway through an investigation.
And the tool list stays ours.
An MCP passthrough once grew a write tool between two deploys, and the agent used it, unprompted, while nothing had changed on our side.
If you use Claude Code you already trust this mechanism, because ripgrep over a local checkout is what makes it good at code.
The same thing works here.

### Guardrails, written as refusals {.decision}

The agent's guardrails are its permissions, not a paragraph of English in the prompt.
It has three identities of its own: a cloud role with no stored key that rotates hourly, for the warehouse; a read-only database role, for the application database; and a GitHub App whose token expires hourly and can see three repositories and no others.
The green arrows in the figure are what each identity may do.
The red ones are the product.

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

Every blocked arrow is proven by a live check that runs the forbidden thing and records the denial.

### Safe to deploy, fast to change {.decision}

I wanted this from day one: a CI strict enough that merging is boring, because boring merges are what let one person deploy continuously and iterate fast without lying awake.
So the guarding happens at every stage.
On commit, 433 tests run as a gate and a red suite cannot land.
On push, CI runs inside the image, the same container the cluster will run, so a green runner proves something about the artefact and not about the runner.
After deploy, live checks run as the pod itself: can it reach every source, are the fences holding, is it the checkout we think it is, and does every answer name its sources.
On every start the pod looks for its grounding files and refuses to come up without them.

None of that says an answer is right, so there is a question bank of real colleague questions with human-verified answers for that.
Each check is one command: evaluate offline, test the live agent, verify a deploy.
Shipping rides the same GitOps path every other service uses, nothing bespoke.
Everything that proves the deployed agent proves it in the image the cluster runs.
No works-on-my-machine.

### Start simple: zero infrastructure {.decision}

The agent is one pod that dials out to Slack over one websocket, and nothing comes in: no endpoint, no webhook, no address to attack.
The thread is the memory, re-read on every mention, so nothing is stored anywhere.
That drawing has not changed since the hackathon, and since the move to the cluster there have been zero outage mentions in roughly 400 questions.
Nothing to host, nothing to store, nothing to be paged about.

### Telemetry from day one {.decision}

Every answer is recorded: the tools, the rounds, the exact SQL.

{{< diagram caption="Fig. 4: two things the record answers without new instrumentation. Where the agent looks, as tool calls grouped by source with the share of answers that touched each; and how long it thinks, as rounds per answer." >}}
<svg viewBox="0 0 960 440" role="img" aria-label="Left: tool calls per tool, grouped by source, from the telemetry of every Slack answer. The application database is queried most, then the warehouse, then the code, then the documentation. Right: rounds per answer, a long-tailed distribution with an average of 6.8.">
<text x="20" y="30" font-family="inherit" font-size="16" font-weight="600" fill="currentColor">Where it looks</text>
<text x="20" y="48" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">tool calls, June to September</text>
<text x="20" y="78" font-family="inherit" font-size="13" font-weight="600" fill="currentColor">App database</text>
<text x="150" y="78" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">in 55% of answers</text>
<text x="142" y="99" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">query_db</text>
<path d="M150 88 h286.0 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-286.0 z" fill="currentColor" opacity="0.85"/>
<text x="446.0" y="99" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">3,876</text>
<text x="142" y="119" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">describe_table</text>
<path d="M150 108 h78.8250773993808 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-78.8250773993808 z" fill="currentColor" opacity="0.85"/>
<text x="238.8250773993808" y="119" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">1,107</text>
<text x="20" y="142" font-family="inherit" font-size="13" font-weight="600" fill="currentColor">Warehouse</text>
<text x="150" y="142" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">in 34% of answers</text>
<text x="142" y="163" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">query_warehouse</text>
<path d="M150 152 h125.96130030959753 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-125.96130030959753 z" fill="currentColor" opacity="0.85"/>
<text x="285.9613003095975" y="163" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">1,737</text>
<text x="142" y="183" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">describe_table</text>
<path d="M150 172 h44.70743034055727 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-44.70743034055727 z" fill="currentColor" opacity="0.85"/>
<text x="204.70743034055727" y="183" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">651</text>
<text x="142" y="203" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">list_tables</text>
<path d="M150 192 h13.732198142414859 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-13.732198142414859 z" fill="currentColor" opacity="0.85"/>
<text x="173.73219814241486" y="203" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">237</text>
<text x="20" y="226" font-family="inherit" font-size="13" font-weight="600" fill="currentColor">The code</text>
<text x="150" y="226" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">in 28% of answers</text>
<text x="142" y="247" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">grep_code</text>
<path d="M150 236 h72.61506707946336 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-72.61506707946336 z" fill="currentColor" opacity="0.85"/>
<text x="232.61506707946336" y="247" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">1,024</text>
<text x="142" y="267" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">read_file</text>
<path d="M150 256 h50.31888544891641 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-50.31888544891641 z" fill="currentColor" opacity="0.85"/>
<text x="210.3188854489164" y="267" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">726</text>
<text x="142" y="287" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">list_files</text>
<path d="M150 276 h3.1078431372549016 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-3.1078431372549016 z" fill="currentColor" opacity="0.85"/>
<text x="163.1078431372549" y="287" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">95</text>
<text x="20" y="310" font-family="inherit" font-size="13" font-weight="600" fill="currentColor">The docs</text>
<text x="150" y="310" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">in 13% of answers</text>
<text x="142" y="331" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">search_docs</text>
<path d="M150 320 h10.8890608875129 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-10.8890608875129 z" fill="currentColor" opacity="0.85"/>
<text x="170.8890608875129" y="331" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">199</text>
<text x="142" y="351" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.8">get_page</text>
<path d="M150 340 h1.3869969040247678 a4 4 0 0 1 4 4 v6 a4 4 0 0 1 -4 4 h-1.3869969040247678 z" fill="currentColor" opacity="0.85"/>
<text x="161.38699690402476" y="351" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor">72</text>
<text x="590" y="30" font-family="inherit" font-size="16" font-weight="600" fill="currentColor">How long it thinks</text>
<text x="590" y="48" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">answers by rounds before the model stopped asking</text>
<path d="M590 330 H940" stroke="currentColor" stroke-width="1" opacity="0.4"/>
<path d="M591.0 330 v-236.0 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v236.0 z" fill="currentColor" opacity="0.85"/>
<text x="597.0" y="346" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">1</text>
<path d="M605.0 330 v-158.5 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v158.5 z" fill="currentColor" opacity="0.85"/>
<path d="M619.0 330 v-181.3 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v181.3 z" fill="currentColor" opacity="0.85"/>
<path d="M633.0 330 v-169.2 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v169.2 z" fill="currentColor" opacity="0.85"/>
<path d="M647.0 330 v-152.5 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v152.5 z" fill="currentColor" opacity="0.85"/>
<text x="653.0" y="346" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">5</text>
<path d="M661.0 330 v-126.6 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v126.6 z" fill="currentColor" opacity="0.85"/>
<path d="M675.0 330 v-105.4 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v105.4 z" fill="currentColor" opacity="0.85"/>
<path d="M689.0 330 v-87.1 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v87.1 z" fill="currentColor" opacity="0.85"/>
<path d="M703.0 330 v-65.9 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v65.9 z" fill="currentColor" opacity="0.85"/>
<path d="M717.0 330 v-44.6 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v44.6 z" fill="currentColor" opacity="0.85"/>
<text x="723.0" y="346" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">10</text>
<path d="M731.0 330 v-53.7 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v53.7 z" fill="currentColor" opacity="0.85"/>
<path d="M745.0 330 v-37.0 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v37.0 z" fill="currentColor" opacity="0.85"/>
<path d="M759.0 330 v-41.6 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v41.6 z" fill="currentColor" opacity="0.85"/>
<path d="M773.0 330 v-23.3 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v23.3 z" fill="currentColor" opacity="0.85"/>
<path d="M787.0 330 v-38.5 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v38.5 z" fill="currentColor" opacity="0.85"/>
<text x="793.0" y="346" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">15</text>
<path d="M801.0 330 v-61.3 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v61.3 z" fill="currentColor" opacity="0.85"/>
<path d="M815.0 330 v-27.9 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v27.9 z" fill="currentColor" opacity="0.85"/>
<path d="M829.0 330 v-23.3 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v23.3 z" fill="currentColor" opacity="0.85"/>
<path d="M843.0 330 v-3.6 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v3.6 z" fill="currentColor" opacity="0.85"/>
<path d="M857.0 330 v-3.6 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v3.6 z" fill="currentColor" opacity="0.85"/>
<text x="863.0" y="346" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">20</text>
<path d="M871.0 330 v-9.7 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v9.7 z" fill="currentColor" opacity="0.85"/>
<path d="M885.0 330 v-0.0 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v0.0 z" fill="currentColor" opacity="0.85"/>
<path d="M899.0 330 v-0.0 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v0.0 z" fill="currentColor" opacity="0.85"/>
<path d="M913.0 330 v-0.0 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v0.0 z" fill="currentColor" opacity="0.85"/>
<path d="M927.0 330 v-6.6 a4 4 0 0 1 4 -4 h4.0 a4 4 0 0 1 4 4 v6.6 z" fill="currentColor" opacity="0.85"/>
<text x="933.0" y="346" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">25</text>
<path d="M677.5 100 V330" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4"/>
<text x="683.5" y="112" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" font-weight="700" fill="currentColor">6.8 rounds on average</text>
<text x="940" y="364" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="currentColor" opacity="0.65">158 answers needed one round; 7 ran to the last</text>
</svg>
{{< /diagram >}}

Out of that one record come the things I actually wanted to know: what people ask, where the gaps are, what data is missing, which of our own words confuse us, and how to tune the agent's tools, rounds and cost.
The figure is two of those, read straight off the log: the application database is where most questions go, the documentation is where the fewest do, and most answers finish in a handful of rounds with a long tail that runs to the cap.
Build the measuring before you need the measurement.
Every number in this post came out of it.

## The one line to leave with

Spend your time on the data foundation: the sources you ground in, and what they say about themselves.
Not on the loop.

Grounding, precisely, means the answer comes from a live call against a source we own rather than from the model's memory.
Anthropic's data team ended up in the same place with their own agent.

“For self-service agentic business analytics, the complexity mainly lies in the ambiguity of the data. The central problem comes down to our ability to map a user’s question to specific and up-to-date entities in our data model and know the correct way of working with them. If we can do that, then the resulting execution and SQL becomes trivial.” Anthropic, on their own data team’s agent.
{.epigraph}

## What people actually ask

I read the first 518 of the 1,057 questions by hand and gave each one a theme.
Six themes cover most of them.

| Theme | Questions |
|---|---|
| Record lookups and exports | 123 |
| How a number is calculated | 75 |
| Ad-hoc statistics | 72 |
| Analysis for external partners | 45 |
| Support debugging | 44 |
| Live progress tracking | 44 |

Two of every three questions ask the agent to query our databases directly.
And there are zero outage mentions in the roughly 400 questions since the cutover.

## The one gap

238 of those 518 questions needed somebody to say which source is the authority.

75 were answered by reading the source code: questions about how a number is calculated, from 20 colleagues in all seven channels, where the rule is written down nowhere except the code itself.
Another 171 needed the agent to reverse-engineer a table before it could answer at all.
On one request it produced five successive answers from five different tables, each of which looked authoritative, and every correction came from one colleague's memory.

We do document our tables.
What we never wrote down is which table is the authority for a given business question, or what its words mean, and one everyday term turns out to name three different things in our own database.

None of that is the loop.
All of it is the data foundation, and that is where the interesting work is.
