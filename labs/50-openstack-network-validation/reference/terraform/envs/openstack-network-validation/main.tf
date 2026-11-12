module "openstack_network" {
  source = "../../modules/openstack-network"

  network_name          = var.network_name
  address_plan_cidr     = var.address_plan_cidr
  private_subnet_name   = var.private_subnet_name
  private_subnet_cidr   = var.private_subnet_cidr
  management_cidr       = var.management_cidr
  dns_nameservers       = var.dns_nameservers
  external_network_name = var.external_network_name
  router_name           = var.router_name
  security_group_name   = var.security_group_name
  tags                  = var.tags
}
