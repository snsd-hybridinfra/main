variable "resource_group_name" {
  description = "Name of the non-production validation resource group."
  type        = string
}

variable "location" {
  description = "Azure location used by the validation definition."
  type        = string
}

variable "vnet_name" {
  description = "Name of the validation virtual network."
  type        = string
}

variable "vnet_cidr" {
  description = "CIDR for the validation virtual network."
  type        = string
}

variable "public_subnet_name" {
  description = "Name of the public-tier validation subnet."
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR for the public-tier validation subnet."
  type        = string
}

variable "private_subnet_name" {
  description = "Name of the private-tier validation subnet."
  type        = string
}

variable "private_subnet_cidr" {
  description = "CIDR for the private-tier validation subnet."
  type        = string
}

variable "network_security_group_name" {
  description = "Name of the baseline network security group."
  type        = string
}

variable "route_table_name" {
  description = "Name of the validation route table."
  type        = string
}

variable "common_tags" {
  description = "Non-sensitive tags applied to supported resources."
  type        = map(string)
  default     = {}
}
