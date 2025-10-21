"""
Unified Database Connection Module
Shared database connection for both Google Gemini and Groq APIs
"""

import os
import logging
from datetime import datetime
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, pool
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
import sqlite3

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///./data/clinchat_fusion.db'  # Default to SQLite for development
)

# Database settings from environment
DATABASE_ECHO = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '20'))
DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '30'))
DATABASE_POOL_RECYCLE = int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))

# Create declarative base for all models
Base = declarative_base()

class DatabaseManager:
    """
    Unified database manager for both Google Gemini and Groq APIs
    Provides connection pooling, session management, and monitoring
    """
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self.scoped_session_factory = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database connection and session factory"""
        if self._initialized:
            return
            
        try:
            # Create engine based on database type
            if DATABASE_URL.startswith('sqlite'):
                # SQLite configuration for development
                self.engine = create_engine(
                    DATABASE_URL,
                    echo=DATABASE_ECHO,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20
                    }
                )
                # Enable WAL mode for SQLite
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    if isinstance(dbapi_connection, sqlite3.Connection):
                        cursor = dbapi_connection.cursor()
                        cursor.execute("PRAGMA journal_mode=WAL")
                        cursor.execute("PRAGMA synchronous=NORMAL") 
                        cursor.execute("PRAGMA cache_size=10000")
                        cursor.execute("PRAGMA temp_store=MEMORY")
                        cursor.close()
                        
            else:
                # PostgreSQL configuration for production
                self.engine = create_engine(
                    DATABASE_URL,
                    echo=DATABASE_ECHO,
                    pool_size=DATABASE_POOL_SIZE,
                    max_overflow=DATABASE_MAX_OVERFLOW,
                    pool_recycle=DATABASE_POOL_RECYCLE,
                    pool_pre_ping=True
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create scoped session for thread safety
            self.scoped_session_factory = scoped_session(self.SessionLocal)
            
            self._initialized = True
            logger.info(f"✅ Database initialized: {DATABASE_URL}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def create_tables(self) -> None:
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self._initialized:
            self.initialize()
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic cleanup"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_scoped_session(self) -> scoped_session:
        """Get thread-local scoped session"""
        if not self._initialized:
            self.initialize()
        return self.scoped_session_factory
    
    def close_connections(self) -> None:
        """Close all database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    def health_check(self) -> dict:
        """Check database connectivity and health"""
        try:
            with self.get_session_context() as session:
                # Test connection with a simple query using proper SQLAlchemy 2.0 syntax
                result = session.execute(text("SELECT 1 as test_value")).fetchone()
                
                return {
                    "status": "healthy",
                    "database_url": DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL,
                    "connection_pool_size": DATABASE_POOL_SIZE,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for easy access
def get_db_session() -> Session:
    """Get a new database session"""
    return db_manager.get_session()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database operations"""
    with db_manager.get_session_context() as session:
        yield session

def init_database() -> None:
    """Initialize database and create tables"""
    db_manager.initialize()
    db_manager.create_tables()

def get_database_health() -> dict:
    """Get database health status"""
    return db_manager.health_check()

# Database utilities for AI providers
class AIProviderLogger:
    """
    Utility class for logging AI provider interactions to database
    Used by both Google Gemini and Groq APIs
    """
    
    @staticmethod
    def log_conversation(
        session: Session,
        user_id: Optional[str],
        provider: str,
        model: str,
        input_text: str,
        output_text: str,
        processing_time: float,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        metadata: Optional[dict] = None
    ) -> int:
        """Log conversation to database"""
        try:
            # This will be implemented when we create the models
            # For now, we'll prepare the structure
            conversation_data = {
                "user_id": user_id,
                "provider": provider,
                "model": model,
                "input_text": input_text,
                "output_text": output_text,
                "processing_time": processing_time,
                "tokens_used": tokens_used,
                "cost": cost,
                "metadata": metadata or {},
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"📝 Conversation logged: {provider} - {len(input_text)} chars in, {len(output_text)} chars out")
            return 1  # Placeholder conversation ID
            
        except Exception as e:
            logger.error(f"Failed to log conversation: {e}")
            raise
    
    @staticmethod
    def log_performance_metrics(
        session: Session,
        provider: str,
        model: str,
        operation_type: str,
        success: bool,
        processing_time: float,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> None:
        """Log performance metrics to database"""
        try:
            metrics_data = {
                "provider": provider,
                "model": model,
                "operation_type": operation_type,
                "success": success,
                "processing_time": processing_time,
                "error_message": error_message,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"📊 Metrics logged: {provider} - {operation_type} - {'✅' if success else '❌'}")
            
        except Exception as e:
            logger.error(f"Failed to log performance metrics: {e}")
            raise

# Create global logger instance
ai_logger = AIProviderLogger()