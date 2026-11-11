# OpenStack Network Module

This module is a reviewable, non-production Terraform definition for the migrated standalone lab. It defines a private network, subnet, external network reference, router, router interface, baseline security group, and one management rule placeholder.

The module contains no provider credentials, provider configuration, backend configuration, public IP resource, project identifiers, authentication URL, or production values. the migrated standalone lab does not run `terraform init`, `validate`, `plan`, or `apply`. Provider validation belongs to the migrated standalone lab, and security group validation belongs to the migrated standalone lab.
