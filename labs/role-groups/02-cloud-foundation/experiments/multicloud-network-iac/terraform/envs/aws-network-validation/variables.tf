variable "vpc_name" {
  description = "Non-production example VPC name."
  type        = string
}

variable "vpc_cidr" {
  description = "Non-production example VPC CIDR."
  type        = string
}

variable "public_subnet_name" {
  description = "Non-production example public subnet name."
  type        = string
}

variable "public_subnet_cidr" {
  description = "Non-production example public subnet CIDR."
  type        = string
}

variable "private_subnet_name" {
  description = "Non-production example private subnet name."
  type        = string
}

variable "private_subnet_cidr" {
  description = "Non-production example private subnet CIDR."
  type        = string
}

variable "internet_gateway_name" {
  description = "Non-production example internet gateway name."
  type        = string
}

variable "internet_destination_cidr" {
  description = "Non-production example public route destination."
  type        = string
}

variable "public_route_table_name" {
  description = "Non-production example public route table name."
  type        = string
}

variable "private_route_table_name" {
  description = "Non-production example private route table name."
  type        = string
}

variable "security_group_name" {
  description = "Non-production example baseline security group name."
  type        = string
}

variable "common_tags" {
  description = "Non-sensitive example resource tags."
  type        = map(string)
  default     = {}
}
