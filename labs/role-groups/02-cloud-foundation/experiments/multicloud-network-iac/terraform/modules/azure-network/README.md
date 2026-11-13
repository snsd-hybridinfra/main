# Azure Network Module

This module is a reviewable, non-production Terraform definition for standalone-lab. It defines a resource group, virtual network, two subnets, a baseline network security group, a route table, and subnet associations.

The module contains no provider credentials, provider configuration, backend configuration, public IP resource, or production values. standalone-lab does not run `terraform init`, `validate`, `plan`, or `apply`. Provider validation belongs to standalone-lab, and NSG least-privilege rule validation belongs to standalone-lab.
