# Software Center installation blocked by Endpoint Protection (reopened)

**Service:** software-center
**Source incident:** INC-SIB-0004
**Priority:** medium

## Symptom

I (<PERSON>, emp ID <EMP_ID>) on Windows 10 Enterprise 21H2 was trying to install FinanceApp v2.1 from Software Center on my workstation <HOSTNAME>, but the application was not visible on the device and installation attempts returned an endpoint policy block message (EP-403). The issue recurred after an earlier temporary fix applied on 2026-03-12, preventing the Finance team member from installing the required application through normal managed software deployment. My device IP is <IP> and I'm based out of the <LOCATION> office.

## Diagnosis

Diagnostics confirmed the FinanceApp v2.1 deployment entitlement for <USER> (EMP <EMP_ID>) on <HOSTNAME> was correct, but the endpoint had stale policy/inventory state (last sync 2026-03-10) and Endpoint Protection was actively blocking the updated installer signature (hash not in allowlist). After <PERSON> updated the allowlist entry and protection policy and <PERSON> forced the device sync from Intune, Software Center displayed the app on the <LOCATION> endpoint and installation succeeded.

## Root cause

Endpoint Protection was blocking the FinanceApp v2.1 installer because the updated installer signature/hash was not present in the approved allowlist, and the device had stale inventory/policy state so Software Center did not show the application correctly.

## Resolution

1. Verified the device <HOSTNAME> and user <USER> (<EMP_ID>) deployment targeting for FinanceApp v2.1 in Intune and confirmed the app assignment was intended for the affected <LOCATION> Finance endpoint.
2. Reviewed Endpoint Protection and application control behavior on <HOSTNAME> to confirm the installer was being blocked by policy (EP-403 / 0x87D00215) rather than a packaging or entitlement issue.
3. Added the FinanceApp v2.1 installer signature/hash to the Endpoint Protection allowlist and updated the applicable protection policy — performed by <PERSON> (<EMAIL>) on the security team.
4. Forced an Intune device inventory refresh and initiated a Software Center policy/application sync on <HOSTNAME> (IP <IP>) to update targeting and compliance state for user <USER>.
5. Retried the installation after policy refresh, confirmed FinanceApp v2.1 became visible in Software Center on <HOSTNAME>, and validated that installation completed successfully without the EP-403 policy block. <PERSON> confirmed the application launches correctly.
