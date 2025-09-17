"""
Communication Query Handler
Handles notification and communication-related queries
"""

import logging
from typing import Dict, List, Any
from .base_handler import BaseQueryHandler

logger = logging.getLogger(__name__)

class CommunicationQueryHandler(BaseQueryHandler):
    """Handles communication-related queries"""
    
    async def get_supported_intents(self) -> List[str]:
        """Return supported communication intents"""
        return [
            "query_notification_history",
            "query_notification_audit"
        ]
    
    async def handle_query(self, intent: str, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Route communication queries to appropriate handlers"""
        try:
            if intent == "query_notification_history":
                return await self.handle_notification_history_query(message, context)
            elif intent == "query_notification_audit":
                return await self.handle_notification_audit_query(message, context)
            else:
                return self.create_error_response(intent, Exception(f"Unsupported intent: {intent}"))
                
        except Exception as e:
            return self.create_error_response(intent, e)
    
    async def handle_notification_history_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle notification history queries"""
        try:
            # Get notification audit data
            audit_data = await self.communication_client.get_notification_audit()
            
            if not audit_data:
                return self.create_success_response(
                    "query_notification_history",
                    "📧 **No notification history found**\n\nNo notifications have been sent yet. Configure notification channels and send some notifications to see history!",
                    {"notifications_count": 0}
                )
            
            message_lower = message.lower()
            
            # Filter notifications based on query
            if 'failed' in message_lower or 'failure' in message_lower:
                filtered_notifications = [n for n in audit_data if n.get('delivery_status') == 'failed']
                filter_desc = "failed notifications"
            elif 'success' in message_lower or 'delivered' in message_lower:
                filtered_notifications = [n for n in audit_data if n.get('delivery_status') == 'delivered']
                filter_desc = "successful notifications"
            elif 'email' in message_lower:
                filtered_notifications = [n for n in audit_data if n.get('channel_type') == 'email']
                filter_desc = "email notifications"
            elif 'slack' in message_lower:
                filtered_notifications = [n for n in audit_data if n.get('channel_type') == 'slack']
                filter_desc = "Slack notifications"
            elif 'sms' in message_lower:
                filtered_notifications = [n for n in audit_data if n.get('channel_type') == 'sms']
                filter_desc = "SMS notifications"
            elif 'today' in message_lower:
                from datetime import date
                today = date.today().strftime('%Y-%m-%d')
                filtered_notifications = [n for n in audit_data if n.get('sent_at', '').startswith(today)]
                filter_desc = "today's notifications"
            elif 'recent' in message_lower or 'latest' in message_lower:
                filtered_notifications = audit_data[:15]  # Recent 15
                filter_desc = "recent notifications"
            else:
                filtered_notifications = audit_data[:20]  # Recent 20
                filter_desc = "recent notifications"
            
            response = f"📧 **Notification History - {filter_desc.title()}**\n\n"
            response += f"**Found:** {len(filtered_notifications)} notifications\n\n"
            
            if not filtered_notifications:
                response += f"No {filter_desc} found.\n"
                response += f"Total notifications: {len(audit_data)}\n\n"
                
                # Suggest alternatives
                if 'failed' in message_lower:
                    delivered_count = len([n for n in audit_data if n.get('delivery_status') == 'delivered'])
                    if delivered_count > 0:
                        response += f"💡 **Good news:** {delivered_count} notifications were delivered successfully!"
                elif 'email' in message_lower:
                    other_channels = len([n for n in audit_data if n.get('channel_type') != 'email'])
                    if other_channels > 0:
                        response += f"💡 **Info:** Found {other_channels} notifications via other channels."
            else:
                # Show notification details
                for i, notification in enumerate(filtered_notifications[:8]):
                    recipient = notification.get('recipient', 'Unknown')
                    subject = notification.get('subject', 'No subject')
                    delivery_status = notification.get('delivery_status', 'unknown')
                    sent_at = notification.get('sent_at', 'Unknown')
                    channel_type = notification.get('channel_type', 'unknown')
                    message_preview = notification.get('message', '')[:50]
                    
                    status_emoji = '✅' if delivery_status == 'delivered' else '❌' if delivery_status == 'failed' else '⏳'
                    channel_emoji = '📧' if channel_type == 'email' else '💬' if channel_type == 'slack' else '📱' if channel_type == 'sms' else '📢'
                    
                    response += f"**{i+1}. {subject[:50]}{'...' if len(subject) > 50 else ''}** {status_emoji}\n"
                    response += f"   • Recipient: {recipient}\n"
                    response += f"   • Channel: {channel_type} {channel_emoji}\n"
                    response += f"   • Status: {delivery_status}\n"
                    response += f"   • Sent: {sent_at}\n"
                    
                    if message_preview:
                        response += f"   • Preview: {message_preview}{'...' if len(notification.get('message', '')) > 50 else ''}\n"
                    
                    response += "\n"
                
                if len(filtered_notifications) > 8:
                    response += f"... and {len(filtered_notifications) - 8} more notifications\n\n"
                
                # Delivery statistics
                delivered_count = len([n for n in filtered_notifications if n.get('delivery_status') == 'delivered'])
                failed_count = len([n for n in filtered_notifications if n.get('delivery_status') == 'failed'])
                pending_count = len(filtered_notifications) - delivered_count - failed_count
                
                response += f"**Delivery Statistics:**\n"
                response += f"• Delivered: {delivered_count} ({(delivered_count/len(filtered_notifications)*100):.1f}%)\n"
                response += f"• Failed: {failed_count} ({(failed_count/len(filtered_notifications)*100):.1f}%)\n"
                
                if pending_count > 0:
                    response += f"• Pending: {pending_count}\n"
                
                # Channel breakdown
                channel_stats = {}
                for notification in filtered_notifications:
                    channel = notification.get('channel_type', 'unknown')
                    channel_stats[channel] = channel_stats.get(channel, 0) + 1
                
                if len(channel_stats) > 1:
                    response += f"\n**Channel Breakdown:**\n"
                    for channel, count in sorted(channel_stats.items(), key=lambda x: x[1], reverse=True):
                        channel_emoji = '📧' if channel == 'email' else '💬' if channel == 'slack' else '📱' if channel == 'sms' else '📢'
                        response += f"• {channel.title()}: {count} notifications {channel_emoji}\n"
                
                # Recipient analysis
                recipient_stats = {}
                for notification in filtered_notifications:
                    recipient = notification.get('recipient', 'unknown')
                    recipient_stats[recipient] = recipient_stats.get(recipient, 0) + 1
                
                if len(recipient_stats) > 1:
                    response += f"\n**Top Recipients:**\n"
                    for recipient, count in sorted(recipient_stats.items(), key=lambda x: x[1], reverse=True)[:3]:
                        response += f"• {recipient}: {count} notifications\n"
                
                # Time analysis
                if len(filtered_notifications) > 5:
                    # Group by hour to find peak notification times
                    hour_stats = {}
                    for notification in filtered_notifications:
                        sent_at = notification.get('sent_at', '')
                        if sent_at and len(sent_at) >= 13:  # YYYY-MM-DD HH format
                            try:
                                hour = sent_at[11:13]
                                hour_stats[hour] = hour_stats.get(hour, 0) + 1
                            except:
                                pass
                    
                    if hour_stats:
                        peak_hour = max(hour_stats.items(), key=lambda x: x[1])
                        response += f"\n**Peak Activity:** {peak_hour[1]} notifications at {peak_hour[0]}:00\n"
            
            return self.create_success_response(
                "query_notification_history",
                response,
                {
                    "notifications_found": len(filtered_notifications),
                    "total_notifications": len(audit_data),
                    "filter_description": filter_desc,
                    "delivered_count": len([n for n in filtered_notifications if n.get('delivery_status') == 'delivered']),
                    "failed_count": len([n for n in filtered_notifications if n.get('delivery_status') == 'failed'])
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_notification_history", e)
    
    async def handle_notification_audit_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle notification audit queries"""
        try:
            # Get notification audit data from communication service
            audit_data = await self.communication_client.get_notification_audit()
            
            if not audit_data:
                return self.create_success_response(
                    "query_notification_audit",
                    "📧 **No notification audit data found**\n\nNo notification delivery records available. Send some notifications to see audit trail.",
                    {"audit_records": 0}
                )
            
            message_lower = message.lower()
            
            # Filter audit data based on query
            if 'failed' in message_lower or 'failure' in message_lower:
                filtered_records = [r for r in audit_data if r.get('delivery_status') == 'failed']
                filter_desc = "failed deliveries"
            elif 'success' in message_lower or 'delivered' in message_lower:
                filtered_records = [r for r in audit_data if r.get('delivery_status') == 'delivered']
                filter_desc = "successful deliveries"
            elif 'email' in message_lower:
                filtered_records = [r for r in audit_data if r.get('channel_type') == 'email']
                filter_desc = "email notifications"
            elif 'slack' in message_lower:
                filtered_records = [r for r in audit_data if r.get('channel_type') == 'slack']
                filter_desc = "Slack notifications"
            elif 'today' in message_lower:
                from datetime import date
                today = date.today().strftime('%Y-%m-%d')
                filtered_records = [r for r in audit_data if r.get('sent_at', '').startswith(today)]
                filter_desc = "today's notifications"
            elif 'error' in message_lower:
                filtered_records = [r for r in audit_data if r.get('error_message', '')]
                filter_desc = "notifications with errors"
            else:
                filtered_records = audit_data[:20]  # Recent 20
                filter_desc = "recent notifications"
            
            response = f"📧 **Notification Audit - {filter_desc.title()}**\n\n"
            response += f"**Found:** {len(filtered_records)} records\n\n"
            
            if not filtered_records:
                response += f"No {filter_desc} found.\n"
                response += f"Total audit records: {len(audit_data)}\n\n"
                
                if filter_desc == "failed deliveries":
                    response += "🎉 **Excellent!** No failed deliveries found. Your notification system is working perfectly!"
                elif filter_desc == "notifications with errors":
                    response += "✅ **Great!** No error messages in notification logs."
            else:
                # Show audit details
                for i, record in enumerate(filtered_records[:8]):
                    recipient = record.get('recipient', 'Unknown')
                    subject = record.get('subject', 'No subject')
                    delivery_status = record.get('delivery_status', 'unknown')
                    sent_at = record.get('sent_at', 'Unknown')
                    channel_type = record.get('channel_type', 'unknown')
                    error_message = record.get('error_message', '')
                    retry_count = record.get('retry_count', 0)
                    delivery_time = record.get('delivery_time_ms', 0)
                    
                    status_emoji = '✅' if delivery_status == 'delivered' else '❌' if delivery_status == 'failed' else '⏳'
                    channel_emoji = '📧' if channel_type == 'email' else '💬' if channel_type == 'slack' else '📱' if channel_type == 'sms' else '📢'
                    
                    response += f"**{i+1}. {subject[:50]}{'...' if len(subject) > 50 else ''}** {status_emoji}\n"
                    response += f"   • Recipient: {recipient}\n"
                    response += f"   • Channel: {channel_type} {channel_emoji}\n"
                    response += f"   • Status: {delivery_status}\n"
                    response += f"   • Sent: {sent_at}\n"
                    
                    if delivery_time > 0:
                        response += f"   • Delivery Time: {delivery_time}ms\n"
                    
                    if retry_count > 0:
                        response += f"   • Retries: {retry_count}\n"
                    
                    if error_message:
                        response += f"   • Error: {error_message[:100]}{'...' if len(error_message) > 100 else ''}\n"
                    
                    response += "\n"
                
                if len(filtered_records) > 8:
                    response += f"... and {len(filtered_records) - 8} more records\n\n"
                
                # Delivery statistics
                delivered_count = len([r for r in filtered_records if r.get('delivery_status') == 'delivered'])
                failed_count = len([r for r in filtered_records if r.get('delivery_status') == 'failed'])
                pending_count = len(filtered_records) - delivered_count - failed_count
                
                response += f"**Delivery Statistics:**\n"
                response += f"• Delivered: {delivered_count} ({(delivered_count/len(filtered_records)*100):.1f}%)\n"
                response += f"• Failed: {failed_count} ({(failed_count/len(filtered_records)*100):.1f}%)\n"
                
                if pending_count > 0:
                    response += f"• Pending: {pending_count}\n"
                
                # Performance metrics
                delivery_times = [r.get('delivery_time_ms', 0) for r in filtered_records if r.get('delivery_time_ms', 0) > 0]
                if delivery_times:
                    avg_delivery_time = sum(delivery_times) / len(delivery_times)
                    max_delivery_time = max(delivery_times)
                    response += f"\n**Performance:**\n"
                    response += f"• Avg Delivery Time: {avg_delivery_time:.0f}ms\n"
                    response += f"• Max Delivery Time: {max_delivery_time}ms\n"
                
                # Error analysis
                error_records = [r for r in filtered_records if r.get('error_message', '')]
                if error_records:
                    error_types = {}
                    for record in error_records:
                        error_msg = record.get('error_message', '').lower()
                        if 'timeout' in error_msg:
                            error_types['timeout'] = error_types.get('timeout', 0) + 1
                        elif 'authentication' in error_msg or 'auth' in error_msg:
                            error_types['authentication'] = error_types.get('authentication', 0) + 1
                        elif 'network' in error_msg or 'connection' in error_msg:
                            error_types['network'] = error_types.get('network', 0) + 1
                        elif 'invalid' in error_msg:
                            error_types['invalid_recipient'] = error_types.get('invalid_recipient', 0) + 1
                        else:
                            error_types['other'] = error_types.get('other', 0) + 1
                    
                    response += f"\n**Error Categories:**\n"
                    for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                        response += f"• {error_type.replace('_', ' ').title()}: {count} errors\n"
                
                # Channel breakdown
                channel_stats = {}
                for record in filtered_records:
                    channel = record.get('channel_type', 'unknown')
                    status = record.get('delivery_status', 'unknown')
                    
                    if channel not in channel_stats:
                        channel_stats[channel] = {'total': 0, 'delivered': 0, 'failed': 0}
                    
                    channel_stats[channel]['total'] += 1
                    if status == 'delivered':
                        channel_stats[channel]['delivered'] += 1
                    elif status == 'failed':
                        channel_stats[channel]['failed'] += 1
                
                if len(channel_stats) > 1:
                    response += f"\n**Channel Performance:**\n"
                    for channel, stats in sorted(channel_stats.items()):
                        total = stats['total']
                        delivered = stats['delivered']
                        success_rate = (delivered / total * 100) if total > 0 else 0
                        
                        channel_emoji = '📧' if channel == 'email' else '💬' if channel == 'slack' else '📱' if channel == 'sms' else '📢'
                        health_emoji = '🟢' if success_rate >= 95 else '🟡' if success_rate >= 80 else '🔴'
                        
                        response += f"• {channel.title()}: {success_rate:.1f}% success rate {channel_emoji} {health_emoji}\n"
                
                # Retry analysis
                retry_records = [r for r in filtered_records if r.get('retry_count', 0) > 0]
                if retry_records:
                    total_retries = sum(r.get('retry_count', 0) for r in retry_records)
                    avg_retries = total_retries / len(retry_records)
                    response += f"\n**Retry Analysis:**\n"
                    response += f"• Records with retries: {len(retry_records)}\n"
                    response += f"• Average retries: {avg_retries:.1f}\n"
                    response += f"• Total retry attempts: {total_retries}\n"
                
                # Recommendations
                if failed_count > 0:
                    response += f"\n**🔧 Recommendations:**\n"
                    if error_types.get('timeout', 0) > 0:
                        response += "• Consider increasing timeout values\n"
                    if error_types.get('authentication', 0) > 0:
                        response += "• Check authentication credentials\n"
                    if error_types.get('network', 0) > 0:
                        response += "• Verify network connectivity\n"
                    if error_types.get('invalid_recipient', 0) > 0:
                        response += "• Validate recipient addresses\n"
            
            return self.create_success_response(
                "query_notification_audit",
                response,
                {
                    "audit_records": len(filtered_records),
                    "total_records": len(audit_data),
                    "filter_description": filter_desc,
                    "delivered_count": len([r for r in filtered_records if r.get('delivery_status') == 'delivered']),
                    "failed_count": len([r for r in filtered_records if r.get('delivery_status') == 'failed']),
                    "error_count": len([r for r in filtered_records if r.get('error_message', '')])
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_notification_audit", e)