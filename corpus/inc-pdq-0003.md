# Print jobs stuck on Print Server PDQ-Print01

**Service:** print-server
**Source incident:** INC-PDQ-0003
**Priority:** medium

## Symptom

Multiple users in the Sales and HR departments were trying to print to shared department printers through print server PDQ-Print01, but jobs remained stuck in a spooling state and the queue reported that the printer driver was unavailable. The issue was first reported by <PERSON> (emp ID <EMP_ID>) at the <LOCATION> office around 06:15 UTC, who noticed her documents to the HR-Floor2-Queue were not printing. Restarting the Print Spooler service briefly released some jobs, but the queue quickly blocked again with the same driver unavailable error. The issue affected Sales and HR printing workflows on the Windows Server 2019 print server PDQ-Print01, preventing normal document output from department queues including \\PDQ-Print01\Sales-Main and \\PDQ-Print01\HR-Floor2-Queue.

## Diagnosis

Diagnostics confirmed this was not a simple spooler stall. Queue inspection on PDQ-Print01 (<IP>) showed jobs from users <USER>, <USER>, and <USER> continuously stuck in spooling state across Sales-Main and HR-Floor2-Queue. Driver validation showed checksum mismatch on the HP Universal Print Driver package v6.9.0 installed on 2026-02-21, and queue mappings still referenced the older v6.7.2 driver version. Temporary relief after spooler restart further indicated the underlying cause was driver corruption or mismatch rather than a transient service outage.

## Root cause

Approved printer driver package on PDQ-Print01 was corrupt or mismatched by checksum, and affected printer queues were still mapped to an older driver version, causing repeated driver unavailable errors and queue blockage.

## Resolution

1. Remove the corrupt or mismatched HP Universal Print Driver package v6.9.0 from PDQ-Print01 (<IP>) using Print Management and install the approved HP Universal Print Driver package v6.9.0-hotfix that passes checksum validation, sourced from the approved driver repository.
2. Stop and restart the Print Spooler service on PDQ-Print01 after clearing all 14 stuck jobs from the affected Sales-Main and HR-Floor2-Queue print queues on the server. Verified by <USER> that spool directory C:\Windows\System32\spool\PRINTERS was empty before service restart.
3. Remap the impacted department printer queues (\\PDQ-Print01\Sales-Main and \\PDQ-Print01\HR-Floor2-Queue) from the stale v6.7.2 driver version to the corrected approved v6.9.0-hotfix driver package, updating queue-to-driver assignments in Print Management.
4. Submit test print jobs from workstations <HOSTNAME> (<USER>) and <HOSTNAME> (<USER>) through the remapped queues to confirm jobs leave spooling state and complete without driver unavailable errors. Both test pages printed successfully within 5 seconds.
5. If any queue still referenced the bad v6.9.0 package, roll back to the last known-good approved driver package (v6.7.2) and revalidate queue-to-driver assignments. Notify <PERSON> (<USER>, <PHONE>) and the <LOCATION> Workplace Services team of the resolution.
