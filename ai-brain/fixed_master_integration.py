#!/usr/bin/env python3
"""
Fixed Master Internet Integration System
Combines internet-sourced data with AI-generated training examples
"""

import sqlite3
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from internet_data_feeder import InternetDataFeeder
from advanced_internet_feeder import AdvancedInternetFeeder
from infinite_training_engine import InfiniteTrainingEngine

class FixedMasterIntegration:
    def __init__(self):
        self.internet_feeder = InternetDataFeeder()
        self.advanced_feeder = AdvancedInternetFeeder()
        self.infinite_engine = InfiniteTrainingEngine()
        
        # Master database for unified storage
        self.master_db_path = "/tmp/master_ai_training.db"
        self.setup_master_database()
    
    def setup_master_database(self):
        """Create unified database schema"""
        conn = sqlite3.connect(self.master_db_path)
        cursor = conn.cursor()
        
        # Unified training data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unified_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                intent TEXT NOT NULL,
                confidence REAL NOT NULL,
                source_type TEXT NOT NULL,  -- 'internet' or 'generated'
                source_name TEXT,           -- 'stackoverflow', 'github', 'ai_generated', etc.
                original_url TEXT,
                title TEXT,
                content TEXT,
                tags TEXT,
                score INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                complexity_score INTEGER DEFAULT 1,
                generation_method TEXT,
                linguistic_pattern TEXT,
                context TEXT,
                batch_id INTEGER,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def convert_internet_data(self, internet_examples: List[Dict]) -> List[Dict]:
        """Convert internet data to unified format"""
        unified_examples = []
        
        for example in internet_examples:
            unified_example = {
                'user_input': example.get('title', example.get('content', ''))[:500],
                'intent': example.get('intent', 'asset_query'),
                'confidence': example.get('confidence', 0.3),
                'source_type': 'internet',
                'source_name': example.get('source', 'unknown'),
                'original_url': example.get('original_url', ''),
                'title': example.get('title', ''),
                'content': example.get('content', ''),
                'tags': example.get('tags', ''),
                'score': example.get('score', 0),
                'quality_score': example.get('quality_score', 0.5),
                'complexity_score': example.get('complexity_level', example.get('complexity', 2)),
                'generation_method': 'internet_sourced',
                'linguistic_pattern': 'natural',
                'context': f"Source: {example.get('source', 'unknown')}",
                'batch_id': None,
                'session_id': None,
                'created_at': example.get('created_at', example.get('fetched_at', datetime.now().isoformat())),
                'processed_at': datetime.now().isoformat()
            }
            unified_examples.append(unified_example)
        
        return unified_examples
    
    def convert_generated_data(self, generated_examples: List[Dict]) -> List[Dict]:
        """Convert AI-generated data to unified format"""
        unified_examples = []
        
        for example in generated_examples:
            unified_example = {
                'user_input': example.get('user_input', ''),
                'intent': example.get('intent', 'asset_query'),
                'confidence': example.get('confidence', 0.9),
                'source_type': 'generated',
                'source_name': 'ai_generated',
                'original_url': '',
                'title': example.get('user_input', '')[:100],
                'content': example.get('user_input', ''),
                'tags': example.get('intent', ''),
                'score': 0,
                'quality_score': example.get('confidence', 0.9),
                'complexity_score': example.get('complexity_score', 3),
                'generation_method': example.get('generation_method', 'advanced'),
                'linguistic_pattern': example.get('linguistic_pattern', 'template'),
                'context': example.get('context', ''),
                'batch_id': example.get('batch_id'),
                'session_id': example.get('session_id'),
                'created_at': example.get('timestamp', datetime.now().isoformat()),
                'processed_at': datetime.now().isoformat()
            }
            unified_examples.append(unified_example)
        
        return unified_examples
    
    def fetch_internet_data(self, target_count: int = 300) -> List[Dict]:
        """Fetch data from internet sources"""
        print("🌐 INTEGRATING INTERNET DATA SOURCES...")
        
        # Get basic internet data
        print("🔍 Fetching from basic internet sources...")
        basic_count = self.internet_feeder.run_internet_feeding_cycle(target_count // 3)
        
        # Get advanced internet data  
        print("🚀 Fetching from advanced internet sources...")
        advanced_count = self.advanced_feeder.run_advanced_feeding_cycle(target_count * 2 // 3)
        
        # Retrieve stored internet data
        internet_examples = []
        
        # From basic feeder
        conn = sqlite3.connect('/tmp/internet_training.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM internet_training_data ORDER BY created_at DESC LIMIT ?', (target_count // 2,))
        basic_rows = cursor.fetchall()
        basic_columns = [desc[0] for desc in cursor.description]
        
        for row in basic_rows:
            example = dict(zip(basic_columns, row))
            internet_examples.append(example)
        
        conn.close()
        
        # From advanced feeder
        conn = sqlite3.connect('/tmp/advanced_internet_training.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM advanced_training_data ORDER BY fetched_at DESC LIMIT ?', (target_count // 2,))
        advanced_rows = cursor.fetchall()
        advanced_columns = [desc[0] for desc in cursor.description]
        
        for row in advanced_rows:
            example = dict(zip(advanced_columns, row))
            internet_examples.append(example)
        
        conn.close()
        
        return internet_examples
    
    def fetch_generated_data(self, target_count: int = 1000) -> List[Dict]:
        """Fetch AI-generated training data"""
        print("🧠 INTEGRATING GENERATED TRAINING DATA...")
        
        # Generate new data
        session_id = self.infinite_engine.feed_infinite_stream(
            examples_per_batch=target_count, 
            batches_per_session=1
        )
        
        # Retrieve generated data
        conn = sqlite3.connect(self.infinite_engine.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM infinite_training ORDER BY timestamp DESC LIMIT ?', (target_count,))
        generated_rows = cursor.fetchall()
        generated_columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        generated_examples = []
        for row in generated_rows:
            example = dict(zip(generated_columns, row))
            generated_examples.append(example)
        
        return generated_examples
    
    def integrate_all_data(self, internet_count: int = 300, generated_count: int = 1000):
        """Master integration of all data sources"""
        print("🚀 FIXED MASTER INTERNET INTEGRATION STARTING...")
        print(f"🎯 Target: {internet_count} internet + {generated_count} generated = {internet_count + generated_count} total examples")
        
        # Fetch internet data
        internet_examples = self.fetch_internet_data(internet_count)
        print(f"✅ Internet data: {len(internet_examples)} examples")
        
        # Fetch generated data
        generated_examples = self.fetch_generated_data(generated_count)
        print(f"✅ Generated data: {len(generated_examples)} examples")
        
        # Convert to unified format
        print("🔄 Converting to unified format...")
        unified_internet = self.convert_internet_data(internet_examples)
        unified_generated = self.convert_generated_data(generated_examples)
        
        # Store in master database
        print("💾 Storing in master database...")
        conn = sqlite3.connect(self.master_db_path)
        cursor = conn.cursor()
        
        # Insert internet data
        for example in unified_internet:
            cursor.execute('''
                INSERT INTO unified_training_data 
                (user_input, intent, confidence, source_type, source_name, original_url, 
                 title, content, tags, score, quality_score, complexity_score, 
                 generation_method, linguistic_pattern, context, batch_id, session_id, 
                 created_at, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                example['user_input'], example['intent'], example['confidence'],
                example['source_type'], example['source_name'], example['original_url'],
                example['title'], example['content'], example['tags'], example['score'],
                example['quality_score'], example['complexity_score'],
                example['generation_method'], example['linguistic_pattern'], 
                example['context'], example['batch_id'], example['session_id'],
                example['created_at'], example['processed_at']
            ))
        
        # Insert generated data
        for example in unified_generated:
            cursor.execute('''
                INSERT INTO unified_training_data 
                (user_input, intent, confidence, source_type, source_name, original_url, 
                 title, content, tags, score, quality_score, complexity_score, 
                 generation_method, linguistic_pattern, context, batch_id, session_id, 
                 created_at, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                example['user_input'], example['intent'], example['confidence'],
                example['source_type'], example['source_name'], example['original_url'],
                example['title'], example['content'], example['tags'], example['score'],
                example['quality_score'], example['complexity_score'],
                example['generation_method'], example['linguistic_pattern'], 
                example['context'], example['batch_id'], example['session_id'],
                example['created_at'], example['processed_at']
            ))
        
        conn.commit()
        conn.close()
        
        total_integrated = len(unified_internet) + len(unified_generated)
        print(f"✅ MASTER INTEGRATION COMPLETE!")
        print(f"📊 Total Examples Integrated: {total_integrated}")
        
        return total_integrated
    
    def export_master_dataset(self, output_path: str = "/tmp/fixed_master_dataset.json"):
        """Export the unified dataset"""
        print("📁 EXPORTING MASTER DATASET...")
        
        conn = sqlite3.connect(self.master_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM unified_training_data ORDER BY created_at DESC')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        dataset = []
        for row in rows:
            example = dict(zip(columns, row))
            dataset.append(example)
        
        with open(output_path, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)
        
        print(f"📁 Master dataset exported: {len(dataset)} examples to {output_path}")
        return len(dataset)
    
    def get_statistics(self):
        """Get comprehensive statistics"""
        conn = sqlite3.connect(self.master_db_path)
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM unified_training_data')
        total_count = cursor.fetchone()[0]
        
        # Source distribution
        cursor.execute('SELECT source_type, COUNT(*) FROM unified_training_data GROUP BY source_type')
        source_dist = dict(cursor.fetchall())
        
        # Intent distribution
        cursor.execute('SELECT intent, COUNT(*) FROM unified_training_data GROUP BY intent')
        intent_dist = dict(cursor.fetchall())
        
        # Quality statistics
        cursor.execute('SELECT AVG(confidence), AVG(quality_score), AVG(complexity_score) FROM unified_training_data')
        avg_stats = cursor.fetchone()
        
        conn.close()
        
        print("\n📊 MASTER DATASET STATISTICS")
        print("=" * 50)
        print(f"📈 Total Examples: {total_count}")
        print(f"🎯 Average Confidence: {avg_stats[0]:.1%}")
        print(f"⭐ Average Quality: {avg_stats[1]:.2f}/1.0")
        print(f"🧠 Average Complexity: {avg_stats[2]:.1f}/5.0")
        
        print(f"\n🌐 Source Distribution:")
        for source, count in source_dist.items():
            print(f"  • {source.title()}: {count} ({count/total_count:.1%})")
        
        print(f"\n🎯 Intent Distribution:")
        for intent, count in intent_dist.items():
            print(f"  • {intent.replace('_', ' ').title()}: {count} ({count/total_count:.1%})")
        
        return {
            'total_count': total_count,
            'source_distribution': source_dist,
            'intent_distribution': intent_dist,
            'average_confidence': avg_stats[0],
            'average_quality': avg_stats[1],
            'average_complexity': avg_stats[2]
        }
    
    def get_training_stats(self):
        """Get training statistics in simplified format"""
        conn = sqlite3.connect(self.master_db_path)
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM unified_training_data')
        total_count = cursor.fetchone()[0]
        
        # Internet vs AI count
        cursor.execute('SELECT COUNT(*) FROM unified_training_data WHERE source_type = "internet"')
        internet_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM unified_training_data WHERE source_type = "generated"')
        ai_count = cursor.fetchone()[0]
        
        # Quality statistics
        cursor.execute('SELECT AVG(confidence), AVG(quality_score) FROM unified_training_data')
        avg_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_examples': total_count,
            'internet_examples': internet_count,
            'ai_examples': ai_count,
            'avg_confidence': (avg_stats[0] or 0) * 100,  # Convert to percentage
            'avg_quality': avg_stats[1] or 0
        }

def main():
    """Run the fixed master integration"""
    print("🚀 FIXED MASTER INTERNET INTEGRATION SYSTEM - LAUNCHING!")
    
    integration = FixedMasterIntegration()
    
    # Integrate all data
    total_examples = integration.integrate_all_data(internet_count=200, generated_count=500)
    
    # Export dataset
    exported_count = integration.export_master_dataset()
    
    # Show statistics
    stats = integration.get_statistics()
    
    print("\n🎉 YOUR AI NOW HAS THE ULTIMATE TRAINING DATASET!")
    print("🌐 Real internet data from multiple sources")
    print("🧠 AI-generated examples for comprehensive coverage")
    print("⭐ High-quality, diverse, and continuously updatable")
    print("🚀 Ready for production AI deployment!")

if __name__ == "__main__":
    main()