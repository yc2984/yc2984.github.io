+++
title = "The loop is free. Eight decisions that made the answers good."
title_html = "The loop is <em>free</em>. Eight decisions that made the answers good."
date = 2026-09-10T09:00:00+02:00
draft = true

summary = "The agent loop behind an internal data bot is seven lines of code, and nothing that makes its answers good is in them. Eight decisions, each with the number that justified it, from a thousand real questions."

labels = ['AI', 'Data']
tags = ['ai-agents', 'llm', 'data-engineering', 'slack', 'tool-design', 'observability']
toc = true
comments = true
+++

The loop that runs the internal data bot I maintain is seven lines: ask the model, run the tool it picks, hand the result back, ask again.
Nothing that makes its answers good is in those seven lines.

The bot lives in Slack and answers colleagues' questions about how our scores are calculated, why a number looks off, and what the data says.
It has answered about a thousand of them since June, and I never wrote an onboarding doc.
People tagged it, it answered, and they told each other.
Under the hood the model gets the question and ten tool descriptions across four sources.
It asks for one tool, the code runs it and hands the result back, and the model asks again, 6.8 times on average.
When it stops asking, whatever it wrote is the answer.
The file that loop lives in is 684 lines.
The other 677 are bookkeeping: telemetry, token accounting, collecting citations.
No framework, no vector database, no managed agent service.
I am not claiming this is clever.
Nobody reading this would struggle to write those seven lines, and that is the point.
The loop is free. Everyone gets the same one.

{{< diagram caption="Fig. 1: one question in, one cited answer out. Four sources, ten tools, one loop, no router." >}}
<svg viewBox="0 0 700 300" role="img" aria-label="A question from a Slack thread enters an agent loop, which reaches for four sources: the documentation, the application database, the source code, and the data warehouse. The loop returns a cited answer plus a note of what it did not check.">
  <g fill="none" stroke="currentColor" stroke-width="1.5">
    <rect x="8" y="30" width="150" height="54"/>
    <rect x="252" y="30" width="180" height="54"/>
    <rect x="526" y="30" width="166" height="54"/>
    <path d="M158 57 H244 M436 57 H522"/>
    <path d="M238 57 l-10 -4 v8 z M516 57 l-10 -4 v8 z" fill="currentColor"/>
    <path d="M342 84 V126" stroke-dasharray="4 4"/>
    <rect x="8" y="126" width="160" height="62"/>
    <rect x="184" y="126" width="160" height="62"/>
    <rect x="360" y="126" width="160" height="62"/>
    <rect x="536" y="126" width="156" height="62"/>
    <path d="M88 126 V110 H612 V126" stroke-dasharray="4 4"/>
  </g>
  <g fill="currentColor" font-family="DM Mono, monospace" font-size="11">
    <text x="20" y="52">QUESTION</text>
    <text x="264" y="52">AGENT LOOP</text>
    <text x="538" y="52">CITED ANSWER</text>
    <text x="20" y="148">THE DOCS</text>
    <text x="196" y="148">APP DATABASE</text>
    <text x="372" y="148">THE CODE</text>
    <text x="548" y="148">WAREHOUSE</text>
  </g>
  <g fill="currentColor" font-family="Hanken Grotesk, sans-serif" font-size="11" opacity="0.75">
    <text x="20" y="70">a Slack thread</text>
    <text x="264" y="70">6.8 rounds on average</text>
    <text x="538" y="70">+ what it did not check</text>
    <text x="20" y="166">the rule as written</text>
    <text x="196" y="166">the records, read-only</text>
    <text x="372" y="166">the rule as implemented</text>
    <text x="548" y="166">history and scale</text>
    <text x="20" y="182">search_docs, get_page</text>
    <text x="196" y="182">query_db, describe_table</text>
    <text x="372" y="182">grep_code, read_file</text>
    <text x="548" y="182">query_warehouse</text>
  </g>
  <g fill="currentColor" font-family="DM Mono, monospace" font-size="10" opacity="0.6">
    <text x="248" y="226">every answer names the source it came from</text>
  </g>
</svg>
{{< /diagram >}}

So if the loop is an afternoon, where does the effort go?
Anthropic's data team made the point about their own analytics agent: a coding agent has documentation and tests that catch it when it invents something, while an analytics question has one correct answer from one correct source and nothing downstream to prove it right.
A coding agent gets caught by its tests.
This one does not.
Nothing tells you the answer was wrong except a colleague who happens to know better.
So what makes the answers good is curated tools with rich descriptions, and grounding in sources we control.
The eight decisions below are that sentence, taken one piece at a time, each with the number that justified it.

## 1. Few questions, answered well

The first decision explains most of the others: answer a small number of questions really well, instead of every question badly.
Four sources are wired in: the methodology documentation, the application database, the scoring source code, and the data warehouse.
Deliberately left out: the internal wiki, free search over Slack, the open web, and anything I cannot vouch for.
Not because those are bad sources.
Because I cannot control the quality of what comes back out of them, and a stale plan and a live decision look identical in a search result.
The arithmetic of trust is asymmetric: one confidently wrong answer costs more than ten questions it politely declines.

## 2. Rich descriptions, not predefined routes

This is the one I would defend hardest.
There is no router.
No classifier decides which source a question belongs to.
The model gets all ten descriptions and picks, and when it picks wrong I sharpen a sentence in a description.
A classifier is an if-else in disguise: every new scenario is another branch, every new source is another retrain, and a wrong guess strands the question at the wrong tool before the real model ever sees it.
Descriptions scale.
A classifier degrades exactly as the thing grows.

The biggest speed-up I have measured came from this, not from the loop.
Code search started as a nested sub-agent.
I replaced it with three flat tools, grep, read a byte range, list files, each with a description longer than one line.
One question went from 148 seconds and more than twenty model calls to 78 seconds and six.
Same model, same loop, same question.

A description that earns its place does real work.
The one on the warehouse query tool is a single paragraph doing six jobs: a guarantee the code enforces, that it is read-only; a disclosure limit of a hundred rows; an economic fact the model cannot infer, that a data lake charges for bytes scanned and not rows returned; how to behave, so never select star; where to look first; and do not invent a table name.
Show of hands: who has written a tool description longer than one line?

## 3. Grounded, and checkable by the reader

Grounding means one specific thing: the answer comes from a live call against a source we own, not from the model's memory.
And it is enforced, not requested.
While the loop runs, every source it opens is recorded as a citation at the moment of the call.
The model does not write that record, so it cannot cite something it never opened.
If an answer finishes with zero recorded sources, the code stamps it: answered from general knowledge, not verified.
Every query is kept verbatim as it ran, and a button on the answer replays the chain in execution order.
The references section the reader sees is the model writing, following a template.
That part is an instruction.
The recorded log underneath is the control, and the log is what I audit.

The third piece of every answer is the one I would ask you to steal: a line saying what it did not check.
It came from a teammate's answer template on the first day of the hackathon, with one instruction I have never taken out: if code or data was not verified, do not imply that it was.
It is very easy to build something that always sounds finished.
A tool that tells you where it stopped looking is a tool you can use for real work.

## 4. Clone the repo. Do not wrap it in a protocol

For code, the bot greps a local clone.
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
So the bot used it.
Halfway through a certification question it filed a real documentation issue, unprompted, and told me it had done so.
Nothing changed on our side.
Somebody else's deploy changed what my agent was capable of.
And since the description is the router, handing your tools to a protocol hands over your routing too.
A passthrough tool list means somebody else decides what your agent can do.
If you use Claude Code, you already know the local-clone mechanism works: ripgrep over a checkout is what makes it good at code.

## 5. Guardrails, written as refusals

The bot's guardrails are its permissions.
Not a paragraph of English in a prompt.
Three identities of its own, and what each one is refused.

Before August all three credential paths traced back to my personal cloud login, so the bot stopped working when my session expired, and while it worked, it acted with my access.
Now it has a cloud role with no stored key that rotates hourly, a read-only database role of its own, and a GitHub App that can read three repositories and nothing else.
The refusals matter more than the grants.

The part I would steal took me two attempts.
An over-broad permission never fails a test.
If I write a test that says the bot can read the assessments table, and someone accidentally grants it write access, the test still passes.
So the acceptance criteria are written backwards: not prove it can, prove it cannot.
Run the forbidden thing as the new identity and record the denial, and pair every refusal check with a permitted neighbour so a check that passes because of a typo gets caught.
No single thing is load-bearing: a write to the application database is stopped three times, independently.
And I am precise about the boundary.
Those are controls.
The rules about masking identifiers and sending raw rows only as a file are instructions in a prompt, and a paragraph of English is not a security boundary.

## 6. Safe to deploy, fast to change

This is the machinery that makes one person safe to run it, and it reads as a timeline.
On every commit, 433 tests run as a pre-commit gate, so a red suite cannot land.
On every push, CI builds the real container and runs its assertions inside it: code search through the real path, the grounding files load, plus a negative control where the same check pointed at the wrong directory must fail.
After deploy, live checks run as the pod, in three families: capabilities, that it reaches every source; fences, that the forbidden thing is denied; and identity, which checkout is actually under test.
Every one is paired with a control that must fail, because a check that cannot fail is not a check.
On every start, the pod refuses to come up if its grounding files are missing.

None of that proves an answer is right, so there is also a question bank of real questions colleagues asked, with answers a human verified.
Each of these runs as one command, so a new maintainer does not have to learn my habits.
What it buys: fifty-four feature and fix commits since June, shipped the same day, by one person, with no staging soak.

## 7. Start simple: zero infrastructure

The bot phones Slack.
Not the other way round.
When the pod starts it opens one connection out and keeps it open, and Slack sends every mention down that line.
So there is no address anyone can reach: no public endpoint, no certificate, no hole in the firewall.
For something holding read access to the database, the warehouse and the code, the safest setup is the one with no door.

It has no memory of its own.
The Slack thread is the memory, re-read on every mention, so a restart loses nothing and there is no state store to run.
What it does not have is memory across conversations, and that is the honest limit.
The cost of one connection is one bot: two replicas would each answer half the questions, so it runs as exactly one, and mentions that arrive during a restart are lost.

This drawing has not changed since the hackathon.
The same architecture ran on a laptop from June to mid-August and runs in the production cluster today.
Since the cutover, zero outage mentions in roughly four hundred questions.
On the laptop, roughly one question in ten was somebody retrying after my session expired.
The stability was not added later with infrastructure.
It fell out of having none.

## 8. Telemetry from day one

Every answer is recorded as one event: which tools ran and in what order, how many rounds, elapsed time, tokens, and for every database query the exact SQL.
It is a file, not a product.
One JSON document per answer.

That one store feeds two things.
It says what people actually ask, where the answers struggle, what data the questions want that we do not expose yet, and which of our own words confuse even the machine reading our schemas.
And it tunes the agent: the speed-up in decision two was measured with these fields, the loop's soft and hard stops are set from the rounds distribution, and it prices itself at about 86 cents an answer.
Every number in this post came out of it, and not one needed new instrumentation.

## What a thousand questions said

I read the first 518 questions by hand and gave each one a theme.
238 of them, nearly half, needed somebody to say which source is the authority.
Seventy-five methodology questions could only be answered by reading the scoring source code, because the rule is written down nowhere else at that level of detail.
On 171 the bot had to inspect what a table and its columns mean before it could answer at all.
On one request it gave five answers in a row from five different tables, each of which looked authoritative.
It got there.
But every correction came out of one colleague's memory.
That is not an AI problem.
That colleague is our documentation.

The word underneath it: "portfolio" means three different things in our own database, and the bot cannot tell them apart.
Neither can a new joiner.
Making that cheap to check turned tacit confusion into a list, and that list is the most valuable thing the bot has produced.

Which is why I say data foundation and not tool descriptions.
A description can live in three places: in the tool's own text, which I write; in a file shipped with the bot, which is a copy of somebody else's schema; or next to the data, written by whoever owns it.
Two tests decide: does the upkeep scale, and is there a single source of truth.
The tool text passes both, because there are only ten tools.
The shipped dictionary fails both: 75 kilobytes, about nineteen thousand tokens riding on every call, and a copy that goes stale without anyone noticing.
Comments next to the data pass both and scale to every column.
Every fact lives once, in the place where it is already true.
The one place that breaks that rule is mine, and the fix is not code.

If you build one of these and it gives bad answers, your instinct will be to reach for the loop.
A bigger model, more rounds, a cleverer framework.
Almost always the fix is a sentence in a description, or a source you have not exposed yet.
Spend your time on the data foundation: the sources you ground in, and what those sources say about themselves.
Not on the loop.
