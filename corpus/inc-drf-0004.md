# Internal hostname svc-db.internal fails DNS resolution

**Service:** dns
**Source incident:** INC-DRF-0004
**Priority:** high

## Symptom

Internal application teams were trying to reach the database service by the internal hostname svc-db.internal, but several application pods intermittently failed name resolution and could not connect to the DB. The issue was first reported by <PERSON> (<EMAIL>) from the platform engineering group in <LOCATION>. Failures were concentrated on queries served by dns-resolver-01.corp.internal, where monitoring showed repeated NXDOMAIN responses from client hosts including <HOSTNAME> (<IP>). Review of the internal DNS zone found an outdated A record pointing to decommissioned IP 10.20.5.14 instead of the current 10.20.9.42, along with a deprecated zone management policy reference (internal-dns-policy-v1), creating impact for internal-order-service, payment-processor, and reporting-worker in corp-datacenter-1.

## Diagnosis

Diagnostics tied the outage to the DNS layer rather than the database service itself. Resolver-specific testing from affected host <HOSTNAME> (<IP>) showed intermittent NXDOMAIN responses from dns-resolver-01.corp.internal, while dns-resolver-02.corp.internal resolved correctly to 10.20.9.42. Zone inspection found a stale A record for svc-db.internal pointing to decommissioned IP 10.20.5.14 (last updated 2025-06-12), and configuration review identified a deprecated internal-dns-policy-v1 reference in zone management that allowed the outdated record to persist. After correcting the A record to 10.20.9.42, updating the policy reference to internal-dns-policy-v2, and flushing resolver caches on dns-resolver-01 through dns-resolver-03, hostname resolution was restored and validated from affected application hosts by network engineer <PERSON>.

## Root cause

Intermittent NXDOMAIN responses were caused by a stale A record for svc-db.internal in the internal DNS zone and a deprecated internal DNS management policy reference that allowed outdated zone data to persist on dns-resolver-01 and dependent resolvers.

## Resolution

1. Verified that svc-db.internal had an outdated A record (10.20.5.14, last modified 2025-06-12) in the internal DNS zone and confirmed the currently required target IP 10.20.9.42 with database infrastructure owner <PERSON> (<USER>) before making changes.
2. Updated the A record for svc-db.internal in the internal DNS zone to the correct current IP 10.20.9.42 and reviewed the zone entry metadata and TTL (set to 300s from previous 86400s) under change record CHG-88214.
3. Replaced the deprecated internal-dns-policy-v1 reference with internal-dns-policy-v2 in the zone management configuration to prevent continued publication of stale record state and ensure automatic zone synchronization across all resolvers.
4. Flushed cache on dns-resolver-01.corp.internal using `rndc flush` and cleared/propagated cache refresh on dependent resolvers dns-resolver-02 and dns-resolver-03 so fresh zone data would be served immediately across the <LOCATION> datacenter.
5. Validated successful hostname resolution from affected application hosts (<HOSTNAME> at <IP>, app-node-03, app-node-07) and confirmed Network Monitoring no longer observed NXDOMAIN responses for svc-db.internal. <PERSON> confirmed internal-order-service, payment-processor, and reporting-worker health checks all passing.
