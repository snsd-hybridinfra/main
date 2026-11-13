variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "vnet_name" { type = string }
variable "vnet_cidr" { type = string }
variable "public_subnet_name" { type = string }
variable "public_subnet_cidr" { type = string }
variable "private_subnet_name" { type = string }
variable "private_subnet_cidr" { type = string }
variable "network_security_group_name" { type = string }
variable "route_table_name" { type = string }
variable "common_tags" {
  type    = map(string)
  default = {}
}
