# Internal hostname fails to resolve — stale A record in internal DNS

**Service:** dns
**Source incident:** INC-DRF-0003
**Priority:** low

## Symptom

Multiple internal users and monitoring agents were trying to reach app.example.internal, but name resolution intermittently returned NXDOMAIN or the outdated IP address 10.20.5.47 from internal DNS. The issue was first reported by <PERSON> (emp ID <EMP_ID>) from the <LOCATION> office, who noticed the internal-app-service dashboard was unreachable by hostname. Additional reports came in from the <LOCATION> development team. The application could not connect to its backend by hostname, impacting internal app access across datacenter-1. Investigation focused on the internal BIND 9 zone data on dns-primary-01.dc1.internal and resolver cache behavior after a stale A record remained in the zone for a decommissioned address (10.20.5.47) instead of the current backend at 10.20.8.112.

## Diagnosis

Diagnostics confirmed the issue was not an application-side hostname parsing failure but an internal DNS data consistency problem on dns-primary-01.dc1.internal. Resolver testing from client <IP> (<HOSTNAME>, user <USER>) showed intermittent NXDOMAIN and stale answers pointing to decommissioned IP 10.20.5.47. Authoritative zone inspection of /etc/named/zones/db.example.internal identified an outdated A record, and cache validation confirmed stale resolver data persisted on both primary and secondary resolvers until the record was corrected and caches were flushed.

## Root cause

A stale A record for app.example.internal remained in the internal DNS zone and pointed to a decommissioned IP. Resolver and downstream cache entries then served outdated or failed responses, causing intermittent NXDOMAIN and incorrect address resolution.

## Resolution

1. Corrected the A record for app.example.internal in the internal DNS zone file /etc/named/zones/db.example.internal so it pointed to the active backend IP 10.20.8.112 instead of the decommissioned address 10.20.5.47.
2. Incremented the zone serial from 2025121801 to 2026010501 and reloaded named on the primary DNS server dns-primary-01.dc1.internal via `rndc reload example.internal` so the updated zone data was published correctly.
3. Reloaded or synchronized the change to secondary DNS server dns-secondary-02.dc1.internal to ensure consistent authoritative responses across internal resolvers. Verified zone transfer completed via `rndc zonestatus example.internal`.
4. Flushed cached DNS entries on the primary and downstream resolvers (dns-primary-01 and dns-secondary-02) using `rndc flush` to remove stale responses for 10.20.5.47 and force retrieval of the updated record.
5. Validated name resolution from affected client paths including <HOSTNAME> (<USER>, <IP>) and Network Monitoring dashboard checks, confirming that app.example.internal consistently resolved to the correct address 10.20.8.112.
6. Recommended adjusting the internal DNS TTL policy from 86400s to 3600s for application-tier hostnames to reduce the duration and impact of stale cached records in future changes. Flagged for review by the network team lead <PERSON>.
