# denied access to department shared drive

**Service:** shared-drive
**Source incident:** INC-SDA-0003
**Priority:** high

## Symptom

I (<USER>, employee ID <EMP_ID>) was trying to open the Marketing department shared folder from mapped drive Z: in Windows Explorer on my Windows 10 workstation <HOSTNAME>. The share was visible, but opening the folder returned "Access is denied" and repeatedly prompted for credentials, preventing access to department files needed for normal work. I'm based in the <LOCATION> office and need these files for an upcoming campaign deadline. Initial checks indicated the file server share and NTFS permissions were in place, suggesting a user-specific access entitlement problem rather than a server outage.

## Diagnosis

Diagnostics ruled out share ACL and path issues on FS-NYC-01 and isolated the failure to missing AD group membership for <USER>. The user could see the share from <HOSTNAME> but did not have the Dept_Share_Access entitlement required for the Marketing folder. After the group was added and the user refreshed their logon token, access was restored and validated by agent <USER>.

## Root cause

User account <USER> was not added to the required Active Directory security group Dept_Share_Access during provisioning, so the user's sign-in token did not contain the group-based permission needed for the Marketing shared folder.

## Resolution

1. Verified the Marketing shared folder access model on FS-NYC-01 and confirmed that AD group Dept_Share_Access is the required entitlement for the mapped drive and NTFS permissions on \\FS-NYC-01\DeptShares\Marketing.
2. Added user <USER> (<EMP_ID>) to the Active Directory security group Dept_Share_Access to restore the missing group-based access. Change approved by manager <PERSON> via email.
3. Forced a policy refresh (gpupdate /force) on workstation <HOSTNAME> and instructed <PERSON> to sign out and sign back in so the updated security token would include the new Dept_Share_Access group membership.
4. Retested access to mapped drive Z: (\\FS-NYC-01\DeptShares\Marketing) from <HOSTNAME> and confirmed <USER> could open the Marketing department folder without further credential prompts or access denied errors.
5. Documented the provisioning gap for <USER> and updated the onboarding checklist to include verification of required department shared-drive group membership. Notified HR contact <PERSON> in the <LOCATION> office to ensure future Marketing hires are flagged for Dept_Share_Access during account setup.
