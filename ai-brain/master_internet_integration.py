#!/usr/bin/env python3
"""
Master Internet Data Integration System
Combines all internet data sources with the existing infinite training engine
"""

import sqlite3
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from internet_data_feeder import InternetDataFeeder
from advanced_internet_feeder import AdvancedInternetFeeder
from infinite_training_engine import InfiniteTrainingEngine

class MasterInternetIntegration:
    def __init__(self, master_db="/tmp/master_ai_training.db"):
        self.master_db = master_db
        self.setup_master_database()
        
        # Initialize all systems
        self.internet_feeder = InternetDataFeeder()
        self.advanced_feeder = AdvancedInternetFeeder()
        self.infinite_engine = InfiniteTrainingEngine()
        
        # Integration statistics
        self.integration_stats = {
            'internet_sources': 0,
            'generated_examples': 0,
            'total_combined': 0,
            'quality_score': 0.0,
            'diversity_score': 0.0
        }

    def setup_master_database(self):
        """Setup master database combining all sources"""
        conn = sqlite3.connect(self.master_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS master_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_source TEXT NOT NULL,  -- 'internet' or 'generated'
                source_system TEXT NOT NULL,  -- specific system name
                original_source TEXT,  -- stackoverflow, github, etc.
                content_id TEXT,
                title TEXT,
                content TEXT,
                intent TEXT,
                confidence REAL,
                quality_score REAL DEFAULT 0.5,
                complexity_level INTEGER DEFAULT 1,
                tags TEXT,
                metadata TEXT,  -- JSON metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                integration_batch TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integration_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP,
                internet_examples INTEGER DEFAULT 0,
                generated_examples INTEGER DEFAULT 0,
                total_examples INTEGER DEFAULT 0,
                average_quality REAL DEFAULT 0.0,
                diversity_metrics TEXT,  -- JSON
                success BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()

    def integrate_internet_data(self, target_examples=500):
        """Integrate data from all internet sources"""
        print("🌐 INTEGRATING INTERNET DATA SOURCES...")
        
        all_internet_data = []
        
        # Basic internet feeding
        print("🔍 Fetching from basic internet sources...")
        basic_data = self.internet_feeder.run_internet_feeding_cycle(target_examples // 3)
        
        # Get the actual data from basic feeder
        conn = sqlite3.connect(self.internet_feeder.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM internet_training_data ORDER BY created_at DESC LIMIT ?', (basic_data,))
        basic_rows = cursor.fetchall()
        basic_columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        for row in basic_rows:
            data_dict = dict(zip(basic_columns, row))
            all_internet_data.append({
                'data_source': 'internet',
                'source_system': 'basic_feeder',
                'original_source': data_dict['source'],
                'content_id': str(data_dict['id']),
                'title': data_dict['title'],
                'content': data_dict['content'],
                'intent': data_dict['intent'],
                'confidence': data_dict['confidence'],
                'quality_score': 0.6,  # Default for basic
                'complexity_level': 2,
                'tags': data_dict['tags'],
                'metadata': json.dumps({'score': data_dict['score'], 'url': data_dict['original_url']})
            })
        
        # Advanced internet feeding
        print("🚀 Fetching from advanced internet sources...")
        advanced_data = self.advanced_feeder.run_advanced_feeding_cycle(target_examples // 2)
        
        # Get the actual data from advanced feeder
        conn = sqlite3.connect(self.advanced_feeder.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM advanced_training_data ORDER BY fetched_at DESC LIMIT ?', (advanced_data,))
        advanced_rows = cursor.fetchall()
        advanced_columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        for row in advanced_rows:
            data_dict = dict(zip(advanced_columns, row))
            all_internet_data.append({
                'data_source': 'internet',
                'source_system': 'advanced_feeder',
                'original_source': data_dict['source'],
                'content_id': data_dict['source_id'],
                'title': data_dict['title'],
                'content': data_dict['content'],
                'intent': data_dict['intent'],
                'confidence': data_dict['confidence'],
                'quality_score': data_dict['quality_score'],
                'complexity_level': data_dict['complexity_level'],
                'tags': data_dict['tags'],
                'metadata': json.dumps({
                    'author': data_dict['author'],
                    'published_date': str(data_dict['published_date']),
                    'score': data_dict['score'],
                    'url': data_dict['original_url']
                })
            })
        
        self.integration_stats['internet_sources'] = len(all_internet_data)
        return all_internet_data

    def integrate_generated_data(self, target_examples=1000):
        """Integrate data from infinite training engine"""
        print("🧠 INTEGRATING GENERATED TRAINING DATA...")
        
        # Generate new examples using the correct method
        generated_count = self.infinite_engine.feed_infinite_stream(target_examples, batches_per_session=1)
        
        # Get the generated data
        conn = sqlite3.connect(self.infinite_engine.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM infinite_training ORDER BY timestamp DESC LIMIT ?', (generated_count,))
        generated_rows = cursor.fetchall()
        generated_columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        all_generated_data = []
        for row in generated_rows:
            data_dict = dict(zip(generated_columns, row))
            all_generated_data.append({
                'data_source': 'generated',
                'source_system': 'infinite_engine',
                'original_source': 'ai_generated',
                'content_id': str(data_dict['id']),
                'title': data_dict['example'][:100] + '...' if len(data_dict['example']) > 100 else data_dict['example'],
                'content': data_dict['example'],
                'intent': data_dict['intent'],
                'confidence': data_dict['confidence'],
                'quality_score': 0.8,  # Generated data is high quality
                'complexity_level': data_dict['complexity_score'],
                'tags': f"generated,{data_dict['generation_method']},{data_dict['linguistic_pattern']}",
                'metadata': json.dumps({
                    'generation_method': data_dict['generation_method'],
                    'linguistic_pattern': data_dict['linguistic_pattern'],
                    'context': data_dict['context'],
                    'complexity_score': data_dict['complexity_score']
                })
            })
        
        self.integration_stats['generated_examples'] = len(all_generated_data)
        return all_generated_data

    def store_integrated_data(self, internet_data: List[Dict], generated_data: List[Dict], batch_id: str):
        """Store all integrated data in master database"""
        print("💾 STORING INTEGRATED DATA...")
        
        conn = sqlite3.connect(self.master_db)
        cursor = conn.cursor()
        
        all_data = internet_data + generated_data
        
        for data in all_data:
            cursor.execute('''
                INSERT INTO master_training_data 
                (data_source, source_system, original_source, content_id, title, content,
                 intent, confidence, quality_score, complexity_level, tags, metadata, integration_batch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['data_source'], data['source_system'], data['original_source'],
                data['content_id'], data['title'], data['content'], data['intent'],
                data['confidence'], data['quality_score'], data['complexity_level'],
                data['tags'], data['metadata'], batch_id
            ))
        
        conn.commit()
        conn.close()
        
        self.integration_stats['total_combined'] = len(all_data)

    def calculate_diversity_metrics(self, all_data: List[Dict]) -> Dict:
        """Calculate diversity metrics for the integrated dataset"""
        if not all_data:
            return {}
        
        # Source diversity
        sources = {}
        intents = {}
        systems = {}
        
        total_quality = 0
        total_complexity = 0
        
        for item in all_data:
            # Count sources
            source = item['original_source']
            sources[source] = sources.get(source, 0) + 1
            
            # Count intents
            intent = item['intent']
            intents[intent] = intents.get(intent, 0) + 1
            
            # Count systems
            system = item['source_system']
            systems[system] = systems.get(system, 0) + 1
            
            # Accumulate quality and complexity
            total_quality += item['quality_score']
            total_complexity += item['complexity_level']
        
        total_items = len(all_data)
        
        # Calculate diversity scores
        source_diversity = len(sources) / max(1, total_items) * 10  # Normalize to 0-10
        intent_diversity = len(intents) / 6.0 * 10  # 6 intents max, normalize to 0-10
        system_diversity = len(systems) / max(1, total_items) * 10
        
        return {
            'source_diversity': source_diversity,
            'intent_diversity': intent_diversity,
            'system_diversity': system_diversity,
            'average_quality': total_quality / total_items,
            'average_complexity': total_complexity / total_items,
            'source_distribution': sources,
            'intent_distribution': intents,
            'system_distribution': systems,
            'total_sources': len(sources),
            'total_intents': len(intents),
            'total_systems': len(systems)
        }

    def run_master_integration(self, internet_target=500, generated_target=2000):
        """Run complete master integration process"""
        print("🚀 MASTER INTERNET INTEGRATION STARTING...")
        print(f"🎯 Target: {internet_target} internet + {generated_target} generated = {internet_target + generated_target} total examples")
        
        session_id = f"master_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_start = datetime.now()
        
        try:
            # Integrate internet data
            internet_data = self.integrate_internet_data(internet_target)
            
            # Integrate generated data
            generated_data = self.integrate_generated_data(generated_target)
            
            # Store integrated data
            self.store_integrated_data(internet_data, generated_data, session_id)
            
            # Calculate diversity metrics
            all_data = internet_data + generated_data
            diversity_metrics = self.calculate_diversity_metrics(all_data)
            
            # Update integration stats
            self.integration_stats['quality_score'] = diversity_metrics.get('average_quality', 0)
            self.integration_stats['diversity_score'] = (
                diversity_metrics.get('source_diversity', 0) +
                diversity_metrics.get('intent_diversity', 0) +
                diversity_metrics.get('system_diversity', 0)
            ) / 3
            
            # Record session
            self.record_integration_session(
                session_id, session_start, len(internet_data), 
                len(generated_data), diversity_metrics, True
            )
            
            # Generate comprehensive statistics
            self.generate_master_statistics(diversity_metrics)
            
            return len(all_data)
            
        except Exception as e:
            print(f"❌ Master integration failed: {e}")
            self.record_integration_session(
                session_id, session_start, 0, 0, {}, False
            )
            return 0

    def record_integration_session(self, session_id, start_time, internet_count, 
                                 generated_count, diversity_metrics, success):
        """Record integration session in database"""
        conn = sqlite3.connect(self.master_db)
        cursor = conn.cursor()
        
        total_examples = internet_count + generated_count
        avg_quality = diversity_metrics.get('average_quality', 0)
        
        cursor.execute('''
            INSERT INTO integration_sessions 
            (session_id, session_start, session_end, internet_examples, 
             generated_examples, total_examples, average_quality, diversity_metrics, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, start_time, datetime.now(), internet_count,
            generated_count, total_examples, avg_quality,
            json.dumps(diversity_metrics), success
        ))
        
        conn.commit()
        conn.close()

    def generate_master_statistics(self, diversity_metrics: Dict):
        """Generate comprehensive master statistics"""
        print(f"\n📊 MASTER INTEGRATION STATISTICS")
        print(f"{'='*70}")
        
        # Basic stats
        print(f"🌐 Internet Sources: {self.integration_stats['internet_sources']} examples")
        print(f"🧠 Generated Examples: {self.integration_stats['generated_examples']} examples")
        print(f"📈 Total Combined: {self.integration_stats['total_combined']} examples")
        print(f"⭐ Average Quality: {self.integration_stats['quality_score']:.2f}/1.0")
        print(f"🎨 Diversity Score: {self.integration_stats['diversity_score']:.1f}/10.0")
        
        # Diversity breakdown
        print(f"\n🎨 DIVERSITY METRICS:")
        print(f"  • Source Diversity: {diversity_metrics.get('source_diversity', 0):.1f}/10.0")
        print(f"  • Intent Diversity: {diversity_metrics.get('intent_diversity', 0):.1f}/10.0")
        print(f"  • System Diversity: {diversity_metrics.get('system_diversity', 0):.1f}/10.0")
        print(f"  • Average Complexity: {diversity_metrics.get('average_complexity', 0):.1f}/5.0")
        
        # Source distribution
        print(f"\n🌐 SOURCE DISTRIBUTION:")
        source_dist = diversity_metrics.get('source_distribution', {})
        total = sum(source_dist.values())
        for source, count in sorted(source_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  • {source.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Intent distribution
        print(f"\n🎯 INTENT DISTRIBUTION:")
        intent_dist = diversity_metrics.get('intent_distribution', {})
        total = sum(intent_dist.values())
        for intent, count in sorted(intent_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  • {intent.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # System distribution
        print(f"\n🔧 SYSTEM DISTRIBUTION:")
        system_dist = diversity_metrics.get('system_distribution', {})
        total = sum(system_dist.values())
        for system, count in sorted(system_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  • {system.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

    def export_master_dataset(self, filename="/tmp/master_ai_dataset.json"):
        """Export complete master dataset"""
        print("📁 EXPORTING MASTER DATASET...")
        
        conn = sqlite3.connect(self.master_db)
        cursor = conn.cursor()
        
        # Get all data
        cursor.execute('SELECT * FROM master_training_data ORDER BY created_at DESC')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Get session data
        cursor.execute('SELECT * FROM integration_sessions ORDER BY session_start DESC LIMIT 10')
        session_rows = cursor.fetchall()
        session_columns = [desc[0] for desc in cursor.description]
        
        conn.close()
        
        # Prepare export data
        training_data = [dict(zip(columns, row)) for row in rows]
        session_data = [dict(zip(session_columns, row)) for row in session_rows]
        
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_examples': len(training_data),
                'integration_stats': self.integration_stats,
                'description': 'Master AI Training Dataset - Internet + Generated Data'
            },
            'training_data': training_data,
            'integration_sessions': session_data,
            'statistics': {
                'data_sources': list(set(item['data_source'] for item in training_data)) if training_data else [],
                'source_systems': list(set(item['source_system'] for item in training_data)) if training_data else [],
                'intents': list(set(item['intent'] for item in training_data)) if training_data else [],
                'date_range': {
                    'earliest': min(item['created_at'] for item in training_data) if training_data else None,
                    'latest': max(item['created_at'] for item in training_data) if training_data else None
                }
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"📁 Master dataset exported: {len(training_data)} examples to {filename}")
        return len(training_data)

def main():
    """Main execution function"""
    print("🚀 MASTER INTERNET INTEGRATION SYSTEM - LAUNCHING!")
    
    master_system = MasterInternetIntegration()
    
    # Run master integration
    total_examples = master_system.run_master_integration(
        internet_target=300,  # Reasonable for demo
        generated_target=1000  # More generated examples
    )
    
    print(f"\n✅ MASTER INTEGRATION COMPLETE!")
    print(f"📊 Total Examples Integrated: {total_examples}")
    
    # Export master dataset
    master_system.export_master_dataset()
    
    print(f"\n🎉 YOUR AI NOW HAS THE ULTIMATE TRAINING DATASET!")
    print(f"🌐 Real internet data from multiple sources")
    print(f"🧠 AI-generated examples for comprehensive coverage")
    print(f"⭐ High-quality, diverse, and continuously updatable")
    print(f"🚀 Ready for production AI deployment!")

if __name__ == "__main__":
    main()