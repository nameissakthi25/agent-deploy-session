# Outlook clients failing to sync with Exchange Online

**Service:** exchange-online
**Source incident:** INC-OES-0005
**Priority:** high

## Symptom

Multiple users in the Sales Division at the <LOCATION> office were trying to receive new email in Outlook for Windows and Outlook for iOS, but desktop clients showed "Disconnected" and mobile mailboxes stopped updating for several hours. The issue was first reported by <PERSON> (<EMAIL>) and subsequently confirmed by at least five other Sales team members. The issue began shortly after a morning Intune compliance policy rollout (Policy ID: CP-2026-0212) and affected Exchange Online synchronization, preventing normal email access on managed desktop and mobile devices. Affected users include employee IDs <EMP_ID> and <EMP_ID> among others.

## Diagnosis

Diagnostics ruled out a broader Exchange Online service issue and showed the primary failure pattern was device compliance enforcement after the Intune policy rollout (CP-2026-0212). Desktop Outlook on <HOSTNAME> (<USER>) and <HOSTNAME> (<USER>) presented as disconnected, while mobile mailbox access for <USER> and others was blocked by non-compliant device state. Local Outlook cache remediation was insufficient on both desktops, confirming the main cause was upstream policy/compliance impact rather than a tenant mail flow outage. MDM admin <USER> assisted with compliance policy review.

## Root cause

A recent Intune compliance policy change incorrectly marked affected managed devices as non-compliant. That compliance state caused Exchange Online mobile access to be blocked and contributed to Outlook client sync failures until policy targeting and device compliance were corrected.

## Resolution

1. Reviewed the morning Intune compliance policy rollout (CP-2026-0212) with MDM admin <PERSON> (<USER>). Identified the encryption requirement setting change that incorrectly flagged managed iOS and Windows devices as non-compliant, and updated the policy to restore the expected allowed criteria for the <LOCATION> Sales device scope.
2. Republished the corrected compliance policy (CP-2026-0212) to the affected device scope targeting the <LOCATION> Sales OU and confirmed impacted devices for <USER>, <USER>, <USER>, and others began returning to a compliant state after policy refresh within approximately 20 minutes.
3. Remediated devices that remained blocked by applying required compliance changes and re-enrolling affected mobile devices — including <HOSTNAME> (<USER>) — where policy state did not recover normally after the corrected policy push.
4. Cleared and re-established mobile sync partnerships for impacted mailboxes (<EMAIL>, <USER>@corplabs.com, <USER>@corplabs.com) so ActiveSync could resume after device compliance was restored. Verified last sync timestamps updated to current time for all three.
5. Rebuilt Outlook cached profiles on the two tested desktops — <HOSTNAME> (<USER>) and <HOSTNAME> (<USER>) — where cache clearing alone did not restore normal mailbox synchronization, then verified inbox updates and mail flow were working again for both users.
