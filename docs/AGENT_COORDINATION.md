# Agent Coordination MVP

P6 turns MMKit's handoff discipline into a small machine-readable coordination layer.

The goal is not to make agents autonomous project managers. The goal is to make repository state sufficient for a new human or AI agent to resume a bounded task without depending on a long chat transcript.

## State file

A workspace uses:

```text
coordination/STATE.json
```

It stores only current coordination facts:

- current task id;
- bounded task title/objective/inputs/outputs/invariants/acceptance;
- current evidence and blockers;
- one exact next action;
- worker/writer/reviewer role leases;
- same-mechanism failure streak;
- latest compact handoff;
- monotonic revision number.

Git history remains the history. `STATE.json` must not become a transcript archive.

## Bootstrap

`mmkit init` now creates `coordination/STATE.json` automatically.

Existing workspaces can opt in without overwriting existing state:

```text
mmkit coord init .
```

The default active task is `PROBLEM_INTAKE`.

## Task lifecycle

Supported states are:

```text
PROPOSED
READY
IN_PROGRESS
VERIFYING
COMPLETE

BLOCKED
NEEDS_ADJUDICATION
SUPERSEDED
ABORTED
```

Create a bounded task:

```text
mmkit coord task . MODEL-ROUTE-01 \
  --title "Choose the baseline model" \
  --objective "Select and justify one baseline before long implementation." \
  --next-action "Compare the two remaining model routes." \
  --invariant "Do not modify official input data." \
  --acceptance "Baseline and verification plan are explicit."
```

## Optimistic revision guard

Every mutation increments the state revision. Mutating commands accept `--expect-revision`.

If another agent has already changed the coordination state, a stale writer fails closed instead of silently overwriting newer state.

Example:

```text
mmkit coord status .
mmkit coord claim . MODEL-ROUTE-01 --agent agent-a --expect-revision 3
```

If the actual revision is no longer `3`, the claim is rejected.

## Role leases

Roles:

- `worker`
- `writer`
- `reviewer`

Claims are time-bounded leases:

```text
mmkit coord claim . MODEL-ROUTE-01 --agent agent-a --role writer --lease-minutes 60
mmkit coord heartbeat . MODEL-ROUTE-01 --agent agent-a --role writer
mmkit coord release . MODEL-ROUTE-01 --agent agent-a --role writer
```

A live role lease blocks another agent from taking the same role. An expired lease can be replaced. `mmkit coord status` reports stale leases without mutating state.

An agent cannot hold both `writer` and `reviewer` for the same task while both leases are live. This is an engineering separation-of-duties primitive, not proof of independent scientific review.

## Checkpoints

A live task participant can write a compact checkpoint:

```text
mmkit coord checkpoint . MODEL-ROUTE-01 \
  --agent agent-a \
  --status VERIFYING \
  --next-action "Have agent-b independently review the route." \
  --evidence "baseline notebook hash recorded"
```

Evidence and blockers are bounded lists. Old narrative belongs in Git history or separate evidence files.

## Two-failure circuit breaker

Repeatedly patching the same failing mechanism is a known context and reliability failure mode.

Record failures explicitly:

```text
mmkit coord fail . MODEL-ROUTE-01 \
  --agent agent-a \
  --mechanism solver-bootstrap \
  --detail "same bootstrap path failed after the second controlled attempt" \
  --next-action "Stop retries and adjudicate the bootstrap design."
```

The second consecutive failure for the same mechanism moves the task to `NEEDS_ADJUDICATION`.

This is a coordination stop signal, not a security boundary. Humans or authorized agents still decide how the task resumes.

## Handoff

Before switching agents:

```text
mmkit coord handoff . MODEL-ROUTE-01 \
  --agent agent-a \
  --to-agent agent-b \
  --summary "Baseline is implemented; independent review remains." \
  --next-action "Claim reviewer role and inspect the verification evidence."
```

The handoff:

- records one compact current summary;
- records one exact next action;
- releases all live roles held by the outgoing agent;
- preserves the active task;
- does not copy chat history.

## Status / takeover

```text
mmkit coord status . --json coordination/status.json
```

A new agent should be able to recover:

- current revision;
- active task;
- task status;
- exact next action;
- current role holders and stale leases;
- failure streak/blocker count;
- latest handoff.

Repository and Git state remain authoritative over agent self-report.

## Boundary

P6 does not:

- approve human competition gates;
- certify scientific correctness;
- prove reviewer independence beyond different agent identifiers;
- synchronize private and public repositories;
- store secrets, prompts, or chat transcripts;
- replace Git/PR review.

It is a small coordination state machine designed to reduce context loss and concurrent-agent clobbering.
