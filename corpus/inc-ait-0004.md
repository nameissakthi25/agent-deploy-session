# API integration timeouts causing delayed data sync

**Service:** api-gateway
**Source incident:** INC-AIT-0004
**Priority:** medium

## Symptom

Overnight scheduled data synchronization jobs between the Integration Gateway (igw-prod-east.corplabs.internal) and the downstream Inventory API service intermittently failed from approximately 02:00 to 03:30 UTC on 2025-12-02 in us-east-1. The gateway received repeated 504 Gateway Timeout and ETIMEDOUT responses on the /api/v2/inventory/sync endpoint, which delayed application data updates and increased integration job failures. Reported by <PERSON> (<EMAIL>) from the <LOCATION> operations center — internal operations needed the scheduled sync process to complete normally so downstream application records would be current by the start of business.

## Diagnosis

Diagnostics ruled out token expiry (<USER> service account token valid through 2026-03-15) and rate limiting (no 429 responses observed), and confirmed that the overnight sync failures aligned with elevated downstream Inventory API latency (p99 response time spiking to 45s vs. normal 2s baseline) beyond the Integration Gateway 30s timeout threshold. Request traces from Jaeger, Monitoring System dashboards, and 504/ETIMEDOUT patterns on node <IP> support downstream service slowness as the primary cause.

## Root cause

Elevated latency on the downstream service caused API responses to exceed the Integration Gateway timeout window, resulting in intermittent 504 Gateway Timeout errors and failed scheduled sync jobs.

## Resolution

1. Correlated the failed sync window (02:00–03:30 UTC) with Integration Gateway latency metrics on igw-prod-east (node <IP>), Jaeger API traces for the /api/v2/inventory/sync endpoint, and downstream Inventory API endpoint health to confirm the timeout condition was external to the scheduler itself. Analysis performed by <PERSON> (<USER>).
2. Escalated the incident to the downstream Inventory API service owners — <PERSON> (<EMAIL>, phone <PHONE>) at the <LOCATION> office — with captured request traces, timeout evidence (47 failed jobs, p99 latency 45s), and the affected overnight time window for remediation.
3. Applied a temporary increase to the Integration Gateway timeout threshold from 30s to 90s on the igw-prod-east configuration (ConfigMap igw-timeout-override) so requests could complete during the period of elevated downstream latency. Change approved by team lead <PERSON> (<USER>, <EMP_ID>).
4. Adjusted retry and backoff settings on the Integration Gateway — increased max retries from 3 to 5 and exponential backoff base from 1s to 2s — to reduce immediate job failure rates and improve recovery for intermittent downstream slow responses. Configuration deployed to igw-prod-east pods via Helm update.
5. Re-ran and validated the 47 previously affected synchronization jobs (sync-inv-20251202-0200 through sync-inv-20251202-0330) after downstream latency stabilized at approximately 06:15 UTC, confirming successful completion and normal data propagation to the order-fulfillment application. Validated by <PERSON> from the <LOCATION> operations center.
6. Removed the temporary timeout increase (reverted igw-prod-east ConfigMap to 30s default) after stability was confirmed at 09:00 UTC and kept Monitoring System alerting in place to verify that 504 and timeout rates returned to baseline. Post-incident review scheduled with <PERSON>'s team for 2025-12-04.
