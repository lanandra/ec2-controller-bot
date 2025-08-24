import json
import boto3
import urllib.parse
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Handle interactive button clicks
        body = event.get('body', '')
        if 'payload=' in body:
            return handle_interactive_action(event)
        
        # Parse the Slack slash command
        if 'body' in event:
            body = urllib.parse.parse_qs(event['body'])
            text = body.get('text', [''])[0].strip()
            user_name = body.get('user_name', ['unknown'])[0]
            channel_name = body.get('channel_name', ['unknown'])[0]
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'text': '❌ Invalid request format'})
            }
        
        logger.info(f"Slash command received from {user_name} in #{channel_name}: {text}")
        
        # Handle empty command - show interactive menu
        if not text:
            return show_interactive_menu()
        
        # Handle help commands - show same error as invalid actions
        if text.lower() in ['help', 'h', '?']:
            return slack_response("❌ Invalid action 'help'. Supported actions are: start, stop, status, list")
        
        # Handle list command
        if text.lower() in ['list', 'ls']:
            return list_instances_with_buttons()
        
        # Parse command parts
        parts = text.split()
        
        # Handle single word commands
        if len(parts) == 1:
            action = parts[0].lower()
            if action in ['start', 'stop', 'status']:
                return show_instances_for_action_with_buttons(action)
            else:
                # Invalid single word command - show error
                return slack_response(f"❌ Invalid action '{action}'. Supported actions are: start, stop, status, list")
        
        # Handle two word commands
        elif len(parts) == 2:
            action, instance_identifier = parts
            action = action.lower()
            
            # Validate action before proceeding
            if action not in ['start', 'stop', 'status']:
                return slack_response(f"❌ Invalid action '{action}'. Supported actions are: start, stop, status")
            
            # Execute the valid command
            return execute_instance_command(action, instance_identifier)
        
        # Handle multiple words (more than 2) - show error
        else:
            return slack_response("❌ Invalid command format. Use: `/ec2 <action> <instance>` or `/ec2` for interactive menu")
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return slack_response(f"❌ Error: {str(e)}")

def handle_interactive_action(event):
    """Handle button clicks and interactive actions"""
    try:
        # Parse the payload
        body = event.get('body', '')
        if 'payload=' in body:
            payload_str = urllib.parse.parse_qs(body)['payload'][0]
            payload = json.loads(payload_str)
        else:
            logger.error("No payload found in interactive request")
            return slack_response("❌ Invalid interactive request")
        
        action_id = payload['actions'][0]['action_id']
        value = payload['actions'][0].get('value', '')
        user_name = payload['user']['name']
        response_url = payload.get('response_url')
        
        logger.info(f"Interactive action: {action_id} by {user_name}")
        
        # For interactive responses, we need to respond immediately with 200
        # and then send the actual response to the response_url
        
        if action_id.startswith('instance_'):
            # Parse action: instance_start_web-server
            parts = action_id.split('_', 2)
            if len(parts) >= 3:
                action = parts[1]  # start, stop, status
                instance_name = parts[2]
            else:
                action = parts[1]
                instance_name = value
            
            result = execute_instance_command(action, instance_name)
            
            # Send response to Slack using response_url
            if response_url:
                send_response_to_slack(response_url, result)
            
            return {"statusCode": 200}
        
        elif action_id == 'show_list':
            result = list_instances_with_buttons()
            
            # Send response to Slack using response_url
            if response_url:
                send_response_to_slack(response_url, result)
            
            return {"statusCode": 200}
        
        elif action_id == 'show_help':
            result = show_interactive_menu()
            
            if response_url:
                send_response_to_slack(response_url, result)
            
            return {"statusCode": 200}
        
        elif action_id.startswith('instance_menu_'):
            # Handle overflow menu selections
            instance_name = action_id.replace('instance_menu_', '')
            if '_' in value:
                action, target_instance = value.split('_', 1)
                result = execute_instance_command(action, target_instance)
                
                if response_url:
                    send_response_to_slack(response_url, result)
                
                return {"statusCode": 200}
        
        else:
            logger.warning(f"Unknown action_id: {action_id}")
            return slack_response("❌ Unknown action")
            
    except Exception as e:
        logger.error(f"Error handling interactive action: {str(e)}")
        return slack_response(f"❌ Error processing action: {str(e)}")

def send_response_to_slack(response_url, lambda_response):
    """Send response to Slack using response_url"""
    try:
        import urllib.request
        
        # Extract the response body from Lambda response
        if isinstance(lambda_response, dict) and 'body' in lambda_response:
            response_data = json.loads(lambda_response['body'])
        else:
            response_data = {"text": "❌ Invalid response format"}
        
        # Prepare the request
        data = json.dumps(response_data).encode('utf-8')
        req = urllib.request.Request(
            response_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Send the request
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            
    except Exception as e:
        logger.error(f"Error sending response to Slack: {str(e)}")

def show_interactive_menu():
    """Show interactive menu with buttons"""
    try:
        ec2 = boto3.client('ec2', region_name='ap-southeast-1')
        instances = get_all_instances(ec2)
        
        # Create blocks for interactive message
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🤖 *EC2 Controller* - Choose an action:"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📋 List All Instances"
                        },
                        "action_id": "show_list",
                        "style": "primary"
                    }
                ]
            }
        ]
        
        # Add quick action buttons for common instances
        if instances:
            running_instances = [i for i in instances if i['state'] == 'running'][:3]
            stopped_instances = [i for i in instances if i['state'] == 'stopped'][:3]
            
            if stopped_instances:
                start_elements = []
                for instance in stopped_instances:
                    start_elements.append({
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"▶️ Start {instance['name']}"
                        },
                        "action_id": f"instance_start_{instance['name']}",
                        "style": "primary"
                    })
                
                if start_elements:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Quick Start:*"
                        }
                    })
                    blocks.append({
                        "type": "actions",
                        "elements": start_elements
                    })
            
            if running_instances:
                stop_elements = []
                for instance in running_instances:
                    stop_elements.append({
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"⏹️ Stop {instance['name']}"
                        },
                        "action_id": f"instance_stop_{instance['name']}",
                        "style": "danger"
                    })
                
                if stop_elements:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Quick Stop:*"
                        }
                    })
                    blocks.append({
                        "type": "actions",
                        "elements": stop_elements
                    })
        
        # Add help text
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Available Commands:*\n• `/ec2` - Show this interactive menu\n• `/ec2 list` - List all instances\n• `/ec2 start <name>` - Start instance\n• `/ec2 stop <name>` - Stop instance\n• `/ec2 status <name>` - Get status"
            }
        })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'in_channel',
                'blocks': blocks
            })
        }
        
    except Exception as e:
        logger.error(f"Error creating interactive menu: {str(e)}")
        return slack_response(f"❌ Error creating interactive menu: {str(e)}")

def list_instances_with_buttons():
    """List instances with action buttons"""
    try:
        ec2 = boto3.client('ec2', region_name='ap-southeast-1')
        instances = get_all_instances(ec2)
        
        if not instances:
            return slack_response("📋 No instances found in ap-southeast-1 region")
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📋 *EC2 Instances in ap-southeast-1* ({len(instances)} total)"
                }
            }
        ]
        
        # Add instances with buttons (limit to 10 to avoid Slack limits)
        for instance in instances[:10]:
            state_emoji = get_state_emoji(instance['state'])
            
            # Create overflow menu options based on instance state
            options = []
            
            if instance['state'] == 'stopped':
                options.append({
                    "text": {"type": "plain_text", "text": "▶️ Start"},
                    "value": f"start_{instance['name']}"
                })
            elif instance['state'] == 'running':
                options.append({
                    "text": {"type": "plain_text", "text": "⏹️ Stop"},
                    "value": f"stop_{instance['name']}"
                })
            
            options.append({
                "text": {"type": "plain_text", "text": "📊 Status"},
                "value": f"status_{instance['name']}"
            })
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{instance['name']}* {state_emoji}\n`{instance['id']}` • {instance['type']} • {instance['state']}"
                },
                "accessory": {
                    "type": "overflow",
                    "options": options,
                    "action_id": f"instance_menu_{instance['name']}"
                }
            })
        
        if len(instances) > 10:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"... and {len(instances) - 10} more instances. Use `/ec2 <action> <name>` for specific instances."
                }
            })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'in_channel',
                'blocks': blocks
            })
        }
        
    except Exception as e:
        logger.error(f"Error listing instances with buttons: {str(e)}")
        return slack_response(f"❌ Error listing instances: {str(e)}")

def show_instances_for_action_with_buttons(action):
    """Show instances for specific action with buttons"""
    try:
        ec2 = boto3.client('ec2', region_name='ap-southeast-1')
        instances = get_all_instances(ec2)
        
        if action == 'start':
            suitable_instances = [i for i in instances if i['state'] in ['stopped']]
            action_desc = "start"
            emoji = "▶️"
            button_style = "primary"
        elif action == 'stop':
            suitable_instances = [i for i in instances if i['state'] in ['running']]
            action_desc = "stop"
            emoji = "⏹️"
            button_style = "danger"
        else:  # status
            suitable_instances = instances
            action_desc = "check status of"
            emoji = "📊"
            button_style = None
        
        if not suitable_instances:
            return slack_response(f"No instances available to {action_desc}")
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *Instances you can {action_desc}:*"
                }
            }
        ]
        
        # Create buttons for suitable instances (limit to 5 per row, max 25 total)
        elements = []
        for instance in suitable_instances[:15]:
            button = {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {instance['name']}"
                },
                "action_id": f"instance_{action}_{instance['name']}"
            }
            if button_style:
                button["style"] = button_style
            
            elements.append(button)
            
            # Add action block every 5 buttons
            if len(elements) == 5:
                blocks.append({
                    "type": "actions",
                    "elements": elements
                })
                elements = []
        
        # Add remaining buttons
        if elements:
            blocks.append({
                "type": "actions",
                "elements": elements
            })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'in_channel',
                'blocks': blocks
            })
        }
        
    except Exception as e:
        return slack_response(f"❌ Error retrieving instances: {str(e)}")

def execute_instance_command(action, instance_identifier):
    """Execute instance command (existing logic)"""
    try:
        ec2 = boto3.client('ec2', region_name='ap-southeast-1')
        
        # Resolve instance identifier to instance ID
        instance_id, instance_name = resolve_instance_identifier(ec2, instance_identifier)
        if not instance_id:
            return slack_response(f"❌ Instance '{instance_identifier}' not found in ap-southeast-1 region")
        
        # Get current instance state
        describe_response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = describe_response['Reservations'][0]['Instances'][0]
        current_state = instance['State']['Name']
        
        # Execute the requested action
        if action == 'start':
            if current_state == 'running':
                return slack_response(f"ℹ️ Instance '{instance_name}' is already running")
            elif current_state in ['stopping', 'pending', 'rebooting']:
                return slack_response(f"ℹ️ Instance '{instance_name}' is currently {current_state}. Please wait.")
            else:
                ec2.start_instances(InstanceIds=[instance_id])
                return slack_response(f"✅ Starting instance '{instance_name}'\nCurrent state: {current_state} → pending")
                
        elif action == 'stop':
            if current_state == 'stopped':
                return slack_response(f"ℹ️ Instance '{instance_name}' is already stopped")
            elif current_state in ['stopping', 'pending', 'rebooting']:
                return slack_response(f"ℹ️ Instance '{instance_name}' is currently {current_state}. Please wait.")
            else:
                ec2.stop_instances(InstanceIds=[instance_id])
                return slack_response(f"🛑 Stopping instance '{instance_name}'\nCurrent state: {current_state} → stopping")
                
        elif action == 'status':
            instance_type = instance['InstanceType']
            launch_time = instance.get('LaunchTime', 'N/A')
            private_ip = instance.get('PrivateIpAddress', 'N/A')
            public_ip = instance.get('PublicIpAddress', 'N/A')
            
            status_message = f"📊 Instance '{instance_name}' Status:\n"
            status_message += f"• State: {current_state}\n"
            status_message += f"• Type: {instance_type}\n"
            status_message += f"• Private IP: {private_ip}\n"
            status_message += f"• Public IP: {public_ip}"
            
            return slack_response(status_message)
        
    except Exception as e:
        return slack_response(f"❌ Error: {str(e)}")



def get_all_instances(ec2):
    """Get all instances in the region"""
    try:
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['pending', 'running', 'stopping', 'stopped', 'rebooting']
                }
            ]
        )
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'id': instance['InstanceId'],
                    'name': get_instance_name(instance),
                    'state': instance['State']['Name'],
                    'type': instance['InstanceType']
                })
        
        instances.sort(key=lambda x: x['name'].lower())
        return instances
        
    except Exception as e:
        logger.error(f"Error getting instances: {str(e)}")
        return []

def get_state_emoji(state):
    """Get emoji for instance state"""
    emoji_map = {
        'running': '🟢',
        'stopped': '🔴',
        'pending': '🟡',
        'stopping': '🟠',
        'rebooting': '🔄',
        'terminated': '⚫'
    }
    return emoji_map.get(state, '⚪')

def resolve_instance_identifier(ec2, identifier):
    """Resolve instance identifier to instance ID and name"""
    try:
        if identifier.startswith('i-') and len(identifier) == 19:
            response = ec2.describe_instances(InstanceIds=[identifier])
            instance = response['Reservations'][0]['Instances'][0]
            instance_name = get_instance_name(instance)
            return identifier, instance_name
        else:
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [identifier]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
                ]
            )
            
            if response['Reservations']:
                instance = response['Reservations'][0]['Instances'][0]
                instance_id = instance['InstanceId']
                instance_name = get_instance_name(instance)
                return instance_id, instance_name
            else:
                return None, None
                
    except ec2.exceptions.ClientError:
        return None, None

def get_instance_name(instance):
    """Extract instance name from tags"""
    tags = instance.get('Tags', [])
    for tag in tags:
        if tag['Key'] == 'Name':
            return tag['Value']
    return instance['InstanceId']

def slack_response(message):
    """Format response for Slack"""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'response_type': 'in_channel',
            'text': message
        })
    }
