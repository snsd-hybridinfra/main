output "vpc_id" {
  description = "Placeholder VPC identifier output."
  value       = module.aws_network.vpc_id
}

output "public_subnet_id" {
  description = "Placeholder public subnet identifier output."
  value       = module.aws_network.public_subnet_id
}

output "private_subnet_id" {
  description = "Placeholder private subnet identifier output."
  value       = module.aws_network.private_subnet_id
}

output "public_route_table_id" {
  description = "Placeholder public route table identifier output."
  value       = module.aws_network.public_route_table_id
}

output "internet_gateway_id" {
  description = "Placeholder internet gateway identifier output."
  value       = module.aws_network.internet_gateway_id
}

output "security_group_id" {
  description = "Placeholder baseline security group identifier output."
  value       = module.aws_network.security_group_id
}
