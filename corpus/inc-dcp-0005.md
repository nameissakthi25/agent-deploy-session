# Intune shows devices as NonCompliant causing Conditional Access blocks

**Service:** intune
**Source incident:** INC-DCP-0005
**Priority:** medium

## Symptom

Multiple corporate-managed Windows 10/11 laptops assigned to the <LOCATION> US-East Sales and Field Engineer population began showing as NonCompliant in Intune after a compliance policy push on the evening of 2025-12-25. As a result, Azure AD Conditional Access blocked affected users—including <PERSON> (<EMAIL>), <PERSON>, and others—from SharePoint Online, GlobalProtect VPN, and other corporate resources. The issue affected approximately 12 devices, appeared intermittent, and was tied to stale device check-ins and missing encryption status reporting following the updated compliance policy (CP-WIN-ENCRYPT-v3). Initial reports were filed by <PERSON> (<EMP_ID>) from her laptop <HOSTNAME> after repeated Conditional Access denials.

## Diagnosis

Investigation followed the device compliance playbook (CP-WIN-ENCRYPT-v3 scope) and showed the primary failure was stale Intune check-in/compliance evaluation after the 2025-12-25 policy push. Nine of twelve affected devices—including those belonging to <USER>, <USER>, and others in the <LOCATION> sales group—returned to Compliant after a forced sync from the admin console, confirming the management reporting delay. The remaining three noncompliant endpoints (<USER> / <HOSTNAME>, <USER>, <USER>) were narrowed to missing BitLocker encryption reporting, while policy scope review against the US-East Corporate Laptops device group did not indicate an assignment problem.

## Root cause

Devices had stale Intune check-in/compliance evaluation data after the policy push, and a subset of endpoints was not reporting the required BitLocker encryption compliance signal, causing Conditional Access to treat them as noncompliant.

## Resolution

1. Forced Intune device sync for all 12 affected endpoints from the admin console (initiated by <PERSON>, <EMP_ID>) to refresh management check-in and trigger a new compliance evaluation against the updated CP-WIN-ENCRYPT-v3 policy.
2. Reviewed the failing compliance state on the three remaining noncompliant devices (<HOSTNAME> / <USER>, <USER>, <USER>) and confirmed the missing signal was the BitLocker encryption status rather than a broad policy assignment failure.
3. Instructed affected users—<PERSON> (<EMAIL>, <PHONE>), <PERSON> (<EMAIL>), and <PERSON> (<EMAIL>)—to reboot their laptops, complete BitLocker enablement where required, and open Company Portal to allow the device to finish reporting updated compliance data to Intune.
4. Reran compliance evaluation for the three remaining devices after user-side BitLocker remediation and verified their status changed back to Compliant in Intune. <HOSTNAME> was the last to clear at 2025-12-26T15:42Z.
5. Monitored Conditional Access access restoration and confirmed previously blocked users—including <PERSON>, <PERSON>, <PERSON>, <PERSON>, and <PERSON>—could again reach SharePoint Online, GlobalProtect VPN, and other corporate resources once device compliance was updated.
6. Added temporary nightly automated check-ins via Intune remediation script and follow-up monitoring by <PERSON> to ensure all 12 impacted endpoints in the <LOCATION> region continued reporting current compliance status after the CP-WIN-ENCRYPT-v3 policy change.
