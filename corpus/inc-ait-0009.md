# Integration Gateway - scheduled job timeouts

**Service:** api-gateway
**Source incident:** INC-AIT-0009
**Priority:** high

## Symptom

Overnight scheduled data sync jobs through the Integration Gateway in Kubernetes (namespace: intg-gateway-prod) began failing against the upstream partner API (partner: Meridian Data Services) in us-east-1. The issue was first flagged by the Monitoring System at 2025-12-02T03:14Z when engineer <PERSON> received PagerDuty alerts on repeated HTTP 401 Unauthorized responses with token expiration indicators from the gateway pod intg-gw-pod-7b4c running on host <HOSTNAME>. These were followed by HTTP 504 timeouts as the gateway retried until backoff limits were reached. The failures delayed expected partner data synchronization for internal API clients (service account: svc-datasync-east) during the 02:00–05:00 UTC scheduled job window. Reported by <PERSON> (emp ID: <EMP_ID>) from the <LOCATION> integration operations team.

## Diagnosis

Diagnostics confirmed the Meridian partner API token (bound to service account svc-datasync-east) had expired at 2025-12-01T23:59Z, producing repeated 401 Unauthorized responses logged on pod intg-gw-pod-7b4c. The Integration Gateway continued retrying these failed authenticated calls with exponential backoff (max 5 retries, 30s timeout ceiling) until backoff thresholds were reached, which caused the scheduled jobs in namespace intg-gateway-prod to overrun and present as HTTP 504 timeout failures. No rate-limiting evidence was found from the upstream Meridian endpoint, narrowing the issue to credential expiration and Kubernetes secret refresh. Investigation performed by <PERSON> and <PERSON> from the <LOCATION> integration operations team.

## Root cause

Expired API token for the upstream partner service caused authentication failures; gateway retries and backoff then extended requests until scheduled jobs timed out.

## Resolution

1. Validated that the upstream Meridian partner credential (secret: intg-partner-token-secret) in use by the Integration Gateway service account svc-datasync-east was expired based on repeated 401 responses showing token expiration, cross-referenced with Vault TTL expiry at 2025-12-01T23:59Z.
2. Rotated the Meridian partner API token via the partner portal (coordinated with <EMAIL>) and updated the Kubernetes secret intg-partner-token-secret consumed by the Integration Gateway in namespace intg-gateway-prod. Rotation performed by <PERSON> (<USER>, <EMP_ID>).
3. Redeployed and restarted the gateway pods (intg-gw-pod-7b4c and replicas) in namespace intg-gateway-prod so the running workloads loaded the new credential from the refreshed Kubernetes secret.
4. Confirmed authenticated calls from service account svc-datasync-east to the Meridian partner API (https://api.meridiandata.io/v2/sync) no longer returned 401 Unauthorized responses after the secret rollout — test call returned HTTP 200 at 2025-12-02T21:04Z.
5. Verified two consecutive scheduled integration job runs (02:00 UTC and 03:00 UTC cycle equivalents triggered manually) completed successfully without retry exhaustion or HTTP 504 timeouts; data sync payloads confirmed in downstream consumers.
6. Monitored gateway and job metrics via the Monitoring System dashboard for 2 hours after deployment (until 2025-12-02T23:15Z) to confirm stable processing, nominal latency, and no recurrence. Alert channel confirmed clear by <PERSON>.
