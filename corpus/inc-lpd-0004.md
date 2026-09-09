# Laptop very slow after login

**Service:** laptop-support
**Source incident:** INC-LPD-0004
**Priority:** high

## Symptom

I'm experiencing severe laptop slowness immediately after morning sign-in on my Windows 10 laptop (<HOSTNAME>). CPU remained near 90% and disk utilization reached 98%, causing Outlook and Google Chrome to take several minutes to open and become responsive. Task Manager showed Microsoft Defender (MsMpEng.exe) actively consuming resources along with multiple startup applications, and Intune showed a pending device policy refresh for my account (<USER>, <EMP_ID>). The issue blocked normal productivity right after login. Please contact me at <EMAIL> or ext <PHONE> if you need remote access.

## Diagnosis

Diagnostics on <HOSTNAME> (user <USER>, <EMP_ID>) confirmed a post-login resource saturation issue rather than application-specific failure. MsMpEng.exe was processing queued Defender scans, disk utilization was near maximum on the 256 GB SSD, startup items were competing for resources, and endpoint policy refresh was pending in Intune. After clearing the scan backlog, reclaiming disk space, and reducing startup load, system performance normalized for the <LOCATION>-based endpoint.

## Root cause

Queued Microsoft Defender scans were running after login and saturating CPU and disk, while low free disk space and several nonessential startup applications amplified the performance degradation.

## Resolution

1. Reviewed Task Manager and Defender activity on <HOSTNAME> (IP <IP>) to confirm MsMpEng.exe was driving sustained post-login CPU usage (55-70%) and disk contention for user <USER>.
2. Cleared the Defender scan backlog (14 queued items) on <HOSTNAME> and refreshed endpoint policy via Intune so queued protection tasks could complete under current management settings for <EMP_ID>.
3. Removed temporary files (Windows Update cache, browser caches, user temp folders) and reclaimed approximately 25 GB of disk space on <HOSTNAME> to reduce disk pressure and improve application startup performance.
4. Disabled two nonessential startup applications (Adobe Updater, Teams auto-launcher) and updated startup settings on <HOSTNAME> to reduce competing resource usage at user sign-in for <USER>.
5. Monitored CPU, disk utilization, and Outlook and Chrome launch times on <HOSTNAME> after remediation until the laptop returned to normal responsiveness. Confirmed with <PERSON> via <EMAIL> that performance was satisfactory.
