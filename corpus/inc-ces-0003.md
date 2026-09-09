# Expired TLS certificate caused internal service TLS outage

**Service:** load-balancer
**Source incident:** INC-CES-0003
**Priority:** high

## Symptom

Users and internal integrations were trying to access the Internal Web Service at internal-web.svc.cluster.local, but browsers showed certificate warnings and dependent API calls began failing TLS validation. The issue was first reported by platform engineer <PERSON> (<EMAIL>) from the <LOCATION> office at approximately 05:15 UTC. Monitoring detected TLS handshake failures from multiple client IPs including <IP>, and load balancer logs on LB-EAST-01 showed an expired certificate was being presented, causing an internal service outage until the certificate chain on the load balancer was corrected.

## Diagnosis

Diagnostics confirmed the outage was caused by an expired certificate being served by the load balancer LB-EAST-01, not by an application-side TLS defect. Certificate authority records showed the certificate for internal-web.svc.cluster.local had passed its expiration date of 2025-12-13T00:00:00Z, and renewal automation logs on cert-mgr-01.corplabs.internal identified the blocking condition: access denied for service account <USER> while attempting to update the load balancer chain. Manual deployment of the renewed chain by <PERSON> (<USER>) and LB reload restored successful TLS handshakes for all clients including <IP> and workstation <HOSTNAME>.

## Root cause

The TLS certificate for internal-web.svc.cluster.local expired, and the replacement certificate chain was not deployed to the load balancer because the automated renewal job failed with access denied due to missing permissions to update load balancer configuration.

## Resolution

1. Issued a replacement TLS certificate from the internal Certificate Authority for internal-web.svc.cluster.local and exported the full certificate chain (new serial 5B:A1:09:EE:44:C7), performed by <PERSON> (<USER>, <EMP_ID>).
2. Uploaded and applied the renewed certificate chain to the internal load balancer instance LB-EAST-01 serving the service endpoint, replacing the expired leaf certificate serial 3A:7F:02:CB:91:DE.
3. Reloaded the load balancer configuration on LB-EAST-01 so the new certificate chain was presented to clients, verified by <USER> at 05:42 UTC.
4. Validated successful TLS handshakes from internal clients including workstation <HOSTNAME> (<IP>) and <HOSTNAME>, and browser access by <PERSON> and <PERSON>, confirming the expired certificate warning was cleared.
5. Corrected the renewal automation permissions so the service account <USER> can update load balancer configuration on LB-EAST-01, reverting the RBAC change made by <USER>, then tested the renewal workflow with a dry run and restored certificate expiry monitoring with alerts routed to <EMAIL>.
