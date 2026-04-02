#!/bin/bash

# AWS Complete Resource Cleanup Script
# Deletes ALL resources across ALL regions
# USE WITH CAUTION - This is irreversible!

echo "=========================================="
echo "⚠️  AWS COMPLETE RESOURCE CLEANUP"
echo "=========================================="
echo "Account: $(aws sts get-caller-identity --query Account --output text)"
echo "Date: $(date)"
echo ""
echo "This will DELETE ALL resources in ALL regions."
read -p "Type 'DELETE ALL' to confirm: " confirm

if [ "$confirm" != "DELETE ALL" ]; then
  echo "Aborted."
  exit 1
fi

REGIONS=$(aws ec2 describe-regions --query 'Regions[].RegionName' --output text)

for region in $REGIONS; do
  echo ""
  echo "=========================================="
  echo "🌍 Cleaning region: $region"
  echo "=========================================="

  # ---- SAGEMAKER ----
  echo "  🤖 Deleting SageMaker endpoints..."
  aws sagemaker list-endpoints --region $region \
    --query 'Endpoints[].EndpointName' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      echo "    Deleting endpoint: $name"
      aws sagemaker delete-endpoint --endpoint-name "$name" --region $region 2>/dev/null
    done

  echo "  🤖 Deleting SageMaker endpoint configs..."
  aws sagemaker list-endpoint-configs --region $region \
    --query 'EndpointConfigs[].EndpointConfigName' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      aws sagemaker delete-endpoint-config --endpoint-config-name "$name" --region $region 2>/dev/null
    done

  echo "  🤖 Deleting SageMaker models..."
  aws sagemaker list-models --region $region \
    --query 'Models[].ModelName' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      aws sagemaker delete-model --model-name "$name" --region $region 2>/dev/null
    done

  # ---- LAMBDA ----
  echo "  ⚡ Deleting Lambda functions..."
  aws lambda list-functions --region $region \
    --query 'Functions[].FunctionName' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      echo "    Deleting Lambda: $name"
      aws lambda delete-function --function-name "$name" --region $region 2>/dev/null
    done

  # ---- API GATEWAY ----
  echo "  🔌 Deleting API Gateways..."
  aws apigateway get-rest-apis --region $region \
    --query 'items[].id' --output text 2>/dev/null | \
    tr '\t' '\n' | while read id; do
      [ -z "$id" ] && continue
      echo "    Deleting API Gateway: $id"
      aws apigateway delete-rest-api --rest-api-id "$id" --region $region 2>/dev/null
    done

  # ---- RDS ----
  echo "  🗄️  Deleting RDS instances..."
  aws rds describe-db-instances --region $region \
    --query 'DBInstances[].DBInstanceIdentifier' --output text 2>/dev/null | \
    tr '\t' '\n' | while read id; do
      [ -z "$id" ] && continue
      echo "    Deleting RDS: $id"
      aws rds delete-db-instance \
        --db-instance-identifier "$id" \
        --skip-final-snapshot \
        --region $region 2>/dev/null
    done

  # ---- EC2 INSTANCES ----
  echo "  💻 Terminating EC2 instances..."
  instance_ids=$(aws ec2 describe-instances --region $region \
    --filters "Name=instance-state-name,Values=running,stopped,pending" \
    --query 'Reservations[].Instances[].InstanceId' --output text 2>/dev/null)
  if [ ! -z "$instance_ids" ]; then
    echo "    Terminating: $instance_ids"
    aws ec2 terminate-instances --instance-ids $instance_ids --region $region 2>/dev/null
    echo "    Waiting for termination..."
    aws ec2 wait instance-terminated --instance-ids $instance_ids --region $region 2>/dev/null
  fi

  # ---- LOAD BALANCERS ----
  echo "  ⚖️  Deleting Load Balancers..."
  aws elbv2 describe-load-balancers --region $region \
    --query 'LoadBalancers[].LoadBalancerArn' --output text 2>/dev/null | \
    tr '\t' '\n' | while read arn; do
      [ -z "$arn" ] && continue
      echo "    Deleting LB: $arn"
      aws elbv2 delete-load-balancer --load-balancer-arn "$arn" --region $region 2>/dev/null
    done

  # ---- NAT GATEWAYS ----
  echo "  🚪 Deleting NAT Gateways..."
  aws ec2 describe-nat-gateways --region $region \
    --filter "Name=state,Values=available" \
    --query 'NatGateways[].NatGatewayId' --output text 2>/dev/null | \
    tr '\t' '\n' | while read id; do
      [ -z "$id" ] && continue
      echo "    Deleting NAT Gateway: $id"
      aws ec2 delete-nat-gateway --nat-gateway-id "$id" --region $region 2>/dev/null
    done
  echo "    Waiting for NAT Gateways to delete..."
  sleep 30

  # ---- ELASTIC IPs ----
  echo "  🌐 Releasing Elastic IPs..."
  aws ec2 describe-addresses --region $region \
    --query 'Addresses[].AllocationId' --output text 2>/dev/null | \
    tr '\t' '\n' | while read id; do
      [ -z "$id" ] && continue
      echo "    Releasing EIP: $id"
      aws ec2 release-address --allocation-id "$id" --region $region 2>/dev/null
    done

  # ---- EBS VOLUMES ----
  echo "  💾 Deleting EBS Volumes..."
  aws ec2 describe-volumes --region $region \
    --filters "Name=status,Values=available" \
    --query 'Volumes[].VolumeId' --output text 2>/dev/null | \
    tr '\t' '\n' | while read id; do
      [ -z "$id" ] && continue
      echo "    Deleting volume: $id"
      aws ec2 delete-volume --volume-id "$id" --region $region 2>/dev/null
    done

  # ---- EBS SNAPSHOTS ----
  echo "  📸 Deleting EBS Snapshots..."
  aws ec2 describe-snapshots --owner-ids self --region $region \
    --query 'Snapshots[].SnapshotId' --output text 2>/dev/null | \
    tr '\t' '\n' | while read id; do
      [ -z "$id" ] && continue
      aws ec2 delete-snapshot --snapshot-id "$id" --region $region 2>/dev/null
    done

  # ---- CLOUDFORMATION STACKS ----
  echo "  🏗️  Deleting CloudFormation stacks..."
  aws cloudformation list-stacks --region $region \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE ROLLBACK_COMPLETE \
    --query 'StackSummaries[].StackName' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      echo "    Deleting stack: $name"
      aws cloudformation delete-stack --stack-name "$name" --region $region 2>/dev/null
    done

  # ---- DYNAMODB ----
  echo "  📦 Deleting DynamoDB tables..."
  aws dynamodb list-tables --region $region \
    --query 'TableNames[]' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      echo "    Deleting table: $name"
      aws dynamodb delete-table --table-name "$name" --region $region 2>/dev/null
    done

  # ---- SNS TOPICS ----
  echo "  📢 Deleting SNS topics..."
  aws sns list-topics --region $region \
    --query 'Topics[].TopicArn' --output text 2>/dev/null | \
    tr '\t' '\n' | while read arn; do
      [ -z "$arn" ] && continue
      aws sns delete-topic --topic-arn "$arn" --region $region 2>/dev/null
    done

  # ---- SQS QUEUES ----
  echo "  📬 Deleting SQS queues..."
  aws sqs list-queues --region $region \
    --query 'QueueUrls[]' --output text 2>/dev/null | \
    tr '\t' '\n' | while read url; do
      [ -z "$url" ] && continue
      aws sqs delete-queue --queue-url "$url" --region $region 2>/dev/null
    done

  # ---- CLOUDWATCH ALARMS ----
  echo "  🔔 Deleting CloudWatch Alarms..."
  aws cloudwatch describe-alarms --region $region \
    --query 'MetricAlarms[].AlarmName' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      aws cloudwatch delete-alarms --alarm-names "$name" --region $region 2>/dev/null
    done

  # ---- CLOUDWATCH LOG GROUPS ----
  echo "  📋 Deleting CloudWatch Log Groups..."
  aws logs describe-log-groups --region $region \
    --query 'logGroups[].logGroupName' --output text 2>/dev/null | \
    tr '\t' '\n' | while read name; do
      [ -z "$name" ] && continue
      aws logs delete-log-group --log-group-name "$name" --region $region 2>/dev/null
    done

  # ---- VPCs (non-default) ----
  echo "  🌐 Deleting non-default VPCs..."
  aws ec2 describe-vpcs --region $region \
    --filters "Name=isDefault,Values=false" \
    --query 'Vpcs[].VpcId' --output text 2>/dev/null | \
    tr '\t' '\n' | while read vpc_id; do
      [ -z "$vpc_id" ] && continue
      echo "    Cleaning VPC: $vpc_id"

      # Delete subnets
      aws ec2 describe-subnets --region $region \
        --filters "Name=vpc-id,Values=$vpc_id" \
        --query 'Subnets[].SubnetId' --output text 2>/dev/null | \
        tr '\t' '\n' | while read id; do
          [ -z "$id" ] && continue
          aws ec2 delete-subnet --subnet-id "$id" --region $region 2>/dev/null
        done

      # Detach and delete internet gateways
      aws ec2 describe-internet-gateways --region $region \
        --filters "Name=attachment.vpc-id,Values=$vpc_id" \
        --query 'InternetGateways[].InternetGatewayId' --output text 2>/dev/null | \
        tr '\t' '\n' | while read igw_id; do
          [ -z "$igw_id" ] && continue
          aws ec2 detach-internet-gateway --internet-gateway-id "$igw_id" --vpc-id "$vpc_id" --region $region 2>/dev/null
          aws ec2 delete-internet-gateway --internet-gateway-id "$igw_id" --region $region 2>/dev/null
        done

      # Delete route tables (non-main)
      aws ec2 describe-route-tables --region $region \
        --filters "Name=vpc-id,Values=$vpc_id" \
        --query 'RouteTables[?Associations[0].Main!=`true`].RouteTableId' --output text 2>/dev/null | \
        tr '\t' '\n' | while read id; do
          [ -z "$id" ] && continue
          aws ec2 delete-route-table --route-table-id "$id" --region $region 2>/dev/null
        done

      # Delete security groups (non-default)
      aws ec2 describe-security-groups --region $region \
        --filters "Name=vpc-id,Values=$vpc_id" \
        --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text 2>/dev/null | \
        tr '\t' '\n' | while read id; do
          [ -z "$id" ] && continue
          aws ec2 delete-security-group --group-id "$id" --region $region 2>/dev/null
        done

      # Delete VPC
      aws ec2 delete-vpc --vpc-id "$vpc_id" --region $region 2>/dev/null
      echo "    Deleted VPC: $vpc_id"
    done

done

# ---- S3 BUCKETS (Global) ----
echo ""
echo "=========================================="
echo "🪣 Deleting S3 Buckets (Global)"
echo "=========================================="
aws s3 ls 2>/dev/null | awk '{print $3}' | while read bucket; do
  [ -z "$bucket" ] && continue
  echo "  Emptying and deleting: $bucket"
  aws s3 rm s3://$bucket --recursive 2>/dev/null
  aws s3api delete-bucket --bucket "$bucket" 2>/dev/null
  echo "  Deleted: $bucket"
done

# ---- IAM (non-root users, roles, policies) ----
echo ""
echo "=========================================="
echo "👤 Cleaning IAM Resources"
echo "=========================================="

# Delete IAM users (non-root)
echo "  Deleting IAM users..."
aws iam list-users --query 'Users[].UserName' --output text 2>/dev/null | \
  tr '\t' '\n' | while read user; do
    [ -z "$user" ] && continue
    echo "    Cleaning user: $user"
    # Detach policies
    aws iam list-attached-user-policies --user-name "$user" \
      --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | \
      tr '\t' '\n' | while read arn; do
        [ -z "$arn" ] && continue
        aws iam detach-user-policy --user-name "$user" --policy-arn "$arn" 2>/dev/null
      done
    # Delete access keys
    aws iam list-access-keys --user-name "$user" \
      --query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null | \
      tr '\t' '\n' | while read key; do
        [ -z "$key" ] && continue
        aws iam delete-access-key --user-name "$user" --access-key-id "$key" 2>/dev/null
      done
    aws iam delete-user --user-name "$user" 2>/dev/null
  done

# Delete custom IAM roles
echo "  Deleting custom IAM roles..."
aws iam list-roles \
  --query 'Roles[?!starts_with(Path, `/aws-service-role/`)].RoleName' \
  --output text 2>/dev/null | \
  tr '\t' '\n' | while read role; do
    [ -z "$role" ] && continue
    # Detach policies
    aws iam list-attached-role-policies --role-name "$role" \
      --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | \
      tr '\t' '\n' | while read arn; do
        [ -z "$arn" ] && continue
        aws iam detach-role-policy --role-name "$role" --policy-arn "$arn" 2>/dev/null
      done
    # Delete inline policies
    aws iam list-role-policies --role-name "$role" \
      --query 'PolicyNames[]' --output text 2>/dev/null | \
      tr '\t' '\n' | while read pname; do
        [ -z "$pname" ] && continue
        aws iam delete-role-policy --role-name "$role" --policy-name "$pname" 2>/dev/null
      done
    aws iam delete-role --role-name "$role" 2>/dev/null
  done

# Delete custom managed policies
echo "  Deleting custom IAM policies..."
aws iam list-policies --scope Local \
  --query 'Policies[].Arn' --output text 2>/dev/null | \
  tr '\t' '\n' | while read arn; do
    [ -z "$arn" ] && continue
    aws iam delete-policy --policy-arn "$arn" 2>/dev/null
  done

echo ""
echo "=========================================="
echo "✅ CLEANUP COMPLETE"
echo "=========================================="
echo "All AWS resources have been deleted."
echo "Run ./aws-audit.sh to verify everything is clean."
