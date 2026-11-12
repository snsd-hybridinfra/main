output "instance_id" {
  description = "Monitoring VM ID."
  value       = openstack_compute_instance_v2.monitoring.id
}

output "private_ip" {
  description = "Private fixed IP used to build reviewed Ansible inventory."
  value       = try(openstack_networking_port_v2.monitoring.all_fixed_ips[0], null)
}

output "port_id" {
  description = "Private Neutron port ID."
  value       = openstack_networking_port_v2.monitoring.id
}

output "data_volume_id" {
  description = "Persistent sanitized-telemetry volume ID."
  value       = openstack_blockstorage_volume_v3.monitoring_data.id
}

output "network_exposure" {
  description = "Explicit public-exposure decision."
  value       = "PRIVATE_ONLY_NO_FLOATING_IP"
}
