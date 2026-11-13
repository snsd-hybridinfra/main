variable "name" {
  description = "Reviewed DNS-safe name for the private monitoring VM."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,47}$", var.name))
    error_message = "name must be a 3-48 character lowercase DNS-safe identifier."
  }
}

variable "network_id" {
  description = "Existing operator-approved private Neutron network ID."
  type        = string

  validation {
    condition     = length(trimspace(var.network_id)) > 0
    error_message = "An existing private network ID is required."
  }
}

variable "security_group_ids" {
  description = "Existing approved security groups; this module creates none."
  type        = list(string)

  validation {
    condition     = length(var.security_group_ids) > 0 && alltrue([for id in var.security_group_ids : length(trimspace(id)) > 0])
    error_message = "At least one existing security group ID is required."
  }
}

variable "image_id" {
  description = "Immutable reviewed Glance image ID."
  type        = string
}

variable "flavor_id" {
  description = "Reviewed Nova flavor ID."
  type        = string
}

variable "keypair_name" {
  description = "Existing operator recovery keypair name."
  type        = string
}

variable "volume_size_gib" {
  description = "Reviewed persistent data volume size in GiB."
  type        = number

  validation {
    condition     = var.volume_size_gib >= 20 && var.volume_size_gib <= 2048
    error_message = "volume_size_gib must be between 20 and 2048."
  }
}

variable "volume_type" {
  description = "Optional approved Cinder volume type; null uses the cloud default."
  type        = string
  default     = null
}

variable "availability_zone" {
  description = "Optional reviewed Nova availability zone."
  type        = string
  default     = null
}

variable "approval_reference" {
  description = "Non-secret approval record identifier embedded as metadata."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9._:-]{8,128}$", var.approval_reference))
    error_message = "approval_reference must be a non-secret record identifier."
  }
}

variable "tags" {
  description = "Additional reviewed non-secret tags."
  type        = list(string)
  default     = []
}
