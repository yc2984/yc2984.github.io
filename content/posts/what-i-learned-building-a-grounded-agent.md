+++
title = "What I learned building a grounded domain agent"
title_html = "What I learned building a <em>grounded</em> domain agent"
date = 2026-08-24T09:00:00+02:00
draft = true

summary = "Five things that worked, one that didn't, and 707 real questions worth of evidence. The short version: make every answer carry a reference, then keep the tooling lean enough that it can."

labels = ['AI', 'Data']
tags = ['ai-agents', 'llm', 'claude', 'data-engineering', 'slack', 'observability']
toc = true
comments = true
+++

I built a Slack bot that answers questions about our sustainability scoring: how an indicator is calculated, why a number looks wrong, how many entities did something last year. It has been in production for three months and has answered 707 real questions from 45 colleagues. This is what I would tell myself if I were starting again.

Almost none of it is about the model. The model was the easy part.

{{< figures caption="GRESB Intelligence Engine, 5 June to 21 August 2026"
           items="investigations=707|colleagues=45|median answer=56 s|cited answers=81 %" >}}

## The shape of it

{{< diagram caption="Fig. 1: one question in, one cited answer out. Four sources, one loop, no router." >}}
<svg viewBox="0 0 700 300" role="img" aria-label="A question from a Slack thread enters an agent loop, which reaches for four sources: the Guide, the portal database, the code, and the data warehouse. The loop returns a cited answer plus a note of what it did not check.">
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
    <text x="20" y="148">THE GUIDE</text>
    <text x="196" y="148">PORTAL DB</text>
    <text x="372" y="148">THE CODE</text>
    <text x="548" y="148">WAREHOUSE</text>
  </g>
  <g fill="currentColor" font-family="Hanken Grotesk, sans-serif" font-size="11" opacity="0.75">
    <text x="20" y="70">a Slack thread</text>
    <text x="264" y="70">up to 15 rounds, avg 5.7</text>
    <text x="538" y="70">+ what it did not check</text>
    <text x="20" y="166">the rule</text>
    <text x="196" y="166">the data, read-only</text>
    <text x="372" y="166">the implementation</text>
    <text x="548" y="166">history and scale</text>
    <text x="20" y="182">searchDocumentation</text>
    <text x="196" y="182">query_portal_db</text>
    <text x="372" y="182">grep_code, read_file</text>
    <text x="548" y="182">query_athena</text>
  </g>
  <g fill="currentColor" font-family="DM Mono, monospace" font-size="10" opacity="0.6">
    <text x="248" y="226">every answer names the source it came from</text>
  </g>
</svg>
{{< /diagram >}}

## 1. Require a reference. Everything else follows from that

This is the rule I would keep if I could keep only one: **an answer must carry a reference, and must say what it did not check.**

It sounds like a quality nicety. It is actually the load-bearing constraint, because it changes what the system is allowed to be. An agent that must cite cannot answer from the model's memory of the internet. It has to go and look. That single requirement forced the sources to be real, the tools to be readable, and the failures to be visible.

It also gives you something to measure. Across 707 answers, **81% carry at least one citation**. The other 19% is not a mystery to be discussed; it is 134 answers I can list, and **114 of them used no tool at all**. The agent had everything it needed to check and did not reach for it.

That number is the whole quality programme. Not "the model isn't smart enough" and not "the data isn't there", but *the agent did not ground when it could have*. That is an engineering problem with a fix, and you only get to see it because you demanded references in the first place.

An agent that guesses confidently is worse than no agent, because a colleague acting on a wrong score is worse off than a colleague who had to ask a human. Requiring a reference is what makes the difference between the two visible.

## 2. Rich tool descriptions beat a router

The fashionable move is a retrieval router: embeddings, a classifier, rules that decide which source a question should hit. With a handful of sources that is a brittle machine solving a problem you do not have.

I gave each source one tool, each with a prescriptive "use this when" description, plus a three-line source map in the system prompt. The model routes itself. It has been right often enough that I have never wanted the router back.

The insight underneath: **the disambiguation that matters is inside a source, not across sources.** Nobody struggles to tell "what does the standard say" from "what is in the database". They struggle with *which of these 200 tables*. A router solves the easy problem and leaves the hard one untouched.

## 3. Curate the tools. A pile of integrations is not capability

Four sources. Ten tools. That is the whole surface, and keeping it that small was a deliberate and repeatedly-defended decision.

Every tool you add is another description the model has to weigh, another way for it to go somewhere plausible and wrong, and another thing you have to keep true. A few high-signal sources beat a pile of integrations, and the difference shows up as the agent picking correctly on the first round rather than wandering.

## 4. Clone the repo. Do not wrap it in a protocol

For code grounding I clone the repositories to local disk and search them with ripgrep. No GitHub API, no MCP server in front of the code.

It clones once, in a few seconds, and every later question reuses the clone. `grep_code` is a grep. `read_file` reads a byte range. There is no rate limit, no auth dance in the hot path, no protocol translating my intent into someone else's idea of a search.

The general lesson: when a thing is already a file on a disk, the fastest and most reliable tool is usually the boring one that reads files.

## 5. Instrument it before you need to

Telemetry went in on day two, before there was much to measure and long before anyone asked for a dashboard. It is one structured record per answer: the question, the sources, tool rounds, latency, the exact SQL, the citations.

Every honest number in this post exists because of that decision. Without it I would be writing "it feels pretty good", which for a bot that answers questions about people's scores is not good enough.

The part I did not expect: the failures became the roadmap. The dashboard has a "couldn't answer well" panel holding **106 questions** where the agent produced no lookup, ran out of budget, or answered from memory. Each one points at a missing help page, a missing table, or a prompt that needs sharpening. Failures stop being embarrassing and start being a to-do list.

## The one that did not work: the subagent

The most useful thing I did was delete a feature I had already shipped.

The first version of code search wrapped a nested "explore" subagent, an inner model loop that read the codebase and handed a distilled note back. It felt sophisticated. The telemetry disagreed.

| signal | nested subagent | flat tools (adopted) |
|---|---|---|
| elapsed on a hard question | 148 s | **78 s** |
| total model calls | ~20+ | **6** |
| inner loop hit its cap | every call | **no inner loop** |

The inner loop never converged. It pegged its iteration cap on every call, even reading a 124-line file, and because it returned a *summary* rather than raw code, the outer agent kept re-asking for the same file four to eight times. Roughly 60% of wall-clock was overhead.

Both decisions are dated the same day in our decisions log: the subagent, then flat tools. Deleting it was worth more than any abstraction I could have added.

## What people actually got

707 investigations between 5 June and 21 August, 662 in Slack, from 45 colleagues across 54 active days, in eight channels. Median answer in **56 seconds**; the slow tail is deep rule questions that read source code.

The questions are the real thing, not demo prompts:

- "What is the average score in the 2025 Asset Assessment?"
- "How many entities submitted their 2025 assessment after June 30?"
- "How did you calculate the like-for-like intensity for GHG and for energy on this asset?"

Questions that used to take a specialist hours now come back in under a minute, with sources attached.

## What it surfaced, which I did not expect

The most valuable output was not the answers. It was what the questions exposed.

**192 questions had to dig through engineering source because the Guide did not cover them.** Each one is a documentation gap with a queue position: evidence that a help page is missing, and evidence of exactly which one.

**150 questions were repeats.** The same thing asked more than once, which is a standing invitation to document something once and make it instant forever.

And a category I did not anticipate: the bot kept finding places where the documentation, the code and the data disagreed. A rule described one way in the Guide, implemented another way in the scoring code, and producing a third thing in the database. Those disagreements existed before the bot; they were just expensive enough to check that nobody checked. Making them cheap to check turned tacit confusion into a list.

## The argument, briefly

Halfway through building this, Anthropic shipped Claude in Slack, free, with thread memory and a tool loop. My first reaction was that I had wasted a month.

I think the answer is that the loop was never the hard part. What no general assistant can conjure is grounded access to your own data, with the guardrails and the domain meaning that make an answer trustworthy: a read-only path to production, cost guards, a maintained data dictionary that says *this column is deprecated, use that one*. Build that, and it survives whichever shell it ends up wearing.

But that is an argument, and this post is about what I learned. The learning is simpler: **require the reference, and keep the tooling lean enough that the agent can actually go and get it.**

---

*Two follow-ups in progress: what it took to move this from my laptop to production, and how I gave an agent access to a production database without losing sleep.*
