output "primary_resource_id" {
  value = openstack_compute_instance_v2.workload.id
}

output "endpoint" {
  value = try(openstack_networking_port_v2.workload.all_fixed_ips[0], "")
}

output "display_name" {
  value = openstack_compute_instance_v2.workload.name
}

output "floating_ip" {
  value = false
}

output "network_exposure" {
  value = "PRIVATE_ONLY"
}
