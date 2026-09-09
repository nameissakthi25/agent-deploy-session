# account locked after repeated failed sign-ins

**Service:** password-reset-portal
**Source incident:** INC-ALP-0005
**Priority:** medium

## Symptom

I was trying to sign in to the SSO Portal and use the Password Reset Portal from an iOS mobile device (hostname <HOSTNAME>), but received an account locked message after several failed sign-in attempts. My username is <USER> and my employee ID is <EMP_ID>. A password reset was attempted on the phone from IP <IP>, but the reset link or token appeared to time out or fail to propagate, leaving me unable to regain access to my account. I need this resolved urgently so I can access my email and collaboration tools at the <LOCATION> office.

## Diagnosis

Diagnostics confirmed the account for <USER> (<EMP_ID>) was locked in AD after repeated failed sign-ins from mobile device <HOSTNAME> at IP <IP>. The prior password reset attempt likely failed because the token expired or was attempted while the account was locked and the device continued using stale cached credentials against https://sso.corplabs.com. The account was unlocked by agent <PERSON>, a new reset token was issued to <EMAIL>, and the user was instructed to clear saved mobile credentials before completing the reset.

## Root cause

Active Directory lockout policy was triggered by repeated failed authentication attempts from a mobile device that continued submitting cached or stale credentials during sign-in and password reset attempts.

## Resolution

1. Reviewed Active Directory lockout events on DC-EAST-03.corplabs.internal and confirmed repeated failed sign-in attempts from a mobile device (<HOSTNAME>, IP <IP>) were the source of the lockout for account <USER>.
2. Unlocked the user's Active Directory account (<USER>, <EMP_ID>) to restore eligibility for authentication and password reset; unlock performed by agent <PERSON>.
3. Issued a new password reset token to <EMAIL> and verified the user should complete the reset with the newly issued token rather than the previous expired or failed token.
4. Instructed the user to remove saved credentials and clear cached passwords on the mobile device <HOSTNAME> before retrying sign-in or password reset, particularly in Outlook and Teams apps.
5. Advised the user to complete the password reset through the Password Reset Portal after clearing cached credentials on <HOSTNAME>, then sign in again to the SSO Portal at https://sso.corplabs.com using the new password.
6. Monitored for additional failed sign-in events after the unlock and reset for account <USER> from IP <IP>; advised escalation to Identity Support if lockouts recur so the originating device or automated retry source can be identified.
