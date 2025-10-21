# Input Variables for ClinChat-RAG Infrastructure

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "clinchat-rag"
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "platform-team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "engineering"
}

#=====================================
# Network Configuration
#=====================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_count" {
  description = "Number of public subnets"
  type        = number
  default     = 2
  validation {
    condition     = var.public_subnet_count >= 2
    error_message = "Must have at least 2 public subnets for high availability."
  }
}

variable "private_subnet_count" {
  description = "Number of private subnets"
  type        = number
  default     = 2
  validation {
    condition     = var.private_subnet_count >= 2
    error_message = "Must have at least 2 private subnets for high availability."
  }
}

variable "database_subnet_count" {
  description = "Number of database subnets"
  type        = number
  default     = 2
  validation {
    condition     = var.database_subnet_count >= 2
    error_message = "Must have at least 2 database subnets for RDS Multi-AZ."
  }
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

#=====================================
# EKS Configuration
#=====================================

variable "eks_cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.28"
}

variable "eks_node_instance_types" {
  description = "EC2 instance types for EKS node group"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
}

variable "eks_node_desired_capacity" {
  description = "Desired number of EKS worker nodes"
  type        = number
  default     = 3
}

variable "eks_node_min_capacity" {
  description = "Minimum number of EKS worker nodes"
  type        = number
  default     = 2
}

variable "eks_node_max_capacity" {
  description = "Maximum number of EKS worker nodes"
  type        = number
  default     = 10
}

variable "eks_node_disk_size" {
  description = "Disk size for EKS worker nodes (GB)"
  type        = number
  default     = 100
}

#=====================================
# RDS Configuration
#=====================================

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage (GB)"
  type        = number
  default     = 100
}

variable "rds_max_allocated_storage" {
  description = "RDS maximum allocated storage (GB)"
  type        = number
  default     = 1000
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 30
}

variable "rds_backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "rds_maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

#=====================================
# OpenSearch Configuration
#=====================================

variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.medium.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 3
}

variable "opensearch_dedicated_master" {
  description = "Enable dedicated master nodes"
  type        = bool
  default     = true
}

variable "opensearch_master_instance_type" {
  description = "OpenSearch master instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_master_instance_count" {
  description = "Number of OpenSearch master instances"
  type        = number
  default     = 3
}

variable "opensearch_volume_size" {
  description = "EBS volume size for OpenSearch (GB)"
  type        = number
  default     = 100
}

variable "opensearch_volume_type" {
  description = "EBS volume type for OpenSearch"
  type        = string
  default     = "gp3"
}

#=====================================
# Security Configuration
#=====================================

variable "enable_waf" {
  description = "Enable AWS WAF for ALB"
  type        = bool
  default     = true
}

variable "enable_shield" {
  description = "Enable AWS Shield Advanced"
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

#=====================================
# Monitoring Configuration
#=====================================

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring for RDS"
  type        = bool
  default     = true
}

variable "monitoring_interval" {
  description = "Enhanced monitoring interval in seconds"
  type        = number
  default     = 60
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = true
}

variable "performance_insights_retention" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7
}

#=====================================
# Application Configuration
#=====================================

variable "app_domain" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "api_version" {
  description = "API version to deploy"
  type        = string
  default     = "latest"
}

variable "app_replicas" {
  description = "Number of application replicas"
  type        = number
  default     = 3
}

variable "app_cpu_request" {
  description = "CPU request for application pods"
  type        = string
  default     = "100m"
}

variable "app_memory_request" {
  description = "Memory request for application pods"
  type        = string
  default     = "256Mi"
}

variable "app_cpu_limit" {
  description = "CPU limit for application pods"
  type        = string
  default     = "500m"
}

variable "app_memory_limit" {
  description = "Memory limit for application pods"
  type        = string
  default     = "512Mi"
}

#=====================================
# HIPAA Compliance Configuration
#=====================================

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for audit logging"
  type        = bool
  default     = true
}

variable "cloudtrail_s3_bucket" {
  description = "S3 bucket for CloudTrail logs"
  type        = string
  default     = ""
}

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "config_s3_bucket" {
  description = "S3 bucket for AWS Config"
  type        = string
  default     = ""
}

variable "enable_guardduty" {
  description = "Enable GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_securityhub" {
  description = "Enable Security Hub for security posture management"
  type        = bool
  default     = true
}

#=====================================
# Backup and Disaster Recovery
#=====================================

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = false
}

variable "backup_region" {
  description = "Region for cross-region backup replication"
  type        = string
  default     = "us-west-2"
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for RDS"
  type        = bool
  default     = true
}

#=====================================
# Cost Optimization
#=====================================

variable "enable_spot_instances" {
  description = "Enable spot instances for EKS node groups (non-production)"
  type        = bool
  default     = false
}

variable "spot_instance_types" {
  description = "EC2 instance types for spot instances"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge", "m5.large", "m5.xlarge"]
}

variable "enable_fargate" {
  description = "Enable Fargate for EKS"
  type        = bool
  default     = false
}