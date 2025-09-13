# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1]

### Fixed
- **Interactive Menu Response Format**: Fixed "Invalid response format" error when clicking overflow menu actions (three-dot menus)
- **Overflow Menu Value Parsing**: Corrected parsing of `selected_option.value` for interactive components
- **Response Message Delivery**: Interactive actions now properly show response messages using `response_url`
- **Action Execution Feedback**: Users now receive confirmation messages when starting/stopping/checking status via interactive menus

### Changed
- **Interactive Component Handling**: Switched from direct response to `response_url` approach for better reliability
- **Error Handling**: Enhanced JSON parsing with proper error handling for interactive responses
- **Logging**: Added detailed logging for interactive action debugging

### Technical Details
- Modified `handle_interactive_action()` to properly parse overflow menu selections
- Updated overflow menu action_id to use single `overflow_menu` identifier
- Implemented `send_response_to_slack()` function for reliable message delivery
- Added comprehensive error handling for JSON parsing failures

### Documentation
- **Updated README.md**: Added changelog entry and version bump
- **Enhanced TROUBLESHOOTING.md**: Added dedicated section for interactive menu issues
- **Maintained SLACK_SETUP.md**: Verified interactivity configuration instructions

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

### Known Issues
- Interactive overflow menu actions may show "Invalid response format" error (Fixed in v0.1.1)
