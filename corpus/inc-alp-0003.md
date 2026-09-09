# account locked after failed sign-ins

**Service:** password-reset-portal
**Source incident:** INC-ALP-0003
**Priority:** low

## Symptom

I (<PERSON>, emp ID <EMP_ID>) was trying to sign in to corporate SSO and internal applications from my iPhone (<HOSTNAME>) after changing my password in the Password Reset Portal. Although the portal at https://passwordreset.corplabs.com showed the reset succeeded, the mobile device continued submitting stale cached credentials from IP <IP>, causing repeated authentication failures and an AD account lockout on my account (<USER>). I was blocked from accessing email (OWA) and other internal apps from mobile until the account was unlocked and the device credential cache was cleared. I'm based out of the <LOCATION> office in the Sales group.

## Diagnosis

Diagnostics confirmed the lockout source was <PERSON>'s iOS device (<HOSTNAME>, IP <IP>), which continued using stale cached credentials for account <USER> after a password reset token had expired before propagation. AD lockout logs on DC-EAST-03.corplabs.internal showed six failed attempts within a 4-minute window. Reissuing the reset token, unlocking the AD account, and clearing stored mobile credentials resolved the issue and prevented further failed sign-in attempts.

## Root cause

Active Directory lockout policy was triggered by repeated failed sign-in attempts from the user's iOS mobile device, which continued using cached pre-reset credentials after the prior password reset token expired before the device updated its stored authentication data.

## Resolution

1. Reviewed the account status for <USER> in Active Directory on DC-EAST-03.corplabs.internal and confirmed the user account (<PERSON>, <EMP_ID>) was locked due to six repeated failed authentication attempts from mobile device <HOSTNAME> at IP <IP>.
2. Unlocked the <USER> AD account via Active Directory Users and Computers to stop the immediate access block and allow a fresh authentication attempt for Marcus.
3. Issued a new password reset token for <USER> and confirmed Marcus successfully completed the password reset through the Password Reset Portal at https://passwordreset.corplabs.com; propagation to DC-EAST-03.corplabs.internal verified.
4. Had Marcus fully sign out of mobile SSO on <HOSTNAME>, remove the stored work account (<EMAIL>) and cached credentials from the device's mail and authenticator apps, and then re-add the account with the new password.
5. Verified successful sign-in to https://sso.corplabs.com and internal applications (OWA, internal portals) for <USER> after the mobile credential cache was cleared on <HOSTNAME> and the account was reauthenticated. No further lockout events observed.
