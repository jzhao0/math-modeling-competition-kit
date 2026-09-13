# AI Trace Disclosure Recovery

Updated: 2026-09-09

## Status of the external `ai-use-statement` skill

A participant-provided screenshot confirms that a skill named `ai-use-statement` exists and is designed for mathematical-modeling competition AI disclosure. Visible elements indicate that it routes CUMCM 2026 rules and can generate/review the paper-end AI statement together with the detailed AI-use PDF.

However, repeated public GitHub repository/code searches did not locate the exact repository, path, owner, or version. The participant reports that the video instructs viewers to contact the author privately to obtain it. Therefore the most likely status is:

- screenshot-confirmed real skill;
- exact source identity unresolved;
- plausibly private, unindexed, or distributed out-of-band;
- **not** vendored and **not** treated as an audited dependency until the actual files/repository are supplied.

MMKit must not invent a repository identity, license, version, or implementation details for this external skill.

## Important functional clue

The participant reports that the skill's important behavior is not merely templated writing. It reads **local AI runtime / interaction traces** and uses those traces to construct the AI-use disclosure.

This capability is materially more valuable than a generic disclosure-writing template because it can reduce post-hoc reconstruction from memory and can support truthful fields such as:

- tool / model when recoverable;
- interaction time when recoverable;
- task stage / purpose;
- representative prompt or prompt summary;
- response / action summary;
- adoption, modification, rejection;
- verification evidence.

## MMKit design decision

MMKit should independently implement the capability pattern without copying an unavailable private skill.

Target architecture:

```text
local AI traces
  -> explicit-source inventory
  -> source-specific adapters
  -> normalization
  -> privacy / secret redaction
  -> evidence records
  -> human selection / confirmation
  -> official teacher/competition AI-use template
```

### Safety / truth rules

1. **Local-only by default.** Trace discovery and parsing must not upload raw chats or credentials to an external service.
2. **No broad home-directory scraping by default.** The user or project config must explicitly authorize source roots/applications.
3. **Read-only acquisition.** Original AI application/runtime logs are never edited in place.
4. **No fabricated gaps.** Missing model, timestamp, exact prompt, or adoption decision remains `UNVERIFIED` / `未留存`, not guessed.
5. **Separate raw evidence from disclosure prose.** Raw traces may contain secrets, personal data, unrelated chats, project paths, or tool noise. They are evidence inputs, not submission artifacts.
6. **Redact before persistence.** Tokens, API keys, credentials, cookies, account identifiers, private paths, and unrelated sensitive content must not be copied into the normalized disclosure ledger.
7. **Human confirmation remains required.** An automatically reconstructed event is `MACHINE_VERIFIED` only for file/timestamp/content extraction; whether it accurately represents the team's actual competition use and adoption decision is `HUMAN_CONFIRMED`.
8. **Official/teacher template is the output schema authority.** Trace recovery supplies facts; it does not define the disclosure format.

## Proposed normalized event schema

Each recoverable AI event should map to a structure similar to:

```yaml
event_id: ai-...
source_application: codex|chatgpt|claude|dsh|other
source_trace_path_hash: ...
source_record_id: ...
timestamp:
  value: ...
  proof_level: MACHINE_VERIFIED|UNVERIFIED
model:
  value: ...
  proof_level: MACHINE_VERIFIED|HUMAN_CONFIRMED|UNVERIFIED
competition_stage: ...
purpose: ...
prompt:
  exact_available: true|false
  safe_summary: ...
response_summary: ...
adoption:
  decision: adopted|modified|rejected|unknown
  proof_level: HUMAN_CONFIRMED|UNVERIFIED
verification: ...
redactions: []
```

The final disclosure generator should select a small number of representative, verified events rather than dumping complete chat histories.

## Current Drill-03 implication

Drill-03 historically has incomplete `08_ai_logs/ai_calls.jsonl`, so a local trace-recovery pass **may** help recover evidence for the final AI-use detail file. It must be performed only after the current G4 packaging correction or as a separately bounded task, because it must not reopen frozen science or interfere with the submission package.

For Drill-03, a recovery pass is useful only if it can improve factual confidence in currently uncertain fields such as:

- exact ChatGPT/Codex model labels;
- recoverable interaction timestamps;
- representative real prompts/interactions;
- whether additional AI tools were used.

If local traces do not support a field, the current truthful `未完整留存/无法核验` wording remains preferable to reconstruction from memory.

## Acquisition policy for the external skill

If the participant later obtains the actual `ai-use-statement` package from the author:

1. save the original archive/file unchanged;
2. compute SHA-256;
3. inventory all files;
4. inspect `SKILL.md`, references, scripts, license and trace-access behavior;
5. check whether it reads browser/app databases, local sessions, keychains, credentials, or network resources;
6. compare its output schema with the current 2026 teacher Word/PPT requirements;
7. only then decide between `TEACHER/EXTERNAL_REFERENCE`, `BOUNDED_RUNTIME`, or `REJECT`.

Until then, status is:

`SCREENSHOT_CONFIRMED / SOURCE_UNRESOLVED / NO_RUNTIME_ADOPTION`.
