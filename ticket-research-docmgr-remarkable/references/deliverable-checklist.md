# Deliverable Checklist

Use this checklist before final handoff.

## Ticket setup

- `docmgr ticket create-ticket` completed (or existing ticket confirmed)
- design doc exists
- diary doc exists
- index/tasks/changelog are updated

## Analysis quality

- architecture mapping is evidence-backed
- key claims reference files
- proposed solution includes APIs and pseudocode
- implementation plan is phased and actionable
- testing strategy is explicit

## Bookkeeping

- key files related via `docmgr doc relate`
- changelog updated with meaningful entries
- tasks reflect completion state

## Validation

- `docmgr doctor --ticket <TICKET-ID> --stale-after 30` passes
- vocabulary warnings resolved or intentionally accepted

## reMarkable delivery

- `remarquee status` OK
- account verified (`remarquee cloud account --non-interactive`)
- dry-run bundle upload completed
- real bundle upload completed
- remote listing verified (`remarquee cloud ls ... --long --non-interactive`)

## Final response

- include ticket path
- include doc paths
- include validation status
- include upload destination and verification result
- include any open questions or residual risks

