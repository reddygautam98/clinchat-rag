# 🏗️ ClinChat-RAG Technical Architecture

## 🎯 Purpose
This document describes the system architecture, data flows, component interactions, scalability strategies, security boundaries, and operational considerations for ClinChat-RAG. It is intended for architects, platform engineers, and auditors.

## 📋 Table of Contents
- [Architecture Overview](#architecture-overview)
- [Component Diagram](#component-diagram)
- [Data Flow and Storage](#data-flow-and-storage)
- [Security Boundaries](#security-boundaries)
- [Scalability and Performance](#scalability-and-performance)
- [Operational Considerations](#operational-considerations)
- [Monitoring & Observability](#monitoring--observability)
- [Disaster Recovery & Backup](#disaster-recovery--backup)
- [Appendix: Sequence Diagrams](#appendix-sequence-diagrams)

## 🏛️ Architecture Overview

ClinChat-RAG is a microservices-based platform composed of API services, clinical NLP, a knowledge graph, vector DB for retrieval-augmented generation (RAG), drug database services, and background workers. The system enforces strict PHI controls and uses a service mesh for secure inter-service communication.

Core components:
- API Gateway (Ingress): Auth, rate limiting, WAF
- Authentication Service: OAuth2, SSO, license verification
- Clinical NLP Service: Named Entity Recognition, PHI detection
- RAG Orchestrator: Retriever + Generator + Ranker
- Vector DB: MongoDB Atlas Vector DB / Milvus
- Knowledge Graph: Neo4j / JanusGraph
- Drug Database Service: Lexicomp/Micromedex adapters
- Background Workers: Celery / RabbitMQ or Redis
- Persistence: PostgreSQL (clinical metadata), S3 (documents), Redis (cache)
- Observability: Prometheus, Grafana, ELK/Datadog
- Secrets: HashiCorp Vault

## 🧭 Component Diagram

(High-level diagram to be rendered by architecture team tools)

API Gateway -> Auth Service -> Clinical NLP -> RAG Orchestrator -> Vector DB -> Knowledge Graph -> Drug DB -> Response

## 🔁 Data Flow and Storage

1. Client Request: Clinician submits clinical query via UI or EMR integration (SMART on FHIR)
2. API Gateway: Validates token, rate-limits, forwards to Query Service
3. PHI Detection: Query content scanned for PHI; blocked or de-identified if PHI found
4. RAG Orchestrator:
   - Retriever: uses vector DB to find relevant documents
   - Reranker: ranks retrieved documents by relevance and evidence level
   - Generator: synthesizes answer using models (on-prem or LLM provider)
5. Drug Interaction Check: Parallel call to Drug DB service for safety checks
6. Response Assembly: Composite response with answer, evidence, confidence
7. Audit Logging: Full audit entry with hashed patient ID (if any)
8. Return to Client: Response delivered via gateway

## 💾 Storage and Retention

- PostgreSQL: structured metadata, user accounts, configurations
- Vector DB: embeddings, short retention (30-90 days depending on policy)
- S3 (or equivalent): raw documents and knowledge-base artifacts, encrypted
- Audit Logs: write-once, append-only storage with retention 7+ years
- Backups: incremental + full snapshots, encrypted

## 🔒 Security Boundaries

- Ingress boundary (WAF, TLS termination)
- Service mesh: mTLS for all inter-service calls
- Vault: central secrets store, short TTLs
- RBAC: enforced at API and UI layers
- PHI detection: enforced pre-processing step
- Audit logging: immutable storage and HMAC signing

## ⚙️ Scalability and Performance

- Horizontal scaling for stateless services (API, NLP, RAG)
- Vector DB scaling: shard and replica sets for read performance
- Autoscaling via HPA based on CPU and custom metrics (query latency)
- Caching: Redis for commonly-requested guideline fragments and drug lookups
- Asynchronous workers for heavy tasks (indexing, ingestion)

## 🛡️ Operational Considerations

- Blue/Green or Canary deployments with Helm
- Health checks and readiness/liveness probes for Kubernetes
- Graceful shutdown and drain connections
- Circuit breakers for external dependencies (drug DB, EMR)
- Test harness for canary traffic (synthetic clinical queries)

## 📈 Monitoring & Observability

- Metrics: latency, error rates, clinical_accuracy_score, phi_detection_failures
- Traces: distributed tracing via OpenTelemetry
- Logs: structured JSON logs, centralized via ELK/Datadog
- Alerts: clinical impact alerts, PHI detection failures, service down

## 🆘 Disaster Recovery & Backup

- RTO/RPO targets defined per component (see deployment guide)
- Cross-region replication for critical data (audit logs, DB)
- Regular DR drills and automated verification

## 🔁 Appendix: Sequence Diagrams

(Sequence diagrams for clinical query processing, drug interaction check, and content update workflows go here.)

---

**Document Version**: 1.0  
**Last Updated**: October 20, 2025  
**Next Review**: January 20, 2026