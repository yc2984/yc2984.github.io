+++
title = "The loop is free. Eight decisions behind a self-serve data agent."
title_html = "The loop is <em>free</em>. Eight decisions behind a self-serve data agent."
date = 2026-09-10T09:00:00+02:00
draft = true

summary = "The agent loop behind a self-serve data agent is seven lines of code, and nothing that makes its answers good is in them. What powers it, the eight decisions that made the answers high quality, and what a thousand real questions revealed about the data underneath."

labels = ['AI', 'Data']
tags = ['ai-agents', 'llm', 'data-engineering', 'slack', 'tool-design', 'observability']
toc = true
comments = true
+++

"Only a single correct answer using a single correct source." Anthropic, on their data team's agent.
{.epigraph}

A coding agent gets caught by its tests.
A data agent does not: one right answer, from one right source, and nothing downstream to prove you got it.
Nothing tells you the answer was wrong except a colleague who happens to know better.

And yet the loop that runs the self-serve data agent I maintain is seven lines: ask the model, run the tool it picks, hand the result back, ask again.
Nothing that makes its answers good is in those seven lines.

The agent lives in Slack and answers colleagues' questions about how a number is calculated, why it looks off, and what the data says.
Since June it has answered about a thousand of them, from a few dozen people across seven channels, and I never wrote a single instruction.
There is no onboarding doc.
People tagged it, it answered, and they told each other.
87% of its answers point at a source you can open.

By the end of this post you will know three things.
What powers it, and why the AI part is the easy part.
The eight decisions that made the answers high quality and checkable.
And what three months of questions revealed about the data underneath, which is where the interesting work is.
Enough, I think, to build one like it yourself.

## What powers it

A question arrives in a Slack thread.
The model gets the question and a list of ten tools across four sources: the documentation, the application database, the source code, and the data warehouse.
It asks to call one.
The code runs it, hands the result back, and asks again.
That circle is the whole engine.
It goes round 6.8 times on average, and when the model stops asking for tools, whatever it wrote is the answer.

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

Notice what is missing.
Nothing decides which box to reach for.
There is no classifier, no router, no if-statement anywhere that says this looks like a data question.
The model gets all ten descriptions at once and reasons its way to one.
Hold on to that, because it comes back as the second decision.

The loop itself is seven lines of code.
The file it lives in is 684 lines, and the other 677 are bookkeeping: telemetry, token accounting, collecting citations.
No framework, no managed agent service, no knowledge base, no vector database.
I am not claiming this is clever.
Nobody reading this would struggle to write those seven lines, and that is exactly the point.
The loop is free.
Everyone gets the same one.

## So where does the effort go?

If the loop is an afternoon, the months went into what the loop reads.
Nothing downstream catches a wrong answer, so the answer has to be right the first time, and that comes from two things: curated tools with rich descriptions, and grounding in sources we control.
Everything that follows is either evidence for that sentence or a consequence of it.

## Eight decisions

Not the model, not the loop.
These are the reasons the answers are good, the reasons one person can maintain it, and the reasons it has been stable enough to change every week.

### 1. Few questions, answered well

The first decision explains most of the others: answer a small number of questions really well, instead of every question badly.
Four sources are wired in.
Deliberately left out: the internal wiki, free search over Slack, the open web, and anything I cannot vouch for.
Not because those are bad sources.
Because I cannot control the quality of what comes back out of them, and in a search result a stale plan and a live decision look identical.
The arithmetic of trust is asymmetric: one confidently wrong answer costs more than ten questions it politely declines.

### 2. Rich descriptions, not predefined routes

This is the one I would defend hardest.
There is no router.
The model gets all ten descriptions and picks, and when it picks wrong I sharpen a sentence in a description.
I do not add a router.

A classifier is an if-else in disguise.
Every new scenario is another branch, every new source is another retrain, and a wrong guess strands the question at the wrong tool before the real model ever sees it.
Descriptions scale.
A classifier degrades exactly as the thing grows.

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

A description that earns its place does real work.
The one on the warehouse query tool is a single paragraph doing six jobs: a guarantee the code enforces, that it is read-only; a disclosure limit of 100 rows; an economic fact the model cannot infer, that a data lake charges for bytes scanned and not rows returned; how to behave, so never select star; where to look first; and do not invent a table name.
Show of hands: who has written a tool description longer than one line?

### 3. Grounded, and checkable by the reader

Grounding means one specific thing: the answer comes from a live call against a source we own, not from the model's memory.
And it is enforced, not requested.
While the loop runs, every source it opens is recorded as a citation at the moment of the call.
The model does not write that record, so it cannot cite something it never opened.
If an answer finishes with zero recorded sources, the code stamps it: answered from general knowledge, not verified.
Every query is kept verbatim as it ran, and a button on the answer replays the chain in execution order.

One distinction matters here.
The references section the reader sees is the model writing, following a template.
That part is an instruction.
The recorded log underneath is the control, and the log is what I audit.

The third piece of every answer is the one I would ask you to steal: a line saying what it did not check.
It came from a teammate's answer template on the first day of the hackathon, with one instruction I have never taken out: if code or data was not verified, do not imply that it was.
It is very easy to build something that always sounds finished.
A tool that tells you where it stopped looking is a tool you can use for real work.

### 4. Clone the repo. Do not wrap it in a protocol

For code, the agent greps a local clone.
No GitHub API, no MCP server in front of the code.
One idea: nothing sits between the agent and the source.

Against the API the argument is mechanical.
Its code search is a keyword index, so you cannot ask it for a regex.
It lags behind the branch.
And it rate-limits, which lands in the middle of an investigation rather than politely up front.

Against MCP the argument is not performance.
It is control.
We did wrap the documentation in an MCP server and passed through whatever it advertised.
My own notes said two tools.
The server started advertising four, and one of the new ones was a write tool that filed feedback against an external system carrying our brand.
So the agent used it.
Halfway through an ordinary question it filed a real documentation issue, unprompted, and told me it had done so.
Nothing changed on our side.
Somebody else's deploy changed what my agent was capable of.

And since the description is the router, handing your tools to a protocol hands over your routing too.
A passthrough tool list means somebody else decides what your agent can do.
If you use Claude Code, you already know the local-clone mechanism works: ripgrep over a checkout is what makes it good at code.

### 5. Guardrails, written as refusals

The agent's guardrails are its permissions.
Not a paragraph of English in a prompt.
Three identities of its own, and what each one is refused.

Before August all three credential paths traced back to my personal cloud login.
The agent stopped working when my session expired, and while it worked, it acted with my access.
Now it has a cloud role with no stored key that rotates hourly, a read-only database role of its own, and a GitHub App that can read three repositories and nothing else.
The refusals matter more than the grants.

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

The part I would steal took me two attempts.
An over-broad permission never fails a test.
If I write a test that says the agent can read a given table, and someone accidentally grants it write access, the test still passes.
So the acceptance criteria are written backwards: not prove it can, prove it cannot.
Run the forbidden thing as the new identity and record the denial, and pair every refusal check with a permitted neighbour so a check that passes because of a typo gets caught.
No single thing is load-bearing: a write to the application database is stopped three times, independently.

And I am precise about the boundary.
Those are controls.
The rules about masking identifiers and sending raw rows only as a file are instructions in a prompt, and a paragraph of English is not a security boundary.

### 6. Safe to deploy, fast to change

This is the machinery that makes one person safe to run it, and it reads as a timeline.
On every commit, 433 tests run as a pre-commit gate, so a red suite cannot land.
On every push, CI builds the real container and runs its assertions inside it: code search through the real path, the grounding files load, plus a negative control where the same check pointed at the wrong directory must fail.
After deploy, live checks run as the pod, in three families: capabilities, that it reaches every source; fences, that the forbidden thing is denied; and identity, which checkout is actually under test.
Every one is paired with a control that must fail, because a check that cannot fail is not a check.
On every start, the pod refuses to come up if its grounding files are missing.

None of that proves an answer is right, so there is also a question bank of real questions colleagues asked, with answers a human verified.
Each of these runs as one command, so a new maintainer does not have to learn my habits.
What it buys: 54 feature and fix commits since June, shipped the same day, by one person, with no staging soak.

### 7. Start simple: zero infrastructure

The agent phones Slack, not the other way round.
One connection out, kept open, and every mention comes down that line.
So there is no address anyone can reach: no public endpoint, no certificate, no hole in the firewall.
For something holding read access to the database, the warehouse and the code, the safest setup is the one with no door.
The Slack thread is its memory, re-read on every mention, so there is no state store to run and a restart loses nothing.
The cost is one replica and no memory across conversations, and that is the honest limit.
The drawing has not changed since the hackathon: the same architecture ran on a laptop until mid-August and runs in the production cluster today.
Since the cutover, zero outage mentions in roughly four hundred questions.
The stability was not added later with infrastructure.
It fell out of having none.

### 8. Telemetry from day one

Every answer is recorded as one JSON document: which tools ran and in what order, how many rounds, elapsed time, tokens, and every query verbatim.
A file, not a product.
It says what people actually ask, where the answers struggle, what data the questions want that we do not expose yet, and which of our own words confuse even the machine reading our schemas.
It also tunes the agent: the loop's stops are set from the rounds distribution, and it prices itself at about 86 cents an answer.
Every number in this post came out of it, and not one needed new instrumentation.

## The one line to leave with

Spend your time on the data foundation.
That is two things: the sources you ground in, and what those sources say about themselves, their descriptions, their meanings, which one is the authority.
Not on the loop.

Anthropic's data team put it better than I can: for self-serve analytics the complexity lies in the ambiguity of the data, and once the question is mapped to the right entity, the SQL is the easy part.

If you build one of these and it gives bad answers, your instinct will be to reach for the loop.
A bigger model, more rounds, a cleverer framework.
Almost always the fix is a sentence in a description, or a source you have not exposed yet.
Two receipts, because otherwise this is just advice.

The single biggest speed-up I have measured was not a loop change.
Code search started as a nested sub-agent.
I replaced it with three flat tools, grep, read a byte range, list files, each with a description longer than one line.
One question went from 148 seconds and more than 20 model calls to 78 seconds and six.
Same model, same loop, same question.

And the worst failure I have had was not a loop failure either.
For 16 days the loop ran perfectly and the answers were worthless, because the grounding files were not in the deployed image.
Nothing about the loop would have told me.

## What a thousand questions said

I read the first 518 questions by hand and gave each one a theme.
The top of the chart was the thing I did not expect.
The most common request is not a question about how something is calculated.
It is a data pull: record lookups and exports, 123 of them, from 25 different people.
Two out of three questions ask the agent to go and query our databases directly.
One theme, 45 questions, is a sustained analysis programme that no product of ours serves today.
Somebody found a way to do their job by asking a Slack bot.

Then the finding that ties the eight decisions to the one line.
238 of those 518 questions, nearly half, needed somebody to say which source is the authority.
75 questions about how a number is calculated could only be answered by reading the source code, because the rule is written down nowhere else at that level of detail.
On 171 the agent had to inspect what a table and its columns mean before it could answer at all.

On one request it gave five answers in a row from five different tables, each of which looked authoritative.
It got there.
But every correction came out of one colleague's memory.
That is not an AI problem.
That colleague is our documentation.

The word underneath it: one everyday term means three different things in our own database, depending on the table, and the agent cannot tell them apart.
Neither can a new joiner.
Making that cheap to check turned tacit confusion into a list, and that list is the most valuable thing the agent has produced.
It is worth more than any answer it gave.

## Work waiting for an owner

So the data foundation is the ceiling.
Here is what that opens up, in three groups, and the honest state of every item is the same: it does not exist yet.

The data foundation is the biggest lever, and most of it is not agent code at all.
A description can live in three places: in the tool's own text, which I write; in a file shipped with the agent, which is a copy of somebody else's schema; or next to the data itself, written by whoever owns it.
Two tests decide which is right: does the upkeep scale, and is there a single source of truth.
The tool text passes both, because there are only ten tools.
The shipped dictionary fails both: 75 kilobytes, about 19,000 tokens riding on every call, and a copy that goes stale without anyone noticing.
Comments next to the data pass both and scale to every column.
Every fact lives once, in the place where it is already true.
So the work is column comments the agent can see, a description on every dataset, and an authority written down for every business question.

Running it safely is the hardening: per-user identity instead of one shared slice, the disclosure rules turned from prompt text into code, memory that survives a restart, and real monitoring, because today a colleague telling me is the monitoring.

And the product side is where it gets interesting: a reaction on an answer that files a ticket, the analysis demand that no product serves, knowledge loaded on demand instead of a growing system prompt, and evaluations per domain.

Curated tools, real grounding.
None of it is hard.
What is hard is that a few dozen people rely on this and one person maintains it.
The rote lookups have already moved to the agent.
What is left is the interesting part.

That is the three things I promised at the top.
What powers it: a free loop over four sources.
Why the answers hold: eight decisions, none of them about the loop.
And what the questions revealed: the data foundation is the ceiling, and it is where the work is.
