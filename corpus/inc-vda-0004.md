# GlobalProtect disconnects shortly

**Service:** vpn
**Source incident:** INC-VDA-0004
**Priority:** low

## Symptom

I was trying to connect to the corporate GlobalProtect VPN from my managed Windows 10 laptop (<HOSTNAME>, IP <IP>) in the <LOCATION> office. After approving the Okta MFA push under my account <EMAIL>, the VPN tunnel connected briefly and then disconnected within about 30 seconds, which prevented access to internal applications including the intranet, finance portal, and email over VPN while working remotely. My employee ID is <EMP_ID> and my username is <USER>. I contacted the helpdesk at ext 4455 but was told to open a ticket.

## Diagnosis

Diagnostics confirmed that authentication through Okta MFA was succeeding for user <USER> (<EMP_ID>) on host <HOSTNAME>, but the VPN session failed during post-authentication certificate validation. Client logs from IP <IP> showed TLS handshake aborts and firewall logs on gw-emea-01.corplabs.internal explicitly identified an expired device certificate (serial 7A:3F:01:CC, expired 2026-03-28). Renewing the device certificate and refreshing the GlobalProtect profile resolved the disconnect.

## Root cause

Expired device certificate on the endpoint caused GlobalProtect post-authentication certificate validation to fail after successful Okta MFA approval, resulting in TLS handshake aborts and tunnel termination.

## Resolution

1. Verified in firewall and client logs on gw-emea-01.corplabs.internal and <HOSTNAME> (IP <IP>) that the VPN tunnel was dropping after successful MFA because device certificate validation returned a certificate expired failure for certificate serial 7A:3F:01:CC (expired 2026-03-28).
2. Renewed the endpoint device certificate through the Device Certificate Service for the affected laptop <HOSTNAME> assigned to <PERSON> (<USER>, <EMP_ID>), replacing expired serial 7A:3F:01:CC with new certificate valid through 2027-04-11.
3. Refreshed the GlobalProtect VPN profile on the endpoint <HOSTNAME> and re-enrolled the renewed device certificate so the active profile matched the current certificate for user <USER>.
4. Had the user <PERSON> reconnect to GlobalProtect from <HOSTNAME> and complete Okta MFA again via <EMAIL>, then confirmed the TLS handshake completed successfully and the tunnel remained established on gateway gw-emea-01.corplabs.internal.
5. Validated access to internal applications (intranet, finance portal, and email over VPN) from <HOSTNAME> at IP <IP> and monitored the connection for 30 minutes to confirm the disconnect did not recur.
