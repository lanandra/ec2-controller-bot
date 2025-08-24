#!/bin/bash

# EC2 Controller Bot Deployment Script
# This script deploys the complete AWS infrastructure for the Slack EC2 controller bot

set -e  # Exit on any error

# Configuration
REGION="ap-southeast-1"
ROLE_NAME="SlackEC2ControlRole"
FUNCTION_NAME="slack-ec2-control"
API_NAME="slack-ec2-api"

echo "🚀 Starting deployment of EC2 Controller Bot..."
echo "Region: $REGION"
echo "Function: $FUNCTION_NAME"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $SCRIPT_DIR"

# Step 1: Create IAM Role
echo "1️⃣ Creating IAM role..."
if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "   ✅ IAM role '$ROLE_NAME' already exists"
else
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://config/iam-trust-policy.json \
        --description "Role for Lambda to manage EC2 instances via Slack commands" \
        --region "$REGION"
    
    echo "   ✅ Created IAM role '$ROLE_NAME'"
fi

# Step 2: Attach permissions policy
echo "2️⃣ Attaching permissions policy..."
aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "EC2ManagementPolicy" \
    --policy-document file://config/iam-permissions.json \
    --region "$REGION"

echo "   ✅ Attached permissions policy"

# Step 3: Get account ID for ARN construction
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"

echo "   📋 Role ARN: $ROLE_ARN"

# Step 4: Create deployment package
echo "3️⃣ Creating deployment package..."
cd src
zip -q ../lambda-deployment-package.zip lambda_function.py
cd ..
echo "   ✅ Created lambda-deployment-package.zip"

# Step 5: Create or update Lambda function
echo "4️⃣ Deploying Lambda function..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "   🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://lambda-deployment-package.zip \
        --region "$REGION" > /dev/null
    
    echo "   ✅ Updated Lambda function '$FUNCTION_NAME'"
else
    echo "   🆕 Creating new Lambda function..."
    # Wait a bit for IAM role to propagate
    echo "   ⏳ Waiting for IAM role to propagate..."
    sleep 10
    
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.13 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://lambda-deployment-package.zip \
        --description "Lambda function to control EC2 instances via Slack commands" \
        --timeout 30 \
        --region "$REGION" > /dev/null
    
    echo "   ✅ Created Lambda function '$FUNCTION_NAME'"
fi

# Step 6: Create API Gateway
echo "5️⃣ Setting up API Gateway..."

# Check if API already exists
API_ID=$(aws apigateway get-rest-apis --region "$REGION" --query "items[?name=='$API_NAME'].id" --output text)

if [ -z "$API_ID" ] || [ "$API_ID" = "None" ]; then
    echo "   🆕 Creating new API Gateway..."
    API_ID=$(aws apigateway create-rest-api \
        --name "$API_NAME" \
        --description "API Gateway for Slack EC2 control commands" \
        --region "$REGION" \
        --query 'id' --output text)
    
    echo "   ✅ Created API Gateway with ID: $API_ID"
else
    echo "   ✅ Using existing API Gateway with ID: $API_ID"
fi

# Get root resource ID
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query 'items[?path==`/`].id' --output text)

# Check if /slack resource exists
SLACK_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query 'items[?pathPart==`slack`].id' --output text)

if [ -z "$SLACK_RESOURCE_ID" ] || [ "$SLACK_RESOURCE_ID" = "None" ]; then
    echo "   🆕 Creating /slack resource..."
    SLACK_RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id "$API_ID" \
        --parent-id "$ROOT_RESOURCE_ID" \
        --path-part "slack" \
        --region "$REGION" \
        --query 'id' --output text)
    
    echo "   ✅ Created /slack resource with ID: $SLACK_RESOURCE_ID"
else
    echo "   ✅ Using existing /slack resource with ID: $SLACK_RESOURCE_ID"
fi

# Create POST method
echo "   🔧 Setting up POST method..."
aws apigateway put-method \
    --rest-api-id "$API_ID" \
    --resource-id "$SLACK_RESOURCE_ID" \
    --http-method POST \
    --authorization-type NONE \
    --region "$REGION" > /dev/null 2>&1 || true

# Set up Lambda integration
LAMBDA_ARN="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME"
INTEGRATION_URI="arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"

aws apigateway put-integration \
    --rest-api-id "$API_ID" \
    --resource-id "$SLACK_RESOURCE_ID" \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "$INTEGRATION_URI" \
    --region "$REGION" > /dev/null 2>&1 || true

echo "   ✅ Configured Lambda integration"

# Step 7: Grant API Gateway permission to invoke Lambda
echo "6️⃣ Setting up Lambda permissions..."
SOURCE_ARN="arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/POST/slack"

aws lambda add-permission \
    --function-name "$FUNCTION_NAME" \
    --statement-id "allow-api-gateway-$(date +%s)" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "$SOURCE_ARN" \
    --region "$REGION" > /dev/null 2>&1 || true

echo "   ✅ Granted API Gateway permissions"

# Step 8: Deploy API
echo "7️⃣ Deploying API..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name prod \
    --region "$REGION" \
    --query 'id' --output text)

echo "   ✅ Deployed API with deployment ID: $DEPLOYMENT_ID"

# Step 9: Clean up
echo "8️⃣ Cleaning up..."
rm -f lambda-deployment-package.zip
echo "   ✅ Removed temporary files"

# Step 10: Display results
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "   • Region: $REGION"
echo "   • IAM Role: $ROLE_NAME"
echo "   • Lambda Function: $FUNCTION_NAME"
echo "   • API Gateway: $API_NAME ($API_ID)"
echo ""
echo "🔗 API Endpoint:"
echo "   https://$API_ID.execute-api.$REGION.amazonaws.com/prod/slack"
echo ""
echo "📱 Next Steps:"
echo "   1. Copy the API endpoint URL above"
echo "   2. Go to https://api.slack.com/apps"
echo "   3. Create a new Slack app or update existing one"
echo "   4. Add a slash command '/ec2' with the API endpoint URL"
echo "   5. Install the app to your workspace"
echo ""
echo "🧪 Test Commands:"
echo "   /ec2"
echo "   /ec2 list"
echo "   /ec2 start <name>"
echo ""
echo "📚 For detailed setup instructions, see docs/SLACK_SETUP.md"
