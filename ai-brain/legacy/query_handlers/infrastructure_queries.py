"""
Infrastructure Query Handler
Handles target, connection, and infrastructure-related queries
"""

import logging
from typing import Dict, List, Any
from .base_handler import BaseQueryHandler

logger = logging.getLogger(__name__)

class InfrastructureQueryHandler(BaseQueryHandler):
    """Handles infrastructure-related queries"""
    
    async def get_supported_intents(self) -> List[str]:
        """Return supported infrastructure intents"""
        return [
            "query_targets",
            "query_target_groups", 
            "query_connection_status",
            "query_target_tags",
            "query_targets_by_tag",
            "query_tag_statistics"
        ]
    
    async def handle_query(self, intent: str, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Route infrastructure queries to appropriate handlers"""
        try:
            if intent == "query_targets":
                return await self.handle_target_query(message, context)
            elif intent == "query_target_groups":
                return await self.handle_target_group_query(message, context)
            elif intent == "query_connection_status":
                return await self.handle_connection_status_query(message, context)
            elif intent == "query_target_tags":
                return await self.handle_target_tags_query(message, context)
            elif intent == "query_targets_by_tag":
                return await self.handle_targets_by_tag_query(message, context)
            elif intent == "query_tag_statistics":
                return await self.handle_tag_statistics_query(message, context)
            else:
                return self.create_error_response(intent, Exception(f"Unsupported intent: {intent}"))
                
        except Exception as e:
            return self.create_error_response(intent, e)
    
    async def handle_target_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle target-related queries"""
        try:
            # Get all targets from asset service
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return self.create_success_response(
                    "query_targets",
                    "🎯 **No targets found**\n\nNo targets are currently registered in the system. Add some targets to get started!",
                    {"targets_count": 0}
                )
            
            message_lower = message.lower()
            
            # Filter targets based on query
            if 'windows' in message_lower:
                filtered_targets = [t for t in targets if 'windows' in t.get('os', '').lower()]
                filter_desc = "Windows targets"
            elif 'linux' in message_lower:
                filtered_targets = [t for t in targets if 'linux' in t.get('os', '').lower()]
                filter_desc = "Linux targets"
            elif 'macos' in message_lower or 'mac' in message_lower:
                filtered_targets = [t for t in targets if 'macos' in t.get('os', '').lower() or 'mac' in t.get('os', '').lower()]
                filter_desc = "macOS targets"
            elif 'server' in message_lower:
                filtered_targets = [t for t in targets if 'server' in t.get('tags', []) or 'server' in t.get('hostname', '').lower()]
                filter_desc = "server targets"
            elif 'workstation' in message_lower or 'desktop' in message_lower:
                filtered_targets = [t for t in targets if 'workstation' in t.get('tags', []) or 'desktop' in t.get('tags', [])]
                filter_desc = "workstation targets"
            elif 'offline' in message_lower or 'down' in message_lower:
                filtered_targets = [t for t in targets if t.get('status') == 'offline']
                filter_desc = "offline targets"
            elif 'online' in message_lower or 'up' in message_lower:
                filtered_targets = [t for t in targets if t.get('status') == 'online']
                filter_desc = "online targets"
            else:
                filtered_targets = targets[:20]  # Show recent 20
                filter_desc = "targets"
            
            response = f"🎯 **Target Query - {filter_desc.title()}**\n\n"
            response += f"**Found:** {len(filtered_targets)} {filter_desc}\n\n"
            
            if not filtered_targets:
                response += f"No {filter_desc} found.\n"
                response += f"Total targets in system: {len(targets)}\n\n"
                
                # Suggest alternatives
                if 'windows' in message_lower:
                    linux_count = len([t for t in targets if 'linux' in t.get('os', '').lower()])
                    if linux_count > 0:
                        response += f"💡 **Suggestion:** Found {linux_count} Linux targets instead."
                elif 'linux' in message_lower:
                    windows_count = len([t for t in targets if 'windows' in t.get('os', '').lower()])
                    if windows_count > 0:
                        response += f"💡 **Suggestion:** Found {windows_count} Windows targets instead."
            else:
                # Show target details
                for i, target in enumerate(filtered_targets[:8]):
                    hostname = target.get('hostname', 'Unknown')
                    ip_address = target.get('ip_address', 'Unknown')
                    os_info = target.get('os', 'Unknown')
                    status = target.get('status', 'unknown')
                    tags = target.get('tags', [])
                    last_seen = target.get('last_seen', 'Never')
                    
                    status_emoji = '🟢' if status == 'online' else '🔴' if status == 'offline' else '🟡'
                    
                    response += f"**{i+1}. {hostname}** {status_emoji}\n"
                    response += f"   • IP: {ip_address}\n"
                    response += f"   • OS: {os_info}\n"
                    response += f"   • Status: {status}\n"
                    response += f"   • Last Seen: {last_seen}\n"
                    
                    if tags:
                        response += f"   • Tags: {', '.join(tags[:3])}\n"
                    
                    response += "\n"
                
                if len(filtered_targets) > 8:
                    response += f"... and {len(filtered_targets) - 8} more {filter_desc}\n\n"
                
                # Target statistics
                online_count = len([t for t in filtered_targets if t.get('status') == 'online'])
                offline_count = len([t for t in filtered_targets if t.get('status') == 'offline'])
                unknown_count = len(filtered_targets) - online_count - offline_count
                
                response += f"**Status Summary:**\n"
                response += f"• Online: {online_count} ({(online_count/len(filtered_targets)*100):.1f}%)\n"
                response += f"• Offline: {offline_count} ({(offline_count/len(filtered_targets)*100):.1f}%)\n"
                
                if unknown_count > 0:
                    response += f"• Unknown: {unknown_count}\n"
                
                # OS breakdown
                os_stats = {}
                for target in filtered_targets:
                    os_name = target.get('os', 'Unknown')
                    os_stats[os_name] = os_stats.get(os_name, 0) + 1
                
                if len(os_stats) > 1:
                    response += f"\n**OS Distribution:**\n"
                    for os_name, count in sorted(os_stats.items()):
                        response += f"• {os_name}: {count} targets\n"
                
                # Tag analysis
                all_tags = []
                for target in filtered_targets:
                    all_tags.extend(target.get('tags', []))
                
                if all_tags:
                    tag_stats = {}
                    for tag in all_tags:
                        tag_stats[tag] = tag_stats.get(tag, 0) + 1
                    
                    if len(tag_stats) > 0:
                        response += f"\n**Common Tags:**\n"
                        for tag, count in sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                            response += f"• {tag}: {count} targets\n"
            
            return self.create_success_response(
                "query_targets",
                response,
                {
                    "targets_found": len(filtered_targets),
                    "total_targets": len(targets),
                    "filter_description": filter_desc,
                    "online_count": len([t for t in filtered_targets if t.get('status') == 'online']),
                    "offline_count": len([t for t in filtered_targets if t.get('status') == 'offline'])
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_targets", e)
    
    async def handle_target_group_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle target group queries"""
        try:
            # Get target groups from asset service
            target_groups = await self.asset_client.get_target_groups()
            
            if not target_groups:
                return self.create_success_response(
                    "query_target_groups",
                    "📁 **No target groups found**\n\nNo target groups are currently configured. Create some groups to organize your targets!",
                    {"groups_count": 0}
                )
            
            message_lower = message.lower()
            
            # Check if asking for specific group
            group_name = None
            for group in target_groups:
                if group.get('name', '').lower() in message_lower:
                    group_name = group.get('name')
                    break
            
            if group_name:
                # Show specific group details
                target_group = next((g for g in target_groups if g.get('name') == group_name), None)
                if target_group:
                    targets = await self.asset_client.get_targets_in_group(target_group['id'])
                    
                    response = f"📁 **Target Group - {group_name}**\n\n"
                    response += f"**Group ID:** {target_group.get('id')}\n"
                    response += f"**Description:** {target_group.get('description', 'No description')}\n"
                    response += f"**Target Count:** {len(targets)}\n"
                    response += f"**Created:** {target_group.get('created_at', 'Unknown')}\n\n"
                    
                    if targets:
                        response += "**Targets in Group:**\n"
                        
                        # Group statistics
                        online_count = len([t for t in targets if t.get('status') == 'online'])
                        offline_count = len([t for t in targets if t.get('status') == 'offline'])
                        
                        response += f"• Online: {online_count}\n"
                        response += f"• Offline: {offline_count}\n\n"
                        
                        # Target list
                        for i, target in enumerate(targets[:8]):
                            hostname = target.get('hostname', 'Unknown')
                            ip_address = target.get('ip_address', 'Unknown')
                            status = target.get('status', 'unknown')
                            os_info = target.get('os', 'Unknown')
                            
                            status_emoji = '🟢' if status == 'online' else '🔴' if status == 'offline' else '🟡'
                            
                            response += f"{i+1}. **{hostname}** {status_emoji}\n"
                            response += f"   • IP: {ip_address}\n"
                            response += f"   • OS: {os_info}\n"
                            response += f"   • Status: {status}\n\n"
                        
                        if len(targets) > 8:
                            response += f"... and {len(targets) - 8} more targets\n"
                    else:
                        response += "**No targets in this group**\n\n"
                        response += "💡 **Tip:** Add targets to this group to organize your infrastructure."
                else:
                    response = f"📁 **Group '{group_name}' not found**\n\n"
                    response += f"Available groups: {len(target_groups)}\n\n"
                    response += "**Available Groups:**\n"
                    for i, group in enumerate(target_groups[:5]):
                        response += f"{i+1}. {group.get('name', 'Unknown')}\n"
            else:
                # Show all groups overview
                response = f"📁 **Target Groups Overview**\n\n"
                response += f"**Total Groups:** {len(target_groups)}\n\n"
                
                # Calculate total targets across all groups
                total_targets_in_groups = 0
                group_stats = []
                
                for group in target_groups:
                    try:
                        targets = await self.asset_client.get_targets_in_group(group['id'])
                        target_count = len(targets)
                        total_targets_in_groups += target_count
                        
                        online_count = len([t for t in targets if t.get('status') == 'online'])
                        
                        group_stats.append({
                            'group': group,
                            'target_count': target_count,
                            'online_count': online_count
                        })
                    except:
                        group_stats.append({
                            'group': group,
                            'target_count': 0,
                            'online_count': 0
                        })
                
                response += f"**Total Targets in Groups:** {total_targets_in_groups}\n\n"
                
                # Sort groups by target count
                group_stats.sort(key=lambda x: x['target_count'], reverse=True)
                
                response += "**Groups by Size:**\n"
                for i, stat in enumerate(group_stats[:10]):
                    group = stat['group']
                    group_name = group.get('name', 'Unknown')
                    group_desc = group.get('description', 'No description')
                    target_count = stat['target_count']
                    online_count = stat['online_count']
                    
                    response += f"**{i+1}. {group_name}** ({target_count} targets)\n"
                    response += f"   • Description: {group_desc[:50]}{'...' if len(group_desc) > 50 else ''}\n"
                    response += f"   • Online: {online_count}/{target_count}\n"
                    
                    if target_count > 0:
                        health = (online_count / target_count) * 100
                        health_emoji = '🟢' if health >= 80 else '🟡' if health >= 50 else '🔴'
                        response += f"   • Health: {health:.1f}% {health_emoji}\n"
                    
                    response += "\n"
                
                if len(target_groups) > 10:
                    response += f"... and {len(target_groups) - 10} more groups\n\n"
                
                # Group health summary
                healthy_groups = len([s for s in group_stats if s['target_count'] > 0 and (s['online_count'] / s['target_count']) >= 0.8])
                response += f"**Group Health Summary:**\n"
                response += f"• Healthy Groups (≥80% online): {healthy_groups}\n"
                response += f"• Total Groups: {len(target_groups)}\n"
            
            return self.create_success_response(
                "query_target_groups",
                response,
                {
                    "groups_count": len(target_groups),
                    "specific_group": group_name,
                    "total_targets_in_groups": total_targets_in_groups if 'total_targets_in_groups' in locals() else 0
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_target_groups", e)
    
    async def handle_connection_status_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle connection status queries"""
        try:
            # Get all targets to check their connection status
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return self.create_success_response(
                    "query_connection_status",
                    "🔌 **No targets to check**\n\nNo targets are registered for connection monitoring. Add some targets first!",
                    {"targets_count": 0}
                )
            
            message_lower = message.lower()
            
            # Categorize targets by connection status
            reachable_targets = []
            unreachable_targets = []
            untested_targets = []
            
            for target in targets:
                connection_status = target.get('connection_status', 'unknown')
                status = target.get('status', 'unknown')
                
                # Determine reachability
                if connection_status == 'success' or status == 'online':
                    reachable_targets.append({'target': target, 'status': 'reachable'})
                elif connection_status == 'failed' or status == 'offline':
                    unreachable_targets.append({'target': target, 'status': 'unreachable'})
                else:
                    untested_targets.append({'target': target, 'status': 'untested'})
            
            # Filter based on query
            if 'failed' in message_lower or 'down' in message_lower or 'unreachable' in message_lower:
                filtered_targets = unreachable_targets
                filter_desc = "unreachable targets"
            elif 'success' in message_lower or 'up' in message_lower or 'reachable' in message_lower:
                filtered_targets = reachable_targets
                filter_desc = "reachable targets"
            elif 'untested' in message_lower or 'unknown' in message_lower:
                filtered_targets = untested_targets
                filter_desc = "untested targets"
            else:
                # Show overview
                connection_stats = {
                    'total_targets': len(targets),
                    'reachable': len(reachable_targets),
                    'unreachable': len(unreachable_targets),
                    'never_tested': len(untested_targets),
                    'unknown': 0
                }
                
                response = f"🔌 **Connection Status Overview**\n\n"
                response += f"**Total Targets:** {connection_stats['total_targets']}\n"
                response += f"**Reachable:** {connection_stats['reachable']} ✅\n"
                response += f"**Unreachable:** {connection_stats['unreachable']} ❌\n"
                response += f"**Never Tested:** {connection_stats['never_tested']} ⚪\n\n"
                
                # Calculate health percentage
                tested_targets = connection_stats['reachable'] + connection_stats['unreachable']
                if tested_targets > 0:
                    health_percentage = (connection_stats['reachable'] / tested_targets) * 100
                    response += f"**Connection Health:** {health_percentage:.1f}% ({connection_stats['reachable']}/{tested_targets} reachable)\n\n"
                
                # Show recent connection issues if any
                if unreachable_targets:
                    response += "**Recent Connection Issues:**\n"
                    for i, target_info in enumerate(unreachable_targets[:3]):
                        target = target_info['target']
                        hostname = target.get('hostname', 'Unknown')
                        last_seen = target.get('last_seen', 'Never')
                        response += f"• {hostname} - Last seen: {last_seen}\n"
                    
                    if len(unreachable_targets) > 3:
                        response += f"... and {len(unreachable_targets) - 3} more\n"
                    response += "\n"
                
                if untested_targets:
                    response += f"💡 **Tip:** {len(untested_targets)} targets haven't been tested yet. Run connection tests to verify reachability."
                
                return self.create_success_response(
                    "query_connection_status",
                    response,
                    {
                        "connection_stats": connection_stats,
                        "reachable_count": len(reachable_targets),
                        "unreachable_count": len(unreachable_targets),
                        "untested_count": len(untested_targets)
                    }
                )
            
            # Show filtered results
            response = f"🔌 **Connection Status - {filter_desc.title()}**\n\n"
            response += f"**Found:** {len(filtered_targets)} {filter_desc}\n\n"
            
            if not filtered_targets:
                response += f"No {filter_desc} found! 🎉\n"
                response += f"Total targets: {len(targets)}\n\n"
                
                if filter_desc == "unreachable targets":
                    response += "✅ **Great news!** All tested targets are reachable."
                elif filter_desc == "untested targets":
                    response += "✅ **All targets have been tested** for connectivity."
            else:
                # Show detailed target information
                for i, target_info in enumerate(filtered_targets[:8]):
                    target = target_info['target']
                    hostname = target.get('hostname', 'Unknown')
                    ip_address = target.get('ip_address', 'Unknown')
                    status = target_info['status']
                    last_seen = target.get('last_seen', 'Never')
                    connection_error = target.get('connection_error', '')
                    
                    status_emoji = '✅' if status == 'reachable' else '❌' if status == 'unreachable' else '⚪'
                    
                    response += f"**{i+1}. {hostname}** {status_emoji}\n"
                    response += f"   • IP: {ip_address}\n"
                    response += f"   • Status: {status}\n"
                    response += f"   • Last Seen: {last_seen}\n"
                    
                    if connection_error and status == 'unreachable':
                        response += f"   • Error: {connection_error[:100]}{'...' if len(connection_error) > 100 else ''}\n"
                    
                    response += "\n"
                
                if len(filtered_targets) > 8:
                    response += f"... and {len(filtered_targets) - 8} more {filter_desc}\n\n"
                
                # Provide actionable insights
                if filter_desc == "unreachable targets":
                    response += "🔧 **Troubleshooting Tips:**\n"
                    response += "• Check network connectivity\n"
                    response += "• Verify target is powered on\n"
                    response += "• Check firewall settings\n"
                    response += "• Validate IP addresses\n"
                elif filter_desc == "untested targets":
                    response += "🔍 **Next Steps:**\n"
                    response += "• Run connection tests on these targets\n"
                    response += "• Verify network configuration\n"
                    response += "• Check target accessibility\n"
            
            return self.create_success_response(
                "query_connection_status",
                response,
                {
                    "filtered_count": len(filtered_targets),
                    "total_targets": len(targets),
                    "filter_description": filter_desc,
                    "reachable_count": len(reachable_targets),
                    "unreachable_count": len(unreachable_targets),
                    "untested_count": len(untested_targets)
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_connection_status", e)
    
    async def handle_target_tags_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about target tags"""
        try:
            # Get all targets from asset service
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return self.create_success_response(
                    "query_target_tags",
                    "🏷️ **No targets found**\n\nNo targets are currently registered in the system.",
                    {"tags_count": 0, "targets_count": 0}
                )
            
            # Extract all tags from targets
            all_tags = set()
            tag_usage = {}
            targets_with_tags = 0
            targets_without_tags = 0
            
            for target in targets:
                target_tags = target.get('tags', [])
                if target_tags:
                    targets_with_tags += 1
                    for tag in target_tags:
                        all_tags.add(tag)
                        tag_usage[tag] = tag_usage.get(tag, 0) + 1
                else:
                    targets_without_tags += 1
            
            if not all_tags:
                return self.create_success_response(
                    "query_target_tags",
                    f"🏷️ **No tags found**\n\nYou have {len(targets)} targets but none have tags assigned.\n\n"
                    "💡 **Tip:** Add tags to organize your targets by environment, role, or team!",
                    {"tags_count": 0, "targets_count": len(targets), "targets_without_tags": targets_without_tags}
                )
            
            # Sort tags by usage (most used first)
            sorted_tags = sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)
            
            response = f"🏷️ **Target Tags Overview**\n\n"
            response += f"**Summary:**\n"
            response += f"• Total unique tags: {len(all_tags)}\n"
            response += f"• Targets with tags: {targets_with_tags}\n"
            response += f"• Targets without tags: {targets_without_tags}\n"
            response += f"• Total targets: {len(targets)}\n\n"
            
            response += f"**Most Used Tags:**\n"
            for i, (tag, count) in enumerate(sorted_tags[:10]):
                percentage = (count / len(targets)) * 100
                response += f"• **{tag}** - {count} targets ({percentage:.1f}%)\n"
            
            if len(sorted_tags) > 10:
                response += f"... and {len(sorted_tags) - 10} more tags\n"
            
            response += f"\n**Tag Categories Detected:**\n"
            # Analyze tag patterns
            env_tags = [tag for tag in all_tags if any(env in tag.lower() for env in ['prod', 'dev', 'test', 'staging', 'qa'])]
            role_tags = [tag for tag in all_tags if any(role in tag.lower() for role in ['web', 'db', 'api', 'worker', 'cache'])]
            team_tags = [tag for tag in all_tags if any(team in tag.lower() for team in ['team', 'dept', 'group', 'squad'])]
            
            if env_tags:
                response += f"• **Environment:** {', '.join(env_tags[:5])}\n"
            if role_tags:
                response += f"• **Role/Service:** {', '.join(role_tags[:5])}\n"
            if team_tags:
                response += f"• **Team/Group:** {', '.join(team_tags[:5])}\n"
            
            return self.create_success_response(
                "query_target_tags",
                response,
                {
                    "tags_count": len(all_tags),
                    "targets_count": len(targets),
                    "targets_with_tags": targets_with_tags,
                    "targets_without_tags": targets_without_tags,
                    "tag_usage": tag_usage,
                    "all_tags": list(all_tags)
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_target_tags", e)
    
    async def handle_targets_by_tag_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries for targets filtered by specific tags"""
        try:
            # Extract tag from message
            message_lower = message.lower()
            
            # Common tag extraction patterns
            tag_patterns = [
                r'tag[:\s]+(["\']?)([^"\']+)\1',
                r'tagged[:\s]+(["\']?)([^"\']+)\1',
                r'with[:\s]+(["\']?)([^"\']+)\1',
                r'labeled[:\s]+(["\']?)([^"\']+)\1',
                r'(["\']?)([a-zA-Z0-9_-]+)\1[:\s]*tag',
            ]
            
            import re
            extracted_tag = None
            for pattern in tag_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    extracted_tag = match.group(2).strip()
                    break
            
            # Get all targets from asset service
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return self.create_success_response(
                    "query_targets_by_tag",
                    "🎯 **No targets found**\n\nNo targets are currently registered in the system.",
                    {"targets_count": 0}
                )
            
            # If no specific tag extracted, show available tags
            if not extracted_tag:
                all_tags = set()
                for target in targets:
                    target_tags = target.get('tags', [])
                    all_tags.update(target_tags)
                
                if not all_tags:
                    return self.create_success_response(
                        "query_targets_by_tag",
                        "🏷️ **No tags available**\n\nNo targets have tags assigned. Add tags to organize your targets!\n\n"
                        "**Example:** *\"Show me targets tagged production\"*",
                        {"available_tags": []}
                    )
                
                response = f"🏷️ **Available Tags**\n\n"
                response += f"Please specify which tag you'd like to filter by:\n\n"
                
                sorted_tags = sorted(all_tags)
                for tag in sorted_tags[:15]:
                    response += f"• `{tag}`\n"
                
                if len(sorted_tags) > 15:
                    response += f"... and {len(sorted_tags) - 15} more\n"
                
                response += f"\n**Example queries:**\n"
                response += f"• *\"Show me production targets\"*\n"
                response += f"• *\"List targets tagged database\"*\n"
                response += f"• *\"Find web servers\"*"
                
                return self.create_success_response(
                    "query_targets_by_tag",
                    response,
                    {"available_tags": sorted_tags}
                )
            
            # Filter targets by tag (case-insensitive partial match)
            matching_targets = []
            for target in targets:
                target_tags = target.get('tags', [])
                for tag in target_tags:
                    if extracted_tag.lower() in tag.lower():
                        matching_targets.append({
                            'target': target,
                            'matching_tag': tag
                        })
                        break
            
            if not matching_targets:
                # Suggest similar tags
                all_tags = set()
                for target in targets:
                    all_tags.update(target.get('tags', []))
                
                similar_tags = [tag for tag in all_tags if extracted_tag.lower() in tag.lower() or tag.lower() in extracted_tag.lower()]
                
                response = f"🔍 **No targets found with tag: '{extracted_tag}'**\n\n"
                
                if similar_tags:
                    response += f"**Did you mean:**\n"
                    for tag in similar_tags[:5]:
                        response += f"• `{tag}`\n"
                    response += f"\n"
                
                response += f"**Available tags:**\n"
                sorted_tags = sorted(all_tags)[:10]
                for tag in sorted_tags:
                    response += f"• `{tag}`\n"
                
                return self.create_success_response(
                    "query_targets_by_tag",
                    response,
                    {"searched_tag": extracted_tag, "available_tags": list(all_tags), "similar_tags": similar_tags}
                )
            
            # Show matching targets
            response = f"🎯 **Targets tagged with '{extracted_tag}'**\n\n"
            response += f"**Found:** {len(matching_targets)} targets\n\n"
            
            for i, target_info in enumerate(matching_targets[:10]):
                target = target_info['target']
                matching_tag = target_info['matching_tag']
                
                name = target.get('name', 'Unknown')
                hostname = target.get('hostname', 'Unknown')
                ip_address = target.get('ip_address', 'Unknown')
                os_type = target.get('os_type', 'Unknown')
                all_tags = target.get('tags', [])
                
                # OS emoji
                os_emoji = {
                    'windows': '🪟',
                    'linux': '🐧',
                    'macos': '🍎',
                    'unix': '🖥️'
                }.get(os_type.lower(), '💻')
                
                response += f"**{i+1}. {name}** {os_emoji}\n"
                response += f"   • Hostname: {hostname}\n"
                response += f"   • IP: {ip_address}\n"
                response += f"   • OS: {os_type}\n"
                response += f"   • Matching tag: `{matching_tag}`\n"
                
                if len(all_tags) > 1:
                    other_tags = [tag for tag in all_tags if tag != matching_tag]
                    if other_tags:
                        response += f"   • Other tags: {', '.join([f'`{tag}`' for tag in other_tags[:3]])}\n"
                
                response += "\n"
            
            if len(matching_targets) > 10:
                response += f"... and {len(matching_targets) - 10} more targets\n\n"
            
            # Add summary statistics
            os_counts = {}
            for target_info in matching_targets:
                os_type = target_info['target'].get('os_type', 'Unknown')
                os_counts[os_type] = os_counts.get(os_type, 0) + 1
            
            if len(os_counts) > 1:
                response += f"**OS Distribution:**\n"
                for os_type, count in sorted(os_counts.items(), key=lambda x: x[1], reverse=True):
                    response += f"• {os_type}: {count} targets\n"
            
            return self.create_success_response(
                "query_targets_by_tag",
                response,
                {
                    "searched_tag": extracted_tag,
                    "matching_count": len(matching_targets),
                    "total_targets": len(targets),
                    "os_distribution": os_counts
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_targets_by_tag", e)
    
    async def handle_tag_statistics_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about tag usage statistics and analytics"""
        try:
            # Get all targets from asset service
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return self.create_success_response(
                    "query_tag_statistics",
                    "📊 **No targets found**\n\nNo targets are currently registered in the system.",
                    {"targets_count": 0}
                )
            
            # Analyze tag usage
            tag_usage = {}
            tag_combinations = {}
            targets_with_tags = 0
            targets_without_tags = 0
            total_tag_assignments = 0
            
            for target in targets:
                target_tags = target.get('tags', [])
                if target_tags:
                    targets_with_tags += 1
                    total_tag_assignments += len(target_tags)
                    
                    # Count individual tag usage
                    for tag in target_tags:
                        tag_usage[tag] = tag_usage.get(tag, 0) + 1
                    
                    # Count tag combinations (for targets with multiple tags)
                    if len(target_tags) > 1:
                        sorted_tags = tuple(sorted(target_tags))
                        tag_combinations[sorted_tags] = tag_combinations.get(sorted_tags, 0) + 1
                else:
                    targets_without_tags += 1
            
            if not tag_usage:
                return self.create_success_response(
                    "query_tag_statistics",
                    f"📊 **Tag Statistics**\n\n"
                    f"**No tags in use**\n\n"
                    f"• Total targets: {len(targets)}\n"
                    f"• Targets without tags: {targets_without_tags}\n\n"
                    f"💡 **Recommendation:** Start organizing your infrastructure by adding tags!",
                    {"targets_count": len(targets), "tags_count": 0}
                )
            
            # Calculate statistics
            avg_tags_per_target = total_tag_assignments / len(targets)
            tag_coverage = (targets_with_tags / len(targets)) * 100
            
            # Sort tags by usage
            sorted_tags = sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)
            
            response = f"📊 **Tag Usage Statistics**\n\n"
            
            # Overview metrics
            response += f"**Overview:**\n"
            response += f"• Total targets: {len(targets)}\n"
            response += f"• Unique tags: {len(tag_usage)}\n"
            response += f"• Tag coverage: {tag_coverage:.1f}% ({targets_with_tags}/{len(targets)})\n"
            response += f"• Avg tags per target: {avg_tags_per_target:.1f}\n"
            response += f"• Total tag assignments: {total_tag_assignments}\n\n"
            
            # Top tags
            response += f"**Most Popular Tags:**\n"
            for i, (tag, count) in enumerate(sorted_tags[:8]):
                percentage = (count / len(targets)) * 100
                bar_length = min(int(percentage / 5), 20)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                response += f"{i+1:2d}. **{tag}** ({count} targets, {percentage:.1f}%)\n"
                response += f"    {bar}\n"
            
            if len(sorted_tags) > 8:
                response += f"    ... and {len(sorted_tags) - 8} more tags\n"
            
            response += f"\n"
            
            # Tag distribution analysis
            single_use_tags = [tag for tag, count in tag_usage.items() if count == 1]
            popular_tags = [tag for tag, count in tag_usage.items() if count >= len(targets) * 0.1]
            
            response += f"**Tag Distribution:**\n"
            response += f"• Single-use tags: {len(single_use_tags)} ({(len(single_use_tags)/len(tag_usage)*100):.1f}%)\n"
            response += f"• Popular tags (>10% usage): {len(popular_tags)}\n"
            
            if single_use_tags:
                response += f"• Rare tags: {', '.join([f'`{tag}`' for tag in single_use_tags[:5]])}\n"
                if len(single_use_tags) > 5:
                    response += f"  ... and {len(single_use_tags) - 5} more\n"
            
            # Tag combinations
            if tag_combinations:
                response += f"\n**Common Tag Combinations:**\n"
                sorted_combinations = sorted(tag_combinations.items(), key=lambda x: x[1], reverse=True)
                for i, (tags, count) in enumerate(sorted_combinations[:5]):
                    tag_list = ', '.join([f'`{tag}`' for tag in tags])
                    response += f"• {tag_list} - {count} targets\n"
            
            # Recommendations
            response += f"\n**📈 Recommendations:**\n"
            if tag_coverage < 50:
                response += f"• **Low tag coverage** ({tag_coverage:.1f}%) - Consider tagging more targets\n"
            if len(single_use_tags) > len(tag_usage) * 0.3:
                response += f"• **Many single-use tags** - Consider standardizing tag names\n"
            if avg_tags_per_target < 2:
                response += f"• **Few tags per target** - Add more descriptive tags (environment, role, team)\n"
            if not popular_tags:
                response += f"• **No popular tags** - Establish tagging conventions for consistency\n"
            
            return self.create_success_response(
                "query_tag_statistics",
                response,
                {
                    "targets_count": len(targets),
                    "tags_count": len(tag_usage),
                    "tag_coverage": tag_coverage,
                    "avg_tags_per_target": avg_tags_per_target,
                    "targets_with_tags": targets_with_tags,
                    "targets_without_tags": targets_without_tags,
                    "tag_usage": tag_usage,
                    "single_use_tags": single_use_tags,
                    "popular_tags": popular_tags,
                    "tag_combinations": dict(tag_combinations)
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_tag_statistics", e)