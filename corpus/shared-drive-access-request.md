# Requesting access to a shared drive

**Service:** shared-drive
**Type:** policy
**Applies to:** all staff

## How access works

Shared drive permissions are granted through security groups, never to
individual accounts. This is deliberate: it keeps access auditable and lets
permissions follow role changes.

## Requesting access

Raise a request with:

- the exact share name, for example `FIN_SHARE`
- the access level you need — read, or read and write
- your business reason
- the name of the data owner, if you know it

## Approval

The **data owner** approves, not IT. IT only implements the decision. For
finance shares this is a named person in the finance team, and requests
without a business reason are routinely rejected.

Once approved, you are added to the relevant security group. **Sign out and
back in** — group membership is read at sign-in, so access will appear to be
missing until you do.

## Access denied when you believe you have access

Usually one of three things:

1. You have not signed out since being added to the group.
2. You are in a group that grants read-only, and you are attempting to write.
3. The share was migrated and the path you have cached no longer exists.

Include the exact error and the full path in your ticket.

## Leaving a team

Access is not removed automatically when you change role. Tell the data owner
so they can remove you — this is a genuine gap and it is on you to raise it.
