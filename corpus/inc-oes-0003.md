# Outlook/ActiveSync: Mobile and desktop email not syncing (device compliance block)

**Service:** exchange-online
**Source incident:** INC-OES-0003
**Priority:** medium

## Symptom

I was trying to access and sync email in Outlook on my Windows 10 laptop (<HOSTNAME>) and Outlook on my iPhone, but mailbox updates for <EMAIL> stopped approximately 48 hours earlier. Outlook desktop showed a disconnected state and the mobile client reported sync failed with a server response. The issue affected Microsoft Exchange Online mail delivery and send/receive behavior on both desktop and mobile, preventing me from receiving current messages while traveling out of the <LOCATION> office and working across managed devices. My employee ID is <EMP_ID> if that helps look things up.

## Diagnosis

Diagnostics showed the issue was not limited to a single Outlook client because both desktop (<HOSTNAME>, IP <IP>) and iOS (<HOSTNAME>) sync failed at the same time for mailbox <EMAIL>. Outlook desktop was disconnected, while Exchange Online logs showed 403 blocked responses for the mobile device. Review of the mailbox's mobile partnership and Intune compliance state for employee <EMP_ID> confirmed a device compliance failure was enforcing a conditional access block. After restoring compliance and resetting the ActiveSync partnership, synchronization resumed normally on both platforms.

## Root cause

Exchange Online mobile access was blocked because the user's managed iOS device fell out of Intune compliance, causing ActiveSync/API requests to be denied and leaving Outlook clients unable to maintain normal mailbox synchronization.

## Resolution

1. Reviewed Intune compliance status for the affected iOS device (<HOSTNAME>, user <USER>, EMP <EMP_ID>) and identified that the device was failing the required OS patch compliance policy (minimum iOS 15.4.1 not met).
2. Remediated the device compliance issue by coordinating with <PERSON> (<PHONE>) to update the required OS patch level on the iPhone, then reapplied the Intune compliance profile until the device returned to a compliant state as verified by agent <PERSON>.
3. Cleared the affected device's (<HOSTNAME>) ActiveSync partnership in Exchange Online via Remove-MobileDevice cmdlet to remove the blocked mobile sync relationship for mailbox <EMAIL>.
4. Forced a fresh device/mailbox synchronization after compliance returned to healthy so Exchange Online could establish a new allowed ActiveSync partnership for <HOSTNAME> against the <EMAIL> mailbox.
5. Had Marcus restart Outlook on <HOSTNAME> and re-initiate mobile sync on the iPhone, then verified successful send/receive and current mailbox updates on both iOS and Outlook desktop. Confirmed no further 403 blocks in Exchange Online logs.
