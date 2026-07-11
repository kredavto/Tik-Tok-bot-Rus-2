# Incident Management

## Priorities

| Priority | Example | Target Response |
| --- | --- | --- |
| P1 | Telegram bot or API is fully unavailable | Immediate response |
| P2 | Video publication or Robokassa payments are unavailable | Same business day |
| P3 | Partial errors in isolated functions | Planned fix |
| P4 | Cosmetic UI or documentation issue | Backlog |

## Response Flow

1. Record the incident.
2. Assign priority.
3. Estimate user impact.
4. Apply temporary mitigation when needed.
5. Fix the root cause.
6. Verify service health and key user flows.
7. Document results and follow-up actions.

## Incident Record Template

```text
Incident ID:
Priority:
Started at:
Detected by:
Affected services:
User impact:
Current status:
Mitigation:
Root cause:
Resolution:
Follow-up actions:
Closed at:
```

## Availability Checks

- Telegram bot responds to `/start`.
- FastAPI `/health` and `/ready` return success.
- Nginx HTTPS endpoint is reachable.
- PostgreSQL and Redis healthchecks are green.
- Worker queue size is not growing unexpectedly.
- Latest backup exists and is readable.
- Robokassa ResultURL events are received.
- TikTok API errors are not above baseline.
- SSL certificate is valid and not close to expiration.

## Escalation

- P1: stop intake if uploads or payments may be corrupted, notify project owner, keep checking every 15 minutes.
- P2: notify project owner, isolate failing integration, keep existing queue data intact.
- P3: open a tracked issue and schedule a fix.
- P4: add to documentation or UI backlog.

## Post-Incident Review

After every P1/P2 incident:

1. Write a short postmortem.
2. Identify the root cause and contributing factors.
3. Add tests or monitoring where useful.
4. Update runbooks and deployment checks.
5. Track follow-up actions to completion.

Risk controls are summarized in [Risk Management](risk-management.md).
