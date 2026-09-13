# G4 Exact-File Lock

G4 is the final **human submission gate**. It is not equivalent to an Agent saying `PASS`, a PDF compiling, or a preview directory existing.

## Canonical artifacts

The final lock applies to the exact bytes of:

1. `competition_paper.pdf`
2. `AI工具使用详情.pdf`
3. `supporting_material.zip`

`09_submission/` is the unique canonical submission directory. `FINAL/` is not a second final location.

## Required sequence

### 1. Human final read

A participant reads the final candidate continuously from page 1 through the end, including:

- abstract;
- formulas and symbols;
- tables and figures at printed size;
- references;
- appendix;
- AI-use statement;
- separate AI-detail PDF.

Any human edit makes prior G4 hashes stale.

### 2. Clean-room support test

Extract `supporting_material.zip` into a fresh directory **outside the modeling project tree**.

The extracted package must not silently reach back into the original workspace.

Check:

- no path traversal / absolute local path;
- no hidden dependency on `D:\Projects\...`, `C:\Users\...`, `/Users/...`, `/home/...`;
- documented software/dependencies;
- documented handling of official contest attachments if they are intentionally external;
- documented run order and commands;
- all shipped intermediate inputs exist, or a deterministic program creates them;
- claimed runnable programs actually execute in the documented clean-room context;
- validation scripts reproduce/check the frozen headline results.

If a package cannot be made standalone because official attachments must stay external, the README must state exactly which official files the reviewer must place where. Missing files must produce a clear error rather than falling back to the author's machine.

### 3. AI-detail identity

There is exactly one canonical AI-detail PDF.

Require:

```text
SHA256(standalone AI工具使用详情.pdf)
==
SHA256(AI工具使用详情.pdf extracted from supporting_material.zip)
```

Text-equivalent or visually-equivalent but byte-different copies are not accepted for the exact-file lock.

### 4. Submission hygiene

Check all final artifacts for:

- participant/team/school identity where prohibited;
- PDF/Office document properties;
- XMP/EXIF metadata;
- local usernames and absolute paths;
- API keys, tokens, passwords and credentials;
- internal workflow labels (`candidate`, `Visual Pass`, internal G numbers in user-facing files, audit handoff paths, etc.);
- unexpected temporary/build files;
- archive path traversal or duplicate entries.

Software `Creator`/`Producer` fields must follow the teacher's current strict instruction. If the teacher requires right-click properties empty, clear them from the canonical final PDFs and recheck visual identity.

### 5. Manifest and checksums

After **all** edits are finished, record:

- byte size;
- MD5;
- SHA-256;
- page count;
- support archive file count;
- AI-detail byte-identity result;
- clean-room result;
- anonymity/metadata/secret result.

Checksums generated before the last edit are preview checksums only.

### 6. Human approval

`human_gates/G4_submission.md` must contain an explicit participant approval such as:

```text
APPROVED: YES
```

and the approval record should bind the three final SHA-256 values.

An Agent must not write the human approval on the participant's behalf.

### 7. Promotion

Only after human approval:

- copy the exact locked artifacts to `09_submission/`;
- verify copied hashes are identical;
- do not rewrite/recompress/regenerate them afterward;
- preserve the submission/checksum record.

If any canonical artifact changes after approval, G4 becomes `STALE` and must be repeated.

## Proof levels at G4

Suggested evidence labels:

| Item | Required proof |
|---|---|
| PDF/ZIP hashes | `MACHINE_VERIFIED` |
| archive path/secret scan | `MACHINE_VERIFIED` |
| clean-room execution | `MACHINE_VERIFIED` |
| page-by-page reading | `HUMAN_CONFIRMED` |
| AI-use truthfulness | `HUMAN_CONFIRMED` + retained evidence where available |
| scientific correctness | prior G2/G3 evidence + final human review |
| G4 approval | `HUMAN_CONFIRMED` |

A snapshot hash alone is `SNAPSHOT_ONLY`; it does not prove the code is runnable or the paper is scientifically correct.

## MMKit helper

Use:

```powershell
python scripts\g4_bundle_audit.py `
  --paper <competition_paper.pdf> `
  --ai <AI工具使用详情.pdf> `
  --support <supporting_material.zip> `
  --extract-dir <fresh-clean-room-dir> `
  --json-out <g4_bundle_audit.json>
```

Add `--execute-manifest` only after inspecting the support package's `RUN_MANIFEST.json` and intentionally allowing the listed commands to run.

The helper verifies submission engineering. It does **not** certify mathematical or scientific correctness.
