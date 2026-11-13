# Authentication is intentionally omitted. A future approved implementation must
# supply credentials through secure local configuration outside this repository.
provider "aws" {}

provider "azurerm" {
  features {}
}

provider "openstack" {}
