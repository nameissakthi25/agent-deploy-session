# Intermittent DNS resolution failure for internal service

**Service:** dns
**Source incident:** INC-DRF-0007
**Priority:** high

## Symptom

Developers on the platform engineering team (reported by <PERSON>, emp ID <EMP_ID>) were trying to reach service.internal.corp for internal-service-api and the developer portal from the <LOCATION> and <LOCATION> office locations, but name resolution from internal resolver 10.1.1.10 intermittently returned NXDOMAIN or timed out. Direct queries to the authoritative DNS server dns-auth-01.internal.corp returned the expected A record (10.40.16.55), so users were blocked by inconsistent internal DNS responses rather than a missing service record. Impact was cross-site and intermittent, affecting access to internal endpoints and application connectivity. Initial report came in via Slack from <EMAIL>.

## Diagnosis

Diagnostics established that the internal zone record for service.internal.corp (A → 10.40.16.55) existed and authoritative DNS on dns-auth-01.internal.corp was healthy. The failure pattern was isolated to resolver 10.1.1.10, which intermittently returned NXDOMAIN or timed out for a hostname that authoritative servers resolved correctly. Approximately 30% of recursive queries failed. Cache flush by itself did not fully remediate the issue, supporting a resolver forwarding/configuration problem — specifically a stale secondary forwarder target (10.1.1.22, decommissioned) combined with stale negative cache behavior. After correcting the resolver conditional forwarder path for the internal zone and clearing cached data, lookups from affected clients (including <HOSTNAME> at <IP> and <HOSTNAME>) became consistent across both <LOCATION> and <LOCATION> sites.

## Root cause

Resolver 10.1.1.10 had an internal DNS forwarding/cache issue for the internal zone: the authoritative server held the correct A record for service.internal.corp, but the resolver intermittently served NXDOMAIN or timed-out responses until conditional forwarder behavior and cached zone data were corrected.

## Resolution

1. Validated that the authoritative DNS server dns-auth-01.internal.corp (10.1.1.30) for the internal zone returned the expected A record for service.internal.corp (10.40.16.55, TTL 300) and confirmed the issue was isolated to recursive resolver 10.1.1.10 behavior rather than a missing zone record. Verification performed by <PERSON> from the <LOCATION> network monitoring host.
2. Reviewed and corrected the conditional forwarder path for the internal zone on resolver 10.1.1.10 — removed stale secondary forwarder target 10.1.1.22 (decommissioned) so queries for service.internal.corp consistently routed only to the valid authoritative DNS server dns-auth-01.internal.corp (10.1.1.30).
3. Cleared stale cached entries and negative cache data (rndc flush) on the affected internal resolver 10.1.1.10 after the forwarder configuration was corrected, ensuring no residual NXDOMAIN responses persisted from the decommissioned target.
4. Retested repeated lookups for service.internal.corp from the affected resolver and from multiple client locations — including <PERSON>'s workstation <HOSTNAME> (<IP>, <LOCATION>) and <PERSON>'s machine <HOSTNAME> (<LOCATION>) — to confirm the resolver now returned 10.40.16.55 consistently without NXDOMAIN or timeout responses. 100/100 queries succeeded.
5. Monitored resolver and DNS query behavior via Network Monitoring dashboards for 2 hours after the change to verify timeout spikes stopped and internal applications (internal-service-api, developer-portal) could consistently resolve the service endpoint. Confirmed with <PERSON> (<EMAIL>) that CI/CD pipeline and portal access were fully restored.
