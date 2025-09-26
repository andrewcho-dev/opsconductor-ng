#!/usr/bin/env python3
"""
Knowledge Learning CLI
Easy command-line interface for teaching the AI about new technical domains
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from knowledge_learner import get_knowledge_learner

def main():
    parser = argparse.ArgumentParser(description="Teach OpsConductor AI about new technical domains")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Learn from API URL
    api_parser = subparsers.add_parser('api', help='Learn from an API URL')
    api_parser.add_argument('url', help='Base URL of the API')
    api_parser.add_argument('name', help='Human-readable name for the domain')
    api_parser.add_argument('--description', help='Description of what this API does')
    api_parser.add_argument('--keywords', nargs='+', help='Keywords that should trigger this domain')
    
    # Learn from documentation file
    doc_parser = subparsers.add_parser('doc', help='Learn from a documentation file')
    doc_parser.add_argument('file', help='Path to JSON documentation file')
    doc_parser.add_argument('name', help='Human-readable name for the domain')
    doc_parser.add_argument('--keywords', nargs='+', help='Additional keywords')
    
    # Learn from interactive input
    interactive_parser = subparsers.add_parser('interactive', help='Interactive learning session')
    
    # List known domains
    list_parser = subparsers.add_parser('list', help='List all known domains')
    
    # Export domain knowledge
    export_parser = subparsers.add_parser('export', help='Export domain knowledge')
    export_parser.add_argument('domain_id', help='Domain ID to export')
    export_parser.add_argument('--output', help='Output file (default: stdout)')
    
    # Get learning suggestions
    suggest_parser = subparsers.add_parser('suggest', help='Get learning suggestions for a request')
    suggest_parser.add_argument('request', help='Request text to analyze')
    
    # Quick setup for common technologies
    quick_parser = subparsers.add_parser('quick', help='Quick setup for common technologies')
    quick_parser.add_argument('tech', choices=['vapix', 'aws', 'docker', 'kubernetes'], 
                             help='Technology to set up')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    learner = get_knowledge_learner()
    
    if args.command == 'api':
        asyncio.run(learn_from_api(learner, args))
    elif args.command == 'doc':
        learn_from_doc(learner, args)
    elif args.command == 'interactive':
        interactive_learning(learner)
    elif args.command == 'list':
        list_domains(learner)
    elif args.command == 'export':
        export_domain(learner, args)
    elif args.command == 'suggest':
        suggest_learning(learner, args)
    elif args.command == 'quick':
        quick_setup(learner, args)

async def learn_from_api(learner, args):
    """Learn from an API URL"""
    print(f"Learning from API: {args.url}")
    print(f"Domain name: {args.name}")
    
    success = await learner.learn_from_api_url(
        args.url, 
        args.name, 
        args.description or "", 
        args.keywords or []
    )
    
    if success:
        print("✅ Successfully learned from API!")
    else:
        print("❌ Failed to learn from API. Check logs for details.")

def learn_from_doc(learner, args):
    """Learn from a documentation file"""
    try:
        doc_path = Path(args.file)
        if not doc_path.exists():
            print(f"❌ Documentation file not found: {args.file}")
            return
        
        with open(doc_path, 'r') as f:
            documentation = json.load(f)
        
        print(f"Learning from documentation: {args.file}")
        print(f"Domain name: {args.name}")
        
        success = learner.learn_from_documentation(
            args.name,
            documentation,
            args.keywords or []
        )
        
        if success:
            print("✅ Successfully learned from documentation!")
        else:
            print("❌ Failed to learn from documentation. Check logs for details.")
            
    except Exception as e:
        print(f"❌ Error reading documentation file: {e}")

def interactive_learning(learner):
    """Interactive learning session"""
    print("🎓 Interactive Learning Session")
    print("=" * 50)
    
    domain_name = input("Enter domain name: ").strip()
    if not domain_name:
        print("❌ Domain name is required")
        return
    
    description = input("Enter description: ").strip()
    
    print("\nEnter keywords (one per line, empty line to finish):")
    keywords = []
    while True:
        keyword = input("Keyword: ").strip()
        if not keyword:
            break
        keywords.append(keyword)
    
    print("\nChoose learning method:")
    print("1. API URL")
    print("2. Manual documentation")
    
    choice = input("Choice (1-2): ").strip()
    
    if choice == "1":
        api_url = input("Enter API URL: ").strip()
        if api_url:
            print("\n🔍 Learning from API...")
            success = asyncio.run(learner.learn_from_api_url(api_url, domain_name, description, keywords))
            if success:
                print("✅ Successfully learned from API!")
            else:
                print("❌ Failed to learn from API.")
    
    elif choice == "2":
        print("\n📝 Manual documentation entry")
        print("Enter capabilities (format: name:description, empty line to finish):")
        
        capabilities = {}
        while True:
            cap_input = input("Capability: ").strip()
            if not cap_input:
                break
            
            if ":" in cap_input:
                name, desc = cap_input.split(":", 1)
                capabilities[name.strip()] = {
                    "description": desc.strip(),
                    "keywords": [],
                    "endpoints": [],
                    "use_cases": []
                }
        
        documentation = {
            "description": description,
            "capabilities": capabilities
        }
        
        success = learner.learn_from_documentation(domain_name, documentation, keywords)
        if success:
            print("✅ Successfully learned from documentation!")
        else:
            print("❌ Failed to learn from documentation.")
    
    else:
        print("❌ Invalid choice")

def list_domains(learner):
    """List all known domains"""
    domains = learner.list_known_domains()
    
    print("📚 Known Knowledge Domains")
    print("=" * 50)
    
    if not domains:
        print("No domains found.")
        return
    
    for domain in domains:
        print(f"\n🔹 {domain['domain_id']}")
        print(f"   Type: {domain['type']}")
        print(f"   Keywords: {', '.join(domain['keywords'][:5])}{'...' if len(domain['keywords']) > 5 else ''}")
        print(f"   Last Updated: {domain['last_updated']}")
        print(f"   Size: {domain['size_bytes']} bytes")

def export_domain(learner, args):
    """Export domain knowledge"""
    knowledge = learner.export_domain_knowledge(args.domain_id)
    
    if not knowledge:
        print(f"❌ Domain not found: {args.domain_id}")
        return
    
    output = json.dumps(knowledge, indent=2, default=str)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✅ Exported to {args.output}")
    else:
        print(output)

def suggest_learning(learner, args):
    """Get learning suggestions for a request"""
    suggestions = learner.get_learning_suggestions(args.request)
    
    print(f"🔍 Learning Suggestions for: '{args.request}'")
    print("=" * 50)
    
    if not suggestions:
        print("No learning suggestions found.")
        return
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion['technology'].upper()}")
        print(f"   Description: {suggestion['description']}")
        print(f"   Confidence: {suggestion['confidence']:.2%}")
        print(f"   Learning Method: {suggestion['learning_method']}")

def quick_setup(learner, args):
    """Quick setup for common technologies"""
    print(f"🚀 Quick setup for {args.tech.upper()}")
    
    if args.tech == 'vapix':
        success = learner.learn_vapix_cameras()
        if success:
            print("✅ VAPIX camera knowledge added!")
        else:
            print("❌ Failed to add VAPIX knowledge.")
    
    elif args.tech == 'aws':
        success = learner.learn_aws_services()
        if success:
            print("✅ AWS services knowledge added!")
        else:
            print("❌ Failed to add AWS knowledge.")
    
    elif args.tech == 'docker':
        print("🔍 Learning Docker API...")
        success = asyncio.run(learner.learn_from_api_url(
            "http://localhost:2376",
            "Docker Engine",
            "Docker container management API",
            ["docker", "container", "image", "registry"]
        ))
        if success:
            print("✅ Docker knowledge added!")
        else:
            print("❌ Failed to add Docker knowledge. Make sure Docker API is accessible.")
    
    elif args.tech == 'kubernetes':
        print("🔍 Learning Kubernetes API...")
        success = asyncio.run(learner.learn_from_api_url(
            "https://kubernetes.default.svc",
            "Kubernetes",
            "Kubernetes cluster management API",
            ["kubernetes", "k8s", "pod", "deployment", "service"]
        ))
        if success:
            print("✅ Kubernetes knowledge added!")
        else:
            print("❌ Failed to add Kubernetes knowledge. Make sure cluster is accessible.")

if __name__ == "__main__":
    main()