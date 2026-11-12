# ZT-NET-001 Rollback

The final ACL change used automatic running-configuration rollback during two
pre-acceptance parser failures. The accepted startup rollback is:

1. Enter configuration mode through the existing approved EVE operator
   console path.
2. Under `FastEthernet0/1.20`, remove only
   `ip access-group ZT-DMZ-IN in`.
3. Remove only the named extended ACL `ZT-DMZ-IN`.
4. Confirm DMZ gateway and approved public traffic still pass, then save the
   startup configuration.

Repository and restricted-validator rollback may separately:

1. Remove only the snsd-r1-validator block from the local SSH config.
2. Remove the dedicated router-validator public/private key pair outside Git.
3. Using the existing EVE operator path, remove the codex-router-validator
   account, its authorized key, the dedicated dispatcher and validator, and its
   exact sudoers fragment.
4. Remove repository wrappers and generated ZT-NET-001 evidence only through a
   separately reviewed repository change.

Rollback must preserve operator access, the existing OpenStack and EVE
validators, EVE lab files, unrelated Cisco and OpenStack configuration, and
unrelated SSH keys. It must not reload the router or delete runtime lab assets.
