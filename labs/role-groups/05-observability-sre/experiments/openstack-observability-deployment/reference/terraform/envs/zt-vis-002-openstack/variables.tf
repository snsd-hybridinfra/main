variable "openstack_cloud" {
  description = "Named entry from an external clouds.yaml."
  type        = string
}

variable "region" {
  description = "Reviewed OpenStack region."
  type        = string
}

variable "name" { type = string }
variable "network_id" { type = string }
variable "security_group_ids" { type = list(string) }
variable "image_id" { type = string }
variable "flavor_id" { type = string }
variable "keypair_name" { type = string }
variable "volume_size_gib" { type = number }
variable "volume_type" {
  type    = string
  default = null
}
variable "availability_zone" {
  type    = string
  default = null
}
variable "approval_reference" { type = string }
variable "tags" {
  type    = list(string)
  default = []
}
