+++
title = "Don't outsource the understanding: a grounded domain agent, and why the data foundation is the moat"
title_html = "Don't outsource the <em>understanding</em>"
date = 2026-08-22T09:00:00+02:00
draft = true

summary = "Anthropic shipped Claude in Slack halfway through building our own agent. Three months and 707 investigations later, here is what the free loop commoditised, what it could not, and the benchmark that told me which failures were mine."

labels = ['AI', 'Data']
tags = ['ai-agents', 'llm', 'claude', 'data-engineering', 'slack', 'observability']
toc = true
comments = true
+++

A few weeks into building a custom AI agent for my team, Anthropic shipped Claude in Slack. You @mention Claude in any channel and it answers, keeps thread memory, runs a tool loop, all for free. My honest first reaction, typed into my own notes that evening, was that I might have just wasted a month. What is the point of building a customised agent if Claude is going to eat all the common use cases? That question is worth sitting with, because it has an answer, and the answer is the whole reason the thing I built still matters.

This is both a build log and an argument. The build log: how a grounded investigation agent ended up answering real questions from 45 colleagues in Slack. The argument: the model loop is being commoditised, so the durable value is not the shell. It is the data foundation and the governance wrapped around it.

{{< figures caption="GRESB Intelligence Engine, 5 June to 21 August 2026"
           items="investigations=707|colleagues=45|median answer=56 s|cited answers=81 %" >}}

## What we built

The Intelligence Engine is a Slack bot that answers domain questions, about sustainability scoring, asset data and methodology rules, and shows its work. Every answer cites the source it came from and says plainly what it did **not** check.

The tagline on the architecture diagram sums up the intent:

> Don't outsource the understanding, only the thinking.

The agent does the searching and the querying. You keep the understanding. It is grounded in four sources:

- **The GRESB Guide**, the rule: what *should* happen.
- **The portal database**, read-only, the data: what actually went in.
- **The scoring codebase**, the implementation: what the system actually does.
- **The data warehouse** (Athena), history and scale.

One question in, a cited answer out. Everything runs through a single function, `answer(question, thread_context) -> Reply`, and every surface (Slack, CLI, evals) calls that one seam. That constraint, more than any framework, is what kept the system small enough to reason about.

## Design philosophy: lean tooling

Not minimal for its own sake. Lean because every extra layer is a place for the agent to get confused, slow down, or lie.

### Rich tools, no router

The fashionable move is a retrieval router: embeddings, a classifier, rules deciding which source to hit. With a handful of sources that is a brittle machine solving a problem you do not have. Instead there is one tool per source, each with a prescriptive "use this when" description, plus a three-line source map in the system prompt. The model routes itself. The disambiguation that actually matters is *inside* a source (which table?), not across three of them.

### The subagent I built, measured, and deleted

The most useful thing I did was kill a feature I had already shipped.

The first version of code search wrapped a nested "explore" subagent, an inner model loop that would read the codebase and hand a distilled note back to the main agent. It felt sophisticated. The telemetry disagreed.

| signal | nested subagent | flat tools (adopted) |
|---|---|---|
| elapsed on a hard question | 148 s | **78 s** |
| total model calls | ~20+ | **6** |
| inner loop hit its cap | every call | **no inner loop** |

The inner loop never converged. It pegged its iteration cap on every call, even reading a 124-line file, and because it returned a *summary* rather than raw code, the main agent kept re-asking for the same file four to eight times. About 60% of wall-clock was pure overhead.

So I deleted the subagent and exposed three flat primitives, `grep_code`, `read_file` and `list_files`, directly to the main agent. It greps, reads a narrow range, reasons, stops. Same answer, half the latency, a third of the model calls. The abstraction I removed was worth more than any I could have added.

### Grounded and honest, by construction

An agent that guesses confidently is worse than no agent, so grounding is the contract rather than a feature. Every answer is expected to cite a source and flag what it could not verify. Across 707 logged investigations, **81% carry at least one citation**, and the average answer carries two.

The remaining 19% is not something I am hiding. **114 answers used no tool at all.** The agent had the tools to check and did not reach for them. That is the top item on the fix list, because "why is my score lower?" is exactly the question the bot must never guess at.

The whole surface is deliberately flat and read-only: `SELECT`-only against the portal, describe and list against the catalogue, no writes anywhere. Lean tooling and safe tooling turn out to be the same discipline.

## Measure it, or it isn't real

"Grounded and honest" is easy to put on a slide. The only way to know is to instrument the thing and score it against reality.

### The usage dashboard

Every call to `answer()` writes one structured record: the question, the surface, the channel and thread, how hard it worked, latency, tokens, the exact SQL it ran, its citations. An offline generator aggregates that into a single self-contained HTML dashboard. No live service, no dependencies, regenerated with one command.

It answers operational questions I actually have. What do people ask? How hard does the agent work? Where is coverage thin? And the part I care about most is the "couldn't answer well" panel: **106 questions** where the agent produced no lookup, ran out of budget, or answered from memory. That panel is a live feature backlog. Each entry points at a missing help page, a missing table, or a prompt that needs sharpening. Failures stop being embarrassing and start being a to-do list.

### The accuracy benchmark against real Slack history

The dashboard tells you what the agent *did*, not whether it was *right*. For that, a colleague on the team built the benchmark I am proudest of. He scraped our past Slack threads for questions colleagues had actually asked along with the human answers that actually satisfied them, mined **371 satisfied pairs**, refined those to **119 bank-grade cases**, and scored the agent against the human answer pair by pair.

The results were clarifying precisely because they were not flattering.

| finding | count |
|---|---|
| pairs where the human answer was right | **97 / 119** |
| pairs where the human answer was itself wrong | 1 |
| pairs where the agent was the weaker side | **25** (15 partial, 10 wrong) |
| of those, answered from pure memory: zero queries, zero citations | **12** |

Humans were right on 97 of 119 and wrong on one, so this is a benchmark of the agent, not of the team. The agent held up on roughly four out of five real historical questions.

The last row reframed the whole quality problem. The dominant failure mode was not "the model isn't smart enough" or "the data isn't there". It was **the agent not grounding when it could have.** That is a fixable, engineering-shaped problem, and it points straight back at the design philosophy: make grounding the default and make ungrounded answers the exception you can see and count.

So the human-verified pairs, especially the ten the agent got outright wrong, became a regression question bank. Each case carries the original thread and a known-good answer, tagged by the kind of gap it exposes. Every prompt change is now measurable: did this fix move the needle, or move the failure somewhere else? One early fix out of the benchmark, a "ground or abstain on unverifiable specifics" rule for things like prices and cut-off dates, turned the two most dangerous confident-wrong-from-memory cases into grounded answers that cite a source and flag what they could not check.

{{< note "The loop I want every AI feature to have" >}}
Ship it, instrument it, benchmark it against reality, turn the failures into a
fixed test set, repeat. Without that, "it feels pretty good" is the best claim
you can make. For a bot that answers questions about people's scores, that is
not good enough.
{{< /note >}}

## The real argument: the moat is the data foundation

Back to the Claude-in-Slack question. If the vendor gives everyone a free agent loop with memory, what is left to build?

The loop is commoditised. Thread memory is commoditised. Those were never the hard part. The hard part, the part no general-purpose assistant can conjure, is grounded access to your own data with the guardrails and domain meaning that make the answers trustworthy.

Concretely, the data foundation is three things:

- **Curated, governed access** to production sources: a read-only database path, cost guards so a runaway query cannot scan a fortune, a channel allowlist, telemetry on every statement the agent runs.
- **Domain metadata that encodes meaning:** a maintained data dictionary and a caveats document that tells the agent *this column is deprecated, use that one instead*. The tacit knowledge that lives in senior engineers' heads and nowhere a language model can find it.
- **The right sources mapped to the right question type:** rule against data against implementation.

This is also the cleanest test of whether a general tool replaces a custom one. My litmus question was simple: can it consume your own MCP servers, so your read-only portal access, your warehouse cost guards and your multi-repo code search survive, or only the vendor's built-in connectors? If your data foundation is real, it is portable. It survives the shell it happens to be wearing.

## Does it actually work?

An awkward truth beats a polished claim, so here is the snapshot, taken from telemetry on 22 August 2026.

**Usage.** 707 investigations between 5 June and 21 August, 662 of them in Slack, from **45 colleagues** across 54 active days. They span 188 threads in eight channels, overwhelmingly the team's `#ask-data` (552). Excluding the engine's own channel, business usage is 658 investigations across 154 threads, and **92% of answers land in a multi-turn thread** rather than a one-shot question. The questions are what you would hope for rather than toy prompts:

- "What is the average score in the 2025 Asset Assessment?"
- "How many entities submitted their 2025 assessment after June 30?"
- "How did you calculate the like-for-like intensity for GHG and for energy on this asset?"

| metric | value |
|---|---|
| investigations (all surfaces) | 707 |
| in Slack | 662 |
| distinct colleagues | 45 |
| threads | 188 |
| active days | 54 |
| median answer time | 56.4 s |
| p95 answer time | 280.9 s |
| answers carrying a citation | 81% |
| tool rounds per answer, mean | 5.7 |

**Effort.** The agent leans hardest on the portal and the code: 2,861 and 1,197 tool calls against 839 for the warehouse and 232 for the Guide, so those two are 79% of everything it does. The median answer comes back in under a minute; the slow tail is deep rule questions that read source code.

**Cost.** Roughly fifty cents an investigation, but that number deserves a caveat, because it is an estimate rather than a bill. It is token counts multiplied by list prices, and for most of this period the model calls were billed to a shared development account where nothing can be attributed to one service. Since the production cutover, where this bot is the only consumer of its model, metered spend is under $100. Three months of production traffic cost about the same as a team lunch, and I would rather say that loosely and honestly than quote a precise figure I cannot reconcile.

**Reception.** Colleagues use it unprompted. One teammate, confirming an answer against a manual check, put it simply: *"That means it's working, and the answer is consistent with what we found here."* Questions that used to take hours now come back in under a minute, grounded and cited. Unlike a demo, that claim is backed by the 119-pair benchmark rather than a good feeling.

**The warts, because they are the roadmap.** It reached for the wrong table often enough to need a human to steer it. Someone rightly asked whether it might be reading test data rather than production, a trust question only a solid data foundation answers. And for its first two months it ran on a laptop, so when two instances collided it threw errors mid-thread. A colleague's dry *"this stresses the importance of running it in the cloud"* became a work item.

## What changed, and what is next

That laptop problem is fixed. Since 18 August the bot runs as a single-replica service on our production Kubernetes platform with a dedicated least-privilege role, always on, with telemetry landing in its own bucket so audit records never share a lifecycle with query scratch. Getting off the laptop was the top roadmap item in the first draft of this post; it shipped before the post did.

What remains follows from the thesis:

- **Enforce the contract in code.** A hook that *requires* every answer to carry its references, so grounding is a guarantee rather than a request.
- **Close the gaps the bot reveals.** Each "no help page for this" is a document worth writing; each repeated question is something to document once and make instant forever.
- **From reading to acting.** The most requested next step is letting the bot open a pull request straight from a thread, moving from "explain the number" to "propose the fix".
- **Pointed outward.** The same engine aimed at members rather than staff is a product: a new way to deliver domain expertise.

## The principle

Compressed to one line: don't build the loop, build the foundation the loop stands on. The model will keep getting better and cheaper, and vendors will keep absorbing the generic parts. What they cannot absorb is your data, your governance, and the hard-won domain meaning that turns a plausible sentence into a correct, cited answer. Keep the tooling lean enough to trust, put the effort into the substrate, and it stops mattering whether the shell is your bot or theirs. The understanding is yours, and it stays.
