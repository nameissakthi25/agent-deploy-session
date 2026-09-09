# Device noncompliant for BitLocker — Intune shows conflicting state

**Service:** device-encryption
**Source incident:** INC-EDE-0003
**Priority:** medium

## Symptom

I noticed that corporate Windows 11 Enterprise laptop <HOSTNAME> (asset tag SLS-4821) assigned to <PERSON> (<USER>, employee ID <EMP_ID>) in the <LOCATION> office is flagged as noncompliant for disk encryption in Intune Device Compliance. The BitLocker policy appeared assigned in Microsoft Endpoint Manager and the device intermittently reported encrypted in MDM, but local BitLocker status showed encryption was not properly enabled and no protector was present. The recovery key was not visible in the tenant, preventing reliable recovery-key-backed encrypted boot support and leaving the device out of compliance. Marcus reported the issue after receiving a compliance notification email at <EMAIL>.

## Diagnosis

Diagnostics confirmed a split state between Intune and endpoint <HOSTNAME> (user <USER>, <LOCATION> office): policy assignment was healthy under the 'Corporate BitLocker Policy - Sales' profile, but the local device lacked a valid BitLocker protector and could not successfully escrow a recovery key to the tenant. Device Compliance Service showed an inconsistent encrypted status until the protector was recreated by <USER> and the key was rotated and escrowed successfully.

## Root cause

BitLocker policy was assigned, but the endpoint did not have a valid TPM/recovery protector in place and repeated recovery key escrow attempts to Intune failed, leaving MDM compliance state out of sync with the local BitLocker configuration.

## Resolution

1. Verified the assigned BitLocker policy 'Corporate BitLocker Policy - Sales' in Microsoft Endpoint Manager for <HOSTNAME> (<USER>, <EMP_ID>) and triggered a fresh device sync via Company Portal to confirm the endpoint was receiving the current encryption configuration.
2. Checked local BitLocker and TPM state on <HOSTNAME> (IP <IP>), then reinitialized the TPM-based protector using Initialize-Tpm and manage-bde after confirming the device was TPM-ready (TPM 2.0, firmware 7.2.1.0) and that no valid protector was present. Performed by <PERSON> (<USER>).
3. Added the required BitLocker TPM protector locally on <HOSTNAME> via manage-bde -protectors -add C: -tpm and confirmed the protector was successfully created (protector ID visible in manage-bde output) before proceeding with key management actions.
4. Rotated and re-escrowed the recovery key to the tenant from Endpoint Manager using BackupToAAD-BitLockerKeyProtector for <HOSTNAME>, then verified the recovery key became visible to support in the management service under <PERSON>'s device record.
5. Ran a follow-up sync on <HOSTNAME> and validated that local BitLocker status (manage-bde -status C: showing FullyEncrypted with TPM protector), escrowed recovery key presence in the tenant, and Intune Device Compliance status all reflected an encrypted and compliant state. Notified <USER> at <EMAIL> that the device is now compliant.
