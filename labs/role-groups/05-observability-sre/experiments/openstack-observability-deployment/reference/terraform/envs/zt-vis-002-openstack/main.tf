module "zt_vis_002" {
  source = "../../modules/zt-vis-002-openstack"

  name               = var.name
  network_id         = var.network_id
  security_group_ids = var.security_group_ids
  image_id           = var.image_id
  flavor_id          = var.flavor_id
  keypair_name       = var.keypair_name
  volume_size_gib    = var.volume_size_gib
  volume_type        = var.volume_type
  availability_zone  = var.availability_zone
  approval_reference = var.approval_reference
  tags               = var.tags
}
