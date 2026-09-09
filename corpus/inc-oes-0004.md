# Outlook mobile not syncing

**Service:** exchange-online
**Source incident:** INC-OES-0004
**Priority:** low

## Symptom

I was trying to access current email from Outlook for iOS on my iPhone (<HOSTNAME>) after a recent iOS 17.3 update, but the mobile inbox stopped receiving new messages and remained stale with older mail. My account is <EMAIL> and I'm based out of the <LOCATION> office. Desktop Outlook on my workstation (<HOSTNAME>) connected to Exchange Online continued to send and receive normally, indicating the issue was isolated to the mobile client/device path. Restarting the Outlook app and rebooting the phone did not restore sync, and no explicit error code was shown. My employee ID is <EMP_ID> for reference.

## Diagnosis

Diagnostics indicate the mailbox for <EMAIL> was healthy because desktop Outlook on <HOSTNAME> continued syncing while only Outlook for iOS on <HOSTNAME> (IP <IP>) remained stale after the iOS 17.3 update. Restarting the app and device did not help, making a transient client hang less likely. The strongest probable cause is a stale Outlook mobile profile or invalid mobile sync partnership on the device, with Intune compliance for <PERSON>'s managed iPhone also needing verification because post-update compliance drift can block Outlook mobile access without a clear in-app error.

## Root cause

Outlook for iOS mobile sync was most likely blocked by a stale mobile Outlook profile or invalid mobile sync partnership after the iOS update; desktop Outlook remained healthy, which narrows the failure to the device-side mobile client or mobile compliance/partnership state rather than a mailbox-wide Exchange Online outage.

## Resolution

1. Validated that the impact was isolated to Outlook for iOS on <HOSTNAME> because desktop Outlook on <HOSTNAME> continued syncing the same Exchange Online mailbox (<EMAIL>) normally.
2. Reviewed the mobile mailbox sync path for <EMAIL> and treated the issue as a stale mobile profile or disrupted device partnership on <HOSTNAME> following the iOS 17.3 update rather than a general Exchange Online service failure.
3. Removed and rebuilt the Outlook mobile account/profile for <EMAIL> on the affected iPhone (<HOSTNAME>) to refresh local sync state and authentication data.
4. If the stale sync state persisted, cleared the existing mobile sync partnership for <HOSTNAME> in Exchange Online via the Exchange admin center and forced the phone to establish a new mobile partnership on the next sign-in.
5. Confirmed with MDM admin <PERSON> that the managed device <HOSTNAME> remained compliant in Microsoft Intune so Outlook mobile access for <PERSON> was not blocked by conditional access after the OS update.
6. After profile rebuild and partnership refresh, instructed <PERSON> to verify that new inbox items and folder updates resume on the iPhone and to contact the service desk at ext. 4200 if sync issues recur.
