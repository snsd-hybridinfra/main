variable "network_name" { type = string }
variable "address_plan_cidr" { type = string }
variable "private_subnet_name" { type = string }
variable "private_subnet_cidr" { type = string }
variable "management_cidr" { type = string }
variable "dns_nameservers" { type = list(string) }
variable "external_network_name" { type = string }
variable "router_name" { type = string }
variable "security_group_name" { type = string }
variable "tags" {
  type    = list(string)
  default = []
}
