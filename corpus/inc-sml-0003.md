# Users experience MFA prompt loop during SSO (Okta/Azure AD)

**Service:** sso
**Source incident:** INC-SML-0003
**Priority:** high

## Symptom

Multiple external contractor users were trying to sign in through the SSO Portal (https://sso.corplabs.com) to access Salesforce and Office365, but after completing Okta MFA they were returned to the MFA challenge again instead of reaching the application landing page. The issue was first reported by <PERSON> (<EMAIL>) and primarily affected users in the recently synced Azure AD contractor group 'CG-External-East'. Okta showed repeated MFA challenges with no successful session creation for accounts including <USER>, <USER>, and <USER>, and Azure AD sign-in activity indicated missing group claims in the token, blocking app access for an estimated 12 users in the <LOCATION> office after the recent group sync change on 2026-03-31.

## Diagnosis

Diagnosis confirmed an identity configuration issue rather than an end-user MFA failure. Reproduction with contractor account <USER> (IP <IP>) showed a true MFA prompt loop after Okta Verify approval, MFA enrollment checks found stale-session side effects for <USER> and <USER> only, and policy assignment review identified the primary fault: missing contractor group claims for 'CG-External-East' in Azure AD tokens due to incorrect conditional access group mapping after the 2026-03-31 sync. Updating the mapping and resyncing group membership via Azure AD Connect resolved the loop for all 12 affected <LOCATION>-based contractor accounts.

## Root cause

Azure AD conditional access policy and group mapping did not include the expected group claim for a recently synced contractor access group, causing affected users to be evaluated incorrectly during SSO and repeatedly challenged for MFA without establishing a valid session.

## Resolution

1. Reviewed Okta authentication logs and Azure AD sign-in records for affected contractor accounts (<USER>, <USER>, <USER>, and 9 others in the 'CG-External-East' group) to confirm repeated MFA challenges and missing group claims in issued SAML tokens. Logs were correlated using source IPs <IP> and <IP> from the <LOCATION> office network.
2. Corrected the Azure AD Conditional Access group mapping so the recently synced contractor access group 'CG-External-East' supplied the expected group claim during SSO evaluation, ensuring Okta could properly validate contractor group membership for application access policies.
3. Resynced Azure AD group membership to Okta via Azure AD Connect to refresh policy scope and ensure all 12 affected contractor users in the <LOCATION> office were associated with the proper access group and claim configuration.
4. Reset MFA enrollment and cleared stale session state for two impacted users — <USER> (<EMP_ID>) and <USER> (<EMP_ID>) — to remove invalid challenge loops created before the mapping correction. Both users re-enrolled via Okta Verify successfully.
5. Validated the fix with test user <USER> (<EMP_ID>) from <HOSTNAME> and then confirmed all 12 impacted contractor accounts, verifying successful SSO completion and restored access to Salesforce and Office365 without repeated MFA prompts. <PERSON> (<EMAIL>) confirmed resolution on behalf of the contractor team.
