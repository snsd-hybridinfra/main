module "aws_network" {
  source = "../../modules/aws-network"

  vpc_name                 = var.vpc_name
  vpc_cidr                 = var.vpc_cidr
  public_subnet_name       = var.public_subnet_name
  public_subnet_cidr       = var.public_subnet_cidr
  private_subnet_name      = var.private_subnet_name
  private_subnet_cidr      = var.private_subnet_cidr
  internet_gateway_name    = var.internet_gateway_name
  internet_destination_cidr = var.internet_destination_cidr
  public_route_table_name  = var.public_route_table_name
  private_route_table_name = var.private_route_table_name
  security_group_name      = var.security_group_name
  common_tags              = var.common_tags
}
