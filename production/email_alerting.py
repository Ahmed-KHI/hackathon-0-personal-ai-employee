"""
Personal AI Employee - Email Alerting System

Sends email notifications for critical system events.
Integrates with orchestrator for real-time monitoring.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmailAlerter:
    """
    Email notification system for critical events.
    
    Supports:
    - Ralph Loop threshold exceeded
    - HITL approval timeouts
    - System errors
    - Daily status summaries
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_email = os.getenv("ALERT_EMAIL", self.smtp_username)
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        
        self.enabled = all([self.smtp_username, self.smtp_password, self.alert_email])
        
        if not self.enabled:
            logger.warning("Email alerting disabled: Missing SMTP credentials in .env")
        else:
            logger.info(f"Email alerting enabled. Alerts sent to: {self.alert_email}")
    
    def send_alert(
        self,
        subject: str,
        body: str,
        priority: str = "normal",
        task_id: Optional[str] = None
    ) -> bool:
        """
        Send email alert.
        
        Args:
            subject: Email subject
            body: Email body (supports HTML)
            priority: "low", "normal", "high", "critical"
            task_id: Associated task ID
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.warning(f"Email alert not sent (disabled): {subject}")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.alert_email
            msg['Subject'] = f"[{priority.upper()}] {subject}"
            
            # Add headers
            msg['X-Priority'] = '1' if priority == "critical" else '3'
            if task_id:
                msg['X-Task-ID'] = task_id
            
            # HTML body
            html_body = self._format_html(subject, body, priority, task_id)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False
    
    def _format_html(self, subject: str, body: str, priority: str, task_id: Optional[str]) -> str:
        """Format alert as HTML email."""
        priority_colors = {
            "low": "#28a745",
            "normal": "#17a2b8",
            "high": "#ffc107",
            "critical": "#dc3545"
        }
        color = priority_colors.get(priority, "#17a2b8")
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f8f9fa; margin-top: 10px; border-radius: 5px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #6c757d; }}
                .metadata {{ font-size: 12px; color: #6c757d; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Personal AI Employee Alert</h2>
                <p>{subject}</p>
            </div>
            <div class="content">
                {body.replace(chr(10), '<br>')}
            </div>
            <div class="metadata">
                <strong>Priority:</strong> {priority.upper()}<br>
                <strong>Timestamp:</strong> {datetime.now(timezone.utc).isoformat()}<br>
                {f'<strong>Task ID:</strong> {task_id}<br>' if task_id else ''}
                <strong>System:</strong> Personal AI Employee v1.0.0
            </div>
            <div class="footer">
                This is an automated alert from your Personal AI Employee system.
            </div>
        </body>
        </html>
        """
        return html
    
    def alert_ralph_loop(self, task_id: str, iterations: int, max_iterations: int):
        """Alert when task exceeds Ralph Loop threshold."""
        subject = f"Ralph Loop Warning: Task {task_id[:8]}"
        body = f"""
        Task has exceeded iteration threshold!
        
        Task ID: {task_id}
        Current Iterations: {iterations}
        Maximum Allowed: {max_iterations}
        
        Action Required:
        - Check task in task_queue/pending/
        - Review audit logs for errors
        - Consider manual intervention
        """
        self.send_alert(subject, body, priority="high", task_id=task_id)
    
    def alert_hitl_timeout(self, task_id: str, hours_pending: int):
        """Alert when HITL approval is pending too long."""
        subject = f"HITL Approval Timeout: Task {task_id[:8]}"
        body = f"""
        Human approval required but not received!
        
        Task ID: {task_id}
        Time Pending: {hours_pending} hours
        Location: task_queue/approvals/{task_id}.json
        
        Action Required:
        - Review approval request
        - Rename file to .approved or .rejected
        """
        priority = "critical" if hours_pending > 48 else "high"
        self.send_alert(subject, body, priority=priority, task_id=task_id)
    
    def alert_system_error(self, component: str, error_message: str):
        """Alert on critical system errors."""
        subject = f"System Error: {component}"
        body = f"""
        Critical error in {component}!
        
        Error: {error_message}
        
        Action Required:
        - Check service status: Get-Service PersonalAI_*
        - Review error logs: logs/{component}_service_error.log
        - Restart if needed: Restart-Service PersonalAI_*
        """
        self.send_alert(subject, body, priority="critical")
    
    def send_daily_summary(self, stats: Dict[str, Any]):
        """Send daily status summary."""
        subject = f"Daily Summary: {datetime.now().strftime('%Y-%m-%d')}"
        body = f"""
        Daily Status Report
        
        Tasks:
        - Completed: {stats.get('completed_tasks', 0)}
        - Pending HITL: {stats.get('pending_hitl', 0)}
        - Failed: {stats.get('failed_tasks', 0)}
        
        Performance:
        - Success Rate: {stats.get('success_rate', 0):.1f}%
        - Average Confidence: {stats.get('avg_confidence', 0):.2f}
        - Total API Cost: ${stats.get('api_cost', 0):.4f}
        
        System Health:
        - Orchestrator Uptime: {stats.get('orchestrator_uptime', 'Unknown')}
        - Watcher Uptime: {stats.get('watcher_uptime', 'Unknown')}
        - Disk Space: {stats.get('disk_space', 'Unknown')}
        
        All systems operational.
        """
        self.send_alert(subject, body, priority="low")


def main():
    """Test email alerting."""
    print("Testing Email Alerting System...")
    print()
    
    alerter = EmailAlerter()
    
    if not alerter.enabled:
        print("❌ Email alerting is disabled")
        print("   Configure SMTP settings in .env:")
        print("   - SMTP_SERVER=smtp.gmail.com")
        print("   - SMTP_PORT=587")
        print("   - SMTP_USERNAME=your-email@gmail.com")
        print("   - SMTP_PASSWORD=your-app-password")
        print("   - ALERT_EMAIL=recipient@example.com")
        return
    
    print("✅ Email alerting is enabled")
    print(f"   Sending test alert to: {alerter.alert_email}")
    print()
    
    # Send test alert
    success = alerter.send_alert(
        subject="Test Alert",
        body="This is a test alert from your Personal AI Employee system. If you received this, email alerting is working correctly!",
        priority="normal"
    )
    
    if success:
        print("✅ Test alert sent successfully!")
    else:
        print("❌ Failed to send test alert")


if __name__ == "__main__":
    main()
