"""
Action Executor - Bridges Orchestrator Plans to MCP Server Execution
Handles: Plan parsing, HITL detection, MCP calls, approval workflow
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Add MCP servers to path
sys.path.append(str(Path(__file__).parent.parent / "mcp_servers"))

load_dotenv()
logger = logging.getLogger(__name__)

class ActionExecutor:
    """Executes actions from Claude-generated plans via MCP servers"""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.pending_approval = vault_path / "Pending_Approval"
        self.approved = vault_path / "Approved"
        self.rejected = vault_path / "Rejected"
        self.logs = vault_path / "Logs"
        self.done = vault_path / "Done"
        
        # HITL thresholds (from approval_skills.md)
        self.approval_thresholds = {
            'payment_amount': 100.0,  # Payments > $100
            'email_new_contact': True,  # Emails to new contacts
            'social_post': True,  # All social posts (for Gold tier)
            'odoo_invoice_amount': 5000.0,  # Invoices > $5000
            'odoo_bill_amount': 1000.0  # Bills > $1000
        }
    
    def parse_plan_for_actions(self, plan_file: Path) -> List[Dict]:
        """
        Parse a plan file to extract executable actions
        
        Returns list of actions with metadata:
        {
            'action_type': 'social_post' | 'email' | 'odoo_invoice' | 'odoo_payment',
            'platform': 'facebook' | 'instagram' | 'linkedin' | 'twitter',
            'data': {...},  # Action-specific data
            'requires_approval': True | False,
            'risk_level': 'low' | 'medium' | 'high'
        }
        """
        try:
            content = plan_file.read_text(encoding='utf-8')
            actions = []
            
            # Extract frontmatter
            frontmatter =self._extract_frontmatter(content)
            task_id = plan_file.stem.replace('_plan', '')
            
            # Detect social media posts
            if any(platform in content.lower() for platform in ['facebook', 'instagram', 'linkedin', 'twitter']):
                social_actions = self._extract_social_actions(content, task_id)
                actions.extend(social_actions)
            
            # Detect Odoo actions
            if 'odoo' in content.lower() or 'invoice' in content.lower() or 'bill' in content.lower():
                odoo_actions = self._extract_odoo_actions(content, task_id)
                actions.extend(odoo_actions)
            
            # Detect email actions
            if 'email' in content.lower() and '@' in content:
                email_actions = self._extract_email_actions(content, task_id)
                actions.extend(email_actions)
            
            logger.info(f"Extracted {len(actions)} action(s) from {plan_file.name}")
            return actions
            
        except Exception as e:
            logger.error(f"Error parsing plan {plan_file}: {e}")
            return []
    
    def _extract_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter from markdown"""
        try:
            if content.startswith('---'):
                end_idx = content.index('---', 3)
                frontmatter_text = content[3:end_idx]
                frontmatter = {}
                for line in frontmatter_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
                return frontmatter
        except:
            pass
        return {}
    
    def _extract_social_actions(self, content: str, task_id: str) -> List[Dict]:
        """Extract social media post actions from plan"""
        actions = []
        
        # Patterns to detect social platforms
        platforms = {
            'facebook': r'(?i)(facebook|fb).*post',
            'instagram': r'(?i)instagram.*post',
            'linkedin': r'(?i)linkedin.*post',
            'twitter': r'(?i)(twitter|x\.com).*post'
        }
        
        for platform, pattern in platforms.items():
            if re.search(pattern, content):
                # Extract post content (look for content between quotes or in code blocks)
                post_text = self._extract_post_content(content, platform)
                
                if post_text:
                    actions.append({
                        'action_type': 'social_post',
                        'platform': platform,
                        'task_id': task_id,
                        'data': {
                            'text': post_text,
                            'visibility': 'PUBLIC'
                        },
                        'requires_approval': self.approval_thresholds['social_post'],
                        'risk_level': 'medium'
                    })
        
        return actions
    
    def _extract_post_content(self, content: str, platform: str) -> Optional[str]:
        """Extract post text from plan content"""
        # Look for sections like "Post Content:", "Caption:", "Text:"
        patterns = [
            r'(?i)(?:post content|caption|text|message):\s*["\']?(.+?)["\']?\n\n',
            r'(?i)' + platform + r'.*?:\s*["\'](.+?)["\']',
            r'```(?:text)?\n(.+?)```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                text = match.group(1).strip()
                if len(text) > 20:  # Reasonable post length
                    return text[:3000]  # Limit to 3000 chars
        
        return None
    
    def _extract_odoo_actions(self, content: str, task_id: str) -> List[Dict]:
        """Extract Odoo ERP actions (invoices, bills, payments)"""
        actions = []
        
        # Detect invoice creation
        if re.search(r'(?i)(create|generate).*invoice', content):
            invoice_data = self._parse_invoice_data(content)
            if invoice_data:
                amount = invoice_data.get('amount', 0)
                requires_approval = amount > self.approval_thresholds['odoo_invoice_amount']
                
                actions.append({
                    'action_type': 'odoo_invoice',
                    'task_id': task_id,
                    'data': invoice_data,
                    'requires_approval': requires_approval,
                    'risk_level': 'high' if amount > 5000 else 'medium'
                })
        
        # Detect bill creation
        if re.search(r'(?i)(create|record).*bill', content):
            bill_data = self._parse_bill_data(content)
            if bill_data:
                amount = bill_data.get('amount', 0)
                requires_approval = amount > self.approval_thresholds['odoo_bill_amount']
                
                actions.append({
                    'action_type': 'odoo_bill',
                    'task_id': task_id,
                    'data': bill_data,
                    'requires_approval': requires_approval,
                    'risk_level': 'high' if amount > 1000 else 'medium'
                })
        
        # Detect payment recording
        if re.search(r'(?i)(record|process).*payment', content):
            payment_data = self._parse_payment_data(content)
            if payment_data:
                actions.append({
                    'action_type': 'odoo_payment',
                    'task_id': task_id,
                    'data': payment_data,
                    'requires_approval': True,  # Always require approval for payments
                    'risk_level': 'high'
                })
        
        return actions
    
    def _parse_invoice_data(self, content: str) -> Optional[Dict]:
        """Parse invoice details from plan content"""
        try:
            data = {}
            
            # Extract customer/partner name
            partner_match = re.search(r'(?i)(?:customer|partner|client):\s*([^\n]+)', content)
            if partner_match:
                data['partner_name'] = partner_match.group(1).strip()
            
            # Extract amount
            amount_match = re.search(r'(?i)(?:amount|total|price):\s*\$?([0-9,]+\.?\d*)', content)
            if amount_match:
                data['amount'] = float(amount_match.group(1).replace(',', ''))
            
            # Extract description
            desc_match = re.search(r'(?i)(?:description|service|product):\s*([^\n]+)', content)
            if desc_match:
                data['description'] = desc_match.group(1).strip()
            
            # Extract due date if present
            date_match = re.search(r'(?i)due date:\s*([^\n]+)', content)
            if date_match:
                data['due_date'] = date_match.group(1).strip()
            
            return data if 'partner_name' in data and 'amount' in data else None
        except Exception as e:
            logger.error(f"Error parsing invoice data: {e}")
            return None
    
    def _parse_bill_data(self, content: str) -> Optional[Dict]:
        """Parse bill details from plan content"""
        try:
            data = {}
            
            # Extract vendor name
            vendor_match = re.search(r'(?i)(?:vendor|supplier|from):\s*([^\n]+)', content)
            if vendor_match:
                data['vendor_name'] = vendor_match.group(1).strip()
            
            # Extract amount
            amount_match = re.search(r'(?i)(?:amount|total):\s*\$?([0-9,]+\.?\d*)', content)
            if amount_match:
                data['amount'] = float(amount_match.group(1).replace(',', ''))
            
            # Extract reference/description
            ref_match = re.search(r'(?i)(?:reference|description):\s*([^\n]+)', content)
            if ref_match:
                data['reference'] = ref_match.group(1).strip()
            
            return data if 'vendor_name' in data and 'amount' in data else None
        except Exception as e:
            logger.error(f"Error parsing bill data: {e}")
            return None
    
    def _parse_payment_data(self, content: str) -> Optional[Dict]:
        """Parse payment details from plan content"""
        try:
            data = {}
            
            # Extract invoice/bill reference
            ref_match = re.search(r'(?i)invoice #?([A-Z0-9-]+)', content)
            if ref_match:
                data['invoice_ref'] = ref_match.group(1)
            
            # Extract amount
            amount_match = re.search(r'(?i)(?:payment|amount):\s*\$?([0-9,]+\.?\d*)', content)
            if amount_match:
                data['amount'] = float(amount_match.group(1).replace(',', ''))
            
            return data if 'amount' in data else None
        except Exception as e:
            logger.error(f"Error parsing payment data: {e}")
            return None
    
    def _extract_email_actions(self, content: str, task_id: str) -> List[Dict]:
        """Extract email actions from plan"""
        actions = []
        
        # Look for email patterns
        email_match = re.search(r'(?i)send email.*?to:\s*([^\n]+)', content)
        if email_match:
            to_addr = email_match.group(1).strip()
            
            # Extract subject
            subject_match = re.search(r'(?i)subject:\s*([^\n]+)', content)
            subject = subject_match.group(1).strip() if subject_match else "No Subject"
            
            # Extract body (look for content after "body:" or "message:")
            body_match = re.search(r'(?i)(?:body|message):\s*(.+?)(?:\n\n|\Z)', content, re.DOTALL)
            body = body_match.group(1).strip() if body_match else ""
            
            if to_addr and body:
                actions.append({
                    'action_type': 'email',
                    'task_id': task_id,
                    'data': {
                        'to': to_addr,
                        'subject': subject,
                        'body': body
                    },
                    'requires_approval': self.approval_thresholds['email_new_contact'],
                    'risk_level': 'medium'
                })
        
        return actions
    
    def execute_action(self, action: Dict) -> Dict:
        """
        Execute an action via appropriate MCP server
        
        Returns:
        {
            'status': 'success' | 'failed' | 'requires_approval',
            'message': str,
            'result': Dict  # MCP server response
        }
        """
        action_type = action['action_type']
        
        # Check if approval required
        if action['requires_approval']:
            return self.create_approval_request(action)
        
        # Execute based on action type
        if action_type == 'social_post':
            return self._execute_social_post(action)
        elif action_type == 'odoo_invoice':
            return self._execute_odoo_invoice(action)
        elif action_type == 'odoo_bill':
            return self._execute_odoo_bill(action)
        elif action_type == 'odoo_payment':
            return self._execute_odoo_payment(action)
        elif action_type == 'email':
            return self._execute_email(action)
        else:
            return {
                'status': 'failed',
                'message': f'Unknown action type: {action_type}'
            }
    
    def create_approval_request(self, action: Dict) -> Dict:
        """Create a HITL approval request file"""
        try:
            task_id = action['task_id']
            action_type = action['action_type']
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            
            # CRITICAL FIX: Include platform/identifier to make filenames unique
            # Prevents overwriting when multiple actions are created simultaneously
            unique_id = ""
            if action_type == 'social_post' and 'platform' in action:
                unique_id = f"_{action['platform']}"
            elif action_type == 'email' and 'data' in action:
                unique_id = f"_{action['data'].get('to', '').replace('@', '_at_')[:20]}"
            elif action_type in ['odoo_invoice', 'odoo_bill'] and 'data' in action:
                partner = action['data'].get('partner_name', action['data'].get('vendor_name', ''))
                unique_id = f"_{partner.replace(' ', '_')[:15]}"
            
            filename = f"APPROVAL_{action_type}{unique_id}_{task_id}_{timestamp}.md"
            filepath = self.pending_approval / filename
            
            # Create approval request content
            content = f"""---
action: {action_type}
task_id: {task_id}
created: {datetime.now(timezone.utc).isoformat()}
risk_level: {action['risk_level']}
status: pending
---

# Approval Request: {action_type.replace('_', ' ').title()}

## Action Details

"""
            
            # Add action-specific details
            if action_type == 'social_post':
                content += f"""**Platform**: {action.get('platform', 'unknown')}
**Text Preview**: 
```
{action['data'].get('text', '')[:500]}
```

## To Approve
Move this file to `/Approved/` folder or rename to `.approved.md`

## To Reject
Move this file to `/Rejected/` folder or rename to `.rejected.md`
"""
            
            elif action_type in ['odoo_invoice', 'odoo_bill']:
                data = action['data']
                content += f"""**{'Customer' if action_type == 'odoo_invoice' else 'Vendor'}**: {data.get('partner_name' if action_type == 'odoo_invoice' else 'vendor_name', 'Unknown')}
**Amount**: ${data.get('amount', 0):,.2f}
**Description**: {data.get('description' if action_type == 'odoo_invoice' else 'reference', 'N/A')}
{'**Due Date**: ' + data.get('due_date', 'Net 30') if action_type == 'odoo_invoice' else ''}

⚠️  **Requires Approval** - Amount exceeds ${self.approval_thresholds['odoo_invoice_amount' if action_type == 'odoo_invoice' else 'odoo_bill_amount']:,.2f} threshold

## To Approve
Move this file to `/Approved/` folder

## To Reject
Move this file to `/Rejected/` folder
"""
            
            elif action_type == 'email':
                data = action['data']
                content += f"""**To**: {data.get('to')}
**Subject**: {data.get('subject')}
**Body Preview**:
```
{data.get('body', '')[:300]}...
```

## To Approve
Move this file to `/Approved/` folder

## To Reject  
Move this file to `/Rejected/` folder
"""
            
            # Write approval request
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created approval request: {filename}")
            
            return {
                'status': 'requires_approval',
                'message': f'Approval request created: {filename}',
                'approval_file': str(filepath)
            }
            
        except Exception as e:
            logger.error(f"Failed to create approval request: {e}")
            return {
                'status': 'failed',
                'message': f'Failed to create approval request: {e}'
            }
    
    def _execute_social_post(self, action: Dict) -> Dict:
        """Execute social media post via MCP server"""
        platform = action.get('platform', 'unknown')
        text = action['data'].get('text', '')
        
        try:
            if platform == 'facebook':
                from facebook_server import FacebookServer
                server = FacebookServer()
                result = server.post_message(message=text)
                
            elif platform == 'instagram':
                from instagram_server import InstagramServer
                server = InstagramServer()
                # Instagram requires image - use Unsplash placeholder
                result = server.post_photo(
                    image_url='https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=1080',
                    caption=text
                )
                
            elif platform == 'linkedin':
                from linkedin_server import LinkedInMCPServer
                server = LinkedInMCPServer()
                result = server.post_update(
                    text=text,
                    visibility=action['data'].get('visibility', 'PUBLIC')
                )
                
            elif platform == 'twitter':
                from twitter_server import TwitterServer
                server = TwitterServer()
                result = server.post_tweet(text=text)
            
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            logger.info(f"Posted to {platform}: {result}")
            
            # Log the action
            self._log_action({
                'action_type': 'social_post',
                'platform': platform,
                'status': 'success',
                'result': result
            })
            
            return {
                'status': 'success',
                'message': f'Successfully posted to {platform}',
                'result': result
            }
            
        except ImportError as e:
            logger.error(f"MCP server not available for {platform}: {e}")
            return {
                'status': 'failed',
                'message': f'MCP server not available: {e}'
            }
        except Exception as e:
            logger.error(f"Failed to post to {platform}: {e}")
            return {
                'status': 'failed',
                'message': str(e)
            }
    
    def _execute_odoo_invoice(self, action: Dict) -> Dict:
        """Execute Odoo invoice creation"""
        try:
            from odoo_server import OdooServer
            
            data = action['data']
            server = OdooServer()
            
            # Create invoice
            result = server.create_invoice(
                partner_name=data['partner_name'],
                amount=data['amount'],
                description=data.get('description', 'Auto-generated invoice')
            )
            
            logger.info(f"Created Odoo invoice: {result}")
            
            self._log_action({
                'action_type': 'odoo_invoice',
                'status': 'success',
                'result': result
            })
            
            return {
                'status': 'success',
                'message': f'Invoice created: {result.get("invoice_number")}',
                'result': result
            }
            
        except ImportError:
            logger.error("Odoo MCP server not available")
            return {
                'status': 'failed',
                'message': 'Odoo MCP server not available'
            }
        except Exception as e:
            logger.error(f"Failed to create Odoo invoice: {e}")
            return {
                'status': 'failed',
                'message': str(e)
            }
    
    def _execute_odoo_bill(self, action: Dict) -> Dict:
        """Execute Odoo bill creation"""
        try:
            from odoo_server import OdooServer
            
            data = action['data']
            server = OdooServer()
            
            result = server.create_bill(
                vendor_name=data['vendor_name'],
                amount=data['amount'],
                description=data.get('reference', 'Auto-generated bill')
            )
            
            logger.info(f"Created Odoo bill: {result}")
            
            self._log_action({
                'action_type': 'odoo_bill',
                'status': 'success',
                'result': result
            })
            
            return {
                'status': 'success',
                'message': f'Bill created: {result.get("bill_number")}',
                'result': result
            }
            
        except ImportError:
            logger.error("Odoo MCP server not available")
            return {
                'status': 'failed',
                'message': 'Odoo MCP server not available'
            }
        except Exception as e:
            logger.error(f"Failed to create Odoo bill: {e}")
            return {
                'status': 'failed',
                'message': str(e)
            }
    
    def _execute_odoo_payment(self, action: Dict) -> Dict:
        """Execute Odoo payment recording"""
        try:
            from odoo_server import OdooServer
            
            data = action['data']
            server = OdooServer()
            
            result = server.record_payment(
                invoice_id=data.get('invoice_id', 0),
                amount=data['amount'],
                payment_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            logger.info(f"Recorded Odoo payment: {result}")
            
            self._log_action({
                'action_type': 'odoo_payment',
                'status': 'success',
                'result': result
            })
            
            return {
                'status': 'success',
                'message': f'Payment recorded',
                'result': result
            }
            
        except ImportError:
            logger.error("Odoo MCP server not available")
            return {
                'status': 'failed',
                'message': 'Odoo MCP server not available'
            }
        except Exception as e:
            logger.error(f"Failed to record payment: {e}")
            return {
                'status': 'failed',
                'message': str(e)
            }
    
    def _execute_email(self, action: Dict) -> Dict:
        """Execute email via Gmail MCP server"""
        try:
            from email_server import EmailMCP
            
            data = action['data']
            server = EmailMCP()
            
            result = server.send_email(
                to=data['to'],
                subject=data['subject'],
                body=data['body']
            )
            
            logger.info(f"Sent email: {result}")
            
            self._log_action({
                'action_type': 'email',
                'status': 'success',
                'to': data['to'],
                'subject': data['subject'],
                'result': result
            })
            
            return {
                'status': 'success',
                'message': f'Email sent to {data["to"]}',
                'result': result
            }
            
        except ImportError:
            logger.error("Email MCP server not available")
            return {
                'status': 'failed',
                'message': 'Email MCP server not available'
            }
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                'status': 'failed',
                'message': str(e)
            }
    
    def _log_action(self, action_data: Dict):
        """Write action to daily audit log"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self.logs / f"{today}.json"
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **action_data
        }
        
        # Append to daily log file
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text(encoding='utf-8'))
            except:
                logs = []
        else:
            logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')
    
    def process_approved_file(self, approved_file: Path) -> Dict:
        """
        Process an approved action file from /Approved folder
        
        Extracts action details and executes via MCP
        """
        try:
            content = approved_file.read_text(encoding='utf-8')
            frontmatter = self._extract_frontmatter(content)
            
            action_type = frontmatter.get('action', '')
            task_id = frontmatter.get('task_id', approved_file.stem)
            
            # Reconstruct action dict
            action = {
                'action_type': action_type,
                'task_id': task_id,
                'data': {},
                'requires_approval': False,  # Already approved
                'risk_level': frontmatter.get('risk_level', 'medium')
            }
            
            # Parse action-specific data from content
            if action_type == 'social_post':
                platform_match = re.search(r'\*\*Platform\*\*:\s*(\w+)', content)
                text_match = re.search(r'```\n(.+?)\n```', content, re.DOTALL)
                
                if platform_match and text_match:
                    action['data'] = {
                        'platform': platform_match.group(1).lower(),
                        'text': text_match.group(1).strip()
                    }
                    return self._execute_social_post(action)
            
            elif action_type in ['odoo_invoice', 'odoo_bill']:
                # Parse Odoo action details
                partner_match = re.search(r'\*\*(?:Customer|Vendor)\*\*:\s*([^\n]+)', content)
                amount_match = re.search(r'\*\*Amount\*\*:\s*\$([0-9,.]+)', content)
                desc_match = re.search(r'\*\*Description\*\*:\s*([^\n]+)', content)
                
                if partner_match and amount_match:
                    action['data'] = {
                        ('partner_name' if action_type == 'odoo_invoice' else 'vendor_name'): partner_match.group(1).strip(),
                        'amount': float(amount_match.group(1).replace(',', '')),
                        ('description' if action_type == 'odoo_invoice' else 'reference'): desc_match.group(1).strip() if desc_match else ''
                    }
                    
                    if action_type == 'odoo_invoice':
                        return self._execute_odoo_invoice(action)
                    else:
                        return self._execute_odoo_bill(action)
            
            elif action_type == 'email':
                to_match = re.search(r'\*\*To\*\*:\s*([^\n]+)', content)
                subject_match = re.search(r'\*\*Subject\*\*:\s*([^\n]+)', content)
                body_match = re.search(r'```\n(.+?)\n```', content, re.DOTALL)
                
                if to_match and subject_match and body_match:
                    action['data'] = {
                        'to': to_match.group(1).strip(),
                        'subject': subject_match.group(1).strip(),
                        'body': body_match.group(1).strip()
                    }
                    return self._execute_email(action)
            
            return {
                'status': 'failed',
                'message': f'Could not parse approved action: {action_type}'
            }
            
        except Exception as e:
            logger.error(f"Error processing approved file {approved_file}: {e}")
            return {
                'status': 'failed',
                'message': str(e)
            }
