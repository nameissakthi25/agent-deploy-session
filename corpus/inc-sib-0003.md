# Software Center installation blocked by Endpoint Protection (resolved)

**Service:** software-center
**Source incident:** INC-SIB-0003
**Priority:** high

## Symptom

I was trying to install ContosoApp from Software Center on my managed Windows 10 21H2 x64 device (hostname <HOSTNAME>), but the installation was immediately blocked with an Endpoint Protection message stating "Installation blocked by Endpoint Protection" and the application was not consistently visible in the Software Center catalog. My username is <USER> (employee ID <EMP_ID>) and I'm based in the <LOCATION> office on the Engineering-Workstations group. I could not complete the required corporate software installation, and installer logging indicated a security policy block (exit code 0x80070490) rather than a packaging failure. I need ContosoApp for an upcoming sprint deadline and would appreciate urgent assistance.

## Diagnosis

Diagnostics confirmed the ContosoApp software deployment itself was valid and properly targeted to the Engineering-Workstations collection, but the installer (ContosoAppSetup_v4.2.1.exe) was actively blocked by Endpoint Protection on device <HOSTNAME> (IP <IP>). A secondary visibility issue in Software Center improved after Intune inventory and machine policy refresh, indicating the main failure was security enforcement rather than missing entitlement or broken packaging. User <USER>'s group membership was confirmed intact.

## Root cause

Endpoint Protection policy quarantined or blocked the approved ContosoApp installer, and the affected device also required an Intune inventory and policy refresh before the application targeting and visibility were restored in Software Center.

## Resolution

1. Confirmed the ContosoApp deployment (DEP-88421) was intended for the affected device <HOSTNAME> belonging to user <USER> (<EMP_ID>) in the <LOCATION> office, and reviewed Software Center catalog visibility and Endpoint Protection block symptoms to rule out a generic packaging failure.
2. Checked Endpoint Protection application control findings on <HOSTNAME> and verified the ContosoApp installer (ContosoAppSetup_v4.2.1.exe) was being blocked by quarantine/allowlist policy rule EP-RULE-2041 on the device, as confirmed by security analyst <PERSON> (<USER>).
3. Approved the ContosoApp installer hash in the applicable Endpoint Protection allowlist policy via the security management console so the trusted package could execute without triggering application control blocks on managed endpoints.
4. Refreshed device inventory on <HOSTNAME> and forced an Intune policy sync (via Company Portal > Sync) so the latest application targeting, security policy state, and updated allowlist were applied to the endpoint. Last sync updated from 2026-03-16T08:12:00Z to current.
5. Triggered a Software Center machine policy refresh on <HOSTNAME> and re-ran the ContosoApp installation after the Endpoint Protection policy change and Intune device sync completed. User <USER> confirmed the installation prompt appeared.
6. Verified that ContosoApp became available to <HOSTNAME> in Software Center and that the installation completed successfully (exit code 0) without further Endpoint Protection blocks. Confirmed with <PERSON> via email at <EMAIL> that the application is functioning as expected.
