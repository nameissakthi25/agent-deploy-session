# Software Center install blocked by Endpoint Protection policy

**Service:** software-center
**Source incident:** INC-SIB-0005
**Priority:** low

## Symptom

I attempted to install the EditorX company application from Software Center on my managed Windows 10 21H2 device (<HOSTNAME>, IP <IP>), but the install failed immediately with "Installer fails policy check" and error 0x80070005. The application was visible in Software Center under my account (<USER>, employee ID <EMP_ID>), but Endpoint Protection blocked execution of the installer, preventing me from completing the requested software installation. I need this application for a project deadline and would appreciate a quick resolution. My manager <PERSON> (<EMAIL>) can confirm the business need if required.

## Diagnosis

Diagnostics confirmed the Software Center deployment for EditorX was present and correctly targeted to user <USER> (<EMP_ID>) on device <HOSTNAME>, ruling out a missing entitlement issue. The primary fault was an Endpoint Protection block (POLICY_BLOCK_403) triggered by a publisher/signature mismatch on the EditorX installer (EditorX_Setup_v4.2.1.exe). A stale Intune inventory state (last sync 2026-03-16) was also identified on the device at IP <IP> and refreshed so the updated allow policy could be applied and validated.

## Root cause

Endpoint Protection policy blocked the EditorX installer because the package was flagged by the protection blocklist due to a publisher/signature policy mismatch; the device also had a stale Intune inventory timestamp, which required a policy and inventory refresh before the approved installer state was reflected.

## Resolution

1. Reviewed Endpoint Protection logs on <HOSTNAME> for user <USER> and confirmed the EditorX installer (EditorX_Setup_v4.2.1.exe) was being denied by an active blocklist/policy signature mismatch (POLICY_BLOCK_403) rather than a missing Software Center deployment.
2. Validated that <HOSTNAME> (<USER>, <EMP_ID>) was targeted for the EditorX deployment in Software Center so the issue was isolated to Endpoint Protection security policy enforcement and not entitlement assignment.
3. Approved the EditorX publisher certificate and installer hash in the Endpoint Protection console with assistance from security analyst <PERSON>, and updated the relevant protection policy for the <LOCATION> device scope covering <HOSTNAME>.
4. Triggered a policy sync and refreshed the device inventory in Intune for <HOSTNAME> (IP <IP>) so the endpoint received the updated Endpoint Protection allow-list and current application state; confirmed new sync timestamp of 2026-03-18T22:42:00Z.
5. Retried the installation from Software Center on <HOSTNAME> after policy refresh and confirmed EditorX installed successfully without the policy check error; user <USER> verified the application launched correctly.
