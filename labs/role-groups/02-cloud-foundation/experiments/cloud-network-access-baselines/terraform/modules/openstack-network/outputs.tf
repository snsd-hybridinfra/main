output "network_id" {
  description = "ID of the private network definition."
  value       = openstack_networking_network_v2.private.id
}

output "private_subnet_id" {
  description = "ID of the private subnet definition."
  value       = openstack_networking_subnet_v2.private.id
}

output "router_id" {
  description = "ID of the router definition."
  value       = openstack_networking_router_v2.this.id
}

output "security_group_id" {
  description = "ID of the baseline security group definition."
  value       = openstack_networking_secgroup_v2.baseline.id
}
