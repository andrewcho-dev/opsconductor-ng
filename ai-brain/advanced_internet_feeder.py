#!/usr/bin/env python3
"""
Advanced Internet Feeder - Multiple Data Sources
Feeds AI training system with data from various internet sources
"""

import requests
import json
import sqlite3
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from urllib.parse import quote
import feedparser
import xml.etree.ElementTree as ET

class AdvancedInternetFeeder:
    def __init__(self, db_path="/tmp/advanced_internet_training.db"):
        self.db_path = db_path
        self.setup_database()
        
        # Comprehensive data sources
        self.sources = {
            'stackoverflow': {
                'url': 'https://api.stackexchange.com/2.3/questions',
                'tags': ['devops', 'monitoring', 'docker', 'kubernetes', 'aws', 'linux', 'troubleshooting', 'performance', 'automation', 'security'],
                'enabled': True
            },
            'github_issues': {
                'url': 'https://api.github.com/search/issues',
                'queries': ['monitoring', 'devops', 'troubleshooting', 'performance', 'automation', 'security', 'kubernetes', 'docker'],
                'enabled': True
            },
            'reddit': {
                'url': 'https://www.reddit.com/r/{}/hot.json',
                'subreddits': ['devops', 'sysadmin', 'kubernetes', 'docker', 'aws', 'monitoring', 'selfhosted', 'homelab'],
                'enabled': True
            },
            'hackernews': {
                'url': 'https://hacker-news.firebaseio.com/v0/topstories.json',
                'item_url': 'https://hacker-news.firebaseio.com/v0/item/{}.json',
                'keywords': ['devops', 'monitoring', 'kubernetes', 'docker', 'aws', 'infrastructure', 'automation'],
                'enabled': True
            },
            'dev_to': {
                'url': 'https://dev.to/api/articles',
                'tags': ['devops', 'monitoring', 'kubernetes', 'docker', 'aws', 'automation', 'infrastructure'],
                'enabled': True
            },
            'rss_feeds': {
                'feeds': [
                    'https://feeds.feedburner.com/oreilly/radar',
                    'https://aws.amazon.com/blogs/devops/feed/',
                    'https://kubernetes.io/feed.xml',
                    'https://blog.docker.com/feed/'
                ],
                'enabled': True
            }
        }

    def setup_database(self):
        """Setup comprehensive database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS advanced_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT,
                original_url TEXT,
                title TEXT,
                content TEXT,
                intent TEXT,
                confidence REAL,
                tags TEXT,
                score INTEGER DEFAULT 0,
                author TEXT,
                published_date TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quality_score REAL DEFAULT 0.5,
                complexity_level INTEGER DEFAULT 1,
                language TEXT DEFAULT 'en'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feeding_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP,
                total_fetched INTEGER DEFAULT 0,
                sources_used TEXT,
                success_rate REAL DEFAULT 0.0,
                average_quality REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()

    def fetch_stackoverflow_advanced(self, limit=100) -> List[Dict]:
        """Advanced Stack Overflow fetching with better filtering"""
        print("🔍 Fetching from Stack Overflow (Advanced)...")
        results = []
        
        for tag in self.sources['stackoverflow']['tags'][:5]:
            try:
                url = f"{self.sources['stackoverflow']['url']}?order=desc&sort=votes&tagged={tag}&site=stackoverflow&pagesize=20&filter=withbody"
                
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        if item.get('score', 0) >= 1:  # Only quality questions
                            title = item.get('title', '')
                            body = self.clean_html(item.get('body', ''))[:800]
                            
                            if len(title) > 15 and len(body) > 50:
                                intent, confidence = self.classify_intent_advanced(title + ' ' + body)
                                quality = self.calculate_quality_score(item)
                                
                                results.append({
                                    'source': 'stackoverflow',
                                    'source_id': str(item.get('question_id', '')),
                                    'original_url': item.get('link', ''),
                                    'title': title,
                                    'content': f"{title}. {body}".strip(),
                                    'intent': intent,
                                    'confidence': confidence,
                                    'tags': ','.join(item.get('tags', [])),
                                    'score': item.get('score', 0),
                                    'author': item.get('owner', {}).get('display_name', 'Unknown'),
                                    'published_date': datetime.fromtimestamp(item.get('creation_date', 0)),
                                    'quality_score': quality,
                                    'complexity_level': self.calculate_complexity(title + ' ' + body)
                                })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Stack Overflow error: {e}")
                continue
        
        return results[:limit]

    def fetch_github_advanced(self, limit=80) -> List[Dict]:
        """Advanced GitHub issues fetching"""
        print("🔍 Fetching from GitHub Issues (Advanced)...")
        results = []
        
        for query in self.sources['github_issues']['queries'][:4]:
            try:
                search_query = f"{query} is:issue state:open comments:>2"
                url = f"{self.sources['github_issues']['url']}?q={quote(search_query)}&sort=updated&per_page=20"
                
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        title = item.get('title', '')
                        body = item.get('body', '')[:600] if item.get('body') else ''
                        
                        if len(title) > 15 and item.get('comments', 0) >= 2:
                            intent, confidence = self.classify_intent_advanced(title + ' ' + body)
                            
                            results.append({
                                'source': 'github',
                                'source_id': str(item.get('id', '')),
                                'original_url': item.get('html_url', ''),
                                'title': title,
                                'content': f"{title}. {body}".strip(),
                                'intent': intent,
                                'confidence': confidence,
                                'tags': ','.join([label.get('name', '') for label in item.get('labels', [])]),
                                'score': item.get('comments', 0),
                                'author': item.get('user', {}).get('login', 'Unknown'),
                                'published_date': datetime.fromisoformat(item.get('created_at', '').replace('Z', '+00:00')),
                                'quality_score': min(0.9, item.get('comments', 0) / 10.0),
                                'complexity_level': self.calculate_complexity(title + ' ' + body)
                            })
                
                time.sleep(1.0)
                
            except Exception as e:
                print(f"❌ GitHub error: {e}")
                continue
        
        return results[:limit]

    def fetch_hackernews(self, limit=50) -> List[Dict]:
        """Fetch from Hacker News API"""
        print("🔍 Fetching from Hacker News...")
        results = []
        
        try:
            # Get top stories
            response = requests.get(self.sources['hackernews']['url'], timeout=10)
            if response.status_code == 200:
                story_ids = response.json()[:100]  # Top 100 stories
                
                for story_id in story_ids[:limit]:
                    try:
                        item_url = self.sources['hackernews']['item_url'].format(story_id)
                        item_response = requests.get(item_url, timeout=5)
                        
                        if item_response.status_code == 200:
                            item = item_response.json()
                            title = item.get('title', '')
                            text = item.get('text', '')[:400] if item.get('text') else ''
                            
                            # Check if relevant to our keywords
                            if any(keyword in title.lower() for keyword in self.sources['hackernews']['keywords']):
                                intent, confidence = self.classify_intent_advanced(title + ' ' + text)
                                
                                results.append({
                                    'source': 'hackernews',
                                    'source_id': str(story_id),
                                    'original_url': item.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                                    'title': title,
                                    'content': f"{title}. {text}".strip(),
                                    'intent': intent,
                                    'confidence': confidence,
                                    'tags': 'hackernews',
                                    'score': item.get('score', 0),
                                    'author': item.get('by', 'Unknown'),
                                    'published_date': datetime.fromtimestamp(item.get('time', 0)),
                                    'quality_score': min(0.9, item.get('score', 0) / 100.0),
                                    'complexity_level': self.calculate_complexity(title + ' ' + text)
                                })
                        
                        time.sleep(0.1)  # Small delay between requests
                        
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"❌ Hacker News error: {e}")
        
        return results

    def fetch_dev_to(self, limit=60) -> List[Dict]:
        """Fetch from Dev.to API"""
        print("🔍 Fetching from Dev.to...")
        results = []
        
        for tag in self.sources['dev_to']['tags'][:3]:
            try:
                url = f"{self.sources['dev_to']['url']}?tag={tag}&per_page=20&top=7"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    articles = response.json()
                    
                    for article in articles:
                        title = article.get('title', '')
                        description = article.get('description', '')[:400]
                        
                        if len(title) > 15 and article.get('positive_reactions_count', 0) >= 5:
                            intent, confidence = self.classify_intent_advanced(title + ' ' + description)
                            
                            results.append({
                                'source': 'dev_to',
                                'source_id': str(article.get('id', '')),
                                'original_url': article.get('url', ''),
                                'title': title,
                                'content': f"{title}. {description}".strip(),
                                'intent': intent,
                                'confidence': confidence,
                                'tags': ','.join(article.get('tag_list', [])),
                                'score': article.get('positive_reactions_count', 0),
                                'author': article.get('user', {}).get('name', 'Unknown'),
                                'published_date': datetime.fromisoformat(article.get('published_at', '').replace('Z', '+00:00')),
                                'quality_score': min(0.9, article.get('positive_reactions_count', 0) / 50.0),
                                'complexity_level': self.calculate_complexity(title + ' ' + description)
                            })
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Dev.to error: {e}")
                continue
        
        return results[:limit]

    def fetch_rss_feeds(self, limit=40) -> List[Dict]:
        """Fetch from RSS feeds"""
        print("🔍 Fetching from RSS Feeds...")
        results = []
        
        for feed_url in self.sources['rss_feeds']['feeds']:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:limit//len(self.sources['rss_feeds']['feeds'])]:
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')[:400]
                    
                    if len(title) > 15:
                        intent, confidence = self.classify_intent_advanced(title + ' ' + summary)
                        
                        results.append({
                            'source': 'rss_feed',
                            'source_id': entry.get('id', ''),
                            'original_url': entry.get('link', ''),
                            'title': title,
                            'content': f"{title}. {summary}".strip(),
                            'intent': intent,
                            'confidence': confidence,
                            'tags': feed.feed.get('title', 'RSS'),
                            'score': 1,
                            'author': entry.get('author', 'Unknown'),
                            'published_date': datetime(*entry.get('published_parsed', time.gmtime())[:6]),
                            'quality_score': 0.7,  # RSS feeds generally have good quality
                            'complexity_level': self.calculate_complexity(title + ' ' + summary)
                        })
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ RSS feed error: {e}")
                continue
        
        return results

    def classify_intent_advanced(self, text: str) -> tuple:
        """Advanced intent classification with better patterns"""
        text_lower = text.lower()
        
        # Enhanced patterns with more sophisticated matching
        patterns = {
            'asset_query': [
                r'what.*(?:server|service|resource|status|version)',
                r'(?:show|list|display|get).*(?:info|status|details)',
                r'which.*(?:running|available|installed)',
                r'find.*(?:resource|service|server)',
                r'how.*(?:many|much).*(?:memory|cpu|disk)'
            ],
            'troubleshooting': [
                r'(?:error|problem|issue|bug).*(?:fix|solve|resolve)',
                r'(?:not|doesn\'t|can\'t).*(?:work|start|connect)',
                r'(?:failed|broken|crashed).*(?:why|how|fix)',
                r'debug.*(?:help|issue|problem)',
                r'troubleshoot.*(?:guide|steps|help)'
            ],
            'automation_request': [
                r'automate.*(?:process|task|deployment)',
                r'(?:script|pipeline).*(?:create|build|setup)',
                r'schedule.*(?:task|job|backup)',
                r'(?:ci/cd|continuous).*(?:integration|deployment)',
                r'workflow.*(?:automation|orchestration)'
            ],
            'monitoring': [
                r'monitor.*(?:system|application|performance)',
                r'(?:alert|notification).*(?:when|if|setup)',
                r'dashboard.*(?:create|setup|configure)',
                r'(?:metrics|logs).*(?:collect|analyze|track)',
                r'observability.*(?:setup|implementation)'
            ],
            'security': [
                r'secure.*(?:access|connection|data)',
                r'(?:permission|access).*(?:control|management)',
                r'(?:vulnerability|security).*(?:scan|audit)',
                r'(?:firewall|encryption).*(?:setup|configure)',
                r'authentication.*(?:setup|implementation)'
            ],
            'performance': [
                r'(?:optimize|improve).*(?:performance|speed)',
                r'(?:slow|high).*(?:response|latency|usage)',
                r'(?:bottleneck|memory leak).*(?:find|identify)',
                r'(?:cpu|memory|disk).*(?:usage|optimization)',
                r'performance.*(?:tuning|optimization)'
            ]
        }
        
        intent_scores = {}
        for intent, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                matches = len(re.findall(pattern, text_lower))
                score += matches * 15
            intent_scores[intent] = score
        
        if not intent_scores or max(intent_scores.values()) == 0:
            return 'asset_query', 0.4
        
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        confidence = min(0.95, max(0.4, max_score / 60.0))
        
        return best_intent, confidence

    def calculate_quality_score(self, item: Dict) -> float:
        """Calculate quality score based on various factors"""
        score = 0.5  # Base score
        
        # Stack Overflow specific scoring
        if 'score' in item:
            score += min(0.3, item['score'] / 20.0)
        if 'answer_count' in item:
            score += min(0.2, item['answer_count'] / 10.0)
        
        return min(0.95, score)

    def calculate_complexity(self, text: str) -> int:
        """Calculate complexity level (1-5) based on text analysis"""
        complexity = 1
        
        # Technical terms increase complexity
        technical_terms = ['kubernetes', 'docker', 'aws', 'microservices', 'api', 'database', 'security', 'performance']
        complexity += sum(1 for term in technical_terms if term in text.lower())
        
        # Length increases complexity
        if len(text) > 200:
            complexity += 1
        if len(text) > 500:
            complexity += 1
        
        return min(5, complexity)

    def clean_html(self, text: str) -> str:
        """Clean HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def store_advanced_data(self, data_list: List[Dict]):
        """Store data with advanced schema"""
        if not data_list:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for data in data_list:
            cursor.execute('''
                INSERT INTO advanced_training_data 
                (source, source_id, original_url, title, content, intent, confidence, 
                 tags, score, author, published_date, quality_score, complexity_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['source'], data['source_id'], data['original_url'],
                data['title'], data['content'], data['intent'], data['confidence'],
                data['tags'], data['score'], data['author'], data['published_date'],
                data['quality_score'], data['complexity_level']
            ))
        
        conn.commit()
        conn.close()

    def run_advanced_feeding_cycle(self, total_examples=500):
        """Run comprehensive internet data feeding"""
        print("🌐 ADVANCED INTERNET FEEDING CYCLE STARTING...")
        print(f"🎯 Target: {total_examples} high-quality examples")
        
        session_start = datetime.now()
        all_data = []
        sources_used = []
        
        # Fetch from all sources
        if self.sources['stackoverflow']['enabled']:
            stackoverflow_data = self.fetch_stackoverflow_advanced(total_examples // 6)
            all_data.extend(stackoverflow_data)
            sources_used.append('stackoverflow')
            print(f"✅ Stack Overflow: {len(stackoverflow_data)} examples")
        
        if self.sources['github_issues']['enabled']:
            github_data = self.fetch_github_advanced(total_examples // 6)
            all_data.extend(github_data)
            sources_used.append('github')
            print(f"✅ GitHub: {len(github_data)} examples")
        
        if self.sources['hackernews']['enabled']:
            hn_data = self.fetch_hackernews(total_examples // 6)
            all_data.extend(hn_data)
            sources_used.append('hackernews')
            print(f"✅ Hacker News: {len(hn_data)} examples")
        
        if self.sources['dev_to']['enabled']:
            devto_data = self.fetch_dev_to(total_examples // 6)
            all_data.extend(devto_data)
            sources_used.append('dev_to')
            print(f"✅ Dev.to: {len(devto_data)} examples")
        
        if self.sources['rss_feeds']['enabled']:
            rss_data = self.fetch_rss_feeds(total_examples // 6)
            all_data.extend(rss_data)
            sources_used.append('rss_feeds')
            print(f"✅ RSS Feeds: {len(rss_data)} examples")
        
        # Store data
        self.store_advanced_data(all_data)
        
        # Record session
        self.record_feeding_session(session_start, len(all_data), sources_used, all_data)
        
        # Generate comprehensive statistics
        self.generate_advanced_statistics(all_data)
        
        return len(all_data)

    def record_feeding_session(self, start_time, total_fetched, sources, data_list):
        """Record feeding session statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        avg_quality = sum(item['quality_score'] for item in data_list) / len(data_list) if data_list else 0
        success_rate = len(data_list) / max(1, total_fetched) * 100
        
        cursor.execute('''
            INSERT INTO feeding_sessions 
            (session_start, session_end, total_fetched, sources_used, success_rate, average_quality)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (start_time, datetime.now(), total_fetched, ','.join(sources), success_rate, avg_quality))
        
        conn.commit()
        conn.close()

    def generate_advanced_statistics(self, data_list: List[Dict]):
        """Generate comprehensive statistics"""
        if not data_list:
            return
        
        print(f"\n📊 ADVANCED INTERNET FEEDING STATISTICS")
        print(f"{'='*60}")
        
        # Basic stats
        total_examples = len(data_list)
        avg_confidence = sum(item['confidence'] for item in data_list) / total_examples
        avg_quality = sum(item['quality_score'] for item in data_list) / total_examples
        avg_complexity = sum(item['complexity_level'] for item in data_list) / total_examples
        
        print(f"📈 Total Examples: {total_examples}")
        print(f"🎯 Average Confidence: {avg_confidence:.1%}")
        print(f"⭐ Average Quality Score: {avg_quality:.2f}/1.0")
        print(f"🧠 Average Complexity: {avg_complexity:.1f}/5.0")
        
        # Source distribution
        source_counts = {}
        intent_counts = {}
        
        for item in data_list:
            source_counts[item['source']] = source_counts.get(item['source'], 0) + 1
            intent_counts[item['intent']] = intent_counts.get(item['intent'], 0) + 1
        
        print(f"\n🌐 Source Distribution:")
        for source, count in sorted(source_counts.items()):
            percentage = (count / total_examples) * 100
            print(f"  • {source.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        print(f"\n🎯 Intent Distribution:")
        for intent, count in sorted(intent_counts.items()):
            percentage = (count / total_examples) * 100
            print(f"  • {intent.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Quality distribution
        high_quality = sum(1 for item in data_list if item['quality_score'] >= 0.7)
        medium_quality = sum(1 for item in data_list if 0.4 <= item['quality_score'] < 0.7)
        low_quality = sum(1 for item in data_list if item['quality_score'] < 0.4)
        
        print(f"\n⭐ Quality Distribution:")
        print(f"  • High Quality (≥0.7): {high_quality} ({high_quality/total_examples*100:.1f}%)")
        print(f"  • Medium Quality (0.4-0.7): {medium_quality} ({medium_quality/total_examples*100:.1f}%)")
        print(f"  • Low Quality (<0.4): {low_quality} ({low_quality/total_examples*100:.1f}%)")

    def export_advanced_data(self, filename="/tmp/advanced_internet_export.json"):
        """Export with advanced metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM advanced_training_data ORDER BY quality_score DESC, fetched_at DESC')
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        
        # Add metadata
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_examples': len(data),
                'sources': list(set(item['source'] for item in data)),
                'date_range': {
                    'earliest': min(item['published_date'] for item in data if item['published_date']),
                    'latest': max(item['published_date'] for item in data if item['published_date'])
                }
            },
            'training_data': data
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        conn.close()
        print(f"📁 Exported {len(data)} examples to {filename}")
        return len(data)

def main():
    """Main execution"""
    print("🚀 ADVANCED INTERNET DATA FEEDER - LAUNCHING!")
    
    feeder = AdvancedInternetFeeder()
    
    # Run comprehensive feeding
    total_fetched = feeder.run_advanced_feeding_cycle(500)
    
    print(f"\n✅ ADVANCED FEEDING COMPLETE!")
    print(f"📊 Total High-Quality Examples: {total_fetched}")
    
    # Export with metadata
    feeder.export_advanced_data()
    
    print(f"\n🎉 YOUR AI NOW HAS PREMIUM INTERNET DATA!")
    print(f"🌐 Sources: Stack Overflow, GitHub, Hacker News, Dev.to, RSS Feeds")
    print(f"⭐ High-quality, curated content for superior training!")

if __name__ == "__main__":
    main()