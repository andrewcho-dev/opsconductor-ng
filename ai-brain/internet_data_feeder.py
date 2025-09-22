#!/usr/bin/env python3
"""
Internet Data Feeder for AI Training System
Pulls training data from various internet sources to continuously feed the AI
"""

import requests
import json
import sqlite3
import time
import random
from datetime import datetime
from typing import List, Dict, Any
import re
from urllib.parse import quote

class InternetDataFeeder:
    def __init__(self, db_path="/tmp/internet_training.db"):
        self.db_path = db_path
        self.setup_database()
        
        # Data sources configuration
        self.sources = {
            'stackoverflow': {
                'base_url': 'https://api.stackexchange.com/2.3/questions',
                'tags': ['devops', 'monitoring', 'docker', 'kubernetes', 'aws', 'linux', 'troubleshooting', 'performance'],
                'rate_limit': 1.0  # seconds between requests
            },
            'github_issues': {
                'base_url': 'https://api.github.com/search/issues',
                'queries': ['monitoring', 'devops', 'troubleshooting', 'performance', 'automation', 'security'],
                'rate_limit': 1.0
            },
            'reddit': {
                'base_url': 'https://www.reddit.com/r/{}/hot.json',
                'subreddits': ['devops', 'sysadmin', 'kubernetes', 'docker', 'aws', 'monitoring'],
                'rate_limit': 2.0
            }
        }
        
        # Intent classification patterns
        self.intent_patterns = {
            'asset_query': [
                r'what.*server', r'show.*status', r'list.*services', r'get.*info',
                r'which.*running', r'find.*resource', r'display.*metrics'
            ],
            'troubleshooting': [
                r'error.*fix', r'problem.*solve', r'issue.*resolve', r'debug.*help',
                r'not.*working', r'failed.*why', r'broken.*repair'
            ],
            'automation_request': [
                r'automate.*process', r'script.*create', r'schedule.*task', r'deploy.*auto',
                r'pipeline.*setup', r'workflow.*build', r'trigger.*when'
            ],
            'monitoring': [
                r'monitor.*system', r'alert.*when', r'watch.*for', r'track.*performance',
                r'dashboard.*show', r'metrics.*collect', r'log.*analyze'
            ],
            'security': [
                r'secure.*access', r'permission.*grant', r'vulnerability.*scan', r'audit.*log',
                r'firewall.*rule', r'encrypt.*data', r'authentication.*setup'
            ],
            'performance': [
                r'optimize.*speed', r'improve.*performance', r'slow.*response', r'bottleneck.*find',
                r'memory.*usage', r'cpu.*high', r'disk.*space'
            ]
        }

    def setup_database(self):
        """Setup SQLite database for storing internet training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS internet_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                original_url TEXT,
                title TEXT,
                content TEXT,
                intent TEXT,
                confidence REAL,
                tags TEXT,
                score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_stats (
                source TEXT PRIMARY KEY,
                total_fetched INTEGER DEFAULT 0,
                successful_processed INTEGER DEFAULT 0,
                last_fetch TIMESTAMP,
                rate_limit REAL
            )
        ''')
        
        conn.commit()
        conn.close()

    def classify_intent(self, text: str) -> tuple:
        """Classify text into intent categories with confidence"""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches * 10
            
            # Bonus for keyword presence
            keywords = {
                'asset_query': ['server', 'service', 'resource', 'status', 'info'],
                'troubleshooting': ['error', 'problem', 'issue', 'debug', 'fix'],
                'automation_request': ['automate', 'script', 'deploy', 'pipeline'],
                'monitoring': ['monitor', 'alert', 'dashboard', 'metrics'],
                'security': ['secure', 'permission', 'audit', 'firewall'],
                'performance': ['performance', 'optimize', 'slow', 'memory', 'cpu']
            }
            
            for keyword in keywords.get(intent, []):
                if keyword in text_lower:
                    score += 5
            
            intent_scores[intent] = score
        
        if not intent_scores or max(intent_scores.values()) == 0:
            return 'asset_query', 0.3  # Default fallback
        
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        confidence = min(0.95, max(0.3, max_score / 50.0))
        
        return best_intent, confidence

    def fetch_stackoverflow_data(self, limit=50) -> List[Dict]:
        """Fetch questions from Stack Overflow API"""
        print("🔍 Fetching from Stack Overflow...")
        results = []
        
        for tag in self.sources['stackoverflow']['tags'][:3]:  # Limit to 3 tags per run
            try:
                url = f"{self.sources['stackoverflow']['base_url']}?order=desc&sort=activity&tagged={tag}&site=stackoverflow&pagesize={limit//len(self.sources['stackoverflow']['tags'])}"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        title = item.get('title', '')
                        body = item.get('body', '')[:500]  # Limit body length
                        
                        if title and len(title) > 10:
                            intent, confidence = self.classify_intent(title + ' ' + body)
                            
                            results.append({
                                'source': 'stackoverflow',
                                'original_url': item.get('link', ''),
                                'title': title,
                                'content': f"{title}. {body}".strip(),
                                'intent': intent,
                                'confidence': confidence,
                                'tags': ','.join(item.get('tags', [])),
                                'score': item.get('score', 0)
                            })
                
                time.sleep(self.sources['stackoverflow']['rate_limit'])
                
            except Exception as e:
                print(f"❌ Error fetching from Stack Overflow: {e}")
                continue
        
        return results

    def fetch_github_issues(self, limit=30) -> List[Dict]:
        """Fetch issues from GitHub API"""
        print("🔍 Fetching from GitHub Issues...")
        results = []
        
        for query in self.sources['github_issues']['queries'][:2]:  # Limit queries
            try:
                search_query = f"{query} is:issue state:open"
                url = f"{self.sources['github_issues']['base_url']}?q={quote(search_query)}&sort=updated&per_page={limit//len(self.sources['github_issues']['queries'])}"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        title = item.get('title', '')
                        body = item.get('body', '')[:300] if item.get('body') else ''
                        
                        if title and len(title) > 10:
                            intent, confidence = self.classify_intent(title + ' ' + body)
                            
                            results.append({
                                'source': 'github',
                                'original_url': item.get('html_url', ''),
                                'title': title,
                                'content': f"{title}. {body}".strip(),
                                'intent': intent,
                                'confidence': confidence,
                                'tags': ','.join([label.get('name', '') for label in item.get('labels', [])]),
                                'score': item.get('comments', 0)
                            })
                
                time.sleep(self.sources['github_issues']['rate_limit'])
                
            except Exception as e:
                print(f"❌ Error fetching from GitHub: {e}")
                continue
        
        return results

    def fetch_reddit_data(self, limit=20) -> List[Dict]:
        """Fetch posts from Reddit API"""
        print("🔍 Fetching from Reddit...")
        results = []
        
        headers = {'User-Agent': 'AI-Training-Bot/1.0'}
        
        for subreddit in self.sources['reddit']['subreddits'][:2]:  # Limit subreddits
            try:
                url = self.sources['reddit']['base_url'].format(subreddit)
                
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for post in data.get('data', {}).get('children', [])[:limit//len(self.sources['reddit']['subreddits'])]:
                        post_data = post.get('data', {})
                        title = post_data.get('title', '')
                        selftext = post_data.get('selftext', '')[:300]
                        
                        if title and len(title) > 10 and not post_data.get('over_18', False):
                            intent, confidence = self.classify_intent(title + ' ' + selftext)
                            
                            results.append({
                                'source': 'reddit',
                                'original_url': f"https://reddit.com{post_data.get('permalink', '')}",
                                'title': title,
                                'content': f"{title}. {selftext}".strip(),
                                'intent': intent,
                                'confidence': confidence,
                                'tags': f"r/{subreddit}",
                                'score': post_data.get('score', 0)
                            })
                
                time.sleep(self.sources['reddit']['rate_limit'])
                
            except Exception as e:
                print(f"❌ Error fetching from Reddit: {e}")
                continue
        
        return results

    def store_training_data(self, data_list: List[Dict]):
        """Store fetched data in database"""
        if not data_list:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for data in data_list:
            cursor.execute('''
                INSERT INTO internet_training_data 
                (source, original_url, title, content, intent, confidence, tags, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['source'],
                data['original_url'],
                data['title'],
                data['content'],
                data['intent'],
                data['confidence'],
                data['tags'],
                data['score']
            ))
        
        conn.commit()
        conn.close()

    def update_source_stats(self, source: str, fetched: int, processed: int):
        """Update statistics for data sources"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO source_stats 
            (source, total_fetched, successful_processed, last_fetch)
            VALUES (?, 
                COALESCE((SELECT total_fetched FROM source_stats WHERE source = ?), 0) + ?,
                COALESCE((SELECT successful_processed FROM source_stats WHERE source = ?), 0) + ?,
                CURRENT_TIMESTAMP)
        ''', (source, source, fetched, source, processed))
        
        conn.commit()
        conn.close()

    def run_internet_feeding_cycle(self, total_examples=200):
        """Run a complete cycle of internet data feeding"""
        print("🌐 Starting Internet Data Feeding Cycle...")
        print(f"🎯 Target: {total_examples} examples from internet sources")
        
        all_data = []
        
        # Fetch from Stack Overflow
        stackoverflow_data = self.fetch_stackoverflow_data(total_examples // 3)
        all_data.extend(stackoverflow_data)
        self.update_source_stats('stackoverflow', len(stackoverflow_data), len(stackoverflow_data))
        
        # Fetch from GitHub
        github_data = self.fetch_github_issues(total_examples // 3)
        all_data.extend(github_data)
        self.update_source_stats('github', len(github_data), len(github_data))
        
        # Fetch from Reddit
        reddit_data = self.fetch_reddit_data(total_examples // 3)
        all_data.extend(reddit_data)
        self.update_source_stats('reddit', len(reddit_data), len(reddit_data))
        
        # Store all data
        self.store_training_data(all_data)
        
        # Generate statistics
        self.generate_statistics(all_data)
        
        return len(all_data)

    def generate_statistics(self, data_list: List[Dict]):
        """Generate and display statistics"""
        if not data_list:
            print("❌ No data to analyze")
            return
        
        print(f"\n📊 INTERNET DATA FEEDING STATISTICS")
        print(f"{'='*50}")
        
        # Source breakdown
        source_counts = {}
        intent_counts = {}
        total_confidence = 0
        
        for item in data_list:
            source = item['source']
            intent = item['intent']
            confidence = item['confidence']
            
            source_counts[source] = source_counts.get(source, 0) + 1
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            total_confidence += confidence
        
        print(f"📈 Total Examples Fetched: {len(data_list)}")
        print(f"🎯 Average Confidence: {total_confidence/len(data_list):.1%}")
        
        print(f"\n🌐 Source Distribution:")
        for source, count in source_counts.items():
            percentage = (count / len(data_list)) * 100
            print(f"  • {source.title()}: {count} examples ({percentage:.1f}%)")
        
        print(f"\n🎯 Intent Distribution:")
        for intent, count in intent_counts.items():
            percentage = (count / len(data_list)) * 100
            print(f"  • {intent.replace('_', ' ').title()}: {count} examples ({percentage:.1f}%)")

    def export_to_json(self, filename="/tmp/internet_training_export.json"):
        """Export all internet training data to JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM internet_training_data ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        conn.close()
        print(f"📁 Exported {len(data)} examples to {filename}")
        return len(data)

def main():
    """Main execution function"""
    print("🚀 INTERNET DATA FEEDER - STARTING UP!")
    
    feeder = InternetDataFeeder()
    
    # Run feeding cycle
    total_fetched = feeder.run_internet_feeding_cycle(200)
    
    print(f"\n✅ INTERNET FEEDING COMPLETE!")
    print(f"📊 Total Examples Fetched: {total_fetched}")
    
    # Export data
    feeder.export_to_json()
    
    print(f"\n🎉 Your AI now has REAL INTERNET DATA for training!")
    print(f"🌐 Sources: Stack Overflow, GitHub Issues, Reddit")
    print(f"🧠 Ready for continuous learning from the internet!")

if __name__ == "__main__":
    main()