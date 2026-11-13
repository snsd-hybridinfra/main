output "primary_resource_id" { value = openstack_compute_instance_v2.workload.id }
output "endpoint" { value = "https://${try(openstack_networking_port_v2.workload.all_fixed_ips[0], "")}:6443" }
output "display_name" { value = "${var.project_name} / OpenStack k3s PaaS Small" }
output "floating_ip" { value = false }
output "network_exposure" { value = "PRIVATE_ONLY" }
output "bootstrap_status" { value = "CONFIGURATION_REQUIRED" }
output "monitoring_status" { value = "NOT_ONBOARDED" }
