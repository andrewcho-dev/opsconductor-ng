#!/usr/bin/env python3
"""
Continuous Internet Learning System
Automatically feeds AI with fresh internet data on a schedule
"""

import schedule
import time
import json
import sqlite3
from datetime import datetime, timedelta
from internet_data_feeder import InternetDataFeeder
from advanced_internet_feeder import AdvancedInternetFeeder
import threading
import logging

class ContinuousInternetLearner:
    def __init__(self, db_path="/tmp/continuous_learning.db"):
        self.db_path = db_path
        self.setup_database()
        self.setup_logging()
        
        # Initialize feeders
        self.basic_feeder = InternetDataFeeder()
        self.advanced_feeder = AdvancedInternetFeeder()
        
        # Learning configuration
        self.config = {
            'basic_feeding_interval': 30,  # minutes
            'advanced_feeding_interval': 120,  # minutes
            'daily_target': 1000,  # examples per day
            'quality_threshold': 0.6,
            'max_examples_per_session': 200,
            'enabled_sources': {
                'stackoverflow': True,
                'github': True,
                'reddit': True,
                'hackernews': True,
                'dev_to': True,
                'rss_feeds': True
            }
        }
        
        self.running = False
        self.stats = {
            'total_sessions': 0,
            'total_examples': 0,
            'last_feeding': None,
            'daily_count': 0,
            'daily_reset': datetime.now().date()
        }

    def setup_database(self):
        """Setup continuous learning database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS continuous_learning_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                examples_fetched INTEGER,
                sources_used TEXT,
                average_quality REAL,
                session_start TIMESTAMP,
                session_end TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_stats (
                date DATE PRIMARY KEY,
                total_examples INTEGER DEFAULT 0,
                basic_sessions INTEGER DEFAULT 0,
                advanced_sessions INTEGER DEFAULT 0,
                average_quality REAL DEFAULT 0.0,
                top_sources TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def setup_logging(self):
        """Setup logging for continuous learning"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/tmp/continuous_learning.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def basic_feeding_job(self):
        """Run basic internet feeding job"""
        if not self.running:
            return
        
        self.logger.info("🔄 Starting basic feeding job...")
        session_start = datetime.now()
        
        try:
            examples_count = self.basic_feeder.run_internet_feeding_cycle(
                min(self.config['max_examples_per_session'], 100)
            )
            
            self.log_session('basic', examples_count, session_start, True)
            self.update_stats(examples_count)
            
            self.logger.info(f"✅ Basic feeding completed: {examples_count} examples")
            
        except Exception as e:
            self.log_session('basic', 0, session_start, False, str(e))
            self.logger.error(f"❌ Basic feeding failed: {e}")

    def advanced_feeding_job(self):
        """Run advanced internet feeding job"""
        if not self.running:
            return
        
        self.logger.info("🚀 Starting advanced feeding job...")
        session_start = datetime.now()
        
        try:
            examples_count = self.advanced_feeder.run_advanced_feeding_cycle(
                min(self.config['max_examples_per_session'], 200)
            )
            
            self.log_session('advanced', examples_count, session_start, True)
            self.update_stats(examples_count)
            
            self.logger.info(f"✅ Advanced feeding completed: {examples_count} examples")
            
        except Exception as e:
            self.log_session('advanced', 0, session_start, False, str(e))
            self.logger.error(f"❌ Advanced feeding failed: {e}")

    def log_session(self, session_type, examples_count, start_time, success, error_msg=None):
        """Log feeding session to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO continuous_learning_log 
            (session_type, examples_fetched, session_start, session_end, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_type, examples_count, start_time, datetime.now(), success, error_msg))
        
        conn.commit()
        conn.close()

    def update_stats(self, examples_count):
        """Update learning statistics"""
        today = datetime.now().date()
        
        # Reset daily count if new day
        if self.stats['daily_reset'] != today:
            self.stats['daily_count'] = 0
            self.stats['daily_reset'] = today
        
        self.stats['total_sessions'] += 1
        self.stats['total_examples'] += examples_count
        self.stats['daily_count'] += examples_count
        self.stats['last_feeding'] = datetime.now()

    def daily_summary_job(self):
        """Generate daily summary and statistics"""
        self.logger.info("📊 Generating daily summary...")
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get yesterday's stats
        cursor.execute('''
            SELECT COUNT(*) as sessions, SUM(examples_fetched) as total_examples,
                   AVG(CASE WHEN success THEN examples_fetched ELSE 0 END) as avg_quality
            FROM continuous_learning_log 
            WHERE DATE(session_start) = ?
        ''', (yesterday,))
        
        result = cursor.fetchone()
        sessions, total_examples, avg_quality = result if result else (0, 0, 0)
        
        # Store daily stats
        cursor.execute('''
            INSERT OR REPLACE INTO learning_stats 
            (date, total_examples, basic_sessions, advanced_sessions, average_quality)
            VALUES (?, ?, ?, ?, ?)
        ''', (yesterday, total_examples or 0, sessions or 0, 0, avg_quality or 0))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"📈 Daily Summary for {yesterday}: {total_examples} examples, {sessions} sessions")

    def health_check_job(self):
        """Perform system health check"""
        self.logger.info("🏥 Performing health check...")
        
        # Check if we're meeting daily targets
        if self.stats['daily_count'] < self.config['daily_target'] * 0.5:
            self.logger.warning(f"⚠️ Daily target not being met: {self.stats['daily_count']}/{self.config['daily_target']}")
        
        # Check last feeding time
        if self.stats['last_feeding']:
            time_since_last = datetime.now() - self.stats['last_feeding']
            if time_since_last > timedelta(hours=3):
                self.logger.warning(f"⚠️ No feeding for {time_since_last}")
        
        self.logger.info("✅ Health check completed")

    def start_continuous_learning(self):
        """Start the continuous learning system"""
        self.logger.info("🚀 STARTING CONTINUOUS INTERNET LEARNING SYSTEM")
        self.running = True
        
        # Schedule jobs
        schedule.every(self.config['basic_feeding_interval']).minutes.do(self.basic_feeding_job)
        schedule.every(self.config['advanced_feeding_interval']).minutes.do(self.advanced_feeding_job)
        schedule.every().day.at("00:01").do(self.daily_summary_job)
        schedule.every().hour.do(self.health_check_job)
        
        # Initial feeding
        self.logger.info("🎯 Running initial feeding...")
        self.basic_feeding_job()
        
        self.logger.info("⏰ Scheduler started - continuous learning active!")
        self.logger.info(f"📅 Basic feeding every {self.config['basic_feeding_interval']} minutes")
        self.logger.info(f"🚀 Advanced feeding every {self.config['advanced_feeding_interval']} minutes")
        
        # Run scheduler
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def stop_continuous_learning(self):
        """Stop the continuous learning system"""
        self.logger.info("🛑 Stopping continuous learning system...")
        self.running = False
        schedule.clear()

    def get_learning_statistics(self):
        """Get comprehensive learning statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent sessions
        cursor.execute('''
            SELECT session_type, COUNT(*) as count, SUM(examples_fetched) as total,
                   AVG(examples_fetched) as avg_per_session
            FROM continuous_learning_log 
            WHERE session_start >= datetime('now', '-7 days')
            GROUP BY session_type
        ''')
        
        recent_sessions = cursor.fetchall()
        
        # Get daily stats for last week
        cursor.execute('''
            SELECT date, total_examples, basic_sessions + advanced_sessions as sessions
            FROM learning_stats 
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC
        ''')
        
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'current_stats': self.stats,
            'recent_sessions': recent_sessions,
            'daily_stats': daily_stats,
            'config': self.config
        }

    def export_learning_data(self, filename="/tmp/continuous_learning_export.json"):
        """Export all learning data"""
        stats = self.get_learning_statistics()
        
        # Add basic feeder data
        try:
            basic_data = self.basic_feeder.export_to_json("/tmp/basic_export.json")
            stats['basic_feeder_examples'] = basic_data
        except:
            stats['basic_feeder_examples'] = 0
        
        # Add advanced feeder data
        try:
            advanced_data = self.advanced_feeder.export_advanced_data("/tmp/advanced_export.json")
            stats['advanced_feeder_examples'] = advanced_data
        except:
            stats['advanced_feeder_examples'] = 0
        
        with open(filename, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        self.logger.info(f"📁 Learning data exported to {filename}")
        return stats

def run_demo_session():
    """Run a demonstration of continuous learning"""
    print("🎯 CONTINUOUS INTERNET LEARNING - DEMO SESSION")
    
    learner = ContinuousInternetLearner()
    
    # Run a few feeding cycles
    print("\n🔄 Running basic feeding demo...")
    learner.basic_feeding_job()
    
    print("\n🚀 Running advanced feeding demo...")
    learner.advanced_feeding_job()
    
    # Show statistics
    print("\n📊 LEARNING STATISTICS:")
    stats = learner.get_learning_statistics()
    
    print(f"📈 Total Sessions: {stats['current_stats']['total_sessions']}")
    print(f"📚 Total Examples: {stats['current_stats']['total_examples']}")
    print(f"📅 Daily Count: {stats['current_stats']['daily_count']}")
    
    # Export data
    learner.export_learning_data()
    
    print("\n✅ Demo session completed!")
    print("🔄 To run continuously, use: learner.start_continuous_learning()")

def main():
    """Main function - can run demo or continuous mode"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Run continuous mode
        learner = ContinuousInternetLearner()
        try:
            learner.start_continuous_learning()
        except KeyboardInterrupt:
            learner.stop_continuous_learning()
            print("\n🛑 Continuous learning stopped by user")
    else:
        # Run demo mode
        run_demo_session()

if __name__ == "__main__":
    main()