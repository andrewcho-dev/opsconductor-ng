#!/usr/bin/env python3
"""
Demo script to test the new tag functionality
This simulates the AI system's tag capabilities with real data
"""

import asyncio
import json
import sys
import os

# Mock target data (based on real data from asset service)
MOCK_TARGETS = [
    {
        "id": 11,
        "name": "192.168.50.211",
        "hostname": "192.168.50.211",
        "ip_address": "192.168.50.211",
        "os_type": "windows",
        "description": "Production web server",
        "tags": ["win10", "production", "web-server", "frontend"],
        "created_at": "2025-09-15T04:56:42.082305+00:00"
    },
    {
        "id": 10,
        "name": "192.168.50.210",
        "hostname": "192.168.50.210",
        "ip_address": "192.168.50.210",
        "os_type": "windows",
        "description": "Development database server",
        "tags": ["win10", "development", "database", "mysql"],
        "created_at": "2025-09-15T04:56:09.942545+00:00"
    },
    {
        "id": 8,
        "name": "192.168.50.214",
        "hostname": "192.168.50.214",
        "ip_address": "192.168.50.214",
        "os_type": "windows",
        "description": "Staging API server",
        "tags": ["win11", "staging", "api-server", "backend"],
        "created_at": "2025-09-15T02:29:37.812276+00:00"
    },
    {
        "id": 9,
        "name": "192.168.50.215",
        "hostname": "192.168.50.215",
        "ip_address": "192.168.50.215",
        "os_type": "windows",
        "description": "Test environment",
        "tags": ["win10", "testing"],
        "created_at": "2025-09-15T02:30:02.785470+00:00"
    },
    {
        "id": 12,
        "name": "192.168.50.212",
        "hostname": "192.168.50.212",
        "ip_address": "192.168.50.212",
        "os_type": "windows",
        "description": "Backup server",
        "tags": ["win11", "production", "backup"],
        "created_at": "2025-09-15T04:57:30.123456+00:00"
    },
    {
        "id": 13,
        "name": "192.168.50.213",
        "hostname": "192.168.50.213",
        "ip_address": "192.168.50.213",
        "os_type": "windows",
        "description": "Monitoring server",
        "tags": [],  # No tags
        "created_at": "2025-09-15T04:58:45.789012+00:00"
    }
]

class MockAssetClient:
    """Mock asset service client"""
    
    async def get_all_targets(self):
        return MOCK_TARGETS

class MockTagHandler:
    """Mock implementation of tag functionality"""
    
    def __init__(self):
        self.asset_client = MockAssetClient()
    
    def create_success_response(self, intent, response, data=None):
        return {
            "response": response,
            "intent": intent,
            "success": True,
            "data": data or {}
        }
    
    async def handle_target_tags_query(self, message: str, context: list) -> dict:
        """Handle queries about target tags"""
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
        role_tags = [tag for tag in all_tags if any(role in tag.lower() for role in ['web', 'db', 'api', 'worker', 'cache', 'backup'])]
        os_tags = [tag for tag in all_tags if any(os in tag.lower() for os in ['win', 'linux', 'ubuntu', 'centos'])]
        
        if env_tags:
            response += f"• **Environment:** {', '.join(env_tags[:5])}\n"
        if role_tags:
            response += f"• **Role/Service:** {', '.join(role_tags[:5])}\n"
        if os_tags:
            response += f"• **Operating System:** {', '.join(os_tags[:5])}\n"
        
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
    
    async def handle_targets_by_tag_query(self, message: str, context: list) -> dict:
        """Handle queries for targets filtered by specific tags"""
        # Extract tag from message (simplified)
        message_lower = message.lower()
        
        # Simple tag extraction
        extracted_tag = None
        if "production" in message_lower:
            extracted_tag = "production"
        elif "development" in message_lower:
            extracted_tag = "development"
        elif "staging" in message_lower:
            extracted_tag = "staging"
        elif "web" in message_lower:
            extracted_tag = "web-server"
        elif "database" in message_lower:
            extracted_tag = "database"
        elif "win10" in message_lower:
            extracted_tag = "win10"
        elif "win11" in message_lower:
            extracted_tag = "win11"
        
        targets = await self.asset_client.get_all_targets()
        
        if not extracted_tag:
            all_tags = set()
            for target in targets:
                all_tags.update(target.get('tags', []))
            
            response = f"🏷️ **Available Tags**\n\n"
            response += f"Please specify which tag you'd like to filter by:\n\n"
            
            sorted_tags = sorted(all_tags)
            for tag in sorted_tags:
                response += f"• `{tag}`\n"
            
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
            response = f"🔍 **No targets found with tag: '{extracted_tag}'**\n\n"
            response += f"**Available tags:**\n"
            all_tags = set()
            for target in targets:
                all_tags.update(target.get('tags', []))
            
            for tag in sorted(all_tags)[:10]:
                response += f"• `{tag}`\n"
            
            return self.create_success_response(
                "query_targets_by_tag",
                response,
                {"searched_tag": extracted_tag, "available_tags": list(all_tags)}
            )
        
        # Show matching targets
        response = f"🎯 **Targets tagged with '{extracted_tag}'**\n\n"
        response += f"**Found:** {len(matching_targets)} targets\n\n"
        
        for i, target_info in enumerate(matching_targets):
            target = target_info['target']
            matching_tag = target_info['matching_tag']
            
            name = target.get('name', 'Unknown')
            hostname = target.get('hostname', 'Unknown')
            ip_address = target.get('ip_address', 'Unknown')
            os_type = target.get('os_type', 'Unknown')
            description = target.get('description', '')
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
            if description:
                response += f"   • Description: {description}\n"
            response += f"   • Matching tag: `{matching_tag}`\n"
            
            if len(all_tags) > 1:
                other_tags = [tag for tag in all_tags if tag != matching_tag]
                if other_tags:
                    response += f"   • Other tags: {', '.join([f'`{tag}`' for tag in other_tags[:3]])}\n"
            
            response += "\n"
        
        return self.create_success_response(
            "query_targets_by_tag",
            response,
            {
                "searched_tag": extracted_tag,
                "matching_count": len(matching_targets),
                "total_targets": len(targets)
            }
        )
    
    async def handle_tag_statistics_query(self, message: str, context: list) -> dict:
        """Handle queries about tag usage statistics and analytics"""
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
        
        # Tag distribution analysis
        single_use_tags = [tag for tag, count in tag_usage.items() if count == 1]
        popular_tags = [tag for tag, count in tag_usage.items() if count >= len(targets) * 0.1]
        
        response += f"\n**Tag Distribution:**\n"
        response += f"• Single-use tags: {len(single_use_tags)} ({(len(single_use_tags)/len(tag_usage)*100):.1f}%)\n"
        response += f"• Popular tags (>10% usage): {len(popular_tags)}\n"
        
        if single_use_tags:
            response += f"• Rare tags: {', '.join([f'`{tag}`' for tag in single_use_tags[:5]])}\n"
        
        # Tag combinations
        if tag_combinations:
            response += f"\n**Common Tag Combinations:**\n"
            sorted_combinations = sorted(tag_combinations.items(), key=lambda x: x[1], reverse=True)
            for i, (tags, count) in enumerate(sorted_combinations[:3]):
                tag_list = ', '.join([f'`{tag}`' for tag in tags])
                response += f"• {tag_list} - {count} targets\n"
        
        # Recommendations
        response += f"\n**📈 Recommendations:**\n"
        if tag_coverage < 90:
            response += f"• **Tag coverage** ({tag_coverage:.1f}%) - Consider tagging more targets\n"
        if len(single_use_tags) > len(tag_usage) * 0.3:
            response += f"• **Many single-use tags** - Consider standardizing tag names\n"
        if avg_tags_per_target < 2:
            response += f"• **Few tags per target** - Add more descriptive tags (environment, role, team)\n"
        
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
                "tag_usage": tag_usage
            }
        )

async def demo_tag_functionality():
    """Demonstrate the new tag functionality"""
    print("🚀 OpsConductor AI - Tag Functionality Demo")
    print("=" * 60)
    
    handler = MockTagHandler()
    
    # Demo queries
    demo_queries = [
        ("Show me all target tags", "handle_target_tags_query"),
        ("Show production targets", "handle_targets_by_tag_query"),
        ("Find database servers", "handle_targets_by_tag_query"),
        ("Tag usage statistics", "handle_tag_statistics_query"),
        ("Show staging environments", "handle_targets_by_tag_query")
    ]
    
    for i, (query, handler_method) in enumerate(demo_queries, 1):
        print(f"\n🔍 **Demo Query {i}:** \"{query}\"")
        print("-" * 50)
        
        # Call the appropriate handler method
        method = getattr(handler, handler_method)
        result = await method(query, [])
        
        # Display the response
        response = result.get('response', 'No response')
        print(response)
        
        if i < len(demo_queries):
            print("\n" + "="*60)
    
    print(f"\n🎉 **Demo Complete!**")
    print("✅ The AI system now fully supports target tag functionality!")
    print("🏷️ Users can discover, filter, and analyze target tags naturally!")

if __name__ == "__main__":
    asyncio.run(demo_tag_functionality())