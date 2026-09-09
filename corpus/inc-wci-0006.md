# Users cannot connect to Corporate Wi-Fi

**Service:** wifi
**Source incident:** INC-WCI-0006
**Priority:** medium

## Symptom

Multiple managed corporate devices used by Sales users on the <LOCATION> US-East floor could not connect to the Corporate Wi-Fi SSID (CorpNet-Secure). Users selected the network but received immediate 802.1X/EAP authentication failures and no network access, blocking normal wireless connectivity on Windows, macOS, and iOS devices. The issue was first reported by <PERSON> (<USER>, <EMP_ID>) and subsequently confirmed by at least six other Sales team members. The issue affected corporate SSID authentication through the wireless controller (WLC-EAST-01.corp.internal) and RADIUS/NAC path and began when the controller certificate expired on 2026-04-25 at approximately 08:45 UTC.

## Diagnosis

Standard Wi-Fi authentication troubleshooting isolated the failure to the infrastructure side rather than a localized endpoint problem. NAC/RADIUS logs consistently showed EAP-TLS rejections due to an expired certificate on WLC-EAST-01.corp.internal, and controller review confirmed the wireless controller server certificate (serial 7A:3F:9B:22:01) had lapsed at 08:00 UTC on 2026-04-25. After certificate renewal and trust propagation performed by <USER>, authentication succeeded again for users including <USER> (<IP>) and <USER>; only a small subset of endpoints needed local profile cleanup or re-enrollment.

## Root cause

The wireless controller server certificate expired, causing EAP-TLS certificate validation to fail during 802.1X authentication for corporate Wi-Fi clients.

## Resolution

1. Generated and installed a renewed server certificate (CN=wlc-east-01.corp.internal, valid through 2028-04-25) on the wireless controller WLC-EAST-01.corp.internal with the correct trust chain (CorpCA-Intermediate → CorpCA-Root) for corporate Wi-Fi authentication. Certificate renewal performed by <PERSON> (<USER>).
2. Applied the updated certificate and trust configuration to the wireless controller WLC-EAST-01.corp.internal and propagated the change to all 12 dependent access points on the <LOCATION> 4th floor handling the Corporate SSID (CorpNet-Secure).
3. Validated in RADIUS (NAC-EAST-02.corp.internal) and controller logs that EAP-TLS authentication failures for 'certificate expired' stopped after the certificate replacement. Confirmed successful authentications for <USER> (<IP>), <USER>, and <USER> within minutes of propagation.
4. Instructed affected users including <PERSON> (<USER>) and <PERSON> (<USER>) to forget and reconnect to the Corporate Wi-Fi SSID (CorpNet-Secure) so devices would establish a fresh trusted connection profile.
5. For endpoints that still failed after reconnection, removed stale or corrupt wireless profiles and re-enrolled or reinstalled the managed network certificate/profile until authentication succeeded. This was required for <HOSTNAME> (<USER>) and <HOSTNAME> (<USER>), as well as one iOS device belonging to <USER>. All devices confirmed connected by 10:30 UTC.
