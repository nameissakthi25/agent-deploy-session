# BitLocker not enabled and recovery key not escrowed

**Service:** device-encryption
**Source incident:** INC-EDE-0008
**Priority:** high

## Symptom

A managed Windows 10 21H2 corporate laptop (hostname: <HOSTNAME>, asset tag ENG-4821) assigned to <PERSON> (emp ID <EMP_ID>) in the <LOCATION> office was reported as noncompliant for disk encryption in Intune. The device, with IP <IP>, could not meet endpoint compliance requirements because BitLocker was not enabled locally and no recovery key was visible in Azure AD/Intune for the user <USER>. Local checks via manage-bde showed the TPM protector was not initialized, which prevented BitLocker from starting, and later MDM sync attempts intermittently failed to escrow the generated recovery key, causing compliance status to lag and temporarily toggle between noncompliant and pending.

## Diagnosis

Diagnostics on <HOSTNAME> (user: <USER>, emp ID <EMP_ID>) identified two linked conditions: the endpoint lacked an initialized TPM protector, which blocked BitLocker activation on the C: drive, and recovery key escrow to Intune/Azure AD was unstable during MDM sync — the escrow API returned intermittent timeouts on the first two attempts. After TPM initialization and local BitLocker enablement, the device encrypted successfully and the recovery key eventually escrowed during a third sync cycle at 11:42 AM, allowing compliance to recover to a compliant state in the Intune portal.

## Root cause

BitLocker could not start because the device TPM protector was not initialized, and recovery key escrow to Intune/Azure AD was intermittently failing during MDM sync, delaying compliant status after local remediation.

## Resolution

1. Confirmed TPM was present on <HOSTNAME> but no usable BitLocker TPM protector had been initialized — Get-Tpm showed TPMReady: False. Ran Initialize-Tpm to prepare the TPM module, then added a TPM protector locally via manage-bde -protectors -add C: -tpm so the device could support BitLocker protectors.
2. Enabled BitLocker on the C: system drive of <HOSTNAME> using manage-bde -on C: and generated a new 48-digit recovery key after the TPM protector was successfully added. Encryption began immediately and progressed without errors.
3. Forced Intune and MDM sync cycles from Company Portal on <HOSTNAME> (user <USER>) and retried recovery key escrow/key rotation until the new recovery key was successfully published to the management service on the third sync attempt at 11:42 AM. Earlier attempts returned HTTP 504 timeout from the key escrow API.
4. Validated that local disk encryption on C: was actively progressing (manage-bde -status showed 'Encryption in Progress') and that a recovery key was now available in Azure AD under <EMAIL>'s device record for support recovery operations.
5. Rechecked Intune compliance after the successful escrow event at approximately 11:44 AM and verified <HOSTNAME> returned to a compliant encryption state in the Device Compliance blade despite earlier intermittent escrow failures. Notified <PERSON> (<EMAIL>) that the device is now fully compliant.
