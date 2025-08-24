# Deployment Guide

This guide provides detailed instructions for deploying the EC2 Controller Bot to AWS.

## Prerequisites

### AWS Requirements
- AWS CLI installed and configured
- AWS account with appropriate permissions
- Access to create IAM roles, Lambda functions, and API Gateway resources

### Required AWS Permissions
Your AWS user/role needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:PutRolePolicy",
                "iam:GetRole",
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:GetFunction",
                "lambda:AddPermission",
                "apigateway:*",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## Automated Deployment

### Quick Deploy
```bash
cd ~/Projects/ec2-controller-bot
./deploy.sh
```

The deployment script will:
1. ✅ Create IAM role with minimal EC2 permissions
2. ✅ Deploy Lambda function to ap-southeast-1
3. ✅ Set up API Gateway with /slack endpoint
4. ✅ Configure Lambda permissions
5. ✅ Deploy API to production stage

### Expected Output
```
🚀 Starting deployment of EC2 Controller Bot...
Region: ap-southeast-1
Function: slack-ec2-control

1️⃣ Creating IAM role...
   ✅ Created IAM role 'SlackEC2ControlRole'
2️⃣ Attaching permissions policy...
   ✅ Attached permissions policy
3️⃣ Creating deployment package...
   ✅ Created lambda-deployment-package.zip
4️⃣ Deploying Lambda function...
   ✅ Created Lambda function 'slack-ec2-control'
5️⃣ Setting up API Gateway...
   ✅ Created API Gateway with ID: abc123def456
6️⃣ Setting up Lambda permissions...
   ✅ Granted API Gateway permissions
7️⃣ Deploying API...
   ✅ Deployed API with deployment ID: xyz789
8️⃣ Cleaning up...
   ✅ Removed temporary files

🎉 Deployment completed successfully!

🔗 API Endpoint:
   https://abc123def456.execute-api.ap-southeast-1.amazonaws.com/prod/slack
```

## Manual Deployment

If you prefer to deploy manually or need to customize the deployment:

### Step 1: Create IAM Role
```bash
aws iam create-role \
    --role-name SlackEC2ControlRole \
    --assume-role-policy-document file://config/iam-trust-policy.json \
    --region ap-southeast-1

aws iam put-role-policy \
    --role-name SlackEC2ControlRole \
    --policy-name EC2ManagementPolicy \
    --policy-document file://config/iam-permissions.json
```

### Step 2: Create Lambda Function
```bash
cd src
zip lambda-deployment-package.zip lambda_function.py
cd ..

aws lambda create-function \
    --function-name slack-ec2-control \
    --runtime python3.13 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/SlackEC2ControlRole \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-deployment-package.zip \
    --timeout 30 \
    --region ap-southeast-1
```

### Step 3: Create API Gateway
```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
    --name slack-ec2-api \
    --region ap-southeast-1 \
    --query 'id' --output text)

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region ap-southeast-1 \
    --query 'items[0].id' --output text)

# Create /slack resource
RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part slack \
    --region ap-southeast-1 \
    --query 'id' --output text)

# Create POST method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --region ap-southeast-1

# Set up Lambda integration
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:ap-southeast-1:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-southeast-1:YOUR_ACCOUNT_ID:function:slack-ec2-control/invocations \
    --region ap-southeast-1

# Grant permissions
aws lambda add-permission \
    --function-name slack-ec2-control \
    --statement-id allow-api-gateway \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:ap-southeast-1:YOUR_ACCOUNT_ID:$API_ID/*/POST/slack" \
    --region ap-southeast-1

# Deploy API
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region ap-southeast-1
```

## Regional Deployment

### Deploying to Different Regions

To deploy to a different region, modify these files:

1. **deploy.sh**: Change the `REGION` variable
2. **src/lambda_function.py**: Update the `region_name` parameter in boto3 client initialization

Example for us-east-1:
```bash
# In deploy.sh
REGION="us-east-1"

# In src/lambda_function.py
ec2 = boto3.client('ec2', region_name='us-east-1')
```

### Multi-Region Deployment

For multi-region deployment, run the deployment script for each region:

```bash
# Deploy to ap-southeast-1
REGION=ap-southeast-1 ./deploy.sh

# Deploy to us-east-1  
REGION=us-east-1 ./deploy.sh

# Deploy to eu-west-1
REGION=eu-west-1 ./deploy.sh
```

## Verification

### Test Lambda Function
```bash
aws lambda invoke \
    --function-name slack-ec2-control \
    --payload '{"body":"text=help"}' \
    --region ap-southeast-1 \
    response.json

cat response.json
```

### Test API Gateway
```bash
curl -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "text=help&user_name=testuser&channel_name=testchannel" \
    https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack
```

## Troubleshooting

### Common Issues

1. **IAM Role Not Found**
   - Wait 10-15 seconds after creating IAM role before creating Lambda function
   - Verify role ARN is correct

2. **Lambda Permission Denied**
   - Check if API Gateway has permission to invoke Lambda
   - Verify source ARN in Lambda permission

3. **API Gateway 502 Error**
   - Check Lambda function logs in CloudWatch
   - Verify Lambda function is in the same region as API Gateway

4. **EC2 Permission Denied**
   - Verify IAM role has EC2 permissions
   - Check if instances exist in the specified region

### Monitoring

View Lambda logs:
```bash
aws logs tail /aws/lambda/slack-ec2-control --region ap-southeast-1 --follow
```

Check API Gateway logs:
```bash
aws logs describe-log-groups --region ap-southeast-1 --log-group-name-prefix API-Gateway
```

## Cleanup

To remove all resources:

```bash
# Delete Lambda function
aws lambda delete-function \
    --function-name slack-ec2-control \
    --region ap-southeast-1

# Delete API Gateway
aws apigateway delete-rest-api \
    --rest-api-id YOUR_API_ID \
    --region ap-southeast-1

# Delete IAM role
aws iam delete-role-policy \
    --role-name SlackEC2ControlRole \
    --policy-name EC2ManagementPolicy

aws iam delete-role \
    --role-name SlackEC2ControlRole
```

## Security Considerations

### IAM Permissions
- The IAM role has minimal required permissions
- Only allows EC2 start/stop/describe operations
- No access to other AWS services

### Network Security
- Lambda function runs in AWS managed VPC
- No custom VPC configuration required
- API Gateway uses HTTPS only

### Instance Access Control
- Consider adding tag-based filtering to restrict which instances can be controlled
- Implement user-based access control in Lambda function if needed

### Audit Trail
- All actions are logged to CloudWatch Logs
- Consider enabling CloudTrail for additional audit logging
