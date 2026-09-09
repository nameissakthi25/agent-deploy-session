# GlobalProtect VPN disconnects immediately

**Service:** vpn
**Source incident:** INC-VDA-0003
**Priority:** medium

## Symptom

Remote users on managed Windows 10 laptops were trying to connect to the corporate network through GlobalProtect VPN from multiple offices. After approving the Okta MFA prompt, the VPN tunnel established briefly and then disconnected within seconds, leaving internal applications such as the intranet, internal Salesforce, and Confluence unreachable. The issue was first reported by <PERSON> (emp ID <EMP_ID>) at the <LOCATION> office around 08:15 local time, and subsequently confirmed by additional users in the <LOCATION> and <LOCATION> regions. The problem blocked normal remote access to internal resources for the remote_workers group throughout the morning.

## Diagnosis

Diagnostics confirmed that Okta MFA was succeeding normally for all affected users including <USER> and <USER>, and that the disconnect occurred after authentication, not during Okta challenge processing. GlobalProtect client logs from <HOSTNAME> (IP <IP>) and <HOSTNAME> consistently showed certificate validation failures tied to expired device certificates issued by the Device Certificate Service, which caused post-authentication tunnel establishment to abort. Re-enrollment and certificate renewal on a test endpoint (<HOSTNAME>) by desktop support analyst <PERSON> restored stable VPN connectivity, confirming the root cause.

## Root cause

Expired device certificates on affected endpoints caused GlobalProtect certificate validation to fail immediately after successful Okta MFA, which terminated the VPN tunnel during post-authentication connection setup.

## Resolution

1. Validated that affected endpoints including <HOSTNAME> (<USER>) and <HOSTNAME> (<USER>) had expired device certificates in the local certificate store (expiry date 2026-04-09) and confirmed the failures aligned with the VPN disconnect timing observed in GlobalProtect gateway logs.
2. Renewed device certificates for affected devices through the Device Certificate Service and re-enrolled endpoints where automatic renewal had not completed successfully. Desktop support analyst <PERSON> (<EMAIL>) coordinated re-enrollment for 14 affected machines across <LOCATION>, <LOCATION>, and <LOCATION> offices.
3. Pushed an updated GlobalProtect VPN profile to enrolled endpoints via the management console to ensure the current certificate and profile association were used for tunnel establishment. Profile version 4.2.7-r3 was deployed to all affected devices.
4. Cleared stale VPN profile data on impacted test devices (<HOSTNAME>, <HOSTNAME>), reconnected GlobalProtect, and verified the tunnel remained established after Okta MFA approval for both <USER> and <USER>.
5. Confirmed restored access to internal applications (Intranet, Salesforce, Confluence) after reconnection for all reported users and added device certificate expiry monitoring and alerting in the Device Certificate Service dashboard to reduce the risk of recurrence. <PERSON> set threshold alerts at 14 and 7 days before expiry.
