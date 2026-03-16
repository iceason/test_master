"""
告警管理系统
"""

import logging
import requests
from typing import List, Dict, Any
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_and_alert(self, batch):
        """
        检查批次结果并发送告警
        
        Args:
            batch: TestExecutionBatch实例
        """
        alerts = []
        
        # 失败率告警
        if batch.total_cases > 0:
            failure_rate = (batch.failed_cases + batch.error_cases) / batch.total_cases
            if failure_rate > 0.2:  # 失败率超过20%
                alerts.append({
                    'severity': 'high',
                    'title': f'测试失败率告警: {failure_rate:.1%}',
                    'message': f'批次 {batch.batch_id} 失败率过高\n'
                              f'总用例: {batch.total_cases}, '
                              f'失败: {batch.failed_cases}, '
                              f'错误: {batch.error_cases}',
                    'channels': ['email', 'slack']
                })
        
        # 性能告警
        if batch.duration_ms and batch.duration_ms > 600000:  # 超过10分钟
            alerts.append({
                'severity': 'warning',
                'title': '测试执行超时',
                'message': f'批次 {batch.batch_id} 执行时间过长: {batch.duration_ms / 1000:.1f}秒',
                'channels': ['slack']
            })
        
        # 发送告警
        for alert in alerts:
            self.send_alert(**alert)
    
    def send_alert(self, severity: str, title: str, message: str, channels: List[str]):
        """
        发送告警到多个渠道
        
        Args:
            severity: 严重程度（info/warning/high/critical）
            title: 告警标题
            message: 告警消息
            channels: 通知渠道列表
        """
        for channel in channels:
            try:
                if channel == 'email':
                    self._send_email(severity, title, message)
                elif channel == 'slack':
                    self._send_slack(severity, title, message)
                elif channel == 'webhook':
                    self._send_webhook(severity, title, message)
                elif channel == 'dingtalk':
                    self._send_dingtalk(severity, title, message)
            except Exception as e:
                self.logger.error(f"发送{channel}告警失败: {e}", exc_info=True)
    
    def _send_email(self, severity: str, title: str, message: str):
        """发送邮件告警"""
        recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
        if not recipients:
            self.logger.warning("未配置告警邮件接收人")
            return
        
        try:
            send_mail(
                subject=f'[{severity.upper()}] {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False
            )
            self.logger.info(f"邮件告警已发送: {title}")
        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}", exc_info=True)
    
    def _send_slack(self, severity: str, title: str, message: str):
        """发送Slack告警"""
        webhook_url = getattr(settings, 'ALERT_SLACK_WEBHOOK', None)
        if not webhook_url:
            self.logger.warning("未配置Slack Webhook")
            return
        
        color_map = {
            'info': '#36a64f',
            'warning': '#ff9900',
            'high': '#ff0000',
            'critical': '#8B0000'
        }
        
        payload = {
            'attachments': [{
                'color': color_map.get(severity, '#808080'),
                'title': title,
                'text': message,
                'footer': 'TestMaster Alert',
                'ts': int(__import__('time').time())
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Slack告警已发送: {title}")
        except Exception as e:
            self.logger.error(f"发送Slack消息失败: {e}", exc_info=True)
    
    def _send_dingtalk(self, severity: str, title: str, message: str):
        """发送钉钉告警"""
        webhook_url = getattr(settings, 'ALERT_DINGTALK_WEBHOOK', None)
        if not webhook_url:
            self.logger.warning("未配置钉钉Webhook")
            return
        
        payload = {
            'msgtype': 'markdown',
            'markdown': {
                'title': title,
                'text': f'## {title}\n\n{message}'
            }
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            self.logger.info(f"钉钉告警已发送: {title}")
        except Exception as e:
            self.logger.error(f"发送钉钉消息失败: {e}", exc_info=True)
    
    def _send_webhook(self, severity: str, title: str, message: str):
        """发送通用Webhook告警"""
        webhook_url = getattr(settings, 'ALERT_WEBHOOK_URL', None)
        if not webhook_url:
            self.logger.warning("未配置Webhook URL")
            return
        
        payload = {
            'severity': severity,
            'title': title,
            'message': message,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'source': 'testmaster'
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Webhook告警已发送: {title}")
        except Exception as e:
            self.logger.error(f"发送Webhook失败: {e}", exc_info=True)
