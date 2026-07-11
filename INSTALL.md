# AIG-Doggy 安装部署与配置手册

**文档版本**: v1.0 | **最后更新**: 2026-07-11

---

## 目录

1. [环境要求](#1-环境要求)
2. [开发环境部署](#2-开发环境部署)
3. [Docker Compose 生产部署](#3-docker-compose-生产部署)
4. [Kubernetes + Helm 生产部署](#4-kubernetes--helm-生产部署)
5. [NIM 微服务集成](#5-nim-微服务集成)
6. [配置指南](#6-配置指南)
7. [验证部署](#7-验证部署)
8. [常见问题排查](#8-常见问题排查)

---

## 1. 环境要求

### 1.1 硬件最低要求

| 环境 | CPU | 内存 | 磁盘 | 说明 |
|------|-----|------|------|------|
| 开发环境 | 4 核 | 8 GB | 50 GB SSD | 仅运行 Doggy + 中间件 |
| 生产环境（单机） | 16 核 | 32 GB | 500 GB SSD | 含全部中间件 |
| 生产环境（K8s） | 3 节点 × 8 核 | 3 × 16 GB | 按需 | 分布式部署 |

### 1.2 软件依赖

| 软件 | 最低版本 | 用途 |
|------|---------|------|
| Python | 3.11 | 运行时 |
| Docker | 24.0 | 容器运行 |
| Docker Compose | 2.20 | 服务编排 |
| Git | 2.40 | 版本控制 |
| kubectl | 1.28 | K8s 集群管理（仅 K8s 部署） |
| Helm | 3.14 | K8s 包管理（仅 K8s 部署） |
| uv | 0.5.0 | Python 包管理 |

### 1.3 外部服务依赖

| 服务 | 用途 | 必须 | 替代方案 |
|------|------|------|---------|
| PostgreSQL 16 | 审计日志 + 配置存储 | 是 | 无 |
| Redis 7 | 缓存 + 限流 | 是 | 无 |
| Kafka 3.6+ | 异步审计消息 | 是 | 本地日志降级 |
| OpenAI API Key | 主 LLM 调用 | 是 | 自托管 vLLM |
| NIM 内容安全 | 内容安全检测 | 否 | 轻量级 LLM 辅助 |
| NIM 主题控制 | 主题管控 | 否 | 关键词过滤 |
| NIM 越狱检测 | 越狱检测 | 否 | 启发式 + 轻量 LLM |

---

## 2. 开发环境部署

### 2.1 克隆项目

```bash
git clone https://github.com/your-org/doggy.git
cd doggy/src
```

### 2.2 安装 Python 依赖

```bash
# 安装 uv（如未安装）
pip install uv

# 创建虚拟环境并安装所有依赖
uv sync
uv sync --group dev
```

### 2.3 启动中间件

```bash
# 启动 PostgreSQL + Redis + Kafka
docker compose -f docker-compose.dev.yml up -d

# 等待所有服务健康
docker compose -f docker-compose.dev.yml ps
# 预期输出: 所有服务 STATUS = healthy
```

### 2.4 初始化数据库

```bash
# 方式 1：通过 Docker 执行
docker exec -i $(docker ps -qf "name=postgres") psql -U doggy -d doggy < scripts/init_db.sql

# 方式 2：通过本地 psql 客户端
psql -h localhost -p 5432 -U doggy -d doggy -f scripts/init_db.sql
```

### 2.5 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
# Doggy 配置路径
DOGGY_CONFIG_PATH=doggy/configs/default

# OpenAI API Key（必填）
DOGGY_OPENAI_API_KEY=sk-your-openai-api-key

# 中间件连接（开发环境默认值）
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_NODES=localhost:6379
DB_WRITE_URL=postgresql://doggy:doggy_dev@localhost:5432/doggy
DB_READ_URL=postgresql://doggy:doggy_dev@localhost:5432/doggy

# NIM 服务（可选，未部署时使用轻量级 LLM 降级）
NIM_CONTENT_SAFETY_URL=http://localhost:8000
NIM_TOPIC_CONTROL_URL=http://localhost:8001
NIM_JAILBREAK_DETECT_URL=http://localhost:8002
NIM_API_KEY=
EOF

# 加载环境变量
source .env  # Linux/Mac
# 或 Windows: set -a; source .env; set +a （Git Bash）
```

### 2.6 启动服务

```bash
# 启动 Doggy 开发服务器
uv run python -m doggy

# 或使用 uvicorn 直接启动（支持热重载）
uv run uvicorn doggy.server.bootstrap:app --reload --host 0.0.0.0 --port 8000
```

### 2.7 验证开发环境

```bash
# 健康检查
curl http://localhost:8000/v1/healthz

# 预期输出
# {"status": "healthy"}
```

---

## 3. Docker Compose 生产部署

### 3.1 准备证书

```bash
# 生成自签名证书（测试用）
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/doggy.key -out certs/doggy.crt \
  -days 365 -nodes -subj "/CN=doggy.your-company.com"

# 生产环境：使用 Let's Encrypt 或购买 CA 证书
```

### 3.2 创建环境变量文件

```bash
cat > .env.prod << 'EOF'
# 版本
DOGGY_VERSION=0.1.0

# 数据库密码（请修改为强密码）
DB_PASSWORD=change-me-to-a-strong-password

# OpenAI API Key
DOGGY_OPENAI_API_KEY=sk-your-openai-api-key

# Grafana 密码
GRAFANA_PASSWORD=change-me-to-a-strong-password

# NIM 服务 URL
NIM_CONTENT_SAFETY_URL=http://nim-content-safety:8000
NIM_TOPIC_CONTROL_URL=http://nim-topic-control:8000
NIM_JAILBREAK_DETECT_URL=http://nim-jailbreak-detect:8000
NIM_API_KEY=your-nim-api-key

# Kafka 连接
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Redis 连接
REDIS_NODES=redis:6379
EOF
```

### 3.3 创建生产 Docker Compose 文件

```bash
cat > docker-compose.prod.yml << 'EOF'
version: "3.8"

services:
  # ═══════════════════════════════════════════
  # Doggy Gateway
  # ═══════════════════════════════════════════
  doggy-gateway:
    image: your-registry/doggy-gateway:${DOGGY_VERSION}
    ports:
      - "8000:8000"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
      - REDIS_NODES=${REDIS_NODES}
      - DB_WRITE_URL=postgresql://doggy:${DB_PASSWORD}@postgres:5432/doggy
      - DB_READ_URL=postgresql://doggy:${DB_PASSWORD}@postgres:5432/doggy
      - DOGGY_OPENAI_API_KEY=${DOGGY_OPENAI_API_KEY}
      - NIM_CONTENT_SAFETY_URL=${NIM_CONTENT_SAFETY_URL}
      - NIM_TOPIC_CONTROL_URL=${NIM_TOPIC_CONTROL_URL}
      - NIM_JAILBREAK_DETECT_URL=${NIM_JAILBREAK_DETECT_URL}
      - NIM_API_KEY=${NIM_API_KEY}
    volumes:
      - ./doggy/configs:/app/doggy/configs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ═══════════════════════════════════════════
  # PostgreSQL
  # ═══════════════════════════════════════════
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: doggy
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: doggy
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U doggy"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ═══════════════════════════════════════════
  # Redis
  # ═══════════════════════════════════════════
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ═══════════════════════════════════════════
  # Kafka (KRaft 模式，无需 Zookeeper)
  # ═══════════════════════════════════════════
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    volumes:
      - kafka_data:/var/lib/kafka/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ═══════════════════════════════════════════
  # Prometheus
  # ═══════════════════════════════════════════
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./configs/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=30d"
    restart: unless-stopped

  # ═══════════════════════════════════════════
  # Grafana
  # ═══════════════════════════════════════════
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./configs/grafana/datasources:/etc/grafana/provisioning/datasources
      - ./configs/grafana/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped

volumes:
  pg_data:
  redis_data:
  kafka_data:
  prometheus_data:
  grafana_data:
EOF
```

### 3.4 构建镜像

```bash
# 构建 Doggy Gateway 镜像
docker build -t your-registry/doggy-gateway:0.1.0 .

# 推送到镜像仓库
docker push your-registry/doggy-gateway:0.1.0
```

### 3.5 启动服务

```bash
# 启动所有服务
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 查看启动日志
docker compose -f docker-compose.prod.yml logs -f doggy-gateway

# 等待所有服务健康
docker compose -f docker-compose.prod.yml ps
```

### 3.6 停止服务

```bash
# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 停止并删除数据卷（危险操作）
docker compose -f docker-compose.prod.yml down -v
```

---

## 4. Kubernetes + Helm 生产部署

### 4.1 前置条件

```bash
# 确认 kubectl 已连接集群
kubectl cluster-info

# 确认 Helm 已安装
helm version

# 安装必需的 Operator
# Strimzi Kafka Operator
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi-operator strimzi/strimzi-kafka-operator \
  --namespace doggy-mq --create-namespace

# CloudNativePG PostgreSQL Operator
kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-v1.24.0.yaml

# Prometheus Operator（如未安装）
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace doggy-monitoring --create-namespace
```

### 4.2 创建命名空间

```bash
kubectl create namespace doggy-gateway
kubectl create namespace doggy-data
kubectl create namespace doggy-mq
kubectl create namespace doggy-monitoring
```

### 4.3 创建 Secrets

```bash
# 数据库凭据
kubectl create secret generic doggy-db-credentials \
  --from-literal=write_url="postgresql://doggy:$(openssl rand -base64 32)@pg-primary.doggy-data:5432/doggy" \
  --from-literal=read_url="postgresql://doggy:$(openssl rand -base64 32)@pg-replica.doggy-data:5432/doggy" \
  --from-literal=password="$(openssl rand -base64 32)" \
  -n doggy-gateway

# NIM 凭据
kubectl create secret generic nim-credentials \
  --from-literal=api_key="${NIM_API_KEY}" \
  -n doggy-gateway

# OpenAI API Key
kubectl create secret generic doggy-api-secrets \
  --from-literal=openai="${DOGGY_OPENAI_API_KEY}" \
  -n doggy-gateway
```

### 4.4 部署基础设施

#### 4.4.1 PostgreSQL 集群

```bash
cat <<'EOF' | kubectl apply -n doggy-data -f -
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: doggy-postgres
spec:
  instances: 3
  storage:
    size: 1Ti
    storageClass: ssd
  resources:
    requests:
      cpu: "4"
      memory: 16Gi
    limits:
      cpu: "8"
      memory: 32Gi
  bootstrap:
    initdb:
      database: doggy
      owner: doggy
      secret:
        name: doggy-db-credentials
EOF
```

#### 4.4.2 Kafka 集群

```bash
cat <<'EOF' | kubectl apply -n doggy-mq -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: doggy-kafka
spec:
  kafka:
    version: 3.7.0
    replicas: 3
    storage:
      type: persistent-claim
      size: 500Gi
      class: ssd
    resources:
      requests:
        cpu: "4"
        memory: 16Gi
      limits:
        cpu: "8"
        memory: 32Gi
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
  entityOperator:
    topicOperator: {}
    userOperator: {}
EOF
```

#### 4.4.3 Redis Cluster

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm upgrade --install doggy-redis bitnami/redis-cluster \
  -n doggy-data \
  --set cluster.nodes=3 \
  --set cluster.replicas=0 \
  --set persistence.size=50Gi \
  --set resources.requests.cpu=2 \
  --set resources.requests.memory=8Gi \
  --set resources.limits.cpu=4 \
  --set resources.limits.memory=16Gi
```

### 4.5 部署 Doggy

```bash
# 创建 values-prod.yaml
cat > values-prod.yaml << 'EOF'
global:
  imageRegistry: your-registry
  imageTag: "0.1.0"
  environment: production

gateway:
  replicas: 3
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  resources:
    requests: { cpu: "2", memory: "4Gi" }
    limits: { cpu: "8", memory: "16Gi" }
  env:
    - name: KAFKA_BOOTSTRAP_SERVERS
      value: "doggy-kafka-kafka-bootstrap.doggy-mq:9092"
    - name: REDIS_NODES
      value: "doggy-redis-redis-cluster-0.doggy-redis-redis-cluster-headless.doggy-data:6379,doggy-redis-redis-cluster-1.doggy-redis-redis-cluster-headless.doggy-data:6379,doggy-redis-redis-cluster-2.doggy-redis-redis-cluster-headless.doggy-data:6379"
    - name: DB_WRITE_URL
      valueFrom:
        secretKeyRef:
          name: doggy-db-credentials
          key: write_url
    - name: DB_READ_URL
      valueFrom:
        secretKeyRef:
          name: doggy-db-credentials
          key: read_url
    - name: DOGGY_OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: doggy-api-secrets
          key: openai
    - name: NIM_CONTENT_SAFETY_URL
      value: "http://nim-content-safety.nim-services:8000"
    - name: NIM_API_KEY
      valueFrom:
        secretKeyRef:
          name: nim-credentials
          key: api_key
EOF

# 安装 Doggy Helm Chart
helm upgrade --install doggy ./helm/doggy \
  -f values-prod.yaml \
  -n doggy-gateway

# 查看部署状态
kubectl get pods -n doggy-gateway
kubectl get svc -n doggy-gateway
kubectl get hpa -n doggy-gateway
```

### 4.6 配置 Ingress

```bash
cat <<'EOF' | kubectl apply -n doggy-gateway -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: doggy-gateway
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - doggy.your-company.com
      secretName: doggy-tls
  rules:
    - host: doggy.your-company.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: doggy-gateway
                port:
                  number: 8000
EOF
```

---

## 5. NIM 微服务集成

### 5.1 部署 NIM 内容安全模型

```bash
kubectl create namespace nim-services

kubectl apply -f k8s/nim/content-safety.yaml -n nim-services

# 查看部署状态
kubectl get pods -n nim-services -w

# 等待健康检查通过
kubectl wait --for=condition=ready pod \
  -l app=nim-content-safety -n nim-services --timeout=300s
```

### 5.2 验证 NIM 服务

```bash
# 端口转发到本地
kubectl port-forward -n nim-services svc/nim-content-safety 8000:8000 &

# 健康检查
curl http://localhost:8000/v1/health/ready
# 预期输出: {"status": "ready"}

# 测试推理
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${NIM_API_KEY}" \
  -d '{
    "model": "nvidia/nemoguard-content-safety",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "max_tokens": 50
  }'
```

### 5.3 配置 Doggy 使用 NIM

```yaml
# doggy/configs/default/config.yml
models:
  - type: content_safety
    engine: nim
    model: nvidia/nemoguard-content-safety
    parameters:
      base_url: "http://nim-content-safety.nim-services:8000"  # K8s 内部域名
      api_key: "${NIM_API_KEY}"
    mode: chat
```

---

## 6. 配置指南

### 6.1 最小配置

```yaml
# 最小可用的 config.yml
colang_version: "2.x"

models:
  - type: main
    engine: openai
    model: gpt-4o-mini
    api_key_env_var: DOGGY_OPENAI_API_KEY

rails:
  input:
    parallel: true
    flows:
      - "content safety check input $model=content_safety"

  output:
    flows:
      - "content safety check output $model=content_safety"
    streaming:
      enabled: true
      chunk_size: 200
      stream_first: true
```

### 6.2 完整配置

```yaml
colang_version: "2.x"

models:
  # 主 LLM
  - type: main
    engine: openai
    model: gpt-4o-mini
    api_key_env_var: DOGGY_OPENAI_API_KEY

  # 内容安全模型（NIM 微服务）
  - type: content_safety
    engine: nim
    model: nvidia/nemoguard-content-safety
    parameters:
      base_url: "${NIM_CONTENT_SAFETY_URL}"
      api_key: "${NIM_API_KEY}"
    mode: chat

  # 主题控制模型（可选）
  - type: topic_control
    engine: nim
    model: nvidia/nemoguard-topic-control
    parameters:
      base_url: "${NIM_TOPIC_CONTROL_URL}"
      api_key: "${NIM_API_KEY}"
    mode: chat

  # 越狱检测模型（可选）
  - type: jailbreak_detection
    engine: nim
    model: nvidia/nemoguard-jailbreak-detect
    parameters:
      base_url: "${NIM_JAILBREAK_DETECT_URL}"
      api_key: "${NIM_API_KEY}"
    mode: chat

  # 轻量级 LLM 辅助检测（可选，NIM 降级时使用）
  - type: lite_guard
    engine: openai
    model: gpt-4o-mini
    api_key_env_var: DOGGY_OPENAI_API_KEY
    parameters:
      temperature: 0.0
      max_tokens: 256

rails:
  input:
    parallel: true
    flows:
      - "content safety check input $model=content_safety"
      - "topic safety check input $model=topic_control"
      - "jailbreak detection heuristics"
      - "jailbreak detection model"
      - "sensitive data detection input"
      - "injection detection input"

  output:
    parallel: false
    flows:
      - "content safety check output $model=content_safety"
      - "sensitive data detection output"
      - "self check output"
    streaming:
      enabled: true
      chunk_size: 200
      context_size: 50
      stream_first: true

  retrieval:
    flows:
      - "sensitive data detection retrieval"

  config:
    sensitive_data_detection:
      input:
        entities:
          - PERSON
          - EMAIL_ADDRESS
          - PHONE_NUMBER
          - CREDIT_CARD
          - US_SSN
          - CN_ID_CARD
        score_threshold: 0.3
      output:
        entities:
          - PERSON
          - EMAIL_ADDRESS
          - PHONE_NUMBER
          - CREDIT_CARD
        score_threshold: 0.3

    regex_detection:
      input:
        patterns:
          - pattern: "(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])\d{6}(?!\d)"
            description: "身份证号"
            level: critical
            action: block
          - pattern: "(?<!\d)1[3-9]\d{9}(?!\d)"
            description: "手机号"
            level: warning
            action: mask
          - pattern: "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
            description: "邮箱"
            level: warning
            action: mask
        case_insensitive: false

    jailbreak_detection:
      length_per_perplexity_threshold: 89.79
      prefix_suffix_perplexity_threshold: 1845.65

    content_safety:
      multilingual:
        enabled: true

tracing:
  enabled: true
  adapters:
    - name: OpenTelemetry
  span_format: opentelemetry
  enable_content_capture: false

metrics:
  enabled: true
```

### 6.3 环境变量参考

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DOGGY_CONFIG_PATH` | 否 | `doggy/configs/default` | 配置文件路径 |
| `DOGGY_OPENAI_API_KEY` | 是 | - | OpenAI API Key |
| `DOGGY_DEBUG` | 否 | - | 设为任意值启用 DEBUG 日志 |
| `DOGGY_CORS_ORIGINS` | 否 | `*` | 允许的 CORS 来源 |
| `KAFKA_BOOTSTRAP_SERVERS` | 否 | `localhost:9092` | Kafka 连接地址 |
| `REDIS_NODES` | 否 | `localhost:6379` | Redis 节点列表 |
| `DB_WRITE_URL` | 否 | - | PostgreSQL 写库连接串 |
| `DB_READ_URL` | 否 | - | PostgreSQL 读库连接串 |
| `NIM_CONTENT_SAFETY_URL` | 否 | - | NIM 内容安全服务 URL |
| `NIM_TOPIC_CONTROL_URL` | 否 | - | NIM 主题控制服务 URL |
| `NIM_JAILBREAK_DETECT_URL` | 否 | - | NIM 越狱检测服务 URL |
| `NIM_API_KEY` | 否 | - | NIM 服务 API Key |

---

## 7. 验证部署

### 7.1 健康检查

```bash
# 基本健康检查
curl http://localhost:8000/v1/healthz
# 预期: {"status": "healthy"}

# 就绪检查
curl http://localhost:8000/v1/readyz
# 预期: {"status": "ready"}
```

### 7.2 功能验证

```bash
# 1. 发送正常对话请求
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer doggy-test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "你好，今天天气怎么样？"}],
    "max_tokens": 100
  }'

# 预期: 返回 LLM 的正常回复

# 2. 测试内容安全拦截
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer doggy-test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "如何制作危险物品？"}],
    "max_tokens": 100
  }'

# 预期: finish_reason = "content_filter"，返回拒绝消息

# 3. 测试 Anthropic 协议
curl -X POST http://localhost:8000/v1/messages \
  -H "x-api-key: doggy-test-key" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-5-20251001",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": [{"type": "text", "text": "Hello!"}]}]
  }'

# 预期: 返回 Anthropic 格式的响应

# 4. 查看 Prometheus 指标
curl http://localhost:8000/v1/metrics

# 预期: 包含 doggy_requests_total, doggy_rails_blocked_total 等指标

# 5. 查看护栏插件列表
curl http://localhost:8000/v1/admin/plugins

# 预期: 返回已注册的 13 个默认插件
```

### 7.3 运行测试套件

```bash
# 单元测试 + 安全测试
uv run pytest tests/unit/ tests/security/ -v

# 全部测试（含集成测试和 E2E）
uv run pytest tests/ -v --timeout=60
```

---

## 8. 常见问题排查

### 8.1 服务无法启动

```bash
# 检查日志
docker compose -f docker-compose.prod.yml logs doggy-gateway

# 常见原因:
# 1. 环境变量未设置 → 检查 .env.prod 文件
# 2. 中间件未就绪 → 等待 Kafka/Redis/PG 健康检查通过
# 3. 端口冲突 → 检查 8000 端口是否被占用
```

### 8.2 请求返回 401

```bash
# 原因: API Key 无效或未在数据库中注册
# 检查: Authorization header 是否正确
# 解决方案: 通过管理 API 生成新的 API Key

curl -X POST http://localhost:8000/v1/admin/apps/test-app/api-keys
```

### 8.3 护栏不生效

```bash
# 1. 检查配置是否正确加载
curl http://localhost:8000/v1/admin/plugins

# 2. 检查 NIM 服务是否可用
curl http://nim-content-safety:8000/v1/health/ready

# 3. 若 NIM 不可用，确认降级策略生效
# 查看日志中是否有 "nim_unavailable" 或 "lite_guard" 相关记录
```

### 8.4 Kafka 消息积压

```bash
# 检查 Kafka 消费者延迟
kubectl exec -n doggy-mq doggy-kafka-0 -- \
  kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group audit-consumer --describe

# 若积压严重，增加消费者实例
kubectl scale deployment/audit-consumer -n doggy-mq --replicas=4
```

### 8.5 Redis 内存不足

```bash
# 检查 Redis 内存使用
redis-cli info memory | grep used_memory_human

# 调整 maxmemory 限制
redis-cli config set maxmemory 4gb
redis-cli config set maxmemory-policy allkeys-lru
```

### 8.6 数据库连接池耗尽

```bash
# 检查当前连接数
psql -h localhost -U doggy -d doggy -c "SELECT count(*) FROM pg_stat_activity;"

# 调整连接池大小（在 doggy/db/postgres.py 中）
# write_pool: min_size=5, max_size=20
# read_pool:  min_size=10, max_size=40
```

---

## 9. 卸载

```bash
# Docker Compose
docker compose -f docker-compose.prod.yml down -v

# Kubernetes
helm uninstall doggy -n doggy-gateway
kubectl delete namespace doggy-gateway
kubectl delete namespace doggy-data
kubectl delete namespace doggy-mq
kubectl delete namespace doggy-monitoring
kubectl delete namespace nim-services
```