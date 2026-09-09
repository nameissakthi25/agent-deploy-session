# Finance users unable to join Corporate Wi-Fi — certificate authentication failures (escalated)

**Service:** wifi
**Source incident:** INC-WCI-0004
**Priority:** low

## Symptom

Multiple Finance users on Windows 10 laptops in the <LOCATION> office were unable to join the Corporate Wi-Fi starting around 07:30 on April 25. The issue was first reported by <PERSON> (<EMP_ID>) and subsequently confirmed by at least four other Finance team members including <PERSON>. Devices failed 802.1X/EAP-TLS authentication and showed certificate expired or certificate validation errors in client and controller logs. Users could not obtain normal network access for business work — affected machines such as <HOSTNAME> and <HOSTNAME> were stuck on limited connectivity. Profile re-adds and device reboots did not restore connectivity.

## Diagnosis

Diagnostics ruled out endpoint profile corruption as the primary issue because profile recreation and reboot on devices like <HOSTNAME> (IP <IP>) did not help. Controller evidence from WLC-PHILA-01 confirmed the corporate wireless certificate (corp-wlan-cert) had expired on 2026-04-24, and NAC review indicated authentication was failing during certificate validation before policy assignment for Finance users including <USER> and <USER>. The incident was resolved by renewing the controller certificate, updating NAC trust, and validating successful post-change EAP-TLS authentication for all affected users in the <LOCATION> office.

## Root cause

The corporate wireless authentication certificate on the Wireless Controller expired, causing EAP-TLS validation failures between endpoints, the controller, and NAC trust policy for the Corporate Wi-Fi SSID.

## Resolution

1. Renew the expired corp-wlan-cert on the Wireless Controller (WLC-PHILA-01) with the correct server certificate and verified intermediate CA chain, ensuring the new certificate validity extends through April 2027.
2. Update Network Access Control trust settings and policy bindings on the NAC authentication service so the renewed wireless certificate is accepted for Corporate Wi-Fi 802.1X authentication across the <LOCATION> office infrastructure.
3. Validate successful EAP-TLS handshakes on WLC-PHILA-01 and NAC by confirming new authentication attempts from test users <USER> and <USER> no longer fail with certificate expired or certificate validation errors.
4. Have affected users (<PERSON>, <PERSON>, <PERSON>, <PERSON>, and others) forget and reconnect to the Corporate Wi-Fi SSID so devices establish a fresh trust path and complete authentication with the renewed certificate.
5. Monitor Finance user authentication attempts in the <LOCATION> office after rollout to confirm normal access policy assignment and no recurring certificate-related failures; <PERSON> (<EMP_ID>) to review NAC logs at 24-hour and 72-hour checkpoints.
