# Print jobs stuck on PS-PRINT01

**Service:** print-server
**Source incident:** INC-PDQ-0005
**Priority:** high

## Symptom

Multiple Finance users in the <LOCATION> office were trying to print to the Dept-Color-Queue hosted on print server PS-PRINT01, but jobs stayed queued at 0%, the printer appeared offline, and the driver showed as unavailable. The issue was first reported by <PERSON> (emp ID <EMP_ID>) around 6:00 PM and affected at least five other team members. The problem began after a scheduled driver update pushed on 2026-02-21 and blocked normal color printing for the department until the server-side driver package and queue mapping were corrected.

## Diagnosis

Standard printer queue diagnostics showed the shared Dept-Color-Queue on PS-PRINT01 was not processing jobs normally for Finance users in the <LOCATION> office. The printer intermittently appeared offline from client workstations including <HOSTNAME> (<IP>) and <HOSTNAME> (<IP>), and spooler recovery actions only provided temporary relief. Driver validation on PS-PRINT01 identified a mismatched and corrupted server-side HP Universal printer driver introduced after the 2026-02-21 scheduled update, confirming the driver package as the cause of queue failure. Diagnostics performed by agent <USER>.

## Root cause

Corrupted and mismatched printer driver files on PS-PRINT01 after a recent driver update caused the Dept-Color-Queue to fail, report the printer as offline, and leave jobs stuck at 0% in the spooler.

## Resolution

1. Reviewed the PS-PRINT01 printer configuration and confirmed the Dept-Color-Queue was bound to a driver package reporting mismatch and unavailable driver files after the 2026-02-21 scheduled update. Agent <PERSON> (<USER>, emp ID <EMP_ID>) verified the corrupted HP Universal v6.2.0.0 package in the driver store.
2. Removed the corrupted HP Universal v6.2.0.0 driver package from PS-PRINT01 using Print Management, deleted residual files from the driver store, and reinstalled the approved HP Universal v6.1.0.2 driver package on the Windows Server 2016 print server from the validated network share.
3. Updated the Dept-Color-Queue to use the reinstalled approved HP Universal v6.1.0.2 driver so the shared queue referenced a valid and consistent server-side driver package. Confirmed the driver status changed from 'unavailable' to 'ready' in Print Management.
4. Cleared all 14 residual stuck print jobs from the queue and restarted the Print Spooler service on PS-PRINT01 to reload the corrected driver files and queue state. Verified no further 'failed to load driver files' errors in the event log.
5. Validated successful test prints from multiple user workstations including <HOSTNAME> (<USER>, <IP>) and <HOSTNAME> (<USER>, <IP>), and confirmed the Dept-Color-Queue remained online without recurring spooler or driver availability errors. Notified <PERSON> and affected Finance team members via email at <EMAIL> that printing was restored.
