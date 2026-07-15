# Metrics and KPI

## Technical KPI

Track these indicators for operational stability:

| Metric | Purpose |
| --- | --- |
| Telegram bot availability | Confirms users can interact with the bot |
| FastAPI availability | Confirms callbacks, health checks, and internal API are reachable |
| Average publication processing time | Measures upload lifecycle performance |
| Successful publication rate | Tracks reliability of video publication flow |
| Average API response time | Tracks backend responsiveness |
| Worker queue size | Shows publication backlog and scaling pressure |
| Worker retry count | Shows temporary failures and external service instability |

## Business Metrics

Track these indicators for project growth:

| Metric | Purpose |
| --- | --- |
| New users | Measures registration growth |
| Active FREE users | Shows free-tier usage |
| Active PRO users | Shows paid PRO adoption |
| Active BUSINESS users | Shows paid BUSINESS adoption |
| FREE to PRO conversion | Measures PRO monetization |
| FREE to BUSINESS conversion | Measures BUSINESS monetization |
| Successful payments | Measures provider-specific payment flow |
| Revenue by plan | Supports pricing and growth analysis |

## Quality Metrics

Track these indicators for release and support quality:

| Metric | Purpose |
| --- | --- |
| Critical error count | Shows production stability |
| Repeated failure count | Shows recurring defects or external instability |
| Incident recovery time | Measures time to restore normal service |
| Pre-release test pass rate | Shows release readiness |
| Failed webhook count | Tracks Telegram, TikTok, and Robokassa callback issues |
| Failed publication count by reason | Helps prioritize reliability work |

## Administrative Dashboard

The admin dashboard should expose:

- Current service availability.
- User counts by tariff.
- New registrations by period.
- Publication volume and success rate.
- RUB and Telegram Stars successful payments and revenue by period, reported separately.
- Conversion FREE to PRO and FREE to BUSINESS.
- Queue size, processing latency, and failed jobs.
- Critical errors and repeated failures.

## Operational Use

Use metrics to:

- Detect incidents.
- Plan worker and API scaling.
- Evaluate release quality.
- Identify bottlenecks in publication processing.
- Review monetization and tariff performance.
- Prioritize technical debt and reliability work.

Capacity planning and threshold handling are described in [Capacity and Performance Management](capacity-management.md).

Metrics must never include TikTok OAuth tokens, Robokassa secrets, Telegram bot tokens, or raw user video contents.

Diagnostic event and log correlation requirements are described in [Observability and Diagnostics](observability-diagnostics.md).
