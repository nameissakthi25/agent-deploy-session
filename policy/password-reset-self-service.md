# How to reset your corporate password

**Service:** password-reset-portal
**Type:** how-to
**Applies to:** all staff

## Before you start

You need access to at least one enrolled MFA factor. If you have lost every
factor, this article will not help — see *Recovering MFA when you have lost
your device*.

## Steps

1. Go to `https://passwordreset.corplabs.com` from any browser. You do not
   need to be on the VPN.
2. Enter your corporate username, not your email address.
3. Approve the Okta MFA prompt on your enrolled device.
4. Choose a new password. It must be at least 14 characters and must not
   reuse any of your previous 10 passwords.
5. Sign out and back in on **every** device that holds your corporate
   credentials, including mobile mail clients.

## Why step 5 matters

The most common ticket after a password reset is an account that locks itself
again within minutes. This is almost always a device still presenting the old
password — a phone mail client is the usual culprit. Active Directory counts
those failures and locks the account under policy.

If your account locks after a reset, clear the saved password on your mobile
device before asking the service desk to unlock it, or it will simply lock
again.

## If you are already locked out

The service desk must unlock the account in Active Directory before a reset
can complete. Raise a ticket and say explicitly that the account is locked.
