module "azure_network" {
  source = "../../modules/azure-network"

  resource_group_name         = var.resource_group_name
  location                    = var.location
  vnet_name                   = var.vnet_name
  vnet_cidr                   = var.vnet_cidr
  public_subnet_name          = var.public_subnet_name
  public_subnet_cidr          = var.public_subnet_cidr
  private_subnet_name         = var.private_subnet_name
  private_subnet_cidr         = var.private_subnet_cidr
  network_security_group_name = var.network_security_group_name
  route_table_name            = var.route_table_name
  common_tags                 = var.common_tags
}
