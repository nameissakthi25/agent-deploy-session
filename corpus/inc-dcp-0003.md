# Devices marked noncompliant after stale policy reference

**Service:** intune
**Source incident:** INC-DCP-0003
**Priority:** low

## Symptom

Multiple Intune-managed Windows 10 and Android 11 devices used by the Sales group in the <LOCATION> office were marked noncompliant after a recent compliance policy consolidation initiated by admin <PERSON> (<EMAIL>). Conditional Access then blocked sign-in because the devices continued evaluating against retired policy CorpCompliance_v2 and reported a missing encryption signal. Affected users, including <PERSON> (<EMP_ID>) and <PERSON> (<EMP_ID>), could not access protected resources such as SharePoint and Teams until the current compliance policy was reassigned and devices completed a fresh check-in and compliance re-evaluation.

## Diagnosis

Diagnostics confirmed this was not a device-only encryption failure but a policy scoping issue compounded by stale check-in state. Impacted Sales devices in the <LOCATION> office — including those belonging to <USER>, <USER>, and <USER> — remained assigned to retired compliance policy CorpCompliance_v2, which no longer carried the current encryption evaluation, so Conditional Access continued treating them as noncompliant until the assignment was corrected and devices re-synced with the Intune Device Compliance Service.

## Root cause

Deprecated compliance policy CorpCompliance_v2 remained assigned through stale Intune group mappings after policy consolidation. Affected devices continued evaluating against the retired policy, which did not report the current encryption requirement, and older device check-in state delayed receipt of the corrected CorpCompliance_v3 assignment and updated compliance evaluation.

## Resolution

1. Removed the stale Intune assignment referencing CorpCompliance_v2 from the SG-Sales-<LOCATION> group mappings and republished the intended compliance scope with CorpCompliance_v3, verified by admin <PERSON> (<EMAIL>) in the Endpoint Manager console.
2. Forced remote device check-in on all 14 impacted endpoints — including <HOSTNAME> (<USER>, IP <IP>), <HOSTNAME> (<USER>), and <USER>'s Android device — so they would download the corrected policy assignment and trigger a fresh compliance evaluation cycle.
3. Pushed the required encryption configuration (BitLocker for Windows 10 devices, device encryption for Android 11 devices) to endpoints that were specifically failing the encryption compliance signal, including <PERSON>'s Surface and <PERSON>'s Pixel device.
4. Reviewed post-sync compliance reports in Endpoint Manager and confirmed all 14 devices were evaluating only against CorpCompliance_v3 with the expected encryption signal present. <PERSON> (<EMP_ID>) and <PERSON> (<EMP_ID>) both confirmed restored access to protected resources.
5. Directed the remaining 2 outlier devices through manual Company Portal sync or re-enrollment where prior stale enrollment state prevented automatic remediation — one belonged to <PERSON> (<USER>) — then verified Conditional Access no longer blocked compliant devices by confirming successful sign-in from each affected user account.
