# Device marked noncompliant by Conditional Access despite Intune reporting compliant

**Service:** intune
**Source incident:** INC-DCP-0004
**Priority:** high

## Symptom

User <PERSON> (<EMP_ID>) on a Windows 10 21H2 managed laptop (hostname <HOSTNAME>) was blocked from accessing Microsoft 365 because Azure AD Conditional Access evaluated the device as noncompliant for missing encryption, while the Microsoft Intune portal continued to show the same device as Compliant. The issue intermittently prevented sign-in for a remote worker based in <LOCATION> and indicated conflicting compliance telemetry between Intune and Conditional Access during access evaluation. The user's client IP at the time of the blocked sign-in was <IP>.

## Diagnosis

Diagnostics confirmed a mismatch between Intune compliance reporting and Conditional Access evaluation for the encryption requirement on <PERSON>'s device <HOSTNAME> (<EMP_ID>). The device accepted sync and reevaluation actions from the Intune service, but Conditional Access initially continued to reference stale noncompliant encryption data cached from a prior evaluation cycle. No policy scope issue was indicated for the Remote Workers group in <LOCATION>, so the incident was resolved as an endpoint compliance telemetry refresh problem affecting the user's access from client IP <IP>.

## Root cause

Conditional Access consumed a stale or delayed encryption compliance signal for the device while Intune still showed the last successful compliant state, creating a mismatch between endpoint compliance telemetry and real-time access evaluation.

## Resolution

1. Forced an Intune device check-in on <HOSTNAME> and initiated a remote sync via the Intune admin center so the endpoint could submit a fresh compliance evaluation for user <USER> (<EMP_ID>).
2. Triggered re-evaluation of the encryption compliance state on <HOSTNAME> and had <PERSON> reboot the device to refresh local BitLocker protection status reporting to the Device Compliance Service.
3. Reviewed Conditional Access sign-in results for <EMAIL> after the new compliance sync to confirm the encryption attribute no longer evaluated as missing. Azure AD sign-in logs from client IP <IP> showed successful authentication post-sync.
4. Validated that <HOSTNAME> returned to an allowed sign-in state for Microsoft 365 after the refreshed compliance signal propagated. Rachel confirmed full access to Exchange Online, Teams, and SharePoint from her <LOCATION> location.
5. Advised follow-up OS updating from Windows 10 21H2 to a supported release and monitoring for recurrence because the condition was tied to delayed compliance telemetry rather than a confirmed encryption configuration failure. Ticket details shared with endpoint team lead <PERSON> (<USER>) for awareness.
