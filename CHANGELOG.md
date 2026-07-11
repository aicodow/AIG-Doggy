# Changelog

All notable changes to AIG-Doggy will be documented in this file.

## [0.1.0] - 2026-07-11

### Added
- Core engine: `DoggyEngineProtocol` + `NeMoAdapter` with three-layer defense against upstream NeMo API changes
- Protocol adapters: OpenAI and Anthropic format support
- Authentication: API Key generation (SHA-256 hashed), verification, and Redis caching
- Input guardrails: content safety, topic control, jailbreak detection (heuristics + NIM model), PII detection, injection detection, context bloat detection
- Output guardrails: content safety, PII masking, tool call validation, streaming output rails
- Lightweight LLM auxiliary detection module (three-tier progressive architecture)
- Regex detection engine (YAML-configured, pre-compiled patterns)
- 14 pre-built guardrail plugins with registry system
- Kafka audit event producer with dual-layer fallback (Kafka → local JSON log)
- Redis Cluster cache client (API Key verification + rate limiting)
- PostgreSQL read/write split connection pool
- Prometheus metrics: 6 custom metrics + `/v1/metrics` endpoint
- JSON structured logging for Filebeat collection
- Admin API: policy CRUD, audit log search, app management, plugin listing
- React + Arco Design admin console (dashboard, policies, audit logs, apps, users)
- Docker Compose development environment (PostgreSQL + Redis + Kafka)
- Docker Compose production deployment (7 services with health checks)
- Kubernetes Helm chart (HPA, Secrets, Prometheus ServiceMonitor)
- NIM microservice deployment configs
- Unit tests (76 tests), security effectiveness tests (25 tests), integration tests, E2E tests
- CI/CD: GitHub Actions workflow (lint + type-check + test) + weekly upstream NeMo compatibility check with Slack alert
- Installation manual with step-by-step instructions for dev, Docker Compose, and K8s deployment