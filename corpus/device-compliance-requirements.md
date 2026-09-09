# Device compliance requirements

**Service:** intune
**Type:** policy
**Applies to:** every device that accesses corporate data

## What compliant means

A device is compliant when it satisfies all of:

- Disk encryption enabled, with the recovery key escrowed
- Operating system within the supported version range
- Endpoint protection installed and reporting
- A screen lock with a passcode
- Checked in to Intune within the last 14 days

Conditional Access blocks non-compliant devices from corporate resources. If
you are suddenly refused access to mail or the intranet, check your compliance
state before assuming an outage.

## Checking your own state

Open **Company Portal** and look at your device. It states whether the device
is compliant and, if not, which setting is failing.

## Most common failure: encryption

BitLocker is required and its recovery key must be escrowed. It commonly fails
to enable because the TPM has not been initialised, so no protector can be
created. Once the TPM is initialised the encryption completes and the key
escrows on the next check-in.

## Second most common: a stale check-in

A device that has been offline reports its last known state. Open Company
Portal and force a check-in before raising a ticket — this resolves a large
share of "marked non-compliant" reports on its own.

## Personal devices

Personal devices may access corporate **mail and calendar** only, and must
still meet the passcode and OS version requirements. Personal devices are
never granted access to shared drives or internal applications. See
*Acceptable use of personal devices*.
