output "vpc_id" {
  description = "Placeholder output for the VPC identifier after future approved provisioning."
  value       = aws_vpc.this.id
}

output "public_subnet_id" {
  description = "Placeholder output for the public subnet identifier."
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "Placeholder output for the private subnet identifier."
  value       = aws_subnet.private.id
}

output "public_route_table_id" {
  description = "Placeholder output for the public route table identifier."
  value       = aws_route_table.public.id
}

output "internet_gateway_id" {
  description = "Placeholder output for the internet gateway identifier."
  value       = aws_internet_gateway.this.id
}

output "security_group_id" {
  description = "Placeholder output for the baseline security group identifier."
  value       = aws_security_group.network_baseline.id
}
