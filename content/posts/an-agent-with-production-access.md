+++
title = "PLACEHOLDER: giving an agent production access without losing sleep"
title_html = "Giving an agent <em>production access</em>"
date = 2026-09-08T09:00:00+02:00
draft = true

summary = "A bot that answers questions about real data needs to reach real data. Here are the identities, the roles and the limits that made that decision survivable."

labels = ['AI', 'Tech']
tags = ['ai-agents', 'security', 'governance', 'aws', 'least-privilege']
toc = true
comments = true
+++

**This is a placeholder. Not written yet.** The substance already exists in the
repo; this post is a rewrite for an outside reader, not new research.

## The thesis

The interesting question is not whether an agent can be trusted. It is what it
can reach, who it is when it reaches, and what it cannot do at all. Answer those
three and the trust question mostly dissolves.

## Material to draw on

Almost all of it is already written in the engine's own
`docs/security-and-governance.md`, which is structured as blast radius, controls,
residual risks and an operational checklist. The controls to cover:

- AWS identity is a fixed machine role, not a person's credentials.
- Access control by channel allowlist.
- The portal database is read-only, with no table denylist, and why that choice
  rather than the denylist.
- Athena limits and cost caps, so a runaway query cannot scan a fortune.
- Secret and error hygiene.
- An audit trail on every statement the agent runs.
- Cost and abuse caps.

And from `docs/decisions.md`, the dated decisions that shaped it:

- Code access runs on a GitHub App installation token, not a personal PAT
  (2026-08-04).
- Always-on in prd EKS on one IRSA role; the laptop path retired (2026-07-27).
- Three independent credential paths, with Athena and Glue pinned to the prd
  profile (2026-06-26).
- Secrets reach the pod through the 1Password Connect operator (2026-08-07).
- Never pass a remote tool list through unfiltered (2026-08-07).

## The honest part

The residual risks are already listed as accepted for the trial. A post that
prints the controls and hides the accepted risks is marketing. The accepted
risks are what make it useful to somebody making the same decision.

## Note before publishing

This one touches security posture. It needs the sensitive-information pass more
than the other two, and probably a colleague's read as well.
