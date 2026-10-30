data "aws_caller_identity" "current" {}

resource "aws_security_group" "app" {
  name_prefix = "${var.name}-app-"
  vpc_id      = var.vpc_id
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [var.load_balancer_security_group_id]
  }
  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [var.load_balancer_security_group_id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_security_group" "data" {
  name_prefix = "${var.name}-data-"
  vpc_id      = var.vpc_id
  dynamic "ingress" {
    for_each = [5432, 6379]
    content {
      from_port       = ingress.value
      to_port         = ingress.value
      protocol        = "tcp"
      security_groups = [aws_security_group.app.id]
    }
  }
}
resource "aws_db_subnet_group" "main" {
  name       = var.name
  subnet_ids = var.private_subnet_ids
}
resource "aws_db_instance" "main" {
  identifier                  = var.name
  engine                      = "postgres"
  engine_version              = "17"
  instance_class              = "db.t4g.small"
  allocated_storage           = 20
  max_allocated_storage       = 100
  db_name                     = "rag"
  username                    = "ragadmin"
  manage_master_user_password = true
  storage_encrypted           = true
  multi_az                    = true
  publicly_accessible         = false
  db_subnet_group_name        = aws_db_subnet_group.main.name
  vpc_security_group_ids      = [aws_security_group.data.id]
  backup_retention_period     = 14
  deletion_protection         = true
  skip_final_snapshot         = false
  final_snapshot_identifier   = "${var.name}-final"
}
resource "aws_elasticache_subnet_group" "main" {
  name       = var.name
  subnet_ids = var.private_subnet_ids
}
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = var.name
  description                = "Ephemeral rate limits"
  node_type                  = "cache.t4g.micro"
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  engine                     = "redis"
  engine_version             = "7.1"
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.data.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}
resource "aws_s3_bucket" "sources" {
  bucket = "${var.name}-${data.aws_caller_identity.current.account_id}-sources"
}
resource "aws_s3_bucket_public_access_block" "sources" {
  bucket                  = aws_s3_bucket.sources.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "sources" {
  bucket = aws_s3_bucket.sources.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_policy" "tls" {
  bucket = aws_s3_bucket.sources.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Deny", Principal = "*", Action = "s3:*", Resource = [aws_s3_bucket.sources.arn, "${aws_s3_bucket.sources.arn}/*"], Condition = { Bool = { "aws:SecureTransport" = "false" } } }] })
}
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.name}"
  retention_in_days = 30
}
resource "aws_ecs_cluster" "main" {
  name = var.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
resource "aws_iam_role" "execution" {
  name               = "${var.name}-execution"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }] })
}
resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "secrets" {
  role   = aws_iam_role.execution.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = [var.runtime_secret_arn] }] })
}
resource "aws_iam_role" "task" {
  for_each           = toset(["api", "worker", "web"])
  name               = "${var.name}-${each.key}"
  assume_role_policy = aws_iam_role.execution.assume_role_policy
}
resource "aws_iam_role_policy" "storage" {
  for_each = toset(["api", "worker"])
  role     = aws_iam_role.task[each.key].id
  policy   = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = ["${aws_s3_bucket.sources.arn}/*"] }, { Effect = "Allow", Action = ["s3:ListBucket"], Resource = [aws_s3_bucket.sources.arn] }] })
}
locals {
  secret_keys = ["DATABASE_URL", "REDIS_URL", "OPENAI_API_KEY", "CHAT_MODEL", "PINECONE_API_KEY", "PINECONE_HOST", "OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL", "CLAMD_HOST", "SCAN_MODE"]
  services = {
    api    = { image = var.api_image, port = 8000, command = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] }
    worker = { image = var.api_image, port = 8000, command = ["python", "-m", "app.worker"] }
    web    = { image = var.web_image, port = 3000, command = ["node", "server.js"] }
  }
}
resource "aws_ecs_task_definition" "app" {
  for_each                 = local.services
  family                   = "${var.name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task[each.key].arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }
  container_definitions = jsonencode([{
    name             = each.key, image = each.value.image, essential = true, command = each.value.command,
    portMappings     = each.key == "worker" ? [] : [{ containerPort = each.value.port, protocol = "tcp" }],
    environment      = each.key == "web" ? [] : [{ name = "ENVIRONMENT", value = "staging" }, { name = "PROVIDER", value = "live" }, { name = "STORAGE", value = "s3" }, { name = "S3_BUCKET", value = aws_s3_bucket.sources.id }, { name = "AWS_REGION", value = var.region }, { name = "CORS_ORIGIN", value = var.web_origin }],
    secrets          = each.key == "web" ? [] : [for key in local.secret_keys : { name = key, valueFrom = "${var.runtime_secret_arn}:${key}::" }],
    logConfiguration = { logDriver = "awslogs", options = { "awslogs-group" = aws_cloudwatch_log_group.app.name, "awslogs-region" = var.region, "awslogs-stream-prefix" = each.key } }
  }])
}
resource "aws_ecs_service" "app" {
  for_each        = local.services
  name            = "${var.name}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app[each.key].arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  dynamic "load_balancer" {
    for_each = each.key == "worker" ? [] : [each.key]
    content {
      target_group_arn = each.key == "api" ? var.api_target_group_arn : var.web_target_group_arn
      container_name   = each.key
      container_port   = each.value.port
    }
  }
}
