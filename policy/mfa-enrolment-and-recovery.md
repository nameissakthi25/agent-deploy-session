# MFA enrolment, and recovering when you lose your device

**Service:** sso
**Type:** how-to
**Applies to:** all staff

## Enrolling

1. Go to `https://sso.corplabs.com` and sign in.
2. Choose **Set up multi-factor authentication**.
3. Enrol the Okta Verify app on your phone as your primary factor.
4. **Enrol a second factor.** A hardware key or a second device. This is
   strongly recommended and it is the difference between a two-minute
   self-service recovery and a two-day identity check.

## If you are stuck in a prompt loop

Repeated MFA prompts during sign-in usually mean the session token is not
being retained — commonly a browser blocking third-party cookies for the SSO
domain, or clock drift on the device large enough to invalidate the token.

Check the device clock is set automatically, then try a private window. If it
persists, raise a ticket and include which browser and which application you
were signing in to.

## If you have lost every factor

Recovery requires identity verification, which the service desk cannot skip.
Expect it to take a working day and to involve your manager confirming your
identity. This is not obstruction — self-service reset of every factor at once
would defeat the point of having them.
