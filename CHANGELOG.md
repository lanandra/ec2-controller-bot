# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0]

### Added
- Initial release of EC2 Controller Bot for Slack
- Slash command `/ec2` with comprehensive functionality
- Interactive buttons and menus for better user experience
- Support for both instance names (Name tags) and instance IDs
- Regional deployment support (configured for ap-southeast-1)
- Comprehensive error handling and user feedback
- Security-focused IAM permissions (minimal required access)
- Automated deployment script (`deploy.sh`)
- Complete documentation suite

### Features
- **Commands**: list, start, stop, status
- **Interactive Elements**: 
  - Clickable buttons for common actions
  - Overflow menus for instance-specific actions
  - Visual state indicators with emojis
  - Smart suggestions based on instance states
- **Security**: IAM-based access control, audit logging
- **Monitoring**: CloudWatch integration for logging and debugging

### Documentation
- Comprehensive README with quick start guide
- Detailed deployment instructions
- Slack app setup guide with interactive configuration
- Troubleshooting guide for common issues
- Example responses and configuration files

### Infrastructure
- AWS Lambda function (Python 3.13)
- API Gateway REST API
- IAM role with minimal EC2 permissions
- CloudWatch Logs for monitoring
