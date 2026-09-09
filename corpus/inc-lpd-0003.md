# Laptop slow after login

**Service:** laptop-support
**Source incident:** INC-LPD-0003
**Priority:** low

## Symptom

I'm experiencing recurring laptop performance degradation immediately after Windows 10 login on my corporate laptop (hostname <HOSTNAME>, asset tag EMEA-SLS-4417). MsMpEng.exe was consuming about 95% CPU, Windows Explorer and Microsoft Edge opened slowly, and normal work was delayed because applications took 10-30 seconds to launch. The issue returned after a prior temporary fix (INC-LPD-0001) that only reduced startup load. My employee ID is <EMP_ID> and I'm based in the <LOCATION> office. Please advise — I have client demos this week and need the machine responsive.

## Diagnosis

Diagnostics on <HOSTNAME> (user <USER>, employee <EMP_ID>, <LOCATION> office) confirmed the slowdown occurred immediately after login and was driven primarily by Defender scan activity rather than general disk pressure. The reopened behavior matched a queued scan backlog in endpoint protection — the Defender engine (MsMpEng.exe) had accumulated three deferred quick-scan jobs dating back to 2026-01-25. Residual startup items (OneDrive sync, Teams auto-launch, Salesforce plugin) added additional contention during the sign-in window, compounding the ~95% CPU saturation observed via Task Manager on the device at IP <IP>.

## Root cause

Microsoft Defender had a queued scan backlog that was driving sustained MsMpEng.exe CPU utilization immediately after login, and remaining nonessential startup items increased contention during the same startup window.

## Resolution

1. Reviewed startup performance at logon on <HOSTNAME> (user <USER>) and confirmed MsMpEng.exe (PID 4892) was the primary process consuming CPU while the device was slow to respond. Captured a 10-minute Performance Monitor trace for baseline comparison.
2. Cleared the Defender queued scan backlog (three deferred quick-scans from 2026-01-25 to 2026-01-28) and forced the endpoint protection engine to resume and complete pending scan activity cleanly using the MpCmdRun.exe -SignatureUpdate and -Scan commands on <HOSTNAME>.
3. Triggered a device policy refresh through Endpoint Management for <HOSTNAME> (<USER>) so the latest endpoint and startup configuration was reapplied to the laptop. Confirmed successful policy sync at 2026-01-29T15:02Z.
4. Disabled remaining nonessential startup applications (OneDrive sync delay, Teams auto-launch, Salesforce plugin pre-load) to reduce concurrent resource usage during the user sign-in phase on <USER>'s profile.
5. Scheduled full Defender scans outside business hours (daily at 01:00 CET) and adjusted scan timing/throttling via Endpoint Management policy so routine protection activity would not contend with interactive logon use. Applied CPU throttle limit of 30% for scheduled scans on the <LOCATION> Sales group devices.
6. Validated that CPU utilization on <HOSTNAME> returned to normal (below 15%) within 90 seconds after login and that Explorer and Edge opened promptly (under 3 seconds) without the previous delay. Confirmed with <PERSON> via email at <EMAIL> that the device was performing normally.
