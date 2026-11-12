output "resource_group_id" {
  description = "ID of the resource group definition."
  value       = azurerm_resource_group.this.id
}

output "virtual_network_id" {
  description = "ID of the virtual network definition."
  value       = azurerm_virtual_network.this.id
}

output "public_subnet_id" {
  description = "ID of the public-tier subnet definition."
  value       = azurerm_subnet.public.id
}

output "private_subnet_id" {
  description = "ID of the private-tier subnet definition."
  value       = azurerm_subnet.private.id
}

output "network_security_group_id" {
  description = "ID of the baseline network security group definition."
  value       = azurerm_network_security_group.baseline.id
}

output "route_table_id" {
  description = "ID of the route table definition."
  value       = azurerm_route_table.this.id
}
