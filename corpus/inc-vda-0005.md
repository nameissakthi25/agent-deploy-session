# VPN disconnects immediately

**Service:** vpn
**Source incident:** INC-VDA-0005
**Priority:** high

## Symptom

I was trying to connect to the corporate GlobalProtect VPN from my managed Windows 10 laptop (<HOSTNAME>) at the <LOCATION> office. My username is <USER> and after approving the Okta MFA push notification, the VPN session established briefly but disconnected within about 30 seconds, leaving internal applications such as the HR Portal, Jira, and Confluence completely unreachable. My client IP at the time was <IP>. The issue recurred after a prior closure under INC-VDA-0004, impacting my ability to work remotely. I reached out to my manager <PERSON> (<EMAIL>) who confirmed no one else on the team was affected.

## Diagnosis

Diagnostics confirmed that Okta MFA for user <USER> (<EMP_ID>) was successful, but the VPN session on <HOSTNAME> failed immediately afterward during post-authentication validation against the gateway. Endpoint review by <PERSON> found an expired device certificate (expired 2026-03-28) and a stale GlobalProtect profile last updated 2025-11-14, matching the observed pattern of short-lived connection followed by IKEv2 tunnel teardown at 25–40 seconds. Re-enrollment and profile refresh temporarily restored service from client IP <IP>, supporting certificate/profile state as the primary cause.

## Root cause

Expired device certificate on the Windows 10 endpoint, combined with a stale GlobalProtect profile, caused conditional access evaluation to fail after Okta MFA succeeded, resulting in VPN tunnel teardown within 25-40 seconds.

## Resolution

1. Renew the endpoint device certificate for <HOSTNAME> through the Device Certificate Service, issuing a new certificate to CN=<USER>,OU=Corp Users,DC=corplabs,DC=internal, and confirm the new certificate is installed and valid on the affected laptop (verified new expiry: 2027-04-12).
2. Remove the stale GlobalProtect VPN profile (last refreshed 2025-11-14) from <HOSTNAME> and refresh the client configuration with the current assigned profile for the Engineering - Remote user group.
3. Force device re-enrollment of <HOSTNAME> so the endpoint posture and certificate state are re-registered with the Device Certificate Service before reconnecting to VPN; confirmed enrollment status updated at 2026-04-12T02:35:00Z.
4. Verify <USER>'s Conditional Access and VPN access group membership (Engineering - Remote, <LOCATION> region) aligns with the expected policy requirements and correct any mismatch; confirmed group assignment is consistent with policy.
5. Reconnect <HOSTNAME> with GlobalProtect after Okta MFA approval by <USER> and monitor session stability for at least 30 minutes to confirm the tunnel no longer tears down; session remained stable for 45 minutes with no IKEv2 teardown events observed.
