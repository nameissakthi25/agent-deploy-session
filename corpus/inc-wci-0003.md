# Multiple users cannot connect to Corporate Wi-Fi

**Service:** wifi
**Source incident:** INC-WCI-0003
**Priority:** medium

## Symptom

Multiple corporate users at the <LOCATION> office were trying to join the corp-employee SSID on managed devices, but after the overnight certificate rotation window (scheduled 2026-04-24T02:00Z) they either failed 802.1X authentication, disconnected immediately after associating, or connected without receiving network access. Users were blocked from normal wireless connectivity for corporate work because authentication to the Wireless Controller-backed RADIUS service (radius01.corp.eastnet.local) was failing. Initial reports came from <PERSON> (<EMP_ID>) and at least six other employees on the 3rd floor. Affected hostnames include <HOSTNAME> and <HOSTNAME> among others. The issue was escalated by the <LOCATION> site lead, <PERSON> (<EMAIL>).

## Diagnosis

Diagnostics confirmed a controller-side certificate failure on WLC-EAST-01 rather than an access point outage or isolated endpoint issue. NAC and controller logs showed 802.1X EAP rejections caused by the expired RADIUS certificate (CN=radius01.corp.eastnet.local, expired 2026-04-24T02:00Z), explaining the widespread authentication failures and missing network access symptoms across the <LOCATION> office. After certificate replacement, service restart, and session clearing, affected devices — including those belonging to <PERSON> (<USER>), <PERSON> (<USER>), and <PERSON> (<USER>) — were able to reauthenticate, with only a small subset of legacy clients needing profile refresh or re-enrollment.

## Root cause

The Wireless Controller's RADIUS server certificate expired at 2026-04-24T02:00Z, causing 802.1X EAP authentication failures and preventing many clients from completing wireless authentication and DHCP access on the corporate Wi-Fi network.

## Resolution

1. Reissued and installed a new valid RADIUS certificate (CN=radius01.corp.eastnet.local, valid through 2027-04-24) on the Cisco Wireless Controller WLC-EAST-01 for 802.1X authentication, coordinated by network engineer <PERSON> (<USER>).
2. Restarted the controller authentication services on WLC-EAST-01 so the renewed certificate was actively presented to wireless clients; verified certificate thumbprint matched the newly issued cert.
3. Cleared cached EAP and authentication sessions on the controller (47 stale sessions) to force affected devices to perform a fresh authentication exchange; confirmed <USER>, <USER>, and <USER> devices reconnected successfully within minutes.
4. Applied a temporary NAC exception (policy override group 'CERT-RENEWAL-TEMP') for impacted endpoints to restore access while clients refreshed trust and profile state; exception set to auto-expire 2026-04-25T06:00Z.
5. Instructed remaining affected users — including two legacy Windows 10 devices belonging to <PERSON> (<USER>, <EMP_ID>) — to forget and re-add the corp-employee SSID or re-enroll legacy device profiles via the self-service portal if they still held stale certificate trust information. Confirmed all users restored by end of business.
