# Access denied to Finance shared drive

**Service:** shared-drive
**Source incident:** INC-SDA-0007
**Priority:** medium

## Symptom

I was trying to open the Finance shared drive from the mapped network path \\FS-FIN-01.corplabs.internal\Finance$ after a recent group membership update. Windows prompted for credentials and then returned Access Denied (0x80070005), preventing me from listing or opening the Finance department folder needed for normal work. My username is <USER> and my workstation is <HOSTNAME>. Directory checks showed I was already in the Finance_SharedDrive AD group (CN=<USER>,OU=Finance Users,DC=corplabs,DC=internal), but access to the file server path still failed. I need this resolved urgently as quarter-end reporting is due this week. My employee ID is <EMP_ID> and I can be reached at <EMAIL> or ext <PHONE>.

## Diagnosis

Diagnostics confirmed that <USER>'s AD entitlement in Finance_SharedDrive was correct and replication had completed across all domain controllers, but FS-FIN-01.corplabs.internal continued logging Access Denied events (0x80070005) for SID lookups against <USER> from client IP <IP>. Token refresh and drive remap on <HOSTNAME> did not restore access. The decisive finding was a conflicting NTFS configuration on the \\FS-FIN-01.corplabs.internal\Finance$\Department_Reports folder: an explicit deny ACE targeting the Finance_SharedDrive group and broken inheritance were overriding group-based allow access. After correcting the folder ACLs and reapplying intended inheritance, <USER> regained full read/write access to the Finance share.

## Root cause

Access was blocked by NTFS permissions on the Finance department folder, where an explicit deny ACE and broken inheritance overrode the allow permissions granted through the Finance_SharedDrive AD group. The issue was not caused by missing group membership; it was caused by conflicting folder ACL configuration on the file server.

## Resolution

1. Confirmed <USER>'s membership in the Finance_SharedDrive AD security group (CN=<USER>,OU=Finance Users,DC=corplabs,DC=internal) and verified replication had completed across all domain controllers so directory entitlement was current.
2. Reviewed the Finance folder ACLs on FS-FIN-01.corplabs.internal, specifically \Finance$\Department_Reports, identified an explicit deny ACE and inheritance inconsistency affecting the target path, and removed the deny condition from the folder permissions.
3. Restored the intended permission inheritance on the Department_Reports folder and reapplied the correct allow access (Read/Write) for the Finance_SharedDrive group, ensuring all subfolders inherited the corrected permissions.
4. Cleared <USER>'s cached network credentials on <HOSTNAME> using 'cmdkey /delete:FS-FIN-01.corplabs.internal' and had the F: drive remapped so the client reconnected with a fresh access token.
5. Retested access from <HOSTNAME> (IP <IP>) to the current Finance shared drive path \\FS-FIN-01.corplabs.internal\Finance$\Department_Reports and confirmed <USER> could open and list the folder without receiving Access Denied events. <PERSON> confirmed normal access was restored.
