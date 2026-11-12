locals {
  fixed_tags = ["zt-managed", "zt-vis-002", "private-only", "non-production"]
}

resource "openstack_networking_port_v2" "monitoring" {
  name                  = "${var.name}-port"
  admin_state_up        = true
  network_id            = var.network_id
  port_security_enabled = true
  security_group_ids    = var.security_group_ids
  tags                  = distinct(concat(local.fixed_tags, var.tags))
}

resource "openstack_compute_instance_v2" "monitoring" {
  name              = var.name
  image_id          = var.image_id
  flavor_id         = var.flavor_id
  key_pair          = var.keypair_name
  availability_zone = var.availability_zone
  config_drive      = true

  network {
    port = openstack_networking_port_v2.monitoring.id
  }

  metadata = {
    ZeroTrustPackage = "ZT-VIS-002"
    ApprovalRef      = var.approval_reference
    Exposure         = "PRIVATE_ONLY"
  }

  tags = distinct(concat(local.fixed_tags, var.tags))
}

resource "openstack_blockstorage_volume_v3" "monitoring_data" {
  name              = "${var.name}-data"
  size              = var.volume_size_gib
  volume_type       = var.volume_type
  availability_zone = var.availability_zone

  metadata = {
    ZeroTrustPackage = "ZT-VIS-002"
    ApprovalRef      = var.approval_reference
    DataClass        = "SANITIZED_TELEMETRY_ONLY"
  }
}

resource "openstack_compute_volume_attach_v2" "monitoring_data" {
  instance_id = openstack_compute_instance_v2.monitoring.id
  volume_id   = openstack_blockstorage_volume_v3.monitoring_data.id
}
