resource "openstack_networking_network_v2" "private" {
  name           = var.network_name
  admin_state_up = true
  tags           = var.tags
}

resource "openstack_networking_subnet_v2" "private" {
  name            = var.private_subnet_name
  network_id      = openstack_networking_network_v2.private.id
  cidr            = var.private_subnet_cidr
  ip_version      = 4
  dns_nameservers = var.dns_nameservers
}

data "openstack_networking_network_v2" "external" {
  name = var.external_network_name
}

resource "openstack_networking_router_v2" "this" {
  name                = var.router_name
  admin_state_up      = true
  external_network_id = data.openstack_networking_network_v2.external.id
  tags                = var.tags
}

resource "openstack_networking_router_interface_v2" "private" {
  router_id = openstack_networking_router_v2.this.id
  subnet_id = openstack_networking_subnet_v2.private.id
}

resource "openstack_networking_secgroup_v2" "baseline" {
  name        = var.security_group_name
  description = "Non-production retired-numbered-case baseline security group placeholder"
  tags        = var.tags
}

resource "openstack_networking_secgroup_rule_v2" "management_ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.management_cidr
  security_group_id = openstack_networking_secgroup_v2.baseline.id
}
