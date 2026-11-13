variable "network_name" {
  description = "Name of the non-production private network definition."
  type        = string
}

variable "address_plan_cidr" {
  description = "Documentation-only CIDR for the broader validation address plan."
  type        = string
}

variable "private_subnet_name" {
  description = "Name of the private validation subnet."
  type        = string
}

variable "private_subnet_cidr" {
  description = "CIDR of the private validation subnet."
  type        = string
}

variable "management_cidr" {
  description = "Non-production management CIDR used by the security rule placeholder."
  type        = string
}

variable "dns_nameservers" {
  description = "Documentation-safe DNS resolver examples for the subnet."
  type        = list(string)
  default     = []
}

variable "external_network_name" {
  description = "Placeholder name of an external network reference."
  type        = string
}

variable "router_name" {
  description = "Name of the validation router definition."
  type        = string
}

variable "security_group_name" {
  description = "Name of the baseline security group definition."
  type        = string
}

variable "tags" {
  description = "Non-sensitive metadata tags applied to supported resources."
  type        = list(string)
  default     = []
}
