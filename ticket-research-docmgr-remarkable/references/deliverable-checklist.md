# Deliverable Checklist

Use this checklist before final handoff.

## Ticket setup

- `docmgr ticket create-ticket` completed (or existing ticket confirmed)
- design doc exists
- diary doc exists
- index/tasks/changelog are updated

## Analysis quality

- a new reader can explain the main concept and overall architecture from the introduction alone, without relying on later implementation details
- essential terminology is introduced before explanations depend on it; examples and diagrams clarify the concept rather than assume it
- architecture mapping is evidence-backed
- key claims reference files
- proposed solution includes APIs and pseudocode
- implementation plan is phased and actionable
- testing strategy is explicit

Reader orientation is a manual content check, not something proved by a heading, a glossary, or `docmgr doctor`. Keep it proportional to the document; do not require a fixed introductory template or an exhaustive overview.

## Bookkeeping

- key files related via `docmgr doc relate`
- changelog updated with meaningful entries
- tasks reflect completion state

## Validation

- `docmgr doctor --ticket <TICKET-ID> --stale-after 30` passes
- vocabulary warnings resolved or intentionally accepted

## reMarkable delivery

- delivery was requested; otherwise this section is not applicable
- specialist `remarkable-upload` policy followed (no duplicated preflight/auth recipe)
- requested bundle uploaded, with successful result and destination retained
- dry-run, independent listing or state inspection performed when explicitly required or needed under that policy
- no unauthorized overwrite/annotation loss; ambiguous outcomes are not reported as success

## Final response

- include ticket path
- include doc paths
- include validation status
- include requested upload destination and the actual evidence level (upload result versus independent listing)
- include any open questions or residual risks

