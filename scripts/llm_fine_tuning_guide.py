#!/usr/bin/env python3
"""
LLM Fine-Tuning Guide and Utilities

This script provides utilities and guidance for fine-tuning your LLM 
to properly populate the capabilities field in intent classification.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

class LLMFineTuningHelper:
    """Helper utilities for LLM fine-tuning"""
    
    def __init__(self, training_data_path: str):
        self.training_data_path = Path(training_data_path)
        self.examples = self._load_training_data()
    
    def _load_training_data(self) -> List[Dict[str, Any]]:
        """Load training data from JSON file"""
        with open(self.training_data_path, 'r') as f:
            return json.load(f)
    
    def create_ollama_training_format(self, output_file: str):
        """Create training data in Ollama fine-tuning format"""
        ollama_examples = []
        
        for example in self.examples:
            # Create the exact system and user prompts your system uses
            system_prompt = """Classify infrastructure request. Return JSON: {"category":"CAT","action":"ACTION","confidence":0.0-1.0,"capabilities":["cap1","cap2"]}

Categories & Actions:
- automation: restart_service|start_service|stop_service|deploy_application|run_script|execute_command|backup_data|restore_data|emergency_response
- monitoring: check_status|view_logs|get_metrics|check_health|monitor_performance|view_dashboard|check_alerts
- troubleshooting: diagnose_issue|fix_problem|investigate_error|diagnose_performance|check_connectivity|analyze_logs|debug_application
- configuration: update_config|change_settings|modify_parameters|update_environment|configure_service|set_permissions|update_security
- information: get_help|explain_concept|show_documentation|list_resources|describe_system|show_examples|get_status_info|calculate|compute|math|answer_question|provide_information
- asset_management: list_assets|get_asset|search_assets|count_assets|get_credentials|list_credentials|find_asset|query_assets|list_servers|list_hosts|get_asset_info|asset_count|asset_discovery

Capabilities: api_query|asset_management|asset_query|credential_access|disk_management|disk_monitoring|dns_query|http_client|infrastructure_info|log_analysis|memory_monitoring|network_info|network_monitoring|network_testing|packet_capture|process_management|process_monitoring|protocol_analysis|resource_listing|secret_retrieval|service_management|system_info|system_monitoring|text_search|windows_automation|windows_service_management

Key distinctions:
- monitoring: LIVE/REAL-TIME checks (is X up?, current CPU, disk space on specific machine, READ file contents for status checks)
- information: Display/show content, read files, get information (cat/view files, show documentation, explain concepts)
- asset_management: INVENTORY queries (list servers, show IPs from database)
- windows_automation: Windows-specific operations (list files, run PowerShell, manage services on Windows machines)
- disk_management: File/directory operations (list files, create directories, check disk space)
- configuration: MODIFY settings (change configs, update parameters - NOT reading configs)
- asset_query: Query asset database for machine information (NOT for executing commands on machines)
- GATED (credential_access, secret_retrieval): explicit credential requests only

FILE READING RULES:
- "Display/show/cat/read file contents" → information category with provide_information action
- "Check/view system files for monitoring" → monitoring category with check_status action
- "Modify/update/change file contents" → configuration category

IMPORTANT: Use ONLY the actions listed above. For disk space checks on specific machines, use monitoring/get_metrics with disk_monitoring capability."""
            
            user_prompt = f"Classify: {example['request']}"
            
            # Create expected response JSON
            expected = example['expected_response']
            response_json = json.dumps(expected, separators=(',', ':'))
            
            ollama_example = {
                "instruction": system_prompt,
                "input": user_prompt,
                "output": response_json
            }
            
            ollama_examples.append(ollama_example)
        
        # Save in JSONL format
        with open(output_file, 'w') as f:
            for example in ollama_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"✅ Ollama training format saved to: {output_file}")
        return output_file
    
    def create_huggingface_training_format(self, output_file: str):
        """Create training data in HuggingFace format"""
        hf_examples = []
        
        for example in self.examples:
            # Create conversation format
            conversation = {
                "messages": [
                    {
                        "role": "system",
                        "content": """Classify infrastructure request. Return JSON: {"category":"CAT","action":"ACTION","confidence":0.0-1.0,"capabilities":["cap1","cap2"]}

Categories & Actions:
- automation: restart_service|start_service|stop_service|deploy_application|run_script|execute_command|backup_data|restore_data|emergency_response
- monitoring: check_status|view_logs|get_metrics|check_health|monitor_performance|view_dashboard|check_alerts
- troubleshooting: diagnose_issue|fix_problem|investigate_error|diagnose_performance|check_connectivity|analyze_logs|debug_application
- configuration: update_config|change_settings|modify_parameters|update_environment|configure_service|set_permissions|update_security
- information: get_help|explain_concept|show_documentation|list_resources|describe_system|show_examples|get_status_info|calculate|compute|math|answer_question|provide_information
- asset_management: list_assets|get_asset|search_assets|count_assets|get_credentials|list_credentials|find_asset|query_assets|list_servers|list_hosts|get_asset_info|asset_count|asset_discovery

Capabilities: api_query|asset_management|asset_query|credential_access|disk_management|disk_monitoring|dns_query|http_client|infrastructure_info|log_analysis|memory_monitoring|network_info|network_monitoring|network_testing|packet_capture|process_management|process_monitoring|protocol_analysis|resource_listing|secret_retrieval|service_management|system_info|system_monitoring|text_search|windows_automation|windows_service_management"""
                    },
                    {
                        "role": "user", 
                        "content": f"Classify: {example['request']}"
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(example['expected_response'], separators=(',', ':'))
                    }
                ]
            }
            hf_examples.append(conversation)
        
        with open(output_file, 'w') as f:
            json.dump(hf_examples, f, indent=2)
        
        print(f"✅ HuggingFace training format saved to: {output_file}")
        return output_file
    
    def create_openai_training_format(self, output_file: str):
        """Create training data in OpenAI fine-tuning format"""
        openai_examples = []
        
        for example in self.examples:
            openai_example = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an infrastructure request classifier. Always return valid JSON with category, action, confidence, and capabilities fields."
                    },
                    {
                        "role": "user",
                        "content": f"Classify this infrastructure request: {example['request']}"
                    },
                    {
                        "role": "assistant", 
                        "content": json.dumps(example['expected_response'])
                    }
                ]
            }
            openai_examples.append(openai_example)
        
        # Save in JSONL format for OpenAI
        with open(output_file, 'w') as f:
            for example in openai_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"✅ OpenAI training format saved to: {output_file}")
        return output_file
    
    def sample_training_examples(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get a sample of training examples for manual review"""
        return random.sample(self.examples, min(count, len(self.examples)))
    
    def analyze_capability_coverage(self) -> Dict[str, Any]:
        """Analyze capability coverage in training data"""
        capability_stats = {}
        category_coverage = {}
        
        for example in self.examples:
            category = example['expected_response']['category']
            capabilities = example['expected_response']['capabilities']
            
            # Track category coverage
            if category not in category_coverage:
                category_coverage[category] = set()
            category_coverage[category].update(capabilities)
            
            # Track capability frequency
            for cap in capabilities:
                capability_stats[cap] = capability_stats.get(cap, 0) + 1
        
        return {
            "capability_frequency": capability_stats,
            "category_capability_map": {cat: list(caps) for cat, caps in category_coverage.items()},
            "total_unique_capabilities": len(capability_stats),
            "least_used_capabilities": sorted(capability_stats.items(), key=lambda x: x[1])[:5],
            "most_used_capabilities": sorted(capability_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def validate_training_data(self) -> Dict[str, Any]:
        """Validate training data quality"""
        issues = []
        stats = {"valid": 0, "invalid": 0}
        
        required_fields = ["category", "action", "confidence", "capabilities"]
        valid_categories = ["automation", "monitoring", "troubleshooting", "configuration", "information", "asset_management"]
        
        for i, example in enumerate(self.examples):
            try:
                # Check structure
                if "request" not in example or "expected_response" not in example:
                    issues.append(f"Example {i}: Missing request or expected_response")
                    stats["invalid"] += 1
                    continue
                
                resp = example["expected_response"]
                
                # Check required fields
                for field in required_fields:
                    if field not in resp:
                        issues.append(f"Example {i}: Missing field '{field}'")
                        stats["invalid"] += 1
                        continue
                
                # Check category validity
                if resp["category"] not in valid_categories:
                    issues.append(f"Example {i}: Invalid category '{resp['category']}'")
                    stats["invalid"] += 1
                    continue
                
                # Check confidence range
                if not (0 <= resp["confidence"] <= 1):
                    issues.append(f"Example {i}: Invalid confidence {resp['confidence']}")
                    stats["invalid"] += 1
                    continue
                
                # Check capabilities is list
                if not isinstance(resp["capabilities"], list) or len(resp["capabilities"]) == 0:
                    issues.append(f"Example {i}: capabilities must be non-empty list")
                    stats["invalid"] += 1
                    continue
                
                stats["valid"] += 1
                
            except Exception as e:
                issues.append(f"Example {i}: Error - {str(e)}")
                stats["invalid"] += 1
        
        return {
            "validation_stats": stats,
            "issues": issues[:20],  # Show first 20 issues
            "total_issues": len(issues),
            "data_quality_score": stats["valid"] / (stats["valid"] + stats["invalid"]) if (stats["valid"] + stats["invalid"]) > 0 else 0
        }

def main():
    """Main fine-tuning helper"""
    print("🎯 LLM Fine-Tuning Helper for Intent Classification")
    print("=" * 60)
    
    # Use the 5k dataset for fine-tuning (good balance of size vs. training time)
    training_file = "/home/opsconductor/opsconductor-ng/training_data/training_data_5k.json"
    
    if not Path(training_file).exists():
        print(f"❌ Training data file not found: {training_file}")
        print("Run generate_llm_training_data.py first!")
        return
    
    helper = LLMFineTuningHelper(training_file)
    
    print(f"📊 Loaded {len(helper.examples)} training examples")
    
    # Validate training data
    print("\n🔍 Validating training data...")
    validation = helper.validate_training_data()
    print(f"✅ Data quality score: {validation['data_quality_score']:.2%}")
    print(f"📈 Valid examples: {validation['validation_stats']['valid']}")
    print(f"❌ Invalid examples: {validation['validation_stats']['invalid']}")
    
    if validation['issues']:
        print(f"⚠️  Found {validation['total_issues']} issues (showing first few):")
        for issue in validation['issues'][:5]:
            print(f"   - {issue}")
    
    # Analyze capability coverage
    print("\n📋 Analyzing capability coverage...")
    coverage = helper.analyze_capability_coverage()
    print(f"🔧 Unique capabilities: {coverage['total_unique_capabilities']}")
    print(f"📊 Most used capabilities: {[cap for cap, count in coverage['most_used_capabilities']]}")
    print(f"📉 Least used capabilities: {[cap for cap, count in coverage['least_used_capabilities']]}")
    
    # Create training formats
    print("\n🔄 Creating training formats...")
    
    output_dir = Path("/home/opsconductor/opsconductor-ng/training_data/formats")
    output_dir.mkdir(exist_ok=True)
    
    # Ollama format
    ollama_file = output_dir / "ollama_training.jsonl"
    helper.create_ollama_training_format(str(ollama_file))
    
    # HuggingFace format  
    hf_file = output_dir / "huggingface_training.json"
    helper.create_huggingface_training_format(str(hf_file))
    
    # OpenAI format
    openai_file = output_dir / "openai_training.jsonl"
    helper.create_openai_training_format(str(openai_file))
    
    print(f"\n📁 Training formats saved to: {output_dir}")
    
    # Show sample
    print(f"\n📝 Sample training examples:")
    samples = helper.sample_training_examples(3)
    for i, sample in enumerate(samples, 1):
        print(f"\n{i}. Request: \"{sample['request']}\"")
        resp = sample['expected_response']
        print(f"   Response: {resp['category']}/{resp['action']} (confidence: {resp['confidence']}) -> {resp['capabilities']}")
    
    print(f"\n🚀 Fine-tuning Instructions:")
    print(f"=" * 40)
    print(f"1. OLLAMA FINE-TUNING:")
    print(f"   ollama create my-model -f Modelfile")
    print(f"   # Use {ollama_file} as training data")
    print(f"")
    print(f"2. HUGGINGFACE FINE-TUNING:")
    print(f"   # Use {hf_file} with transformers library")
    print(f"   # Focus on JSON output format consistency")
    print(f"")
    print(f"3. OPENAI FINE-TUNING:")
    print(f"   openai api fine_tunes.create -t {openai_file}")
    print(f"")
    print(f"🎯 KEY TRAINING FOCUS:")
    print(f"   - ALWAYS include 'capabilities' field")
    print(f"   - Map file reading requests to 'system_info' capability")
    print(f"   - Ensure JSON format is consistent")
    print(f"   - Test with: 'Display contents of /etc/hostname'")

if __name__ == "__main__":
    main()