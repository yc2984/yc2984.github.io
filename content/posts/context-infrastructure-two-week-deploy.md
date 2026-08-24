+++
title = "PLACEHOLDER: the two-week deploy, and the context traps behind it"
title_html = "The two-week deploy, and the <em>context traps</em> behind it"
date = 2026-09-01T09:00:00+02:00
draft = true

summary = "Moving a working laptop prototype into production took two weeks. Almost none of that was deployment. It was my own context system failing to be trusted."

labels = ['AI', 'Tech']
tags = ['ai-agents', 'context-engineering', 'kubernetes', 'developer-experience']
toc = true
comments = true
+++

**This is a placeholder. Not written yet.** Thesis, material and open questions
are below so the next session can pick it up without rediscovering them.

## The thesis

The bottleneck was never the model or the cluster. It was that I did not trust
my own context system, so I re-typed things it already knew, every session.

The strongest single fact: on a real prompt, five pieces of background were
typed by hand, and **four of them were already written down** in the wiki. The
system had the answers and could not be relied on to surface them.

## Material to draw on

- The AI-community post, which is the raw draft of this piece: babysitting
  agents, the 1M context window degrading past 30-40%, restarting sessions to
  summarise unfinished work, headaches by 5pm.
- The three-way contradiction: a product renamed A to B and back to A, with the
  code still on B, and three stores disagreeing about which was current.
- Wiki shape as a measurable problem. Index at 1,418 lines, of which 1,315 were
  a second body of cross-cutting connections. Pages averaging 670 lines, largest
  around 2,000. The agent could find the page and not the line.
- 22 memory stores sharded by working directory, main repo 86 entries, the
  parent of every repo only 2. Setting the workspace to the parent to "own all
  context" lands in the empty store.
- Cross-repo knowledge has no home: which product lives in which repo, which
  link in the deploy chain has the trap. A full deploy crosses four repos and
  that knowledge belongs to none of them.
- Goal definition. The spec was written by an agent and not read closely; the
  real goals surfaced mid-project as (1) reproduce every local feature,
  (2) use a new identity rather than a personal one, (3) read-only.
- No stated way to verify. The prototype's features were not written down, so
  nothing could confirm the port was complete until tests were demanded.
- The parts only a human can do: PR approvals, a database role, a GitHub App
  install, a token into 1Password.

## What is genuinely unresolved, and belongs in the post as unresolved

- Where the line sits. If every caveat is thought through in advance, what is
  left for the agent? The agent is at intern level; the goal is junior.
- Contradiction resolution. Supersede-rather-than-overwrite produced a bloated
  wiki. Nobody has reviewed the daily queue in days because the volume is too
  high.
- Whether "own your context" means demoting the harness memory to pointers into
  a library you control, with cross-repo knowledge promoted to a global layer.

## Open question for the draft

Whether the two-week deploy is the spine and context is the diagnosis, or
context is the spine and the deploy is the case study. The second is probably
the better post and the harder one to write.
