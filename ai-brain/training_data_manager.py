#!/usr/bin/env python3
"""
Training Data Manager

Manages import/export of training data for the adaptive training system.
Allows sharing, backup, and restoration of training datasets.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

# Add the ai-brain directory to the path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

from adaptive_training_system import AdaptiveTrainingSystem, TrainingExample

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingDataManager:
    """Manages training data import/export operations"""
    
    def __init__(self, training_system: AdaptiveTrainingSystem):
        self.training_system = training_system
    
    async def export_training_data(self, output_file: str, format: str = "json") -> Dict[str, Any]:
        """Export all training data to a file"""
        
        try:
            logger.info(f"Exporting training data to {output_file}")
            
            # Get all training data from database
            conn = sqlite3.connect(self.training_system.db_path)
            cursor = conn.cursor()
            
            # Export training examples
            cursor.execute('SELECT * FROM training_examples ORDER BY timestamp DESC')
            examples_data = []
            for row in cursor.fetchall():
                examples_data.append({
                    "id": row[0],
                    "text": row[1],
                    "intent": row[2],
                    "confidence": row[3],
                    "user_feedback": row[4],
                    "context": json.loads(row[5]) if row[5] else None,
                    "timestamp": row[6],
                    "source": row[7]
                })
            
            # Export intent patterns
            cursor.execute('SELECT * FROM intent_patterns ORDER BY created_at DESC')
            patterns_data = []
            for row in cursor.fetchall():
                patterns_data.append({
                    "id": row[0],
                    "pattern": row[1],
                    "intent": row[2],
                    "confidence_base": row[3],
                    "success_count": row[4],
                    "failure_count": row[5],
                    "last_used": row[6],
                    "created_at": row[7],
                    "pattern_type": row[8],
                    "semantic_embedding": json.loads(row[9]) if row[9] else None,
                    "context_requirements": json.loads(row[10]) if row[10] else None
                })
            
            # Export training sessions
            cursor.execute('SELECT * FROM training_sessions ORDER BY session_start DESC')
            sessions_data = []
            for row in cursor.fetchall():
                sessions_data.append({
                    "id": row[0],
                    "session_start": row[1],
                    "session_end": row[2],
                    "examples_processed": row[3],
                    "patterns_created": row[4],
                    "patterns_updated": row[5],
                    "accuracy_improvement": row[6],
                    "notes": row[7]
                })
            
            conn.close()
            
            # Create export data structure
            export_data = {
                "export_metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_examples": len(examples_data),
                    "total_patterns": len(patterns_data),
                    "total_sessions": len(sessions_data),
                    "format_version": "1.0"
                },
                "training_examples": examples_data,
                "intent_patterns": patterns_data,
                "training_sessions": sessions_data
            }
            
            # Write to file
            if format.lower() == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            result = {
                "success": True,
                "output_file": output_file,
                "examples_exported": len(examples_data),
                "patterns_exported": len(patterns_data),
                "sessions_exported": len(sessions_data),
                "file_size": os.path.getsize(output_file)
            }
            
            logger.info(f"Export completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def import_training_data(self, input_file: str, merge_mode: str = "append") -> Dict[str, Any]:
        """Import training data from a file"""
        
        try:
            logger.info(f"Importing training data from {input_file}")
            
            # Read import file
            with open(input_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate format
            if "export_metadata" not in import_data:
                raise ValueError("Invalid import file format")
            
            metadata = import_data["export_metadata"]
            logger.info(f"Importing data from {metadata.get('export_timestamp', 'unknown date')}")
            
            imported_examples = 0
            imported_patterns = 0
            skipped_examples = 0
            skipped_patterns = 0
            
            # Import training examples
            if "training_examples" in import_data:
                for example_data in import_data["training_examples"]:
                    try:
                        # Check if example already exists (based on text and intent)
                        if merge_mode == "skip_duplicates":
                            existing = await self._check_example_exists(
                                example_data["text"], 
                                example_data["intent"]
                            )
                            if existing:
                                skipped_examples += 1
                                continue
                        
                        # Add training example
                        success = await self.training_system.add_training_example(
                            text=example_data["text"],
                            intent=example_data["intent"],
                            confidence=example_data["confidence"],
                            user_feedback=example_data.get("user_feedback"),
                            context=example_data.get("context"),
                            source=f"imported_{example_data.get('source', 'unknown')}"
                        )
                        
                        if success:
                            imported_examples += 1
                        else:
                            skipped_examples += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to import example: {e}")
                        skipped_examples += 1
            
            # Import patterns (if merge_mode allows)
            if "intent_patterns" in import_data and merge_mode in ["append", "replace"]:
                for pattern_data in import_data["intent_patterns"]:
                    try:
                        # For now, we'll let the system regenerate patterns through training
                        # Direct pattern import could be added later
                        pass
                    except Exception as e:
                        logger.warning(f"Failed to import pattern: {e}")
                        skipped_patterns += 1
            
            # Trigger retraining with new data
            if imported_examples > 0:
                logger.info("Retraining system with imported data...")
                training_result = await self.training_system.retrain_system()
                logger.info(f"Retraining completed: {training_result}")
            
            result = {
                "success": True,
                "input_file": input_file,
                "examples_imported": imported_examples,
                "examples_skipped": skipped_examples,
                "patterns_imported": imported_patterns,
                "patterns_skipped": skipped_patterns,
                "total_available": len(import_data.get("training_examples", [])),
                "merge_mode": merge_mode
            }
            
            logger.info(f"Import completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_example_exists(self, text: str, intent: str) -> bool:
        """Check if a training example already exists"""
        try:
            conn = sqlite3.connect(self.training_system.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM training_examples WHERE text = ? AND intent = ?',
                (text, intent)
            )
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False
    
    async def create_training_backup(self, backup_dir: str = "/tmp/training_backups") -> str:
        """Create a timestamped backup of training data"""
        
        # Create backup directory if it doesn't exist
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/training_backup_{timestamp}.json"
        
        # Export data
        result = await self.export_training_data(backup_file)
        
        if result["success"]:
            logger.info(f"Backup created: {backup_file}")
            return backup_file
        else:
            raise Exception(f"Backup failed: {result.get('error', 'Unknown error')}")
    
    async def list_available_backups(self, backup_dir: str = "/tmp/training_backups") -> List[Dict[str, Any]]:
        """List available training data backups"""
        
        backups = []
        backup_path = Path(backup_dir)
        
        if backup_path.exists():
            for backup_file in backup_path.glob("training_backup_*.json"):
                try:
                    # Get file info
                    stat = backup_file.stat()
                    
                    # Try to read metadata
                    with open(backup_file, 'r') as f:
                        data = json.load(f)
                        metadata = data.get("export_metadata", {})
                    
                    backups.append({
                        "filename": backup_file.name,
                        "full_path": str(backup_file),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "examples": metadata.get("total_examples", 0),
                        "patterns": metadata.get("total_patterns", 0),
                        "export_timestamp": metadata.get("export_timestamp", "unknown")
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not read backup {backup_file}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    async def restore_from_backup(self, backup_file: str, merge_mode: str = "replace") -> Dict[str, Any]:
        """Restore training data from a backup file"""
        
        if merge_mode == "replace":
            # Clear existing data first
            logger.info("Clearing existing training data...")
            await self._clear_training_data()
        
        # Import from backup
        return await self.import_training_data(backup_file, merge_mode)
    
    async def _clear_training_data(self):
        """Clear all existing training data (use with caution!)"""
        try:
            conn = sqlite3.connect(self.training_system.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM training_examples')
            cursor.execute('DELETE FROM intent_patterns')
            cursor.execute('DELETE FROM training_sessions')
            
            conn.commit()
            conn.close()
            
            # Reset in-memory data
            self.training_system.training_examples.clear()
            self.training_system.intent_patterns.clear()
            self.training_system.semantic_matcher = type(self.training_system.semantic_matcher)()
            
            logger.info("Training data cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear training data: {e}")
            raise
    
    async def generate_training_report(self) -> Dict[str, Any]:
        """Generate a comprehensive training data report"""
        
        try:
            stats = await self.training_system.get_training_statistics()
            
            # Additional analysis
            conn = sqlite3.connect(self.training_system.db_path)
            cursor = conn.cursor()
            
            # Get source distribution
            cursor.execute('''
                SELECT source, COUNT(*) as count
                FROM training_examples
                GROUP BY source
                ORDER BY count DESC
            ''')
            source_distribution = dict(cursor.fetchall())
            
            # Get confidence distribution
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN confidence >= 0.9 THEN 'very_high'
                        WHEN confidence >= 0.7 THEN 'high'
                        WHEN confidence >= 0.5 THEN 'medium'
                        WHEN confidence >= 0.3 THEN 'low'
                        ELSE 'very_low'
                    END as confidence_level,
                    COUNT(*) as count
                FROM training_examples
                GROUP BY confidence_level
                ORDER BY count DESC
            ''')
            confidence_distribution = dict(cursor.fetchall())
            
            # Get recent activity
            cursor.execute('''
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM training_examples
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 10
            ''')
            recent_activity = dict(cursor.fetchall())
            
            conn.close()
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "basic_stats": stats,
                "source_distribution": source_distribution,
                "confidence_distribution": confidence_distribution,
                "recent_activity": recent_activity,
                "data_quality": {
                    "high_confidence_examples": sum(
                        count for level, count in confidence_distribution.items()
                        if level in ['very_high', 'high']
                    ),
                    "total_examples": stats.get('total_examples', 0),
                    "quality_ratio": 0.0
                }
            }
            
            # Calculate quality ratio
            total = report["data_quality"]["total_examples"]
            high_conf = report["data_quality"]["high_confidence_examples"]
            if total > 0:
                report["data_quality"]["quality_ratio"] = high_conf / total
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {"error": str(e)}

async def main():
    """Demonstrate training data management capabilities"""
    
    print("📊 === Training Data Manager Demo ===")
    
    # Initialize systems
    training_system = AdaptiveTrainingSystem("/tmp/internet_training.db")
    data_manager = TrainingDataManager(training_system)
    
    # Generate training report
    print("\n📈 Generating Training Report...")
    report = await data_manager.generate_training_report()
    
    if "error" not in report:
        print(f"📊 Training Data Report (Generated: {report['generated_at']})")
        print(f"  Total Examples: {report['basic_stats'].get('total_examples', 0)}")
        print(f"  Total Patterns: {report['basic_stats'].get('total_patterns', 0)}")
        print(f"  Training Sessions: {report['basic_stats'].get('training_sessions', 0)}")
        
        print(f"\n  Source Distribution:")
        for source, count in report['source_distribution'].items():
            print(f"    {source}: {count} examples")
        
        print(f"\n  Confidence Distribution:")
        for level, count in report['confidence_distribution'].items():
            print(f"    {level}: {count} examples")
        
        print(f"\n  Data Quality:")
        print(f"    High confidence examples: {report['data_quality']['high_confidence_examples']}")
        print(f"    Quality ratio: {report['data_quality']['quality_ratio']:.2%}")
        
        if report['recent_activity']:
            print(f"\n  Recent Activity (last 10 days):")
            for date, count in list(report['recent_activity'].items())[:5]:
                print(f"    {date}: {count} examples")
    
    # Create backup
    print(f"\n💾 Creating Training Data Backup...")
    backup_file = await data_manager.create_training_backup()
    print(f"✅ Backup created: {backup_file}")
    
    # Export training data
    print(f"\n📤 Exporting Training Data...")
    export_result = await data_manager.export_training_data("/tmp/training_export.json")
    
    if export_result["success"]:
        print(f"✅ Export successful:")
        print(f"  File: {export_result['output_file']}")
        print(f"  Examples: {export_result['examples_exported']}")
        print(f"  Patterns: {export_result['patterns_exported']}")
        print(f"  File size: {export_result['file_size']} bytes")
    else:
        print(f"❌ Export failed: {export_result['error']}")
    
    # List available backups
    print(f"\n📋 Available Backups:")
    backups = await data_manager.list_available_backups()
    
    for backup in backups[:3]:  # Show top 3
        print(f"  📁 {backup['filename']}")
        print(f"     Created: {backup['created']}")
        print(f"     Examples: {backup['examples']}, Patterns: {backup['patterns']}")
        print(f"     Size: {backup['size']} bytes")
    
    print(f"\n🎉 Training Data Management Demo Complete!")
    print(f"\n📚 **Available Operations:**")
    print(f"   ✅ Export training data to JSON")
    print(f"   ✅ Import training data from JSON")
    print(f"   ✅ Create timestamped backups")
    print(f"   ✅ List and restore from backups")
    print(f"   ✅ Generate comprehensive reports")
    print(f"   ✅ Merge or replace data on import")
    
    print(f"\n🔄 **Use Cases:**")
    print(f"   • Share training data between environments")
    print(f"   • Backup before major changes")
    print(f"   • Restore from known good state")
    print(f"   • Analyze training data quality")
    print(f"   • Migrate training data to new systems")

if __name__ == "__main__":
    asyncio.run(main())