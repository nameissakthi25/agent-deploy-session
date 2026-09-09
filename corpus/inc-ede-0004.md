# BitLocker not enabled

**Service:** device-encryption
**Source incident:** INC-EDE-0004
**Priority:** low

## Symptom

I was trying to get the Azure AD joined Windows 10 21H2 device (hostname <HOSTNAME>, asset tag SLS-4821) assigned to <PERSON> (<EMAIL>, <EMP_ID>) into encryption compliance through Intune, but the endpoint showed BitLocker EncryptionState as Off, no recovery key was visible in Azure AD for this device, and the user never received a BitLocker PIN prompt. TPM management (tpm.msc) showed the TPM was not initialized, which prevented the device from enabling disk encryption and left it noncompliant in the Device Compliance Service. The device is located at our <LOCATION> office and connects from IP <IP>.

## Diagnosis

Diagnostics on <HOSTNAME> (user <USER>, <EMP_ID>) found BitLocker was blocked because the TPM was not initialized, leaving the device without a usable TPM protector. Follow-up checks confirmed the Intune BitLocker policy and compliance state updated after a forced sync from IP <IP>, and the recovery key successfully escrowed to Azure AD once encryption was enabled on the system volume.

## Root cause

The device TPM was not initialized, so BitLocker could not create and use the required TPM protector to start encryption. In addition, the Intune BitLocker policy had not fully applied before remediation, so recovery key escrow to Azure AD had not occurred while the device remained noncompliant.

## Resolution

1. Validated the endpoint state on <HOSTNAME> (assigned to <PERSON>, <USER>, <EMP_ID>) in TPM management and BitLocker tooling, confirming TPM status was Not initialized, BitLocker was Off on C:, and no recovery key was escrowed to Azure AD for this device.
2. Initialized the TPM on <HOSTNAME> using Initialize-Tpm and enabled the required TPM-based BitLocker protector on the device so the encryption prerequisites were satisfied. Verified tpm.msc now showed 'The TPM is ready for use.'
3. Started BitLocker encryption on the C: system volume of <HOSTNAME> using the TPM protector (Enable-BitLocker -MountPoint C: -TpmProtector) and confirmed encryption began successfully — manage-bde reported Conversion Status: Encryption in Progress.
4. Forced an Intune device sync on <HOSTNAME> via Company Portal so the assigned BitLocker configuration policy (Corp-Encryption-Win10) and compliance evaluation were reapplied to the endpoint. Device compliance state for <USER> updated to Compliant.
5. Backed up and rotated the BitLocker recovery key on <HOSTNAME> using BackupToAAD-BitLockerKeyProtector and verified the current key (ID 7A3F2B) was escrowed to Azure AD under <USER>'s device record, then confirmed the device compliance state changed to compliant in the Device Compliance Service. Sent confirmation to <PERSON> at <EMAIL>.
