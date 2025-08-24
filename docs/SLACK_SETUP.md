# Slack App Setup Guide

This guide walks you through setting up the Slack app to work with your deployed EC2 Controller Bot.

## Prerequisites

- Deployed AWS infrastructure (Lambda function and API Gateway)
- Slack workspace with admin permissions
- API Gateway endpoint URL from deployment

## Step 1: Create Slack App

### Option A: Create New App
1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter app details:
   - **App Name**: `EC2 Controller`
   - **Pick a workspace**: Select your workspace
5. Click **"Create App"**

### Option B: Use App Manifest (Recommended)
1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From an app manifest"**
4. Choose your workspace
5. Paste this manifest (replace `YOUR_API_ENDPOINT` with your actual endpoint):

```yaml
display_information:
  name: EC2 Controller
  description: Control EC2 instances from Slack
  background_color: "#232f3e"
features:
  bot_user:
    display_name: EC2 Controller
    always_online: false
  slash_commands:
    - command: /ec2
      url: YOUR_API_ENDPOINT
      description: Control EC2 instances
      usage_hint: list | start|stop|status <name>
      should_escape: false
oauth_config:
  scopes:
    bot:
      - commands
settings:
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

## Step 2: Configure Slash Command

If you created the app from scratch, add the slash command manually:

1. In your app settings, go to **"Slash Commands"**
2. Click **"Create New Command"**
3. Fill in the details:
   - **Command**: `/ec2`
   - **Request URL**: `https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack`
   - **Short Description**: `Control EC2 instances`
   - **Usage Hint**: `list | start|stop|status <name>`
4. Click **"Save"**

## Step 3: Configure Interactivity (Required for Buttons)

**Important**: This step is required for interactive buttons to work.

1. In your app settings, go to **"Interactivity & Shortcuts"**
2. Toggle **"Interactivity"** to **ON**
3. In the **"Request URL"** field, enter the same URL as your slash command:
   ```
   https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack
   ```
4. Click **"Save Changes"**

### Command Configuration Details

| Field | Value | Description |
|-------|-------|-------------|
| Command | `/ec2` | The slash command users will type |
| Request URL | Your API Gateway endpoint | Where Slack sends the command |
| Short Description | `Control EC2 instances` | Brief description shown in Slack |
| Usage Hint | `list \| start\|stop\|status <instance-name>` | Shows available options |
| Escape channels, users, and links | ❌ Unchecked | Allow raw text processing |

## Step 4: Install App to Workspace

1. In your app settings, go to **"Install App"**
2. Click **"Install to Workspace"**
3. Review the permissions:
   - **Add shortcuts and/or slash commands that people can use**
4. Click **"Allow"**

## Step 5: Test the Integration

### Basic Tests
Try these commands in any Slack channel:

```
/ec2
/ec2 list
/ec2 status web-server
```

### Expected Responses

**Interactive Menu (`/ec2`):**
```
🤖 EC2 Controller - Choose an action:

[📋 List All Instances]

Quick Start:
[▶️ Start database-server] [▶️ Start backup-server]

Quick Stop:  
[⏹️ Stop web-server] [⏹️ Stop api-server]

Text Commands:
• /ec2 list - List all instances
• /ec2 start <name> - Start instance
• /ec2 stop <name> - Stop instance
• /ec2 status <name> - Get status
```

**List Command (`/ec2 list`):**
```
📋 All EC2 Instances in ap-southeast-1: (3 total)

Running 🟢:
• web-server (t3.micro)
• api-server (t3.small)

Stopped 🔴:
• database-server (t3.medium)
• backup-server (t3.micro)
```

## Step 6: Advanced Configuration (Optional)

### Add App Icon
1. Go to **"Basic Information"** in your app settings
2. Scroll to **"Display Information"**
3. Upload an icon (512x512 px recommended)
4. Suggested icon: AWS EC2 logo or server icon

### Customize App Description
Update the app description to be more specific:
```
Control your EC2 instances in ap-southeast-1 directly from Slack. 
Start, stop, and check the status of instances using simple commands.
```

### Set App Colors
- **Background Color**: `#232f3e` (AWS Dark Blue)
- **Accent Color**: `#ff9900` (AWS Orange)

## Step 7: User Permissions and Distribution

### Workspace Distribution
For internal use within your workspace:
1. The app is automatically available to all workspace members
2. Users can start using `/ec2` commands immediately

### Public Distribution (Optional)
To distribute to other workspaces:
1. Go to **"Manage Distribution"**
2. Complete the required information
3. Submit for Slack App Directory review

## Troubleshooting

### Common Issues

#### 1. "Command not found" Error
**Symptoms**: `/ec2` shows "Sorry, that didn't work. Please try again."

**Solutions**:
- Verify the slash command is created and saved
- Check that the Request URL is correct
- Ensure the app is installed to the workspace

#### 2. "This app responded with an error" 
**Symptoms**: Command executes but returns an error message

**Solutions**:
- Check API Gateway endpoint is accessible
- Verify Lambda function is deployed and working
- Check CloudWatch logs for Lambda errors

#### 3. No Response from Bot
**Symptoms**: Command appears to execute but no response

**Solutions**:
- Verify API Gateway integration with Lambda
- Check Lambda function permissions
- Test API endpoint directly with curl

#### 4. Permission Denied Errors
**Symptoms**: Bot responds but can't perform EC2 actions

**Solutions**:
- Verify IAM role has correct EC2 permissions
- Check if instances exist in ap-southeast-1 region
- Ensure instance names match Name tags

### Testing API Endpoint

Test your API endpoint directly:
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=list&user_name=testuser&channel_name=testchannel" \
  https://YOUR_API_ID.execute-api.ap-southeast-1.amazonaws.com/prod/slack
```

Expected response:
```json
{
  "response_type": "in_channel",
  "text": "🤖 EC2 Control Commands:\n\n..."
}
```

### Debugging Steps

1. **Check Slack App Configuration**:
   - Verify slash command URL is correct
   - Ensure app is installed to workspace

2. **Test AWS Resources**:
   - Test Lambda function directly in AWS Console
   - Check API Gateway test feature
   - Review CloudWatch logs

3. **Verify Permissions**:
   - Check IAM role permissions
   - Verify Lambda execution role
   - Test EC2 API access

## Security Considerations

### Slack App Permissions
The app only requests minimal permissions:
- **commands**: Ability to add slash commands

### User Access Control
Consider implementing user-based access control:
- Restrict commands to specific Slack users
- Add approval workflows for production instances
- Log all user actions for audit purposes

### Channel Restrictions
You can restrict the bot to specific channels by:
1. Creating a private channel for infrastructure team
2. Only installing the app to that channel
3. Monitoring usage through Slack audit logs

## Usage Guidelines

### Best Practices
1. **Use descriptive instance names**: Ensure EC2 instances have clear Name tags
2. **Test in development first**: Try commands on non-production instances
3. **Monitor usage**: Review CloudWatch logs regularly
4. **Document procedures**: Share usage guidelines with team members

### Command Examples
```bash
# Get interactive menu
/ec2

# List all instances
/ec2 list

# Start an instance
/ec2 start web-server

# Stop an instance  
/ec2 stop web-server

# Check instance status
/ec2 status web-server
```

## Next Steps

After successful setup:
1. ✅ Train team members on available commands
2. ✅ Set up monitoring and alerting
3. ✅ Consider adding more regions if needed
4. ✅ Implement additional features like scheduling
5. ✅ Set up backup and disaster recovery procedures

For additional features and customization, see the main README.md file.
