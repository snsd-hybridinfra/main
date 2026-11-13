locals {
  expected_product_id = "DEV-OS-VM-S"
  instance_name       = "zt-${var.project_name}-${substr(replace(var.request_id, "-", ""), 0, 8)}"
}

resource "openstack_networking_port_v2" "workload" {
  name                   = "${local.instance_name}-port"
  admin_state_up         = true
  network_id             = var.network_id
  port_security_enabled  = true
  security_group_ids     = var.security_group_ids
}

resource "openstack_compute_instance_v2" "workload" {
  name        = local.instance_name
  image_name  = var.approved_image_name
  flavor_name = var.flavor_name
  key_pair    = var.keypair_name
  config_drive = true

  network {
    port = openstack_networking_port_v2.workload.id
  }

  metadata = merge(var.required_tags, {
    WorkloadPurpose = var.workload_purpose
    ApprovedBy      = var.approved_by
    ModuleVersion   = var.module_version
  })

  tags = ["zt-managed", "private-only", "dev-os-vm-s"]

  lifecycle {
    precondition {
      condition     = var.product_id == local.expected_product_id && var.product_version == 1
      error_message = "The signed product identity does not match this module."
    }
  }
}
