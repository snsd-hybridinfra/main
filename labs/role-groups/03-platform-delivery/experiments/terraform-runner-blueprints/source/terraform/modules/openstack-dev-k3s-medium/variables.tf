variable "openstack_cloud" { type = string }
variable "target_region" { type = string }
variable "network_id" { type = string }
variable "security_group_ids" {
  type = list(string)
  validation {
    condition     = length(var.security_group_ids) > 0
    error_message = "At least one operator-approved security group is required."
  }
}
variable "approved_image_name" { type = string }
variable "keypair_name" { type = string }
variable "flavor_name" { type = string }
variable "request_id" { type = string }
variable "owner_id" { type = string }
variable "project_name" { type = string }
variable "workload_purpose" { type = string }
variable "product_id" { type = string }
variable "product_version" { type = number }
variable "module_version" { type = string }
variable "artifact_digest" { type = string }
variable "expires_at" { type = string }
variable "approved_by" { type = string }
variable "required_tags" { type = map(string) }
