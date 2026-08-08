# Safety Policy

Operating guardrails for loops and agents in this repo. These rules are binding and complement `loop-constraints.md`.

## Path Denylist (never edit, never delete)

- `.env`, `.env.*` (local secrets)
- `auth/`, `payments/`, `secrets/`, `credentials/`
- `ec2-key.pem` and any SSH keys / identity files
- Infrastructure configs (systemd units, nginx, terraform) without explicit human approval
- Anything under `.git/`

## Auto-Merge Policy

- **L1 (report-only):** no auto-fix, no auto-merge. The loop reports; the human decides.
- **L2 (assisted):** changes may be proposed as draft PRs only. Human reviews before marking ready.
- **L3 (unattended):** not enabled. Requires explicit human opt-in AND a passing `loop doctor` health check.

## Merge Rules

- Never auto-merge to main without human approval.
- Always run `npm test` (and `npm run lint`) before proposing a fix.
- Never disable tests or skip assertions to make CI green.
- Max 3 fix attempts per item; escalate to human after.

## MCP / External Scopes

- No destructive external actions (deletes, sends, payments) without human approval.
- Email sends are gated by business hours and per-day caps (see `admin/agency/sba_autopilot.py`).

## Escalation

- Any medium+ risk change → `ESCALATE_HUMAN` via the `loop-verifier` agent.
- Kill switch: `loop-pause-all` pauses schedulers and notifies human.

## Budget

- Max tokens/day: 100k (see `loop-budget.md`).
- If token spend hits 80% of daily cap, switch to report-only.
- Append each run to `loop-run-log.md`.
