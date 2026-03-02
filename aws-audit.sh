#!/bin/bash

# AWS Account Audit Script
# Checks all regions for resources and estimates costs

set -e

echo "=========================================="
echo "AWS Account Audit Report"
echo "Date: $(date)"
echo "Account: $(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo 'Not configured')"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Run 'aws configure' first."
    exit 1
fi

# Get all enabled regions
echo "📍 Getting all AWS regions..."
REGIONS=$(aws ec2 describe-regions --query 'Regions[].RegionName' --output text)
echo "Found $(echo $REGIONS | wc -w) regions"
echo ""

# Cost Analysis
echo "=========================================="
echo "💰 COST ANALYSIS"
echo "=========================================="

echo "Current month costs by service:"
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' \
  --output table 2>/dev/null || echo "Unable to fetch cost data"

echo ""
echo "Current month costs by region:"
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=REGION \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' \
  --output table 2>/dev/null || echo "Unable to fetch regional cost data"

echo ""

# Resource Audit by Region
echo "=========================================="
echo "🔍 RESOURCE AUDIT BY REGION"
echo "=========================================="

TOTAL_EC2=0
TOTAL_RDS=0
TOTAL_LAMBDA=0
TOTAL_EBS=0
TOTAL_EIPS=0
TOTAL_NATS=0
TOTAL_ALBS=0
TOTAL_SAGEMAKER=0

for region in $REGIONS; do
  HAS_RESOURCES=false
  REGION_OUTPUT=""
  
  # EC2 Instances
  instances=$(aws ec2 describe-instances --region $region \
    --query 'Reservations[].Instances[?State.Name!=`terminated`].[InstanceId,InstanceType,State.Name,LaunchTime]' \
    --output text 2>/dev/null)
  if [ ! -z "$instances" ]; then
    count=$(echo "$instances" | wc -l)
    TOTAL_EC2=$((TOTAL_EC2 + count))
    HAS_RESOURCES=true
    REGION_OUTPUT="${REGION_OUTPUT}\n  💻 EC2 Instances ($count):\n$instances\n"
  fi
  
  # RDS Databases
  rds=$(aws rds describe-db-instances --region $region \
    --query 'DBInstances[].[DBInstanceIdentifier,DBInstanceClass,DBInstanceStatus,Engine]' \
    --output text 2>/dev/null)
  if [ ! -z "$rds" ]; then
    count=$(echo "$rds" | wc -l)
    TOTAL_RDS=$((TOTAL_RDS + count))
    HAS_RESOURCES=true
    REGION_OUTPUT="${REGION_OUTPUT}\n  🗄️  RDS Instances ($count):\n$rds\n"
  fi
  
  # Lambda Functions
  lambdas=$(aws lambda list-functions --region $region \
    --query 'Functions[].[FunctionName,Runtime,MemorySize,LastModified]' \
    --output text 2>/dev/null)
  if [ ! -z "$lambdas" ]; then
    count=$(echo "$lambdas" | wc -l)
    TOTAL_LAMBDA=$((TOTAL_LAMBDA + count))
    HAS_RESOURCES=true
    REGION_OUTPUT="${REGION_OUTPUT}\n  ⚡ Lambda Functions ($count):\n$lambdas\n"
  fi
  
  # EBS Volumes
  volumes=$(aws ec2 describe-volumes --region $region \
    --query 'Volumes[?State!=`deleted`].[VolumeId,Size,State,VolumeType,Attachments[0].InstanceId]' \
    --output text 2>/dev/null)
  if [ ! -z "$volumes" ]; then
    count=$(echo "$volumes" | wc -l)
    TOTAL_EBS=$((TOTAL_EBS + count))
    HAS_RESOURCES=true
    REGION_OUTPUT="${REGION_OUTPUT}\n  💾 EBS Volumes ($count):\n$volumes\n"
  fi
  
  # Elastic IPs (unattached = costing money!)
  eips=$(aws ec2 describe-addresses --region $region \
    --query 'Addresses[].[PublicIp,AllocationId,AssociationId]' \
    --output text 2>/dev/null)
  if [ ! -z "$eips" ]; then
    count=$(echo "$eips" | wc -l)
    TOTAL_EIPS=$((TOTAL_EIPS + count))
    unattached=$(echo "$eips" | grep "None$" | wc -l)
    HAS_RESOURCES=true
    if [ $unattached -gt 0 ]; then
      REGION_OUTPUT="${REGION_OUTPUT}\n  ⚠️  Elastic IPs ($count, $unattached UNATTACHED - DELETE THESE!):\n$eips\n"
    else
      REGION_OUTPUT="${REGION_OUTPUT}\n  🌐 Elastic IPs ($count, all attached):\n$eips\n"
    fi
  fi
  
  # NAT Gateways (expensive!)
  nats=$(aws ec2 describe-nat-gateways --region $region \
    --query 'NatGateways[?State==`available`].[NatGatewayId,VpcId,State]' \
    --output text 2>/dev/null)
  if [ ! -z "$nats" ]; then
    count=$(echo "$nats" | wc -l)
    TOTAL_NATS=$((TOTAL_NATS + count))
    HAS_RESOURCES=true
    REGION_OUTPUT="${REGION_OUTPUT}\n  🚪 NAT Gateways ($count - \$0.045/hour each!):\n$nats\n"
  fi
  
  # Load Balancers
  albs=$(aws elbv2 describe-load-balancers --region $region \
    --query 'LoadBalancers[].[LoadBalancerName,Type,State.Code,CreatedTime]' \
    --output text 2>/dev/null)
  if [ ! -z "$albs" ]; then
    count=$(echo "$albs" | wc -l)
    TOTAL_ALBS=$((TOTAL_ALBS + count))
    HAS_RESOURCES=true
    REGION_OUTPUT="${REGION_OUTPUT}\n  ⚖️  Load Balancers ($count):\n$albs\n"
  fi
  
  # SageMaker Endpoints (very expensive!)
  endpoints=$(aws sagemaker list-endpoints --region $region \
    --query 'Endpoints[].[EndpointName,EndpointStatus,CreationTime]' \
    --output text 2>/dev/null)
  if [ ! -z "$endpoints" ]; then
    count=$(echo "$endpoints" | wc -l)
    TOTAL_SAGEMAKER=$((TOTAL_SAGEMAKER + count))
    HAS_RESOURCES=true
    REGION_OUTPUT="${REGION_OUTPUT}\n  🤖 SageMaker Endpoints ($count - VERY EXPENSIVE!):\n$endpoints\n"
  fi
  
  # Print region info if it has resources
  if [ "$HAS_RESOURCES" = true ]; then
    echo ""
    echo "--- 📍 Region: $region ---"
    echo -e "$REGION_OUTPUT"
  fi
done

# S3 Buckets (global service)
echo ""
echo "=========================================="
echo "🪣 S3 BUCKETS (Global)"
echo "=========================================="
buckets=$(aws s3 ls 2>/dev/null)
if [ ! -z "$buckets" ]; then
  echo "$buckets"
  echo ""
  echo "Bucket sizes:"
  aws s3 ls | awk '{print $3}' | while read bucket; do
    size=$(aws s3 ls s3://$bucket --recursive --summarize 2>/dev/null | grep "Total Size" | awk '{print $3}')
    if [ ! -z "$size" ]; then
      size_mb=$((size / 1024 / 1024))
      echo "  $bucket: ${size_mb} MB"
    fi
  done
else
  echo "No S3 buckets found"
fi

# Summary
echo ""
echo "=========================================="
echo "📊 SUMMARY"
echo "=========================================="
echo "Total EC2 Instances: $TOTAL_EC2"
echo "Total RDS Instances: $TOTAL_RDS"
echo "Total Lambda Functions: $TOTAL_LAMBDA"
echo "Total EBS Volumes: $TOTAL_EBS"
echo "Total Elastic IPs: $TOTAL_EIPS"
echo "Total NAT Gateways: $TOTAL_NATS (💰 ~\$$(echo "$TOTAL_NATS * 0.045 * 730" | bc) per month)"
echo "Total Load Balancers: $TOTAL_ALBS"
echo "Total SageMaker Endpoints: $TOTAL_SAGEMAKER"

echo ""
echo "=========================================="
echo "⚠️  RECOMMENDED DELETIONS"
echo "=========================================="
echo "1. Check for unattached Elastic IPs (charged hourly)"
echo "2. Delete unused SageMaker endpoints (very expensive)"
echo "3. Remove NAT Gateways if not needed"
echo "4. Clean up old EBS volumes and snapshots"
echo "5. Delete unused Load Balancers"
echo "6. Set S3 lifecycle policies for old data"
echo ""
echo "Run 'aws-cleanup.sh' to interactively delete resources"
echo ""
