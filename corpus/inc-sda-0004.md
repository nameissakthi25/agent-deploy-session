# Access denied to Finance shared drive

**Service:** shared-drive
**Source incident:** INC-SDA-0004
**Priority:** medium

## Symptom

I was trying to open the Finance shared drive from my Windows 10 client (<HOSTNAME>, IP <IP>) using the mapped network path \\Shared\\Finance. Windows prompted for credentials and then returned "Access is denied," preventing access to Finance files. My username is <USER> and I reported membership in the FINANCE_USERS AD group, but access still failed, indicating a likely mismatch between group-based entitlement and the file server folder ACL. I need this resolved urgently as quarter-end reporting deadlines are approaching.

## Diagnosis

Diagnostics confirmed the user <USER> (employee ID <EMP_ID>) was correctly assigned to FINANCE_USERS, but the expected group was absent from the \\Shared\\Finance folder ACL on FS-EAST-02.corplabs.internal. This isolated the failure to file server permissions rather than user identity, stale path, or incorrect group membership. Credential re-entry alone did not restore access until the ACL was corrected and the drive was remapped on <HOSTNAME>.

## Root cause

NTFS permissions on \\Shared\\Finance were misconfigured: the FINANCE_USERS Active Directory group was not present on the folder ACL, likely due to broken or removed permission inheritance. The user's group membership was valid, but the file server ACL did not grant the expected access, which caused the credential prompt and access denied response.

## Resolution

1. Reviewed the Finance share NTFS permissions on FS-EAST-02.corplabs.internal and confirmed the FINANCE_USERS group was missing from the \\Shared\\Finance folder ACL despite valid AD membership for <USER> (employee ID <EMP_ID>).
2. Restored the intended permission inheritance or reapplied the approved Finance folder ACL so that FINANCE_USERS was included with the correct access rights (Read/Write). Change performed by file services admin <USER> in the <LOCATION> office.
3. Validated that share and NTFS permissions were aligned on FS-EAST-02.corplabs.internal and that no explicit deny entry or broken inheritance continued to block access for FINANCE_USERS members.
4. Cleared any cached Windows credentials and removed the stale mapped drive connection on the user's workstation <HOSTNAME> (IP <IP>), then remapped \\Shared\\Finance using net use commands executed by <USER>.
5. Retested access with the user <USER> after the ACL correction and confirmed the Finance shared drive opened successfully without prompting again for credentials. <PERSON> confirmed via email at <EMAIL> that all Finance files were accessible.
