output "database_endpoint" { value = aws_db_instance.main.address }
output "database_admin_secret_arn" { value = aws_db_instance.main.master_user_secret[0].secret_arn }
output "redis_endpoint" { value = aws_elasticache_replication_group.main.primary_endpoint_address }
output "source_bucket" { value = aws_s3_bucket.sources.id }
output "cluster" { value = aws_ecs_cluster.main.name }
