# EC2 Controller Bot for Slack

A Slack bot that allows you to control EC2 instances directly from Slack using slash commands. The bot supports starting, stopping, and checking the status of EC2 instances using either instance names or instance IDs.

## Features

- 🚀 **Start/Stop EC2 instances** via Slack commands
- 📊 **Check instance status** with detailed information
- 🏷️ **Support for instance names** (using Name tags) and instance IDs
- 🎯 **Interactive buttons and menus** for better user experience
- 📋 **List all instances** with visual state indicators
- 🔍 **Smart suggestions** based on instance states
- 🌏 **Regional support** (currently configured for ap-southeast-1)
- 🔒 **IAM-based security** with minimal required permissions

## Architecture

```
Slack Slash Command (/ec2)
         ↓
    API Gateway
         ↓
    Lambda Function
         ↓
    EC2 API (ap-southeast-1)
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS account with EC2 instances in ap-southeast-1 region
- Slack workspace with admin permissions to create apps
- Python 3.13+ (for local development/testing)

## Quick Start

### 1. Clone and Setup

```bash
cd ~/Projects
git clone <your-repo> ec2-controller-bot
cd ec2-controller-bot
```

### 2. Deploy AWS Resources

```bash
# Deploy the complete stack
./deploy.sh
```

### 3. Configure Slack App

1. Go to https://api.slack.com/apps
2. Create new app → "From scratch"
3. Add slash command with the API Gateway URL from deployment output
4. **Configure Interactivity**: Go to "Interactivity & Shortcuts" → Enable → Use same API Gateway URL
5. Install app to your workspace

**Important**: Interactive features require both slash command AND interactivity URL to be configured.

### 4. Test the Bot

```
/ec2                          # Shows interactive menu with buttons
/ec2 list                     # List all instances
/ec2 start web-server         # Start instance
/ec2 stop web-server          # Stop instance
/ec2 status web-server        # Get status
```

**Interactive Features**: Click buttons and menus for one-click actions!

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/ec2` | Show interactive menu with buttons | `/ec2` |
| `/ec2 list` | List all instances | `/ec2 list` |
| `/ec2 start <name>` | Start instance | `/ec2 start web-server` |
| `/ec2 stop <name>` | Stop instance | `/ec2 stop web-server` |
| `/ec2 status <name>` | Get status | `/ec2 status web-server` |

## Invalid Commands

All invalid commands now return clear error messages:

| Command Type | Example | Response |
|--------------|---------|----------|
| Invalid actions | `/ec2 help`, `/ec2 delete` | `❌ Invalid action 'help'. Supported actions are: start, stop, status, list` |
| Invalid with instance | `/ec2 delete myserver` | `❌ Invalid action 'delete'. Supported actions are: start, stop, status` |
| Wrong format | `/ec2 start my server name` | `❌ Invalid command format. Use: /ec2 <action> <instance> or /ec2 for interactive menu` |

## Interactive Features

The bot provides interactive buttons and menus for better user experience:

- **Interactive Menu**: Type `/ec2` to get clickable buttons for all actions
- **Quick Action Buttons**: One-click start/stop for common instances  
- **Instance Lists**: Visual indicators with emojis (🟢 Running, 🔴 Stopped, etc.)
- **Overflow Menus**: Three-dot menus with available actions per instance
- **Smart Suggestions**: Only show relevant actions based on instance state

**Note**: Interactive features require the updated Lambda function. Run `./deploy.sh` to deploy the latest version with interactive buttons.

## Project Structure

```
ec2-controller-bot/
├── README.md                 # This file
├── deploy.sh                 # Deployment script
├── src/
│   └── lambda_function.py    # Main Lambda function
├── config/
│   ├── iam-trust-policy.json # IAM trust policy for Lambda
│   └── iam-permissions.json  # IAM permissions policy
├── docs/
│   ├── DEPLOYMENT.md         # Detailed deployment guide
│   ├── SLACK_SETUP.md        # Slack app configuration guide
│   └── TROUBLESHOOTING.md    # Common issues and solutions
└── examples/
    └── slack-responses.json  # Example Slack response formats
```

## Security

The bot follows AWS security best practices:

- **Minimal IAM permissions**: Only EC2 start/stop/describe permissions
- **Regional restrictions**: Limited to ap-southeast-1 region
- **Instance validation**: Validates instance existence before actions
- **Error handling**: Graceful error handling with user-friendly messages
- **Audit logging**: All actions are logged to CloudWatch

## Deployment Details

### AWS Resources Created

1. **IAM Role**: `SlackEC2ControlRole` with minimal EC2 permissions
2. **Lambda Function**: `slack-ec2-control` in ap-southeast-1
3. **API Gateway**: REST API with `/slack` endpoint
4. **CloudWatch Logs**: Automatic logging for debugging

### Environment Variables

The Lambda function uses these configurations:
- **Region**: `ap-southeast-1` (hardcoded in function)
- **Timeout**: 30 seconds
- **Memory**: 128 MB
- **Runtime**: Python 3.13

## Customization

### Change Region

To deploy in a different region, update:
1. `src/lambda_function.py` - Change the `region_name` parameter
2. `deploy.sh` - Update the AWS CLI region parameter

### Add Instance Filtering

To restrict which instances can be controlled, modify the `resolve_instance_identifier` function to add tag-based filtering.

### Custom Instance Naming

The bot uses the `Name` tag for instance identification. To use different tags, modify the `get_instance_name` function.

## Monitoring and Troubleshooting

### CloudWatch Logs

Monitor the Lambda function logs:
```bash
aws logs tail /aws/lambda/slack-ec2-control --region ap-southeast-1 --follow
```

### Common Issues

1. **"Instance not found"**: Check if instance exists and has Name tag
2. **"Permission denied"**: Verify IAM role has correct permissions
3. **"Timeout"**: Check if Lambda function has network access to EC2 API

See `docs/TROUBLESHOOTING.md` for detailed solutions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
1. Check the troubleshooting guide
2. Review CloudWatch logs
3. Open an issue in the repository

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and release notes.

---

**Note**: This bot is designed for ap-southeast-1 region. Modify the configuration to use in other regions.
