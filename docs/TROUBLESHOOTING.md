# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the EC2 Controller Bot.

## Quick Diagnostics

### Health Check Commands
```bash
# Test AWS CLI access
aws sts get-caller-identity

# Check Lambda function
aws lambda get-function --function-name slack-ec2-control --region ap-southeast-1

# Test API Gateway
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=list" \
  https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack

# Check EC2 instances
aws ec2 describe-instances --region ap-southeast-1
```

## Common Issues and Solutions

### 1. Slack Command Not Working

#### Symptoms
- `/ec2` command shows "Sorry, that didn't work. Please try again."
- No response from the bot

#### Diagnosis
```bash
# Check if slash command exists in Slack app
# Go to https://api.slack.com/apps → Your App → Slash Commands

# Test API endpoint directly
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=list&user_name=test&channel_name=test" \
  https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack
```

#### Solutions
1. **Verify Slack App Configuration**:
   - Check slash command URL is correct
   - Ensure app is installed to workspace
   - Verify command is `/ec2` (not `/EC2` or other variations)

2. **Check API Gateway**:
   - Verify API Gateway is deployed
   - Test endpoint accessibility
   - Check API Gateway logs

3. **Lambda Function Issues**:
   - Verify Lambda function exists and is active
   - Check Lambda permissions for API Gateway

### 2. "Instance Not Found" Errors

#### Symptoms
- Bot responds: "❌ Instance 'web-server' not found in ap-southeast-1 region"
- Commands work but can't find specific instances

#### Diagnosis
```bash
# Check instances in region
aws ec2 describe-instances --region ap-southeast-1 \
  --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
  --output table

# Check specific instance by name
aws ec2 describe-instances --region ap-southeast-1 \
  --filters "Name=tag:Name,Values=web-server" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' \
  --output table
```

#### Solutions
1. **Verify Instance Exists**:
   - Check instance is in ap-southeast-1 region
   - Verify instance has Name tag
   - Ensure Name tag value matches command exactly (case-sensitive)

2. **Check Instance State**:
   - Instance must not be terminated
   - Verify instance is in valid state (running, stopped, pending, etc.)

3. **Name Tag Issues**:
   ```bash
   # Add Name tag to instance
   aws ec2 create-tags --region ap-southeast-1 \
     --resources i-1234567890abcdef0 \
     --tags Key=Name,Value=web-server
   ```

### 3. Permission Denied Errors

#### Symptoms
- "❌ Error accessing instance: An error occurred (UnauthorizedOperation)"
- Bot can find instances but can't start/stop them

#### Diagnosis
```bash
# Check IAM role permissions
aws iam get-role-policy --role-name SlackEC2ControlRole --policy-name EC2ManagementPolicy

# Test EC2 permissions directly
aws ec2 describe-instances --region ap-southeast-1
aws ec2 start-instances --instance-ids i-1234567890abcdef0 --region ap-southeast-1 --dry-run
```

#### Solutions
1. **Verify IAM Role**:
   - Check role exists: `SlackEC2ControlRole`
   - Verify role has correct permissions policy
   - Ensure Lambda function uses the correct role

2. **Update IAM Permissions**:
   ```bash
   # Re-apply permissions policy
   aws iam put-role-policy \
     --role-name SlackEC2ControlRole \
     --policy-name EC2ManagementPolicy \
     --policy-document file://config/iam-permissions.json
   ```

3. **Check Resource-Based Restrictions**:
   - Verify no resource-based policies blocking access
   - Check if instances have specific tags required by policies

### 4. Lambda Function Timeout

#### Symptoms
- Commands take long time and then fail
- "Task timed out after 30.00 seconds" in CloudWatch logs

#### Diagnosis
```bash
# Check Lambda function configuration
aws lambda get-function-configuration --function-name slack-ec2-control --region ap-southeast-1

# Monitor CloudWatch logs
aws logs tail /aws/lambda/slack-ec2-control --region ap-southeast-1 --follow
```

#### Solutions
1. **Increase Timeout**:
   ```bash
   aws lambda update-function-configuration \
     --function-name slack-ec2-control \
     --timeout 60 \
     --region ap-southeast-1
   ```

2. **Optimize Function**:
   - Reduce number of API calls
   - Implement caching for instance data
   - Add pagination for large instance lists

### 5. API Gateway 502 Bad Gateway

#### Symptoms
- Slack shows "This app responded with an error"
- API Gateway returns 502 status code

#### Diagnosis
```bash
# Check Lambda function logs
aws logs tail /aws/lambda/slack-ec2-control --region ap-southeast-1

# Test Lambda function directly
aws lambda invoke \
  --function-name slack-ec2-control \
  --payload '{"body":"text=list"}' \
  --region ap-southeast-1 \
  response.json && cat response.json
```

#### Solutions
1. **Check Lambda Function**:
   - Verify function is not crashing
   - Check for syntax errors in code
   - Ensure proper response format

2. **API Gateway Integration**:
   - Verify Lambda proxy integration is configured
   - Check API Gateway method configuration
   - Ensure Lambda permissions are correct

### 6. Slow Response Times

#### Symptoms
- Commands work but take 5-10 seconds to respond
- Slack shows "thinking..." for extended periods

#### Diagnosis
```bash
# Check Lambda function performance
aws logs filter-log-events \
  --log-group-name /aws/lambda/slack-ec2-control \
  --region ap-southeast-1 \
  --filter-pattern "REPORT"
```

#### Solutions
1. **Optimize Lambda Function**:
   - Increase memory allocation (more CPU)
   - Implement connection pooling
   - Cache EC2 client initialization

2. **Reduce API Calls**:
   - Batch EC2 describe operations
   - Implement smart filtering
   - Use pagination for large results

## Debugging Tools

### CloudWatch Logs Analysis
```bash
# View recent logs
aws logs tail /aws/lambda/slack-ec2-control --region ap-southeast-1

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/slack-ec2-control \
  --region ap-southeast-1 \
  --filter-pattern "ERROR"

# Monitor in real-time
aws logs tail /aws/lambda/slack-ec2-control --region ap-southeast-1 --follow
```

### Lambda Function Testing
```bash
# Test with sample Slack payload
aws lambda invoke \
  --function-name slack-ec2-control \
  --payload '{
    "body": "text=list&user_name=testuser&channel_name=testchannel"
  }' \
  --region ap-southeast-1 \
  response.json

cat response.json
```

### API Gateway Testing
```bash
# Test API endpoint
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=list&user_name=testuser&channel_name=testchannel" \
  https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack
```

## Monitoring and Alerting

### CloudWatch Metrics
Monitor these key metrics:
- Lambda function duration
- Lambda function errors
- API Gateway 4xx/5xx errors
- Lambda concurrent executions

### Set Up Alerts
```bash
# Create CloudWatch alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name "EC2-Controller-Lambda-Errors" \
  --alarm-description "Alert on Lambda function errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=slack-ec2-control \
  --evaluation-periods 1 \
  --region ap-southeast-1
```

## Performance Optimization

### Lambda Function Optimization
1. **Memory Allocation**: Increase from 128MB to 256MB for better performance
2. **Connection Reuse**: Initialize boto3 clients outside handler function
3. **Error Handling**: Implement proper exception handling
4. **Logging**: Add structured logging for better debugging

### API Gateway Optimization
1. **Caching**: Enable API Gateway caching for read operations
2. **Throttling**: Set appropriate throttling limits
3. **Monitoring**: Enable detailed CloudWatch metrics

## Recovery Procedures

### Complete Redeployment
If all else fails, redeploy the entire stack:
```bash
# Clean up existing resources
aws lambda delete-function --function-name slack-ec2-control --region ap-southeast-1
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID --region ap-southeast-1

# Redeploy
./deploy.sh
```

### Rollback Lambda Function
```bash
# List function versions
aws lambda list-versions-by-function --function-name slack-ec2-control --region ap-southeast-1

# Rollback to previous version
aws lambda update-alias \
  --function-name slack-ec2-control \
  --name LIVE \
  --function-version 1 \
  --region ap-southeast-1
```

## Getting Help

### Log Analysis
When reporting issues, include:
1. CloudWatch logs from Lambda function
2. API Gateway access logs
3. Exact Slack command that failed
4. Expected vs actual behavior

### Useful Commands for Support
```bash
# Get function configuration
aws lambda get-function-configuration --function-name slack-ec2-control --region ap-southeast-1

# Get API Gateway information
aws apigateway get-rest-apis --region ap-southeast-1

# Check IAM role
aws iam get-role --role-name SlackEC2ControlRole
aws iam get-role-policy --role-name SlackEC2ControlRole --policy-name EC2ManagementPolicy

# List EC2 instances
aws ec2 describe-instances --region ap-southeast-1 --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' --output table
```

## Prevention

### Best Practices
1. **Regular Testing**: Test bot functionality weekly
2. **Monitoring**: Set up CloudWatch alarms
3. **Documentation**: Keep instance naming conventions documented
4. **Backup**: Maintain backup of configuration files
5. **Version Control**: Use git for code changes

### Health Checks
Create automated health checks:
```bash
#!/bin/bash
# health-check.sh
curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=list" \
  https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack | \
  grep -q "instances" && echo "✅ Bot is healthy" || echo "❌ Bot is down"
```

Run this script daily to ensure the bot is functioning properly.
