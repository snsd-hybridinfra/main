terraform {
  required_version = ">= 1.7.0, < 2.0.0"

  backend "local" {}

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 3.4.0"
    }
  }
}

provider "openstack" {
  cloud  = var.openstack_cloud
  region = var.target_region
}
