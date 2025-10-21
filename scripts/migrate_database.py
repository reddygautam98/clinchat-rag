#!/usr/bin/env python3
"""
Database Migration Script for ClinChat-RAG Fusion AI
Initialize database with unified schema for Google Gemini & Groq APIs
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Database imports
from database.connection import DatabaseManager, Base
from database.models import (
    User, UserSession, Conversation, ProviderResponse,
    ClinicalDocument, DocumentAnalysis, ProviderMetrics,
    SystemUsage, AuditLog, SystemConfiguration
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database():
    """Create database and all tables"""
    logger.info("🚀 Starting ClinChat-RAG Database Migration")
    logger.info("=" * 60)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        logger.info("✅ Database manager initialized")
        
        # Initialize connection
        db_manager.initialize()
        logger.info("✅ Database connection established")
        
        # Create all tables
        logger.info("📊 Creating database tables...")
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("✅ All tables created successfully")
        
        # Verify table creation
        inspector = db_manager.engine.dialect.get_table_names(db_manager.engine.connect())
        expected_tables = [
            'users', 'user_sessions', 'conversations', 'provider_responses',
            'clinical_documents', 'document_analyses', 'provider_metrics',
            'system_usage', 'audit_logs', 'system_configuration'
        ]
        
        created_tables = [table for table in expected_tables if table in inspector]
        logger.info(f"📋 Tables created: {len(created_tables)}/{len(expected_tables)}")
        
        for table in created_tables:
            logger.info(f"   ✓ {table}")
        
        if missing_tables := set(expected_tables) - set(created_tables):
            logger.warning(f"⚠️ Missing tables: {missing_tables}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def seed_initial_data():
    """Seed database with initial configuration and sample data"""
    logger.info("\n🌱 Seeding initial data...")
    
    try:
        db_manager = DatabaseManager()
        
        with db_manager.get_session_context() as session:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@clinchat.local",
                full_name="System Administrator",
                role="admin",
                department="IT",
                is_active=True
            )
            session.add(admin_user)
            logger.info("👤 Admin user created")
            
            # Create system configurations
            configs = [
                {
                    "config_key": "fusion_ai_enabled",
                    "config_value": "true",
                    "config_type": "boolean",
                    "description": "Enable Fusion AI functionality",
                    "category": "ai_providers"
                },
                {
                    "config_key": "google_gemini_enabled",
                    "config_value": "true",
                    "config_type": "boolean",
                    "description": "Enable Google Gemini API",
                    "category": "ai_providers"
                },
                {
                    "config_key": "groq_enabled",
                    "config_value": "true",
                    "config_type": "boolean",
                    "description": "Enable Groq Cloud API",
                    "category": "ai_providers"
                },
                {
                    "config_key": "default_analysis_type",
                    "config_value": "detailed_analysis",
                    "config_type": "string",
                    "description": "Default analysis type for new conversations",
                    "category": "features"
                },
                {
                    "config_key": "enable_audit_logging",
                    "config_value": "true",
                    "config_type": "boolean",
                    "description": "Enable comprehensive audit logging",
                    "category": "security"
                },
                {
                    "config_key": "max_conversation_history",
                    "config_value": "100",
                    "config_type": "integer",
                    "description": "Maximum conversations to keep in user history",
                    "category": "performance"
                }
            ]
            
            for config_data in configs:
                config = SystemConfiguration(**config_data)
                session.add(config)
            
            logger.info(f"⚙️ {len(configs)} system configurations created")
            
            # Create initial system usage record
            system_usage = SystemUsage(
                total_conversations=0,
                total_users=1,
                active_users_daily=0,
                total_documents_processed=0,
                gemini_requests=0,
                groq_requests=0,
                fusion_requests=0,
                emergency_assessments=0,
                diagnostic_analyses=0,
                triage_requests=0,
                avg_response_time=0.0,
                system_uptime_hours=0.0,
                date=datetime.now(timezone.utc)
            )
            session.add(system_usage)
            logger.info("📈 Initial system usage record created")
            
            session.commit()
            logger.info("✅ Initial data seeded successfully")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Data seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_operations():
    """Test basic database operations"""
    logger.info("\n🧪 Testing database operations...")
    
    try:
        db_manager = DatabaseManager()
        
        with db_manager.get_session_context() as session:
            # Test user query
            user_count = session.query(User).count()
            logger.info(f"👥 Users in database: {user_count}")
            
            # Test configuration query
            config_count = session.query(SystemConfiguration).count()
            logger.info(f"⚙️ Configurations in database: {config_count}")
            
            # Test health check
            health = db_manager.health_check()
            logger.info(f"💚 Database health: {health['status']}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Database operation test failed: {e}")
        return False

def display_migration_summary():
    """Display migration summary and next steps"""
    logger.info("\n" + "=" * 60)
    logger.info("🎉 DATABASE MIGRATION COMPLETE!")
    logger.info("=" * 60)
    
    logger.info("✅ Components Successfully Initialized:")
    logger.info("   • Unified database schema for both APIs")
    logger.info("   • User management and session tracking")
    logger.info("   • Conversation and provider response logging")
    logger.info("   • Clinical document management")
    logger.info("   • Performance metrics and analytics")
    logger.info("   • Audit trail for compliance")
    logger.info("   • System configuration management")
    
    logger.info("\n🔮 Fusion AI Database Features:")
    logger.info("   • Google Gemini conversation logging")
    logger.info("   • Groq Cloud response tracking")
    logger.info("   • Fusion strategy analytics")
    logger.info("   • Performance comparison metrics")
    logger.info("   • Clinical entity extraction storage")
    logger.info("   • Multi-provider cost tracking")
    
    logger.info("\n📊 Next Steps:")
    logger.info("   1. Start Fusion AI API: python -m uvicorn api.fusion_api:app --port 8003")
    logger.info("   2. Test API health: GET http://localhost:8003/health")
    logger.info("   3. Run conversation analysis with database logging")
    logger.info("   4. Monitor analytics: Check provider_metrics table")
    logger.info("   5. Review audit logs: Check audit_logs table")
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'sqlite:///./data/clinchat_fusion.db')
    if db_url.startswith('sqlite'):
        db_path = db_url.replace('sqlite:///', '')
        logger.info(f"\n💾 SQLite Database Location: {Path(db_path).absolute()}")
    else:
        logger.info(f"\n🐘 Database Connection: {db_url.split('@')[-1] if '@' in db_url else 'External Database'}")

def main():
    """Main migration function"""
    logger.info("🚀 ClinChat-RAG Unified Database Migration")
    logger.info(f"📅 Migration Date: {datetime.now().isoformat()}")
    logger.info(f"🌐 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Ensure data directory exists for SQLite
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    success = True
    
    # Step 1: Create database and tables
    if not create_database():
        logger.error("❌ Database creation failed")
        success = False
        return
    
    # Step 2: Seed initial data
    if not seed_initial_data():
        logger.error("❌ Data seeding failed")
        success = False
        return
    
    # Step 3: Test operations
    if not test_database_operations():
        logger.error("❌ Database operation tests failed")
        success = False
        return
    
    # Step 4: Display summary
    if success:
        display_migration_summary()
        logger.info("\n🎯 Database is ready for both Google Gemini and Groq APIs!")
    else:
        logger.error("\n❌ Migration completed with errors. Please check logs.")

if __name__ == "__main__":
    main()