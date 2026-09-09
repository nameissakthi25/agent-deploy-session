# Integration Gateway API timeouts causing failed sync jobs

**Service:** api-gateway
**Source incident:** INC-AIT-0005
**Priority:** low

## Symptom

Customers were trying to run scheduled data synchronization through the Integration Gateway (igw-prod-east-01), but starting around 2025-12-02 03:10 UTC the gateway began returning repeated 504 Gateway Timeout errors on downstream API calls to the Order Fulfillment API Service. Two scheduled sync jobs (sync-job-4417 and sync-job-4418, owned by <USER>) failed, data delivery to the Application was delayed by over 3 hours, and monitoring reported elevated latency and timeout alerts in us-east-1. The issue was initially reported by <PERSON> (<EMAIL>) from the <LOCATION> operations team, who noticed the failed jobs in the morning dashboard review.

## Diagnosis

Diagnostics covered token validity for service account <USER>, timing correlation between job failures (sync-job-4417, sync-job-4418) and gateway timeouts on igw-prod-east-01, and exclusion of API rate limiting. The decisive finding was that the Integration Gateway's downstream API token (secret ref: vault/igw/downstream-api-token, expired 2025-12-01T23:59:59Z) had expired, causing authentication failures that manifested externally as 504 timeouts. Investigation was performed by <PERSON> with assistance from the <LOCATION> operations team.

## Root cause

The Integration Gateway was using an expired API token to authenticate to the downstream API Service. Authentication failures on downstream calls led to repeated retries and eventual upstream 504 timeout responses, which caused scheduled sync jobs to fail.

## Resolution

1. Validated that the token configured on the Integration Gateway (secret ref: vault/igw/downstream-api-token, associated with service account <USER>) had expired on 2025-12-01T23:59:59Z and no longer authenticated successfully to the downstream Order Fulfillment API Service.
2. Rotated the expired API token via Vault and updated the stored secret (vault/igw/downstream-api-token) used by the Integration Gateway for downstream API authentication. Rotation was performed by <PERSON> (<USER>, emp ID <EMP_ID>) at 2025-12-02T14:42:00Z.
3. Confirmed authenticated API requests from igw-prod-east-01 (<IP>) completed successfully after the secret update, with response times returning to baseline ~200ms, and removed reliance on the temporary timeout increase as the primary mitigation.
4. Re-ran queued sync jobs (sync-job-4417 and sync-job-4418) and verified previously failed synchronization jobs completed successfully without further 504 errors. <PERSON> confirmed data delivery to the Application was restored and consistent.
5. Updated the token rotation policy to enforce automated renewal 14 days before expiry via Vault auto-rotate and reviewed secret management ownership for the integration path, assigning <PERSON> as the designated secret owner for the igw-prod-east-01 integration credentials.
6. Adjusted retry and backoff behavior on igw-prod-east-01 from linear (5s fixed interval, 10 retries) to exponential backoff (initial 2s, max 60s, 5 retries) so future transient downstream issues are less likely to surface as repeated gateway timeouts. Configuration change reviewed by <PERSON>.
