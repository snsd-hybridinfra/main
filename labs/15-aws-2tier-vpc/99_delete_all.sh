#!/bin/bash
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -euo pipefail
if [[ "${CONFIRM_LAB_DESTROY:-}" != "YES" ]]; then
  echo "Cleanup blocked. Review scoped AWS resources, then set CONFIRM_LAB_DESTROY=YES." >&2
  exit 2
fi

REGION="ap-northeast-2"
PROJECT="ansible-vpc-lab"
OWNER="jjh"
KEY_NAME="ansible-jjh-key"

echo "======================================"
echo "AWS Ansible Lab Cleanup"
echo "======================================"
echo "Region : $REGION"
echo "Project: $PROJECT"
echo "Owner  : $OWNER"
echo "======================================"

tag_filter_project="Name=tag:Project,Values=${PROJECT}"
tag_filter_owner="Name=tag:Owner,Values=${OWNER}"

echo ""
echo "[1] Delete ALB Listeners and Load Balancers"

ALB_ARNS=$(aws elbv2 describe-load-balancers \
  --region "$REGION" \
  --query "LoadBalancers[?contains(LoadBalancerName, 'ansible-jjh')].LoadBalancerArn" \
  --output text 2>/dev/null || true)

if [ -n "$ALB_ARNS" ]; then
  for ALB_ARN in $ALB_ARNS; do
    echo "Deleting ALB: $ALB_ARN"

    LISTENER_ARNS=$(aws elbv2 describe-listeners \
      --region "$REGION" \
      --load-balancer-arn "$ALB_ARN" \
      --query "Listeners[].ListenerArn" \
      --output text 2>/dev/null || true)

    for LISTENER_ARN in $LISTENER_ARNS; do
      echo "Deleting Listener: $LISTENER_ARN"
      aws elbv2 delete-listener \
        --region "$REGION" \
        --listener-arn "$LISTENER_ARN" || true
    done

    aws elbv2 delete-load-balancer \
      --region "$REGION" \
      --load-balancer-arn "$ALB_ARN" || true
  done

  echo "Waiting for ALB deletion..."
  aws elbv2 wait load-balancers-deleted \
    --region "$REGION" \
    --load-balancer-arns $ALB_ARNS || true
else
  echo "No ALB found"
fi

echo ""
echo "[2] Delete Target Groups"

TG_ARNS=$(aws elbv2 describe-target-groups \
  --region "$REGION" \
  --query "TargetGroups[?contains(TargetGroupName, 'ansible-jjh')].TargetGroupArn" \
  --output text 2>/dev/null || true)

if [ -n "$TG_ARNS" ]; then
  for TG_ARN in $TG_ARNS; do
    echo "Deleting Target Group: $TG_ARN"
    aws elbv2 delete-target-group \
      --region "$REGION" \
      --target-group-arn "$TG_ARN" || true
  done
else
  echo "No Target Group found"
fi

echo ""
echo "[3] Terminate EC2 Instances"

INSTANCE_IDS=$(aws ec2 describe-instances \
  --region "$REGION" \
  --filters "$tag_filter_project" "$tag_filter_owner" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text 2>/dev/null || true)

if [ -n "$INSTANCE_IDS" ]; then
  echo "Terminating instances: $INSTANCE_IDS"

  aws ec2 terminate-instances \
    --region "$REGION" \
    --instance-ids $INSTANCE_IDS >/dev/null || true

  echo "Waiting for EC2 termination..."
  aws ec2 wait instance-terminated \
    --region "$REGION" \
    --instance-ids $INSTANCE_IDS || true
else
  echo "No EC2 instances found"
fi

echo ""
echo "[4] Find VPCs"

VPC_IDS=$(aws ec2 describe-vpcs \
  --region "$REGION" \
  --filters "$tag_filter_project" "$tag_filter_owner" \
  --query "Vpcs[].VpcId" \
  --output text 2>/dev/null || true)

if [ -z "$VPC_IDS" ]; then
  echo "No VPC found"
else
  echo "VPCs found: $VPC_IDS"
fi

for VPC_ID in $VPC_IDS; do
  echo ""
  echo "======================================"
  echo "Cleaning VPC: $VPC_ID"
  echo "======================================"

  echo ""
  echo "[4-1] Delete NAT Gateways"

  NAT_IDS=$(aws ec2 describe-nat-gateways \
    --region "$REGION" \
    --filter "Name=vpc-id,Values=$VPC_ID" \
    --query "NatGateways[?State!='deleted'].NatGatewayId" \
    --output text 2>/dev/null || true)

  if [ -n "$NAT_IDS" ]; then
    for NAT_ID in $NAT_IDS; do
      echo "Deleting NAT Gateway: $NAT_ID"

      ALLOC_IDS=$(aws ec2 describe-nat-gateways \
        --region "$REGION" \
        --nat-gateway-ids "$NAT_ID" \
        --query "NatGateways[0].NatGatewayAddresses[].AllocationId" \
        --output text 2>/dev/null || true)

      aws ec2 delete-nat-gateway \
        --region "$REGION" \
        --nat-gateway-id "$NAT_ID" >/dev/null || true

      echo "Waiting for NAT Gateway deletion: $NAT_ID"

      for i in {1..40}; do
        NAT_STATE=$(aws ec2 describe-nat-gateways \
          --region "$REGION" \
          --nat-gateway-ids "$NAT_ID" \
          --query "NatGateways[0].State" \
          --output text 2>/dev/null || echo "deleted")

        echo "NAT state: $NAT_STATE"

        if [ "$NAT_STATE" = "deleted" ] || [ "$NAT_STATE" = "None" ]; then
          break
        fi

        sleep 15
      done

      if [ -n "$ALLOC_IDS" ]; then
        for ALLOC_ID in $ALLOC_IDS; do
          echo "Releasing EIP allocation: $ALLOC_ID"
          aws ec2 release-address \
            --region "$REGION" \
            --allocation-id "$ALLOC_ID" || true
        done
      fi
    done
  else
    echo "No NAT Gateway found"
  fi

  echo ""
  echo "[4-2] Delete non-main Route Tables"

  RTB_IDS=$(aws ec2 describe-route-tables \
    --region "$REGION" \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "RouteTables[?Associations[?Main!=\`true\`]].RouteTableId" \
    --output text 2>/dev/null || true)

  if [ -n "$RTB_IDS" ]; then
    for RTB_ID in $RTB_IDS; do
      echo "Processing Route Table: $RTB_ID"

      ASSOC_IDS=$(aws ec2 describe-route-tables \
        --region "$REGION" \
        --route-table-ids "$RTB_ID" \
        --query "RouteTables[0].Associations[?Main!=\`true\`].RouteTableAssociationId" \
        --output text 2>/dev/null || true)

      for ASSOC_ID in $ASSOC_IDS; do
        echo "Disassociating Route Table Association: $ASSOC_ID"
        aws ec2 disassociate-route-table \
          --region "$REGION" \
          --association-id "$ASSOC_ID" || true
      done

      echo "Deleting Route Table: $RTB_ID"
      aws ec2 delete-route-table \
        --region "$REGION" \
        --route-table-id "$RTB_ID" || true
    done
  else
    echo "No non-main Route Table found"
  fi

  echo ""
  echo "[4-3] Detach and Delete Internet Gateways"

  IGW_IDS=$(aws ec2 describe-internet-gateways \
    --region "$REGION" \
    --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
    --query "InternetGateways[].InternetGatewayId" \
    --output text 2>/dev/null || true)

  if [ -n "$IGW_IDS" ]; then
    for IGW_ID in $IGW_IDS; do
      echo "Detaching IGW: $IGW_ID"
      aws ec2 detach-internet-gateway \
        --region "$REGION" \
        --internet-gateway-id "$IGW_ID" \
        --vpc-id "$VPC_ID" || true

      echo "Deleting IGW: $IGW_ID"
      aws ec2 delete-internet-gateway \
        --region "$REGION" \
        --internet-gateway-id "$IGW_ID" || true
    done
  else
    echo "No IGW found"
  fi

  echo ""
  echo "[4-4] Delete Subnets"

  SUBNET_IDS=$(aws ec2 describe-subnets \
    --region "$REGION" \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "Subnets[].SubnetId" \
    --output text 2>/dev/null || true)

  if [ -n "$SUBNET_IDS" ]; then
    for SUBNET_ID in $SUBNET_IDS; do
      echo "Deleting Subnet: $SUBNET_ID"
      aws ec2 delete-subnet \
        --region "$REGION" \
        --subnet-id "$SUBNET_ID" || true
    done
  else
    echo "No Subnet found"
  fi

  echo ""
  echo "[4-5] Delete Security Groups except default"

  SG_IDS=$(aws ec2 describe-security-groups \
    --region "$REGION" \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "SecurityGroups[?GroupName!='default'].GroupId" \
    --output text 2>/dev/null || true)

  if [ -n "$SG_IDS" ]; then
    for SG_ID in $SG_IDS; do
      echo "Revoking SG references for: $SG_ID"

      aws ec2 revoke-security-group-ingress \
        --region "$REGION" \
        --group-id "$SG_ID" \
        --ip-permissions "$(aws ec2 describe-security-groups \
          --region "$REGION" \
          --group-ids "$SG_ID" \
          --query "SecurityGroups[0].IpPermissions" \
          --output json)" 2>/dev/null || true

      aws ec2 revoke-security-group-egress \
        --region "$REGION" \
        --group-id "$SG_ID" \
        --ip-permissions "$(aws ec2 describe-security-groups \
          --region "$REGION" \
          --group-ids "$SG_ID" \
          --query "SecurityGroups[0].IpPermissionsEgress" \
          --output json)" 2>/dev/null || true
    done

    sleep 5

    for SG_ID in $SG_IDS; do
      echo "Deleting Security Group: $SG_ID"
      aws ec2 delete-security-group \
        --region "$REGION" \
        --group-id "$SG_ID" || true
    done
  else
    echo "No custom Security Group found"
  fi

  echo ""
  echo "[4-6] Delete VPC"

  echo "Deleting VPC: $VPC_ID"
  aws ec2 delete-vpc \
    --region "$REGION" \
    --vpc-id "$VPC_ID" || true
done

echo ""
echo "[5] Delete Key Pair"

aws ec2 delete-key-pair \
  --region "$REGION" \
  --key-name "$KEY_NAME" 2>/dev/null || true

echo "Deleted AWS Key Pair if it existed: $KEY_NAME"

echo ""
echo "[6] Delete local generated files"

rm -f $LAB_ROOT/ansible-jjh-key
rm -f $LAB_ROOT/ansible-jjh-key.pub
rm -f $LAB_ROOT/inventory.ini

echo "Deleted local key and inventory files if they existed"

echo ""
echo "[7] Final verification"

REMAINING_VPCS=$(aws ec2 describe-vpcs \
  --region "$REGION" \
  --filters "$tag_filter_project" "$tag_filter_owner" \
  --query "Vpcs[].VpcId" \
  --output text 2>/dev/null || true)

REMAINING_INSTANCES=$(aws ec2 describe-instances \
  --region "$REGION" \
  --filters "$tag_filter_project" "$tag_filter_owner" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text 2>/dev/null || true)

REMAINING_ALBS=$(aws elbv2 describe-load-balancers \
  --region "$REGION" \
  --query "LoadBalancers[?contains(LoadBalancerName, 'ansible-jjh')].LoadBalancerArn" \
  --output text 2>/dev/null || true)

echo "Remaining VPCs      : ${REMAINING_VPCS:-none}"
echo "Remaining Instances : ${REMAINING_INSTANCES:-none}"
echo "Remaining ALBs      : ${REMAINING_ALBS:-none}"

echo ""
echo "======================================"
echo "Cleanup completed"
echo "======================================"
echo "If remaining VPCs are shown, wait a moment and run this script again."
echo "This can happen while AWS finishes deleting ENIs, NAT Gateways, or dependent resources."
echo "======================================"
