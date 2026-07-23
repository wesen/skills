---
name: upwork-bid-operations
description: Capture and review Upwork jobs with Surf and upwork-tracker, maintain private local agent audit logs, refresh shortlisted details, build evidence-grounded proposals, safely fill bid forms, record human-confirmed submissions, and archive old jobs. Use when the user asks to scrape/search Upwork jobs, review or mutate a canonical Tracker job, prepare or bid on an Upwork job, manage proposal lifecycle, or clean up the job queue.
---

# Upwork Bid Operations

Use this skill for the complete Upwork operating workflow: read-only job collection, evidence review, shortlist refresh, proposal drafting, form preparation, human submission, tracker synchronization, and queue maintenance.

This skill uses the local Surf browser tooling and `upwork-tracker`. It does not bypass login, CAPTCHA, rate limits, or marketplace controls.

## Non-negotiable safety rules

1. **Submission is human-only.** Never run `surf upwork bid-apply --submit`. Never click **Send for N Connects** or **Submit proposal**. A filled browser form is still a draft.
2. **Do not mark a job submitted without explicit operator confirmation.** Surf success and tracker state are not proof that Upwork accepted a proposal.
3. **Retry reads, not mutations.** Bounded retries are allowed for search/detail captures. Do not automatically replay submission, tracker writes, saves, deletes, publishes, or uncertain uploads.
4. **Claims require evidence.** A job description is client requirement evidence, not freelancer experience evidence. Use reviewed profile/résumé snapshots, public project sources, portfolio items, provenance-backed project notes, or a direct operator statement.
5. **Operator facts are private memory.** Retrieve and inspect them before drafting; do not create facts from job requirements or inference. Facts do not authorize Connects spending or submission.
6. **Keep private data outside git.** Store authenticated captures, profile snapshots, proposal bodies, and form receipts under the operator-managed private directory.
7. **Inspect before import.** Search/detail captures are immutable operational evidence. Confirm they are non-empty, valid, and relevant before importing them.
8. **Use one browser detail capture at a time.** Do not parallelize Upwork page navigation or proposal-form work.
9. **Read back the live form.** React rerenders can erase values after a command succeeds. Verify the cover letter, screening answers, commercial terms, milestones, totals, Connects, and attachments in the DOM/UI.
10. **Do not confuse fixed-price milestone amounts.** Upwork milestone inputs are individual amounts and are summed by Upwork. A `$1,000` plan may be `$400 + $300 + $300`, not cumulative `$400 + $700 + $1,000`.
11. **Audit logs describe local Tracker work only.** They never prove submission, remote archival, marketplace mutation, or Connects spending. Only a human-confirmed submission flow may record `submitted`.
12. **Keep audit descriptions non-sensitive.** Never log proposal bodies, receipts, prompts, transcripts, secrets, arbitrary environment values, or claims about remote Upwork actions.

## Private agent audit logs

Use private job-coupled audit logs for meaningful local work on canonical `upwork:<id>` jobs. The Tracker records allowlisted Pi identity fields automatically; audit entries remain local/private and do not interact with Upwork.

### Automatic logs for successful mutations

Successful Tracker job patches, tag changes, triage decisions, and private proposal-draft saves already create automatic logs. Rely on those records and do not add a duplicate manual entry unless it supplies distinct useful reasoning.

### One manual log for meaningful read-only work

After meaningful read-only research or review of one canonical job, add exactly one audit entry with an allowed action kind, a concise non-sensitive description, a unique idempotency key, and the explicit DB path:

```bash
upwork-tracker verbs upwork job-action-log-add "upwork:<id>" \
  --action-kind triage-reviewed \
  --description "Reviewed local evidence and left the job unchanged." \
  --idempotency-key "agent-action-<id>-$(date +%s)" \
  --db-path "$HOME/.local/share/upwork-tracker/upwork.db" \
  --output json --output-as-objects
```

Allowed action kinds are fixed:

```text
triage-reviewed
comment-added
fact-pinned
tag-added
archive-requested
proposal-draft-requested
proposal-draft-saved
fact-created
fact-updated
application-transition-requested
```

Use one idempotency key per logical action and reuse it only for an exact retry. Do not create canonical Upwork audit entries for `freelancer:<id>` records.

Inspect a canonical job's private action history with:

```bash
upwork-tracker verbs upwork job-action-log-list "upwork:<id>" \
  --limit 50 \
  --db-path "$HOME/.local/share/upwork-tracker/upwork.db" \
  --output json --output-as-objects
```

Never pass secrets, prompt text, proposal content, receipt data, transcript paths, or arbitrary environment data in descriptions or `--runtime-json`. An `archive-requested` entry is only a local request record; it does not mean the remote job was archived.

## Prerequisites and private paths

```bash
BIN="${UPWORK_TRACKER_BIN:-upwork-tracker}"
DB="${UPWORK_TRACKER_DB:-$HOME/.local/share/upwork-tracker/upwork.db}"
PRIVATE="${UPWORK_PRIVATE_DIR:-$HOME/.local/share/upwork-tracker/private/upwork-proposals}"
CAPTURES="${UPWORK_CAPTURE_DIR:-$HOME/.local/share/upwork-tracker/private/captures/$(date -u +%F)}"
mkdir -p "$PRIVATE/profile" "$PRIVATE/proposals" "$CAPTURES"

command -v surf
command -v jq
command -v sqlite3
command -v "$BIN"
test -f "$DB"
```

Read the current project playbook before a new workflow or after tool changes:

```text
/home/manuel/code/others/llms/pi/nicobailon/surf-cli/ttmp/2026/07/21/SURF-UPWORK-BID-RELIABILITY-2026-07-21--reliable-upwork-proposal-form-automation/playbook/01-upwork-bid-and-portfolio-operations-playbook.md
```

Read tracker help when command behavior is unclear:

```bash
$BIN help upwork-fetch-and-import-jobs
$BIN help upwork-shortlist-proposal-preparation
$BIN help upwork-operator-facts
$BIN help upwork-proposal-lifecycle-migration
```

## Phase 1: Capture a bounded Upwork search

Use focused queries and bounded result counts. Keep captures outside the repository.

```bash
SEARCH="$CAPTURES/upwork-esp32-firmware-page-1.yaml"

$BIN capture search \
  --marketplace upwork \
  --query 'ESP32 firmware' \
  --sort recency \
  --page 1 \
  --page-size 50 \
  --max-results 50 \
  --out "$SEARCH"
```

For another workstream, use a separate capture:

```bash
$BIN capture search \
  --marketplace upwork \
  --query 'Golang' \
  --sort recency \
  --page 1 \
  --page-size 50 \
  --max-results 50 \
  --out "$CAPTURES/upwork-golang-page-1.yaml"
```

The current `marketplace-capture/v1` envelope may not carry a login assertion. If the signed-in capture is rejected with an authentication-assertion error, use public mode only when that limitation is acceptable:

```bash
$BIN capture search \
  --marketplace upwork \
  --query 'ESP32 firmware' \
  --sort recency \
  --page 1 \
  --page-size 50 \
  --max-results 50 \
  --require-auth=false \
  --out "$SEARCH"
```

Record that the capture is public evidence. Do not describe it as proof of an authenticated session. Never bypass login or CAPTCHA to obtain a capture.

### Inspect before importing

```bash
test -s "$SEARCH"
head -30 "$SEARCH"
rg -n '^(schemaVersion:|remoteId:|title:|postedAt:)' "$SEARCH" | head -100
```

Review relevance. Do not import an empty, malformed, or obviously wrong query result.

### Import and rebuild

```bash
$BIN import search \
  --db "$DB" \
  --marketplace upwork \
  --source "$SEARCH"

$BIN projection rebuild --db "$DB"
sqlite3 "$DB" 'PRAGMA integrity_check;'
```

Expect `ok` from SQLite. Re-importing the same capture is idempotent, but it is not a substitute for obtaining a fresh search.

### Determine “today” correctly

Search captures store `postedAt` in UTC. The operator may mean local calendar date. Convert timestamps to the operator's timezone before filtering; do not compare mixed ISO and human-formatted timestamps lexically. Preserve the capture timestamp and timezone in any report.

## Phase 2: Refresh shortlisted jobs

Start with the current shortlist; do not use a stale hard-coded candidate list.

```bash
SHORTLIST="$CAPTURES/shortlisted-jobs.json"
$BIN verbs upwork jobs-list \
  --db-path "$DB" \
  --status shortlisted \
  --sort posted-desc \
  --limit 100 \
  --output json --output-as-objects > "$SHORTLIST"

jq '.data[] | {id,version,title:.attributes.title,posted:.attributes.posted,url:.attributes.url}' "$SHORTLIST"
```

Refresh each URL sequentially. Require a non-empty capture before importing. Keep failures and continue with successful jobs.

```bash
DETAILS="$CAPTURES/shortlisted-details"
mkdir -p "$DETAILS"

jq -r '.data[] | [.id,.attributes.url,.attributes.title] | @tsv' "$SHORTLIST" |
while IFS=$'\t' read -r id url title; do
  remote="${id#upwork:}"
  out="$DETAILS/${remote}-job-detail.yaml"
  err="$DETAILS/${remote}-surf.err"
  captured=0

  for attempt in 1 2 3; do
    rm -f "$out"
    if surf upwork job "$url" --capture-envelope >"$out" 2>"$err" && test -s "$out"; then
      captured=1
      break
    fi
    sleep 3
  done

  if [ "$captured" -ne 1 ]; then
    printf 'detail capture failed: %s\n' "$id" >&2
    continue
  fi

  $BIN import details \
    --db "$DB" \
    --marketplace upwork \
    --source "$out"
done

$BIN projection rebuild --db "$DB"
sqlite3 "$DB" 'PRAGMA integrity_check;'
```

If a job reports “not found or no longer available,” preserve the error and do not fabricate a detail record. A successful detail refresh is evidence of the page capture, not authorization to shortlist or bid.

For a reviewed search capture, the built-in cohort command can also be used:

```bash
$BIN capture detail \
  --marketplace upwork \
  --source "$SEARCH" \
  --out-dir "$DETAILS" \
  --retries 2

$BIN import details --db "$DB" --marketplace upwork --source "$DETAILS"
$BIN projection rebuild --db "$DB"
```

## Phase 3: Review candidates and evidence

Use bounded tracker queries:

```bash
$BIN verbs upwork jobs-list \
  --db-path "$DB" \
  --status shortlisted \
  --sort posted-desc \
  --limit 50 \
  --output json --output-as-objects

$BIN verbs upwork jobs-list \
  --db-path "$DB" \
  --starred true \
  --sort posted-desc \
  --limit 50 \
  --output json --output-as-objects
```

Before selecting a job for a proposal, inspect the complete aggregate and faithful context:

```bash
JOB_ID='upwork:012345678901234567890'
JOB="$PRIVATE/proposals/${JOB_ID#upwork:}-job-context.md"

job=$($BIN verbs upwork jobs-get "$JOB_ID" \
  --db-path "$DB" \
  --output json --output-as-objects)

jq '.data | {id,version,attributes,relationships}' <<<"$job"
$BIN verbs upwork jobs-context "$JOB_ID" --db-path "$DB" > "$JOB"
```

Build an evidence table before drafting:

```text
Client requirement | Verified evidence | Treatment
------------------- | ----------------- | ---------
Go systems work    | Public repository/project report | Claim with link
Embedded firmware  | Profile/project evidence | Claim narrowly
Exact MCU/panel    | Not established | State boundary and plan
Client hardware    | Job description only | Treat as requirement, not experience
```

Do not turn a related skill, tag, job requirement, or private fact summary into a stronger claim than its source supports.

### Profile and portfolio evidence

Reuse a reviewed snapshot when current; otherwise refresh it read-only:

```bash
PROFILE="$PRIVATE/profile/upwork-profile.md"
# Only if absent or stale:
surf upwork freelancer "$PROFILE_URL" > "$PROFILE"
surf upwork portfolio list --profile-url "$PROFILE_URL"
```

Use exact published portfolio titles for highlights. Public project reports and repositories are evidence; private local notes are not public evidence unless a public link or operator-approved wording supports the claim.

### Operator facts

Facts are local reusable memory, not marketplace evidence:

```bash
facts=$($BIN verbs upwork operator-facts-list \
  --db-path "$DB" \
  --query 'Go embedded ESP32' \
  --status active \
  --limit 20 \
  --output json --output-as-objects)

jq '.data[] | {id,version,title:.attributes.title,summary:.attributes.summary,tags:.attributes.tags}' <<<"$facts"

FACT_ID=$(jq -r '.data[0].id // empty' <<<"$facts")
$BIN verbs upwork operator-facts-get "$FACT_ID" \
  --db-path "$DB" \
  --output json --output-as-objects | jq '.data'
```

Read the body, caveats, validity, and provenance. Only link an exact fact version as `used_in` after it genuinely appears in a saved proposal version.

## Phase 4: Prepare and review a bid

Choose exactly one job for live form preparation. Do not open many application forms in parallel.

### Inspect the form

```bash
JOB_URL=$(jq -r '.data.attributes.url // empty' <<<"$job")
REMOTE_ID="${JOB_ID#upwork:}"
TEMPLATE="$PRIVATE/proposals/${REMOTE_ID}-bid.txt"

surf upwork bid-prepare "$JOB_URL" \
  --out "$TEMPLATE" \
  --keep-tab-open
```

Record the returned tab ID. Inspect the generated template and compare it with the live DOM:

- cover-letter field and label;
- screening question count and exact labels;
- hourly versus fixed-price mode;
- required Connects and any boost;
- requested profile highlights;
- attachment controls.

Do not assume a `$0.00` detected rate is an hourly bid; on fixed-price forms it may be a milestone amount or unsupported detection.

Import form evidence only after inspection:

```bash
$BIN import proposals \
  --db "$DB" \
  --marketplace upwork \
  --proposals "$TEMPLATE"
```

### Draft from evidence

A sound proposal contains:

1. Direct fit statement in the operator's voice.
2. One or two evidence-backed examples.
3. A short plan tied to the client's actual requirements.
4. Relevant public links.
5. Explicit boundaries for unverified hardware or experience.
6. Clear commercial terms only after approval.

Present the exact cover letter, answers, rate or fixed total, milestones, highlights, attachments, boost, and required Connects for human approval. A polished draft is not implicit approval.

### Persist the private proposal draft

Save the reviewed draft before filling the live form. Read the current job revision immediately before writing.

```bash
DRAFT="$PRIVATE/proposals/${REMOTE_ID}-draft.md"
version=$($BIN verbs upwork jobs-get "$JOB_ID" \
  --db-path "$DB" --output json --output-as-objects | jq -r '.data.version')

$BIN verbs upwork proposal-draft-import "$JOB_ID" \
  --db-path "$DB" \
  --proposal-file "$DRAFT" \
  --change-comment 'Store reviewed proposal draft before live form fill.' \
  --expected-version "$version" \
  --idempotency-key "proposal-import-$REMOTE_ID-v1" \
  --output json --output-as-objects
```

A retry with the same intended body should reuse the same idempotency key. A changed body requires a fresh read, change comment, expected version, and idempotency key. Proposal versions are immutable.

## Phase 5: Fill the form, never submit

Only after explicit approval of exact text and terms:

```bash
surf upwork bid-apply \
  --file "$TEMPLATE" \
  --tab-id "$TAB_ID" \
  --keep-tab-open
```

Never add `--submit`.

Read back the live page after filling:

- cover letter and character count;
- every screening answer and label;
- hourly rate or fixed total;
- rate increase setting;
- profile highlights;
- required and boost Connects;
- milestone descriptions, dates, amounts, and calculated total;
- attachment filenames and file-input state.

### Fixed-price milestones

Treat each Upwork milestone amount as an individual amount. Pace React-controlled updates one field at a time, reacquire controls after rerenders, and verify the final total, fee, payout, and Connects.

### Attachments

The current text-template flow may not reliably set a browser file chooser. Treat the cover-letter sentence and actual attachment as separate states. Prepare a private sanitized copy, remove unnecessary metadata where practical, verify size/duration/dimensions and hash, and have the human upload it in the browser when automation cannot. Confirm the visible attachment tile or `input[type=file].files` before submission.

## Phase 6: Record a human-confirmed submission

After the operator explicitly says the marketplace submission succeeded:

1. Read the current job aggregate and revision.
2. Preserve the exact proposal version used.
3. Apply legal application transitions sequentially, rereading the revision after each mutation.
4. Use a unique idempotency key for every transition.

Typical path:

```bash
JOB_ID='upwork:022079271086430468859'

# Read current revision first.
$BIN verbs upwork jobs-get "$JOB_ID" --db-path "$DB" \
  --output json --output-as-objects

$BIN verbs upwork application-transition "$JOB_ID" \
  --db-path "$DB" --to review \
  --expected-version "$VERSION" \
  --idempotency-key "application-$REMOTE_ID-review-confirmed-20260722" \
  --output json --output-as-objects

# Read again, then transition review -> ready.
# Read again, then transition ready -> submitted.
```

Never use a stale expected version. The final application status should be `submitted`; the aggregate job status normally becomes `applied`. The agent records the operator's confirmation; it does not claim to have clicked Send.

## Phase 7: Archive old jobs safely

`archived` is a job workflow status separate from application statuses. `jobs-list` supports:

```text
new, shortlisted, applied, interviewing, won, rejected, archived
```

For a date cutoff, enumerate all pages, parse timestamps correctly, review the exact set, and use versioned `jobs-update` mutations. Do not rely on `stale-execute` when the requested set includes shortlisted, rejected, or applied jobs; stale archival is a narrower workflow.

```bash
$BIN verbs upwork jobs-update "$JOB_ID" \
  --db-path "$DB" \
  --patch-json '{"status":"archived"}' \
  --expected-version "$VERSION" \
  --idempotency-key "archive-before-2026-07-20-$REMOTE_ID" \
  --output json --output-as-objects
```

Archiving retains history. Verify after the batch that no matching non-archived jobs remain and rebuild the projection. Do not archive a submitted/won job merely because it is old unless the operator explicitly included those states in the instruction.

## Lifecycle and status model

Job workflow status and application status are different fields.

```text
Job status:         new -> shortlisted -> applied -> interviewing -> won
                   \-> rejected
                   \-> archived

Application status: not_started -> planning -> drafting -> review -> ready -> submitted
```

A confirmed submission changes the application lifecycle; a job may become `applied`. Archiving affects the job queue and does not erase proposal versions or activity history.

## Common failures

### Authentication assertion failure

If capture reports that `marketplace-capture/v1` does not carry an authentication assertion, either resolve the browser/session tooling or explicitly use `--require-auth=false` for public evidence. Do not mislabel public capture as authenticated evidence.

### Empty or partial capture

Delete the failed output, retry the read-only capture up to a bounded limit, and import only a non-empty valid file. Preserve the error.

### Job not found

A shortlisted job can disappear or become unavailable. Keep the failure receipt; do not create a placeholder or remove the local record without an explicit queue decision.

### `document_format` schema error

If proposal commands fail with `SQL logic error: no such column: document_format`, back up the private DB, run the repository's schema-aware importer against a valid detail capture, verify migrations and columns, then retry. Do not manually mark migrations applied.

### React form values disappear

Pace updates, reacquire DOM controls after rerenders, and read back the full form. Never trust a successful command alone.

### Attachment missing

A cover-letter mention is not an upload. Inspect the actual file input or attachment tile. If Surf cannot set it, stop and ask the human to upload it.

### Mutation outcome unclear

Stop. Do not replay the mutation. Read the tracker and live marketplace state, reconcile, and use the existing idempotency key only if the operation is known to be safely retryable.

## Final response checklist

Report:

- search queries and capture date/timezone;
- number of records captured/imported;
- detail refresh successes and failures;
- selected jobs and evidence limitations;
- proposal version and live tab when preparing a bid;
- exact commercial terms and attachment state;
- whether the human submitted;
- final tracker lifecycle state;
- archive cutoff and counts when cleaning the queue.

Never say “submitted” unless the operator explicitly confirmed it.

## Primary references

- Surf playbook: `/home/manuel/code/others/llms/pi/nicobailon/surf-cli/ttmp/2026/07/21/SURF-UPWORK-BID-RELIABILITY-2026-07-21--reliable-upwork-proposal-form-automation/playbook/01-upwork-bid-and-portfolio-operations-playbook.md`
- Tracker capture tutorial: `/home/manuel/code/wesen/go-go-golems/upwork/docs/help/upwork-fetch-and-import-jobs.md`
- Tracker proposal tutorial: `/home/manuel/code/wesen/go-go-golems/upwork/docs/help/upwork-shortlist-proposal-preparation.md`
- Tracker schema: `/home/manuel/code/wesen/go-go-golems/upwork/docs/help/upwork-tracker-database-schema.md`
- Tracker safe workflow: `/home/manuel/code/wesen/go-go-golems/upwork/docs/help/upwork-agent-safe-workflow.md`
