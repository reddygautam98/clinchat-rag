"""
Scalable Vector Database Implementation for ClinChat-RAG
Replaces FAISS with OpenSearch and managed vector databases (Pinecone, Weaviate)
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np

# Vector database implementations
try:
    from opensearchpy import OpenSearch
    from opensearchpy.helpers import bulk, scan
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

from improvements.metadata_filters import MetadataFilter, DocumentMetadata, metadata_filter_engine

@dataclass
class VectorSearchResult:
    """Standardized vector search result"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

@dataclass
class VectorDatabaseConfig:
    """Configuration for vector database connections"""
    database_type: str  # "opensearch", "pinecone", "weaviate", "faiss"
    
    # Connection settings
    host: Optional[str] = None
    port: Optional[int] = None
    api_key: Optional[str] = None
    environment: Optional[str] = None
    
    # Index/Collection settings
    index_name: str = "clinchat-medical-docs"
    dimension: int = 768
    
    # Performance settings
    batch_size: int = 100
    timeout: int = 30
    
    # Security settings
    use_ssl: bool = True
    verify_certs: bool = True
    username: Optional[str] = None
    password: Optional[str] = None

class VectorDatabase(ABC):
    """Abstract base class for vector database implementations"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the vector database"""
        pass
    
    @abstractmethod
    async def create_index(self, config: VectorDatabaseConfig) -> bool:
        """Create vector index/collection"""
        pass
    
    @abstractmethod
    async def upsert_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        """Insert or update vectors with metadata"""
        pass
    
    @abstractmethod
    async def search_vectors(self, query_vector: List[float], 
                           filters: Optional[MetadataFilter] = None,
                           top_k: int = 10) -> List[VectorSearchResult]:
        """Search for similar vectors with metadata filtering"""
        pass
    
    @abstractmethod
    async def delete_vectors(self, doc_ids: List[str]) -> bool:
        """Delete vectors by document IDs"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        pass

class OpenSearchVectorDatabase(VectorDatabase):
    """OpenSearch implementation for vector storage and search"""
    
    def __init__(self, config: VectorDatabaseConfig):
        if not OPENSEARCH_AVAILABLE:
            raise ImportError("opensearch-py not installed. Install with: pip install opensearch-py")
        
        self.config = config
        self.client = None
        self.logger = logging.getLogger(__name__)
        
    async def connect(self) -> bool:
        """Connect to OpenSearch cluster"""
        try:
            auth = None
            if self.config.username and self.config.password:
                auth = (self.config.username, self.config.password)
            
            self.client = OpenSearch(
                hosts=[{
                    'host': self.config.host or 'localhost',
                    'port': self.config.port or 9200
                }],
                http_auth=auth,
                use_ssl=self.config.use_ssl,
                verify_certs=self.config.verify_certs,
                timeout=self.config.timeout
            )
            
            # Test connection
            info = self.client.info()
            self.logger.info(f"Connected to OpenSearch cluster: {info['version']['number']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to OpenSearch: {e}")
            return False
    
    async def create_index(self, config: VectorDatabaseConfig) -> bool:
        """Create OpenSearch index with vector search capabilities"""
        try:
            # Define index mapping with kNN vector field
            mapping = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 512,
                    },
                    "number_of_shards": 2,
                    "number_of_replicas": 1
                },
                "mappings": {
                    "properties": {
                        "doc_id": {"type": "keyword"},
                        "content": {"type": "text", "analyzer": "standard"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": config.dimension,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 24
                                }
                            }
                        },
                        "metadata": {
                            "properties": {
                                "document_type": {"type": "keyword"},
                                "trial_id": {"type": "keyword"},
                                "publication_date": {"type": "date"},
                                "therapeutic_area": {"type": "keyword"},
                                "drug_name": {"type": "keyword"},
                                "evidence_level": {"type": "keyword"},
                                "source_system": {"type": "keyword"},
                                "custom_metadata": {"type": "object", "enabled": False}
                            }
                        },
                        "timestamp": {"type": "date", "format": "epoch_millis"}
                    }
                }
            }
            
            # Create index if it doesn't exist
            if not self.client.indices.exists(index=config.index_name):
                response = self.client.indices.create(
                    index=config.index_name,
                    body=mapping
                )
                self.logger.info(f"Created OpenSearch index: {config.index_name}")
                return True
            else:
                self.logger.info(f"OpenSearch index already exists: {config.index_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create OpenSearch index: {e}")
            return False
    
    async def upsert_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        """Bulk upsert vectors to OpenSearch"""
        try:
            actions = []
            
            for doc_id, embedding, metadata in vectors:
                action = {
                    "_index": self.config.index_name,
                    "_id": doc_id,
                    "_source": {
                        "doc_id": doc_id,
                        "content": metadata.get("content", ""),
                        "embedding": embedding,
                        "metadata": metadata,
                        "timestamp": int(time.time() * 1000)
                    }
                }
                actions.append(action)
            
            # Bulk index
            response = bulk(self.client, actions, refresh=True)
            success_count = len(response[1]) if response[0] == len(vectors) else 0
            
            self.logger.info(f"Upserted {success_count}/{len(vectors)} vectors to OpenSearch")
            return success_count == len(vectors)
            
        except Exception as e:
            self.logger.error(f"Failed to upsert vectors to OpenSearch: {e}")
            return False
    
    async def search_vectors(self, query_vector: List[float], 
                           filters: Optional[MetadataFilter] = None,
                           top_k: int = 10) -> List[VectorSearchResult]:
        """Semantic search with metadata filtering in OpenSearch"""
        try:
            # Build kNN search query
            knn_query = {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": top_k
                    }
                }
            }
            
            # Add metadata filters if specified
            if filters:
                filter_conditions = self._build_opensearch_filters(filters)
                if filter_conditions:
                    knn_query["knn"]["embedding"]["filter"] = filter_conditions
            
            # Execute search
            response = self.client.search(
                index=self.config.index_name,
                body={
                    "query": knn_query,
                    "size": top_k,
                    "_source": ["doc_id", "content", "metadata"]
                }
            )
            
            # Parse results
            results = []
            for hit in response["hits"]["hits"]:
                result = VectorSearchResult(
                    doc_id=hit["_source"]["doc_id"],
                    content=hit["_source"]["content"],
                    score=hit["_score"],
                    metadata=hit["_source"]["metadata"]
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search vectors in OpenSearch: {e}")
            return []
    
    def _build_opensearch_filters(self, filters: MetadataFilter) -> Dict[str, Any]:
        """Convert MetadataFilter to OpenSearch query filters"""
        filter_conditions = {"bool": {"must": []}}
        
        # Trial ID filter
        if filters.trial_ids:
            filter_conditions["bool"]["must"].append({
                "terms": {"metadata.trial_id": filters.trial_ids}
            })
        
        # Date range filter
        if filters.date_from or filters.date_to:
            date_filter = {"range": {"metadata.publication_date": {}}}
            if filters.date_from:
                date_filter["range"]["metadata.publication_date"]["gte"] = filters.date_from
            if filters.date_to:
                date_filter["range"]["metadata.publication_date"]["lte"] = filters.date_to
            filter_conditions["bool"]["must"].append(date_filter)
        
        # Document type filter
        if filters.document_types:
            doc_types = [dt.value for dt in filters.document_types]
            filter_conditions["bool"]["must"].append({
                "terms": {"metadata.document_type": doc_types}
            })
        
        # Therapeutic area filter
        if filters.therapeutic_areas:
            filter_conditions["bool"]["must"].append({
                "terms": {"metadata.therapeutic_area": filters.therapeutic_areas}
            })
        
        return filter_conditions if filter_conditions["bool"]["must"] else {}
    
    async def delete_vectors(self, doc_ids: List[str]) -> bool:
        """Delete vectors by document IDs"""
        try:
            actions = [
                {"_op_type": "delete", "_index": self.config.index_name, "_id": doc_id}
                for doc_id in doc_ids
            ]
            
            response = bulk(self.client, actions, refresh=True)
            success_count = len(response[1]) if response[0] == len(doc_ids) else 0
            
            self.logger.info(f"Deleted {success_count}/{len(doc_ids)} vectors from OpenSearch")
            return success_count == len(doc_ids)
            
        except Exception as e:
            self.logger.error(f"Failed to delete vectors from OpenSearch: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get OpenSearch index statistics"""
        try:
            stats = self.client.indices.stats(index=self.config.index_name)
            index_stats = stats["indices"][self.config.index_name]
            
            return {
                "total_documents": index_stats["total"]["docs"]["count"],
                "index_size_bytes": index_stats["total"]["store"]["size_in_bytes"],
                "search_time_ms": index_stats["total"]["search"]["time_in_millis"],
                "search_count": index_stats["total"]["search"]["query_total"],
                "index_name": self.config.index_name,
                "database_type": "opensearch"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get OpenSearch stats: {e}")
            return {}

class PineconeVectorDatabase(VectorDatabase):
    """Pinecone managed vector database implementation"""
    
    def __init__(self, config: VectorDatabaseConfig):
        if not PINECONE_AVAILABLE:
            raise ImportError("pinecone-client not installed. Install with: pip install pinecone-client")
        
        self.config = config
        self.index = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """Connect to Pinecone"""
        try:
            pinecone.init(
                api_key=self.config.api_key,
                environment=self.config.environment
            )
            
            # Connect to index
            if self.config.index_name in pinecone.list_indexes():
                self.index = pinecone.Index(self.config.index_name)
                self.logger.info(f"Connected to Pinecone index: {self.config.index_name}")
                return True
            else:
                self.logger.error(f"Pinecone index not found: {self.config.index_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Pinecone: {e}")
            return False
    
    async def create_index(self, config: VectorDatabaseConfig) -> bool:
        """Create Pinecone index"""
        try:
            if config.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=config.index_name,
                    dimension=config.dimension,
                    metric="cosine",
                    metadata_config={
                        "indexed": ["document_type", "trial_id", "therapeutic_area", "source_system"]
                    }
                )
                self.logger.info(f"Created Pinecone index: {config.index_name}")
            
            self.index = pinecone.Index(config.index_name)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Pinecone index: {e}")
            return False
    
    async def upsert_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        """Upsert vectors to Pinecone"""
        try:
            # Convert to Pinecone format
            upsert_data = [
                (doc_id, embedding, metadata)
                for doc_id, embedding, metadata in vectors
            ]
            
            # Batch upsert
            response = self.index.upsert(vectors=upsert_data)
            
            self.logger.info(f"Upserted {response['upserted_count']} vectors to Pinecone")
            return response['upserted_count'] == len(vectors)
            
        except Exception as e:
            self.logger.error(f"Failed to upsert vectors to Pinecone: {e}")
            return False
    
    async def search_vectors(self, query_vector: List[float], 
                           filters: Optional[MetadataFilter] = None,
                           top_k: int = 10) -> List[VectorSearchResult]:
        """Search vectors in Pinecone with metadata filtering"""
        try:
            # Build Pinecone filter
            pinecone_filter = self._build_pinecone_filters(filters) if filters else None
            
            # Execute search
            response = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter
            )
            
            # Parse results
            results = []
            for match in response['matches']:
                result = VectorSearchResult(
                    doc_id=match['id'],
                    content=match['metadata'].get('content', ''),
                    score=match['score'],
                    metadata=match['metadata']
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search vectors in Pinecone: {e}")
            return []
    
    def _build_pinecone_filters(self, filters: MetadataFilter) -> Dict[str, Any]:
        """Convert MetadataFilter to Pinecone filter format"""
        pinecone_filter = {}
        
        if filters.trial_ids:
            pinecone_filter["trial_id"] = {"$in": filters.trial_ids}
        
        if filters.document_types:
            doc_types = [dt.value for dt in filters.document_types]
            pinecone_filter["document_type"] = {"$in": doc_types}
        
        if filters.therapeutic_areas:
            pinecone_filter["therapeutic_area"] = {"$in": filters.therapeutic_areas}
        
        return pinecone_filter
    
    async def delete_vectors(self, doc_ids: List[str]) -> bool:
        """Delete vectors from Pinecone"""
        try:
            response = self.index.delete(ids=doc_ids)
            self.logger.info(f"Deleted {len(doc_ids)} vectors from Pinecone")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete vectors from Pinecone: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "total_documents": stats['total_vector_count'],
                "index_fullness": stats.get('index_fullness', 0),
                "dimension": stats['dimension'],
                "index_name": self.config.index_name,
                "database_type": "pinecone"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Pinecone stats: {e}")
            return {}

class VectorDatabaseManager:
    """Manager for different vector database implementations"""
    
    def __init__(self):
        self.databases = {
            "opensearch": OpenSearchVectorDatabase,
            "pinecone": PineconeVectorDatabase,
        }
        self.active_db = None
        self.config = None
    
    async def initialize(self, config: VectorDatabaseConfig) -> bool:
        """Initialize vector database connection"""
        try:
            self.config = config
            
            if config.database_type not in self.databases:
                raise ValueError(f"Unsupported database type: {config.database_type}")
            
            # Create database instance
            db_class = self.databases[config.database_type]
            self.active_db = db_class(config)
            
            # Connect and create index
            if await self.active_db.connect():
                return await self.active_db.create_index(config)
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to initialize vector database: {e}")
            return False
    
    async def search(self, query_vector: List[float], 
                    filters: Optional[MetadataFilter] = None,
                    top_k: int = 10) -> List[VectorSearchResult]:
        """Search across all configured databases"""
        if not self.active_db:
            raise RuntimeError("Vector database not initialized")
        
        return await self.active_db.search_vectors(query_vector, filters, top_k)
    
    async def upsert(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        """Upsert vectors to the active database"""
        if not self.active_db:
            raise RuntimeError("Vector database not initialized")
        
        return await self.active_db.upsert_vectors(vectors)
    
    async def delete(self, doc_ids: List[str]) -> bool:
        """Delete vectors from the active database"""
        if not self.active_db:
            raise RuntimeError("Vector database not initialized")
        
        return await self.active_db.delete_vectors(doc_ids)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics from the active database"""
        if not self.active_db:
            return {"error": "No active database"}
        
        return await self.active_db.get_stats()

# Configuration examples
OPENSEARCH_CONFIG = VectorDatabaseConfig(
    database_type="opensearch",
    host="localhost",
    port=9200,
    index_name="clinchat-medical-docs",
    dimension=768,
    use_ssl=False,
    verify_certs=False
)

PINECONE_CONFIG = VectorDatabaseConfig(
    database_type="pinecone",
    api_key="your-pinecone-api-key",
    environment="us-west1-gcp",
    index_name="clinchat-medical-docs",
    dimension=768
)

# Global manager instance
vector_db_manager = VectorDatabaseManager()

# Export main components
__all__ = [
    'VectorDatabase',
    'VectorDatabaseManager', 
    'VectorDatabaseConfig',
    'VectorSearchResult',
    'OpenSearchVectorDatabase',
    'PineconeVectorDatabase',
    'vector_db_manager',
    'OPENSEARCH_CONFIG',
    'PINECONE_CONFIG'
]