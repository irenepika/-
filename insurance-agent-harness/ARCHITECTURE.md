# Insurance Agent Harness - 技术架构图

## 1. 系统全景架构图

```mermaid
flowchart TB
    subgraph Realtime["🔵 实时对话链路 (Real-time Runtime Loop)"]
        User[👤 用户输入] -->|1| Memory1[(📊 Memory<br/>User Profile + DISC)]
        Memory1 -->|2| Core[⚙️ Harness Core Loop<br/>主循环编排器]
        Core -->|3| Guard[🛡️ Guardrails<br/>合规拦截器]
        Guard -->|4| Sales[🤖 Sales Actor<br/>GPT-4o]
        Sales -->|5| Tools[🔧 Tool Registry<br/>工具注册表]
        Tools -->|6| Calc[💰 Mock API<br/>保费计算/条款检索]
        Calc -->|7| Sales
        Sales -->|8| Response[💬 回复用户]
    end

    subgraph Async["🟠 异步状态更新链路 (Async State Tracking)"]
        Response -.->|9| Window[📝 对话窗口<br/>最近3-5轮]
        Window -->|10| Intent[🎯 Intent Classifier<br/>GPT-4o-mini]
        Intent -->|11| State[🌡️ 客温 + 漏斗状态]
        State -.->|12| Memory2[(📊 Memory<br/>状态更新)]
    end

    subgraph Offline["🟢 离线批处理链路 (Offline Batch & Evals)"]
        Logs[📜 历史日志] -->|13| Profiler[🔬 Offline Profiler<br/>DISC分析器]
        Profiler -->|14| DISC[📈 DISC 报告<br/>性格侧写]
        DISC -.->|15| DB[(💾 DB/Memory)]

        Tests[📋 测试集<br/>JSONL] -->|16| Evals[⚡ Evals Engine<br/>评测引擎]
        Evals -->|17| Judge[⚖️ Judge Evaluator<br/>LLM-as-a-Judge]
        Judge -->|18| Report[📊 Benchmark 报告<br/>JSON/MD/HTML]
    end

    User -.->|异步触发| Async

    style Realtime fill:#e3f2fd,stroke:#2196f3
    style Async fill:#fff3e0,stroke:#ff9800
    style Offline fill:#e8f5e9,stroke:#4caf50
```

## 2. 模块详细架构图

```mermaid
graph TB
    subgraph Agents["🤖 Agents Layer - 核心大模型执行节点"]
        SalesActor[Sales Actor<br/>━━━━━━━━━━<br/>• 模型: GPT-4o<br/>• 职责: 话术生成<br/>• 特性: 个性化风格]
        IntentClassifier[Intent Classifier<br/>━━━━━━━━━━<br/>• 模型: GPT-4o-mini<br/>• 职责: 状态判定<br/>• 特性: 异步执行]
        JudgeEvaluator[Judge Evaluator<br/>━━━━━━━━━━<br/>• 模型: GPT-4o<br/>• 职责: 离线打分<br/>• 特性: 多维评测]
    end

    subgraph Harness["⚙️ Harness Layer - 编排基座"]
        CoreLoop[Core Loop<br/>━━━━━━━━━━<br/>• 主循环编排<br/>• 流程控制<br/>• 异步任务调度]
        Guardrails[Guardrails<br/>━━━━━━━━━━<br/>• 关键词过滤<br/>• 合规检查<br/>• 0延迟拦截]
        Memory[Memory Manager<br/>━━━━━━━━━━<br/>• 用户画像缓存<br/>• 对话历史<br/>• 状态管理]
        ToolRegistry[Tool Registry<br/>━━━━━━━━━━<br/>• 工具注册<br/>• Schema生成<br/>• Function Calling]
    end

    subgraph Tools["🔧 Tools Layer - 外部工具"]
        Calculator[Insurance Calculator<br/>━━━━━━━━━━<br/>保费计算]
        Retriever[Clause Retriever<br/>━━━━━━━━━━<br/>条款检索]
    end

    subgraph Offline["📊 Offline Layer - 离线处理"]
        DataLoader[Data Loader<br/>━━━━━━━━━━<br/>历史数据加载]
        DISCAnalyzer[DISC Analyzer<br/>━━━━━━━━━━<br/>性格侧写生成]
    end

    subgraph Evals["⚖️ Evals Layer - 评测系统"]
        ModelGraded[Model Graded<br/>━━━━━━━━━━<br/>LLM-as-a-Judge]
        ExactMatch[Exact Match<br/>━━━━━━━━━━<br/>规则匹配]
        BatchRunner[Batch Runner<br/>━━━━━━━━━━<br/>批量评测]
    end

    subgraph Schemas["📋 Schemas Layer - 数据契约"]
        StateModels[State Models<br/>━━━━━━━━━━<br/>UserProfile<br/>FunnelState]
        EvalMetrics[Eval Metrics<br/>━━━━━━━━━━<br/>评测结果定义]
    end

    CoreLoop --> SalesActor
    CoreLoop --> Guardrails
    CoreLoop --> Memory
    CoreLoop --> IntentClassifier

    SalesActor --> ToolRegistry
    ToolRegistry --> Calculator
    ToolRegistry --> Retriever

    Memory --> StateModels
    JudgeEvaluator --> EvalMetrics

    DataLoader --> DISCAnalyzer
    BatchRunner --> ModelGraded
    BatchRunner --> ExactMatch

    style Agents fill:#bbdefb
    style Harness fill:#ffcc80
    style Tools fill:#c8e6c9
    style Offline fill:#f8bbd0
    style Evals fill:#d1c4e9
    style Schemas fill:#ffecb3
```

## 3. 数据流转时序图

```mermaid
sequenceDiagram
    participant U as 👤 用户
    participant CL as ⚙️ Core Loop
    participant M as 📊 Memory
    participant G as 🛡️ Guardrails
    participant SA as 🤖 Sales Actor
    participant T as 🔧 Tools
    participant IC as 🎯 Intent Classifier
    participant DB as 💾 Database

    U->>CL: 1. 发送消息
    CL->>M: 2. 获取用户画像<br/>(DISC类型)
    M-->>CL: UserProfile

    CL->>G: 3. 合规检查
    G-->>CL: ✓ 通过 / ✗ 拦截

    CL->>SA: 4. 生成话术<br/>+ 画像 + 历史
    SA->>T: 5. 调用工具<br/>(如需要)
    T-->>SA: 计算结果
    SA-->>CL: 6. 返回回复

    CL->>M: 7. 保存对话历史
    CL-->>U: 8. 实时回复

    Note over CL,DB: 🔄 异步状态更新(非阻塞)
    CL->>IC: 9. 提交对话窗口
    IC->>IC: 10. 分析客温+漏斗
    IC->>DB: 11. 更新状态

    U->>CL: 12. 下一轮对话
    CL->>M: 13. 获取更新后的状态
```

## 4. 部署架构图

```mermaid
graph TB
    subgraph Client["📱 客户端层"]
        Web[Web App]
        Mobile[Mobile App]
    end

    subgraph API["🌐 API 网关层"]
        Gateway[API Gateway<br/>━━━━━━━━━━<br/>• 负载均衡<br/>• 认证鉴权<br/>• 限流熔断]
    end

    subgraph Runtime["⚡ 运行时层"]
        Agent1[Agent Instance 1<br/>GPT-4o]
        Agent2[Agent Instance 2<br/>GPT-4o]
        AgentN[Agent Instance N<br/>GPT-4o]
    end

    subgraph Async["🔄 异步处理层"]
        Queue[消息队列<br/>━━━━━━━━━━<br/>Redis/RabbitMQ]
        Worker[Intent Classifier<br/>Workers]
    end

    subgraph Storage["💾 存储层"]
        Redis[(Redis<br/>━━━━━━━━━━<br/>热数据缓存)]
        PG[(PostgreSQL<br/>━━━━━━━━━━<br/>持久化存储)]
        S3[(S3/OSS<br/>━━━━━━━━━━<br/>日志存储)]
    end

    subgraph Offline["📊 离线处理层"]
        Profiler[DISC Profiler<br/>定时任务]
        Evals[Evaluation<br/>定时任务]
    end

    Web --> Gateway
    Mobile --> Gateway

    Gateway --> Agent1
    Gateway --> Agent2
    Gateway --> AgentN

    Agent1 --> Queue
    Agent2 --> Queue
    AgentN --> Queue

    Queue --> Worker

    Agent1 --> Redis
    Agent2 --> Redis
    AgentN --> Redis

    Worker --> PG
    Agent1 --> PG
    Agent2 --> PG
    AgentN --> PG

    Agent1 --> S3
    Agent2 --> S3
    AgentN --> S3

    PG --> Profiler
    PG --> Evals
    S3 --> Profiler
    S3 --> Evals

    style Client fill:#e3f2fd
    style API fill:#fff3e0
    style Runtime fill:#f3e5f5
    style Async fill:#e0f2f1
    style Storage fill:#fff9c4
    style Offline fill:#fce4ec
```

## 5. 核心组件关系图

```mermaid
graph LR
    subgraph Input["输入层"]
        UI[用户界面]
        API[API 接口]
    end

    subgraph Orchestration["编排层"]
        CoreLoop[Core Loop<br/>主控制器]
    end

    subgraph Intelligence["智能层"]
        SalesActor[Sales Actor<br/>话术生成]
        IntentClassifier[Intent Classifier<br/>意图识别]
        JudgeEvaluator[Judge Evaluator<br/>质量评测]
    end

    subgraph Protection["防护层"]
        Guardrails[Guardrails<br/>合规拦截]
        Schemas[Pydantic Schemas<br/>数据验证]
    end

    subgraph Enhancement["增强层"]
        ToolRegistry[Tool Registry<br/>工具管理]
        Calculator[Calculator<br/>保费计算]
        Retriever[Retriever<br/>条款检索]
    end

    subgraph Storage["存储层"]
        Memory[Memory<br/>内存管理]
        DB[(数据库)]
        Logs[日志系统]
    end

    subgraph Analysis["分析层"]
        Profiler[DISC Analyzer<br/>画像生成]
        Evals[Evals Engine<br/>评测系统]
    end

    UI --> CoreLoop
    API --> CoreLoop

    CoreLoop --> SalesActor
    CoreLoop --> IntentClassifier

    SalesActor --> Guardrails
    SalesActor --> Schemas

    SalesActor --> ToolRegistry
    ToolRegistry --> Calculator
    ToolRegistry --> Retriever

    CoreLoop --> Memory
    IntentClassifier --> Memory

    Memory --> DB
    CoreLoop --> Logs

    Logs --> Profiler
    Logs --> Evals

    SalesActor --> JudgeEvaluator

    style Input fill:#e1f5fe
    style Orchestration fill:#fff3e0
    style Intelligence fill:#f3e5f5
    style Protection fill:#ffebee
    style Enhancement fill:#e8f5e9
    style Storage fill:#fffde7
    style Analysis fill:#fce4ec
```

## 6. 技术栈架构图

```mermaid
graph TB
    subgraph Stack["技术栈"]
        subgraph LLM["大模型层"]
            GPT4[GPT-4o<br/>━━━━━━━━━━<br/>Sales Actor<br/>Judge Evaluator]
            GPT4Mini[GPT-4o-mini<br/>━━━━━━━━━━<br/>Intent Classifier]
        end

        subgraph Framework["框架层"]
            Pydantic[Pydantic<br/>━━━━━━━━━━<br/>数据验证]
            OpenAI[OpenAI SDK<br/>━━━━━━━━━━<br/>LLM调用]
            AsyncIO[AsyncIO<br/>━━━━━━━━━━<br/>异步处理]
        end

        subgraph Storage["存储层"]
            FileSystem[文件系统<br/>━━━━━━━━━━<br/>日志/画像]
            Redis[Redis<br/>━━━━━━━━━━<br/>缓存]
            PG[PostgreSQL<br/>━━━━━━━━━━<br/>关系数据]
        end

        subgraph Monitoring["监控层"]
            Logs[结构化日志<br/>━━━━━━━━━━<br/>JSONL格式]
            Metrics[性能指标<br/>━━━━━━━━━━<br/>延迟/吞吐]
            Evals[Evals<br/>━━━━━━━━━━<br/>质量评测]
        end
    end

    LLM --> Framework
    Framework --> Storage
    Framework --> Monitoring

    style LLM fill:#e3f2fd
    style Framework fill:#fff3e0
    style Storage fill:#e8f5e9
    style Monitoring fill:#f3e5f5
```

## 7. 安全与合规架构

```mermaid
graph TB
    subgraph Security["安全与合规层"]
        subgraph InputSecurity["输入安全"]
            Sanitize[输入清洗<br/>━━━━━━━━━━<br/>PII过滤]
            GuardrailsInput[Guardrails<br/>━━━━━━━━━━<br/>关键词拦截]
            RateLimit[限流<br/>━━━━━━━━━━<br/>防刷]
        end

        subgraph OutputSecurity["输出安全"]
            GuardrailsOutput[输出检查<br/>━━━━━━━━━━<br/>夸大表述检测]
            RiskWarning[风险提示<br/>━━━━━━━━━━<br/>强制披露]
            AuditLog[审计日志<br/>━━━━━━━━━━<br/>完整溯源]
        end

        subgraph DataSecurity["数据安全"]
            Encryption[加密存储<br/>━━━━━━━━━━<br/>敏感信息]
            AccessControl[访问控制<br/>━━━━━━━━━━<br/>权限管理]
            Retention[数据保留<br/>━━━━━━━━━━<br/>合规清理]
        end
    end

    InputSecurity --> OutputSecurity
    OutputSecurity --> DataSecurity

    style InputSecurity fill:#ffebee
    style OutputSecurity fill:#fff3e0
    style DataSecurity fill:#e8f5e9
```

---

## 架构设计亮点

### 🎯 三层解耦
- **实时层**：零延迟响应，用户体验优先
- **异步层**：后台分析，不阻塞主流程
- **离线层**：深度分析，持续优化

### 🛡️ 防幻觉设计
- **Pydantic 强类型**：所有数据结构严格定义
- **双模式评测**：规则 + LLM 双重保障
- **完整审计**：每次交互可溯源

### ⚡ 高性能
- **轻量级 Guardrails**：Regex 实现零延迟
- **异步状态更新**：后台任务不阻塞
- **智能缓存**：减少重复计算

### 🔧 可扩展
- **模块化设计**：组件独立，易于替换
- **工具注册表**：轻松集成新工具
- **评测框架**：支持自定义维度
