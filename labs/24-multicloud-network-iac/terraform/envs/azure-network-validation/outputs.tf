output "resource_group_id" { value = module.azure_network.resource_group_id }
output "virtual_network_id" { value = module.azure_network.virtual_network_id }
output "public_subnet_id" { value = module.azure_network.public_subnet_id }
output "private_subnet_id" { value = module.azure_network.private_subnet_id }
output "network_security_group_id" { value = module.azure_network.network_security_group_id }
output "route_table_id" { value = module.azure_network.route_table_id }
