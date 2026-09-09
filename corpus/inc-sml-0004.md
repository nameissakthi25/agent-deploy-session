# Users stuck in MFA prompt loop

**Service:** sso
**Source incident:** INC-SML-0004
**Priority:** medium

## Symptom

Multiple remote employees in the <LOCATION> office were trying to sign in to corporate SaaS applications through the SSO Portal using Okta, but after completing authenticator-based MFA they were returned to repeated MFA prompts instead of reaching applications such as Salesforce, Confluence, and Workday. The issue was first reported by <PERSON> (<EMAIL>, <EMP_ID>) and subsequently confirmed by at least four other users. The loop blocked normal SaaS access in web-based SSO flows and was correlated with affected accounts showing token validation failures (401 invalid_token) during authentication against the Okta tenant.

## Diagnosis

Diagnosis reproduced the MFA loop for users <USER>, <USER>, <USER>, and <USER>, ruled out conditional access policy and application assignment mismatches in Azure AD and Okta, and linked the failure to stale Okta MFA enrollment records causing repeated challenge issuance and token validation failures (ERR_MFA_ENROLL_STALE). A targeted MFA reset on pilot user <USER> restored access to Salesforce and Confluence, confirming the root cause and resolution path for the remaining affected accounts.

## Root cause

Stale MFA enrollment metadata in Okta caused repeated MFA challenge issuance and token validation failures for affected user accounts, resulting in an MFA prompt loop after SSO login.

## Resolution

1. Identify impacted Okta user accounts (<USER>, <USER>, <USER>, <USER>, and any additional accounts) showing repeated MFA challenge events and token validation failures (ERR_MFA_ENROLL_STALE) during SSO authentication by querying the Okta system log for the period 2026-03-28 through 2026-04-01.
2. Reset MFA enrollment for affected users in the Okta admin console to remove the stale factor enrollment state tied to the failed authentication flow. Identity team analyst <PERSON> (<USER>) performed the bulk reset for all confirmed accounts.
3. Require users to complete fresh enrollment of their Okta Verify authenticator app or approved MFA factor before retrying SSO access. Users were directed to https://sso.corplabs.com/enroll to initiate re-enrollment.
4. Provide affected users with re-enrollment instructions via email (sent to <EMAIL>, <EMAIL>, <EMAIL>, <EMAIL>) and assisted support through a scheduled Teams call for users unable to complete the new MFA setup independently. Contact phone <PHONE> was provided for direct assistance.
5. Validate successful login to representative SaaS applications (Salesforce, Confluence, Workday) after re-enrollment for all four affected users and monitor Okta authentication success metrics for 24 hours to confirm the MFA prompt loop does not recur. Final confirmation received from <PERSON> at 2026-04-01T14:22:00Z.
