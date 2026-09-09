# Setting up the VPN on a new device

**Service:** vpn
**Type:** how-to
**Applies to:** staff with a corporate laptop

## What you need

- A corporate laptop enrolled in Intune and reporting compliant
- A valid device certificate issued by the Device Certificate Service
- An enrolled Okta MFA factor

The device certificate is the part people miss. GlobalProtect authenticates
you with Okta **and** validates the device certificate; if the certificate is
missing or expired the tunnel establishes and then drops within seconds.

## Steps

1. Open Software Center and install **GlobalProtect**. It is pre-approved.
2. Launch it. The portal address is pre-filled by the deployed profile — if it
   is blank, your device has not received the VPN profile and you should raise
   a ticket rather than typing an address in.
3. Sign in with your corporate username.
4. Approve the Okta MFA prompt.
5. Confirm you can reach an internal resource, for example the intranet.

## Choosing a gateway

The client picks the nearest gateway automatically. Do not pin a gateway
manually unless the service desk asks you to.

## If the tunnel drops immediately after MFA

This is the single most common VPN symptom and it is almost never Okta. Check
your device certificate first: open the local certificate store and confirm
the Device Certificate Service certificate has not expired. If it has, the
service desk can trigger re-enrolment.

Certificate expiry is monitored and alerts fire 14 and 7 days ahead, so this
should be rare — but a device that has been offline for a long period can miss
automatic renewal.
