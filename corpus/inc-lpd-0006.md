# Laptop slow

**Service:** laptop-support
**Source incident:** INC-LPD-0006
**Priority:** low

## Symptom

I have a Windows 10 Pro Dell Latitude 5500 (hostname <HOSTNAME>, asset tag MKT-04821) assigned to <PERSON> (emp ID <EMP_ID>) in the Marketing group becoming very slow immediately after login, with CPU rising above 85-90% within minutes and common applications such as Outlook and Chrome taking 20-30 seconds to open. The issue was reported from our <LOCATION> office and affected normal post-login work. Investigation traced the root cause to endpoint protection activity and concurrent startup load on the laptop.

## Diagnosis

Diagnostics on <HOSTNAME> (user <USER>, IP <IP>) confirmed that the login slowdown was not a general hardware failure but a post-login resource contention issue. High CPU usage correlated with four queued endpoint protection full-disk scans and multiple startup applications launching concurrently. After clearing the scan backlog, disabling unnecessary startup items, refreshing the endpoint management policy, and cleaning approximately 8 GB of temporary files from the user profile, CPU utilization normalized to ~15% and application launch times improved to under 3 seconds.

## Root cause

Queued endpoint protection scans were triggering at user login while several nonessential startup applications were also launching, causing sustained CPU contention and delayed application startup.

## Resolution

1. Reviewed Task Manager resource usage on <HOSTNAME> after login by user <USER> and confirmed CPU spikes (88-92%) were tied to EndpointProtectionService.exe activity and concurrent startup processes.
2. Cleared the queued endpoint protection scan backlog (four deferred full-disk scans) on <HOSTNAME> to stop repeated scan execution immediately after sign-in.
3. Disabled three nonessential startup applications (Adobe Updater, OneDrive auto-sync, Teams background launch) on <HOSTNAME> to reduce concurrent CPU load during the login sequence.
4. Refreshed device policy from endpoint management for <HOSTNAME> so scan behavior and startup-related policy state were updated on the laptop; confirmed successful policy sync at 2026-01-30T02:10Z.
5. Removed temporary files from C:\Users\<USER>\AppData\Local\Temp and C:\Windows\Temp, reclaiming approximately 8 GB of disk space on the 256 GB SSD to reduce endpoint performance pressure and help prevent future scan queuing.
