variable "vpc_name" {
  description = "Non-production example name for the VPC."
  type        = string
}

variable "vpc_cidr" {
  description = "Example CIDR for the VPC."
  type        = string
}

variable "public_subnet_name" {
  description = "Non-production example name for the public subnet placeholder."
  type        = string
}

variable "public_subnet_cidr" {
  description = "Example CIDR for the public subnet placeholder."
  type        = string
}

variable "private_subnet_name" {
  description = "Non-production example name for the private subnet placeholder."
  type        = string
}

variable "private_subnet_cidr" {
  description = "Example CIDR for the private subnet placeholder."
  type        = string
}

variable "internet_gateway_name" {
  description = "Non-production example name for the internet gateway placeholder."
  type        = string
}

variable "internet_destination_cidr" {
  description = "Example destination CIDR for the public route placeholder."
  type        = string
}

variable "public_route_table_name" {
  description = "Non-production example name for the public route table."
  type        = string
}

variable "private_route_table_name" {
  description = "Non-production example name for the private route table."
  type        = string
}

variable "security_group_name" {
  description = "Non-production example name for the empty baseline security group."
  type        = string
}

variable "common_tags" {
  description = "Non-sensitive example tags applied to module resources."
  type        = map(string)
  default     = {}
}
