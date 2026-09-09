# Print jobs stuck on print-server-02 after driver update

**Service:** print-server
**Source incident:** INC-PDQ-0004
**Priority:** low

## Symptom

Corporate Office users in the <LOCATION> location were trying to print to the shared queue PrinterQueue-Corp on print-server-02 after an overnight printer driver deployment pushed by the Workplace Services team. Submitted jobs from multiple users, including <PERSON> (<USER>, <EMP_ID>) in Accounting and <PERSON> (<USER>) in Legal, remained stuck in a printing state for over three hours. Users received a 'driver unavailable' message when attempting to print, preventing normal printing to shared office printers across multiple departments on the 4th and 5th floors.

## Diagnosis

Diagnostics confirmed the issue began after the scheduled driver deployment at 02:15 AM on 2026-02-22. Queue review on print-server-02 showed 47 jobs stuck in a printing state submitted by users across Accounting, Legal, and HR in the <LOCATION> office. Spooler log review identified repeated HP Universal PCL6 driver load failures with error 0x80070643 tied to the newly deployed package v7.1.0.25054. The combination of queue symptoms, driver errors, and successful post-reinstall validation confirmed a corrupted driver package on print-server-02 as the service-impacting fault affecting the PrinterQueue-Corp shared queue.

## Root cause

A corrupted HP Universal PCL6 driver package deployed to print-server-02 caused the Windows Print Spooler to fail loading the driver for PrinterQueue-Corp, leaving submitted jobs stuck in the queue.

## Resolution

1. Reviewed PrinterQueue-Corp on print-server-02 and cleared the backlog of 47 stuck print jobs submitted by users including <USER>, <USER>, and <USER> so the queue could be reset cleanly.
2. Restarted the Windows Print Spooler service on print-server-02 to release locked queue entries and reset driver load state. Confirmed spooler PID recycled and service returned to running status.
3. Removed the corrupted HP Universal PCL6 driver package (v7.1.0.25054) from the server driver store on print-server-02 after spooler logs showed 312 repeated driver load failures with error 0x80070643 since the overnight deployment.
4. Installed the approved HP Universal PCL6 driver package (v7.0.0.24980) from the internal repository at \\pkg-repo-east\drivers\hp-upcl6 and re-associated PrinterQueue-Corp with the restored driver. Verified driver load succeeded without errors in the spooler log.
5. Submitted validation print jobs through the shared queue from <HOSTNAME> (<USER>, <IP>) and <HOSTNAME> (<USER>, <IP>) and confirmed jobs completed successfully within seconds without further 'driver unavailable' errors. Notified affected users <PERSON>, <PERSON>, and <PERSON> via email that printing services were restored.
