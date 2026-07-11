# AIG-Doggy — 企业级 LLM 安全护栏

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![Tests](https://img.shields.io/badge/tests-76%20passed-brightgreen)]()

基于 NVIDIA NeMo Guardrails 的企业级 LLM 安全护栏，为 LLM 应用提供统一的内容安全、主题管控、敏感信息检测和防越狱（Jailbreak）防护能力。

## 特性

- **五层护栏体系**：输入 → 检索 → 对话 → 执行 → 输出，全面覆盖 LLM 交互全链路
- **双协议兼容**：同时支持 OpenAI 和 Anthropic API 格式，业务代码无需修改
- **三级递进检测**：规则引擎（<1ms）→ NIM 专用模型 → 轻量级 LLM 辅助裁决
- **组合模式隔离上游**：`NeMoAdapter` 是唯一接触 NeMo 的模块，上游变更零影响
- **流式实时护栏**：对流式 LLM 输出进行分块安全检查
- **13 个预置护栏插件**：内容安全、主题管控、越狱检测、PII 检测、注入检测、幻觉检测等
- **企业级中间件**：Kafka 异步审计、Redis Cluster 缓存、PostgreSQL 读写分离
- **Prometheus 指标**：6 种自定义指标 + Grafana 仪表盘
- **管理控制台**：React + Arco Design，策略配置、审计日志、应用管理
- **生产级部署**：Docker Compose + Kubernetes Helm + NIM 微服务集成

## 快速开始

```bash
git clone https://github.com/your-org/doggy.git
cd doggy/src

# 启动中间件
docker compose -f docker-compose.dev.yml up -d

# 安装依赖
uv sync --group dev

# 初始化数据库
psql -h localhost -U doggy -d doggy -f scripts/init_db.sql

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DOGGY_OPENAI_API_KEY

# 启动服务
uv run python -m doggy
```

## 验证

```bash
curl http://localhost:8000/v1/healthz
# {"status": "healthy"}

curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer doggy-test-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello!"}]}'
```

## 架构

```
Client → Doggy Gateway (FastAPI)
           ├── 认证 (API Key SHA-256 + Redis)
           ├── 输入护栏 (内容安全/主题/越狱/PII/注入)
           ├── 输出护栏 (内容安全/脱敏/幻觉)
           ├── Kafka 审计 (异步，双层降级)
           ├── Prometheus 指标 (/v1/metrics)
           └── LLM 调用 (OpenAI/Anthropic/自托管)
```

## 文档

| 文档 | 说明 |
|------|------|
| [INSTALL.md](INSTALL.md) | 完整安装部署手册（开发/Docker/K8s/NIM） |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [SECURITY.md](SECURITY.md) | 安全策略 |
| [CHANGELOG.md](CHANGELOG.md) | 变更日志 |

## 许可证

Apache 2.0 — 详见 [LICENSE](LICENSE)

本项目基于 [NVIDIA NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)（Apache 2.0）构建。