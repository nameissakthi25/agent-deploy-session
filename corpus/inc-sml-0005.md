# blocked by repeated MFA prompt and SSO sign-in rejected

**Service:** sso
**Source incident:** INC-SML-0005
**Priority:** low

## Symptom

I was trying to sign in to the company SSO portal at https://sso.corplabs.com through Okta to reach multiple SaaS applications including Office365, Salesforce, and Concur from my workstation <HOSTNAME> at IP <IP>. Instead of completing sign-in, the browser repeatedly returned to the MFA challenge with a "Sign-in rejected" message, and I reported no matching approval activity in the Microsoft Authenticator app on my phone. My username is <USER> and I'm based out of the <LOCATION> office. Access to business applications was blocked through the web SSO flow, and Azure AD logs also showed intermittent AADSTS50020-related token rejection evidence for the External Contractors group (CN=<USER>,OU=External Contractors,DC=corplabs,DC=internal).

## Diagnosis

Diagnostics covered the reported MFA loop for user <USER> (<EMP_ID>), the user's Okta Verify push factor enrollment state, and possible Azure AD conditional access policy interaction for the External Contractors group. The strongest remediation evidence was that resetting the Okta MFA enrollment and clearing sessions from source IP <IP> / host <HOSTNAME> restored access to all three affected SaaS apps, indicating stale factor state was the direct cause of the active outage. Azure AD conditional access rejections (AADSTS50020) tied to the External Contractors group remained as secondary conflicting evidence and were escalated to the Identity team (<PERSON>) for policy review rather than treated as the confirmed primary root cause.

## Root cause

Stale Okta MFA factor enrollment caused the user's authentication session to loop, while separate Azure AD conditional access log entries for the External Contractors group indicated a policy mismatch that required follow-up review but did not prevent immediate restoration after factor reset and session cleanup.

## Resolution

1. Validated the reported symptom as an MFA loop in the Okta SSO flow for user <USER> (<EMP_ID>) connecting from <HOSTNAME> at <IP> in the <LOCATION> office, and confirmed the user was being returned to sign-in with rejected authentication behavior across Office365, Salesforce, and Concur.
2. Reset <USER>'s Okta MFA enrollment (Okta Verify push factor, originally enrolled 2025-08-14) and required re-enrollment of the active authenticator factor to remove the stale factor state that was causing the sign-in loop.
3. Cleared all active Okta sessions for <USER> and browser session state on <HOSTNAME>, then had the user retry from a fresh incognito browser session to avoid reuse of invalid cached tokens or stale session cookies.
4. Forced a new authentication attempt through the SSO portal at https://sso.corplabs.com and confirmed <USER> could complete sign-in with a single MFA challenge and regain access to Office365, Salesforce, and Concur. Rosa confirmed all three applications loaded successfully at 17:14 UTC.
5. Raised follow-up review to <PERSON> on the Identity team to inspect External Contractors group conditional access scope in Azure AD because AADSTS50020 token rejection events remained in logs for <USER> and needed policy reconciliation after service restoration. Tracking under follow-up task TASK-IDT-1192.
