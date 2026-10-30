variable "region" { type = string }
variable "name" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "load_balancer_security_group_id" { type = string }
variable "api_target_group_arn" { type = string }
variable "web_target_group_arn" { type = string }
variable "api_image" { type = string }
variable "web_image" { type = string }
variable "runtime_secret_arn" {
  type        = string
  description = "Existing JSON Secrets Manager secret, populated before rollout. Never put values in Terraform variables."
}
variable "desired_count" {
  type        = number
  default     = 0
  description = "Keep zero until migrations, identity, providers and production gates are configured."
}
variable "web_origin" { type = string }
