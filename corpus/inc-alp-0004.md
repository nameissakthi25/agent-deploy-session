# account locked after repeated failed sign-ins

**Service:** password-reset-portal
**Source incident:** INC-ALP-0004
**Priority:** high

## Symptom

I am unable to sign in to the SSO Portal (https://sso.corplabs.com) after multiple failed sign-in attempts across devices triggered an Active Directory account lockout on my account (username: <USER>). I completed a password reset in the Password Reset Portal, but the new credential did not become usable through SSO and the account remained locked. The issue affects a Sales I team member (<PERSON>, <EMP_ID>) based in the <LOCATION> office and is blocking normal account access across desktop (<HOSTNAME>) and mobile sign-in paths. Please contact me at <EMAIL> or <PHONE> if additional information is needed.

## Diagnosis

Diagnostics confirmed an AD lockout condition on account <USER> (<EMP_ID>) and successful submission of a password reset request via the Password Reset Portal, but the account remained unable to authenticate through the SSO Portal at https://sso.corplabs.com. The strongest evidence points to <PERSON>'s mobile device (iPhone) repeatedly sending stale cached credentials from a secondary IP, causing lockout recurrence and preventing clean propagation of the updated password to DC-EAST-03.corplabs.internal until the device cache, account lock state, and SSO synchronization are corrected together.

## Root cause

The Active Directory lockout policy was triggered by repeated authentication attempts from a mobile device using stale cached credentials. While the password reset request completed in the Password Reset Portal, the locked account state and delayed propagation of the new credential to the SSO path prevented successful sign-in until the lockout source was remediated and the account state was synchronized.

## Resolution

1. Unlock the user's Active Directory account (CN=<USER>,OU=Sales,DC=corplabs,DC=internal) on the authoritative domain controller DC-EAST-03.corplabs.internal and confirm the lockout state is cleared across all domain controllers via repadmin /syncall.
2. Have <PERSON> remove or update saved credentials on the affected mobile device (iPhone), including mail and collaboration applications that may still be submitting the old password, to eliminate the stale cached credential source.
3. Issue a fresh password reset for <USER> via the Password Reset Portal and confirm the new password is accepted by directory services on DC-EAST-03.corplabs.internal without generating additional lockout events (Event ID 4740).
4. Verify directory replication across domain controllers and SSO synchronization so the updated password and unlocked account state for <USER> are recognized by the SSO Portal at https://sso.corplabs.com.
5. Retest sign-in through the SSO Portal from both <HOSTNAME> (<IP>) and the mobile device after credential cleanup and confirm <PERSON> can authenticate successfully without the account re-locking.
