# Agent 路由决策流程图

可视化展示 GustoBot 多 Agent 系统的路由决策和智能子决策流程

---

## 总体架构流程

```mermaid
graph TD
    Start([用户提问]) --> LG[LangGraph START]
    LG --> Analyze[analyze_and_route_query<br/>路由分析节点]

    Analyze --> LLM{LLM 分类}
    LLM -->|成功| Valid{类型有效?}
    LLM -->|失败/无效| Heuristic[启发式 Fallback<br/>_heuristic_router]

    Valid -->|是| Route[route_query<br/>条件分支]
    Valid -->|否| Heuristic
    Heuristic --> Route

    Route -->|general-query| General[respond_to_general_query]
    Route -->|additional-query| Additional[get_additional_info]
    Route -->|kb-query| KB[create_kb_query]
    Route -->|graphrag-query<br/>text2sql-query| GraphRAG[create_research_plan]
    Route -->|image-query| Image[create_image_query]
    Route -->|file-query| File[create_file_query]

    General --> End([返回回复])
    Additional --> End
    KB --> End
    GraphRAG --> End
    Image --> End
    File --> End

    style Analyze fill:#FFE4B5
    style Route fill:#FFE4B5
    style KB fill:#B0E0E6
    style GraphRAG fill:#FFB6C1
    style Additional fill:#98FB98
```

---

## 详细决策流程

### 1. 路由分析节点（analyze_and_route_query）

```mermaid
graph TD
    Input[用户问题 + 历史消息] --> Check{OpenAI API<br/>可用?}
    Check -->|否| Error[RuntimeError]
    Check -->|是| Model[ChatOpenAI<br/>temperature=0.7]

    Model --> Prompt[ROUTER_SYSTEM_PROMPT<br/>+ 用户消息]
    Prompt --> LLM[LLM 结构化输出<br/>Router: type, logic, question]

    LLM -->|异常| FallbackDefault[默认 kb-query]
    LLM -->|成功| Validate{类型在<br/>allowed_types?}

    Validate -->|否| Heuristic[_heuristic_router<br/>关键词匹配]
    Validate -->|是| Sanitize[标准化路由结果]

    Heuristic -->|匹配| SanitizeH[返回启发式路由]
    Heuristic -->|不匹配| DefaultFallback[默认 kb-query]

    Sanitize --> Output[返回 Router]
    SanitizeH --> Output
    DefaultFallback --> Output
    FallbackDefault --> Output

    style LLM fill:#FFD700
    style Heuristic fill:#FFA500
    style Output fill:#90EE90
```

**Allowed Types**:
- `general-query`
- `additional-query`
- `kb-query`
- `graphrag-query`
- `image-query`
- `file-query`
- `text2sql-query`

**启发式关键词**:
- **GraphRAG**: "怎么做"、"如何做"、"做法"、"步骤"、"火候"、"食材"、"原料"、"需要什么"、"配料"、"用什么"
- **Text2SQL**: "统计"、"多少"、"总数"、"数量"、"排名"

---

### 2. 条件分支（route_query）

```mermaid
graph TD
    Input[AgentState + config] --> Config{config 中有<br/>image_path?}
    Config -->|是| ImagePath[create_image_query]
    Config -->|否| FileCheck{config 中有<br/>file_path?}

    FileCheck -->|是| FilePath[create_file_query]
    FileCheck -->|否| RouterType{router.type}

    RouterType -->|general-query| General[respond_to_general_query]
    RouterType -->|additional-query| Additional[get_additional_info]
    RouterType -->|kb-query| KB[create_kb_query]
    RouterType -->|graphrag-query<br/>或 text2sql-query| Research[create_research_plan]
    RouterType -->|image-query| Image[create_image_query]
    RouterType -->|file-query| File[create_file_query]
    RouterType -->|其他| ValueError[ValueError: Unknown type]

    style Config fill:#FFE4B5
    style FileCheck fill:#FFE4B5
    style RouterType fill:#FFE4B5
```

---

### 3. General-Query 流程

```mermaid
graph TD
    Input[AgentState] --> Model[ChatOpenAI<br/>temperature=0.7]
    Model --> Prompt[GENERAL_QUERY_SYSTEM_PROMPT<br/>+ router.logic]
    Prompt --> History[+ state.messages]
    History --> LLM[LLM 生成回复]
    LLM --> Response[礼貌、温暖的回复<br/>包含 emoji]
    Response --> Output[返回 messages]

    style Response fill:#98FB98
```

**特点**:
- ✅ 无需任何数据库查询
- ✅ 直接 LLM 生成
- ✅ 使用"亲～"、"厨友您好～"
- ✅ 适当 emoji

---

### 4. Additional-Query 流程（含 Guardrails）

```mermaid
graph TD
    Input[AgentState] --> Neo4j{Neo4j<br/>连接成功?}
    Neo4j -->|否| NoGraph[neo4j_graph = None]
    Neo4j -->|是| Graph[获取 Graph Schema]

    NoGraph --> Scope[加载服务范围描述]
    Graph --> Scope

    Scope --> GuardrailPrompt[GUARDRAILS_SYSTEM_PROMPT<br/>+ scope_description<br/>+ graph_context]
    GuardrailPrompt --> GuardrailLLM[LLM 结构化输出<br/>AdditionalGuardrailsOutput]

    GuardrailLLM --> Decision{decision}

    Decision -->|end| Reject[礼貌拒绝<br/>"不太属于菜谱范围"]
    Decision -->|proceed| InfoPrompt[GET_ADDITIONAL_SYSTEM_PROMPT<br/>+ router.logic]

    InfoPrompt --> AskLLM[LLM 生成补充询问]
    AskLLM --> AskOutput[友好询问用户]

    Reject --> Output[返回 messages]
    AskOutput --> Output

    style Decision fill:#FFD700
    style Reject fill:#FF6B6B
    style AskOutput fill:#98FB98
```

**Guardrails 判断逻辑**:

| 问题 | 决策 | 原因 |
|-----|------|------|
| "我想做菜" | `proceed` | 菜谱相关但信息不足 |
| "这个菜怎么做好吃" | `proceed` | 菜谱相关但缺菜名 |
| "今天天气怎么样" | `end` | 与菜谱无关 |
| "我肚子疼吃什么药" | `end` | 医疗诊断（边界） |

---

### 5. KB-Query 流程（向量知识库多工具）

```mermaid
graph TD
    Input[AgentState + config] --> Question{问题<br/>非空?}
    Question -->|否| EmptyError[提示:请告诉我具体问题]
    Question -->|是| Config[解析 config 参数<br/>top_k, similarity_threshold, filter_expr]

    Config --> LLM[初始化 ChatOpenAI<br/>temperature=0.3]
    LLM --> Service[初始化 KnowledgeService]
    Service --> External[检查外部搜索配置]

    External --> Workflow[create_kb_multi_tool_workflow]

    Workflow --> SubGraph[KB Multi-tool Workflow]
    SubGraph --> SubGuardrails[子节点: Guardrails]
    SubGuardrails --> SubRouter[子节点: Router]
    SubRouter --> SubMilvus[子节点: Milvus Query]
    SubRouter --> SubPG[子节点: pgvector Query]
    SubMilvus --> SubReranker[子节点: Reranker]
    SubPG --> SubReranker
    SubReranker --> SubFinalizer[子节点: Finalizer]

    SubFinalizer --> Response[返回 answer]

    Workflow -->|异常| Fallback[Fallback: 直接 KB 查询]
    Fallback --> DirectKB[create_knowledge_query_node]
    DirectKB --> FallbackResponse[返回部分结果]

    Response --> Output[返回 messages]
    FallbackResponse --> Output
    EmptyError --> Output

    style Workflow fill:#B0E0E6
    style SubGraph fill:#87CEEB
    style Fallback fill:#FFA500
```

#### KB Multi-tool Workflow 子流程

```mermaid
graph TD
    Start[输入: question, history] --> Guardrails[Guardrails 节点]
    Guardrails --> GuardCheck{相关性检查}

    GuardCheck -->|不相关| Reject[返回:不在服务范围]
    GuardCheck -->|相关| Router[Router 节点]

    Router --> Analyze[LLM 分析问题类型]
    Analyze --> Select{选择工具}

    Select -->|简单问题| OnlyMilvus[tools: milvus]
    Select -->|复杂问题| BothSources[tools: milvus, pgvector]
    Select -->|需要外部| WithExternal[tools: milvus, external]

    OnlyMilvus --> ExecuteMilvus[Milvus Query 节点]
    BothSources --> ExecuteMilvus
    BothSources --> ExecutePG[pgvector Query 节点]
    WithExternal --> ExecuteMilvus
    WithExternal --> ExecuteExt[External Search 节点]

    ExecuteMilvus --> Collect[收集结果]
    ExecutePG --> Collect
    ExecuteExt --> Collect

    Collect --> Rerank{结果 > 1 源?}
    Rerank -->|是| RerankerNode[Reranker 节点<br/>Cohere/Jina/Voyage/BGE]
    Rerank -->|否| DirectFinal[直接传递]

    RerankerNode --> Finalizer[Finalizer 节点]
    DirectFinal --> Finalizer

    Finalizer --> Generate[LLM 生成连贯回答]
    Generate --> Output[返回 answer + sources]
    Reject --> Output

    style Router fill:#FFD700
    style RerankerNode fill:#FF69B4
    style Finalizer fill:#90EE90
```

**工具选择逻辑**（Router 节点内部）:

| 问题特征 | 选择工具 | 理由 |
|---------|---------|------|
| 简单历史查询 | `[milvus]` | 单一来源足够 |
| 复杂文化背景 | `[milvus, pgvector]` | 多源融合提高准确性 |
| 罕见问题 | `[milvus, external]` | 需要外部搜索补充 |
| 高优先级 | `[milvus, pgvector, external]` | 全面检索 |

**Reranker 流程**:
1. 合并所有来源结果（如 Milvus 5条 + pgvector 3条 = 8条）
2. 调用 Reranker API（Cohere/Jina/Voyage/BGE）
3. 重新排序并返回 top_k（如5条）
4. 传递给 Finalizer

---

### 6. GraphRAG-Query 流程（图谱多工具）

```mermaid
graph TD
    Input[AgentState] --> Model[初始化 ChatOpenAI<br/>temperature=0.7]
    Model --> Neo4j{Neo4j<br/>连接成功?}
    Neo4j -->|否| NoNeo4j[neo4j_graph = None]
    Neo4j -->|是| GraphOK[获取 Neo4j 连接]

    NoNeo4j --> Retriever[初始化 RecipeCypherRetriever]
    GraphOK --> Retriever

    Retriever --> Tools[定义工具 schemas:<br/>- cypher_query<br/>- predefined_cypher<br/>- microsoft_graphrag_query<br/>- text2sql_query]

    Tools --> PredefinedDict[加载 predefined_cypher_dict]
    PredefinedDict --> Scope[加载服务范围描述]

    Scope --> Workflow[create_multi_tool_workflow]

    Workflow --> SubGraph[Multi-tool Workflow]
    SubGraph --> SubPlanner[子节点: Planner]
    SubPlanner --> SubTools[子节点: Tool Executors]
    SubTools --> SubFinalizer[子节点: Finalizer]

    SubFinalizer --> Response[返回 answer]
    Response --> Output[返回 messages]

    style Workflow fill:#FFB6C1
    style SubGraph fill:#FF69B4
```

#### Multi-tool Workflow 子流程（核心智能决策）

```mermaid
graph TD
    Start[输入: question, route_type] --> Planner[Planner 节点]

    Planner --> Analyze[LLM 分析问题]
    Analyze --> Intent{问题意图}

    Intent -->|菜谱做法| Predefined[选择: predefined_cypher]
    Intent -->|通用查询| Dynamic[选择: cypher_query]
    Intent -->|技巧推理| GraphRAG[选择: microsoft_graphrag_query]
    Intent -->|统计数字| Text2SQL[选择: text2sql_query]
    Intent -->|复杂问题| Multiple[选择多个工具]

    Predefined --> Execute1[Tool Executor]
    Dynamic --> Execute2[Tool Executor]
    GraphRAG --> Execute3[Tool Executor]
    Text2SQL --> Execute4[Tool Executor]
    Multiple --> Execute5[Tool Executor<br/>并行执行]

    Execute1 --> Tool1[Predefined Cypher 执行]
    Execute2 --> Tool2[Cypher Query 执行]
    Execute3 --> Tool3[GraphRAG 执行]
    Execute4 --> Tool4[Text2SQL 执行]
    Execute5 --> Tool2
    Execute5 --> Tool3

    Tool1 --> Template[匹配预定义模板]
    Template --> Neo4jExec1[执行 Neo4j 查询]

    Tool2 --> Retrieve[检索相似 Cypher 示例]
    Retrieve --> LLMGenerate[LLM 生成 Cypher]
    LLMGenerate --> Validate{语法验证}
    Validate -->|失败| Retry[重试生成<br/>最多1次]
    Validate -->|成功| Neo4jExec2[执行 Neo4j 查询]
    Retry --> Validate

    Tool3 --> Mode{GraphRAG 模式}
    Mode -->|local| LocalSearch[局部搜索<br/>快速]
    Mode -->|global| GlobalSearch[全局搜索<br/>全面]
    LocalSearch --> GraphResult[图推理结果]
    GlobalSearch --> GraphResult

    Tool4 --> Schema[获取数据库表结构]
    Schema --> LLMSQL[LLM 生成 SQL]
    LLMSQL --> MySQLExec[执行 MySQL 查询]

    Neo4jExec1 --> Collect[收集所有工具结果]
    Neo4jExec2 --> Collect
    GraphResult --> Collect
    MySQLExec --> Collect

    Collect --> Finalizer[Finalizer 节点]
    Finalizer --> Merge[合并多源数据]
    Merge --> Deduplicate[去重和排序]
    Deduplicate --> LLMAnswer[LLM 生成连贯回答]
    LLMAnswer --> Source[标注数据来源]
    Source --> Output[返回 answer]

    style Planner fill:#FFD700
    style Tool2 fill:#87CEEB
    style Tool3 fill:#FF69B4
    style Finalizer fill:#90EE90
```

**Planner 工具选择逻辑**:

| 问题示例 | 选择工具 | 原因 |
|---------|---------|------|
| "红烧肉怎么做" | `[predefined_cypher]` | 高频场景，有预定义模板 |
| "什么菜含牛肉" | `[cypher_query]` | 通用查询，动态生成 |
| "怎么判断鱼熟了" | `[microsoft_graphrag_query]` | 需要推理经验 |
| "数据库有多少道菜" | `[text2sql_query]` | 统计查询 |
| "炒青菜怎么保持翠绿" | `[cypher_query, microsoft_graphrag_query]` | 方法 + 技巧 |
| "为什么红烧肉发柴" | `[cypher_query, microsoft_graphrag_query]` | 正确做法 + 原因推理 |
| "什么菜适合感冒吃" | `[cypher_query, microsoft_graphrag_query]` | 图谱关系 + 食疗推理 |
| "麻辣口味的菜有多少" | `[cypher_query, text2sql_query]` | 图谱查询 + 统计 |

**Cypher 生成和验证**:

```mermaid
graph TD
    Input[用户问题] --> Retriever[RecipeCypherRetriever]
    Retriever --> Search[向量检索相似 Cypher 示例]
    Search --> Examples[返回 top 3 示例]

    Examples --> Prompt[构建 Few-shot Prompt:<br/>- Graph Schema<br/>- 3个示例<br/>- 用户问题]

    Prompt --> LLM[LLM 生成 Cypher]
    LLM --> Syntax[语法验证]

    Syntax --> Valid{验证结果}
    Valid -->|失败| Count{重试次数 < 1?}
    Count -->|是| Retry[重新生成]
    Count -->|否| Error[返回错误]

    Valid -->|成功| Execute[执行 Neo4j 查询]
    Execute --> Result[返回结果]

    Retry --> LLM

    style LLM fill:#FFD700
    style Syntax fill:#FFA500
    style Execute fill:#90EE90
```

**GraphRAG 模式选择**:

| 问题类型 | 模式 | 理由 |
|---------|------|------|
| 单个菜谱相关 | `local` | 局部搜索快速 |
| 菜系比较 | `global` | 需要全局视角 |
| 食疗推荐 | `global` | 跨多个实体 |
| 技巧查询 | `local` | 聚焦单一主题 |

---

### 7. Image-Query 流程

```mermaid
graph TD
    Input[AgentState + config] --> Path{config 中有<br/>image_path?}
    Path -->|否| CheckKeyword{问题中有<br/>生成关键词?}
    Path -->|是| Exist{文件存在?}

    CheckKeyword -->|是| Generation[图片生成流程]
    CheckKeyword -->|否| NoPath[提示:请重新上传]

    Exist -->|否| NotFound[提示:请重新上传]
    Exist -->|是| Recognition[图片识别流程]

    Generation --> EnhancePrompt[LLM 优化提示词<br/>IMAGE_GENERATION_ENHANCE_PROMPT]
    EnhancePrompt --> CogView[CogView-4 API 调用]
    CogView --> ImageURL[返回图片 URL]
    ImageURL --> Success[成功提示 + URL]

    Recognition --> Compress[压缩图片<br/>max 1024px, JPEG quality=85]
    Compress --> Base64[转换为 base64]
    Base64 --> Vision[Vision API 调用<br/>gpt-4o-vision]
    Vision --> Description[图片描述]
    Description --> ImagePrompt[GET_IMAGE_SYSTEM_PROMPT<br/>+ description]
    ImagePrompt --> LLM[LLM 生成回复]
    LLM --> Answer[基于描述的专业回答]

    Success --> Output[返回 messages]
    Answer --> Output
    NoPath --> Output
    NotFound --> Output

    style Generation fill:#FF69B4
    style Recognition fill:#87CEEB
```

**生成关键词**: "生成"、"画"、"创建"、"制作图片"、"做一张"、"给我一张"、"来一张"

---

### 8. File-Query 流程

```mermaid
graph TD
    Input[AgentState + config] --> Path{config 中有<br/>file_path?}
    Path -->|否| NoPath[提示:请提供文件路径]
    Path -->|是| Exist{文件存在?}

    Exist -->|否| NotFound[提示:未找到文件]
    Exist -->|是| Size{文件大小 <<br/>MAX_MB?}

    Size -->|否| TooBig[提示:文件过大]
    Size -->|是| Type{文件类型}

    Type -->|.xlsx/.xls| Excel[Excel 处理流程]
    Type -->|.txt/.md/.csv/.log| Text[文本文件流程]
    Type -->|.json| JSON[JSON 文件流程]
    Type -->|其他| Unsupported[提示:不支持的格式]

    Excel --> ExternalCheck{外部服务<br/>配置?}
    ExternalCheck -->|否| NoService[提示:未配置 Ingest Service]
    ExternalCheck -->|是| CallAPI[调用外部 Ingest API]
    CallAPI --> ExcelSuccess[提示:Excel 导入中]

    Text --> Read[读取文本内容]
    JSON --> Parse[解析 JSON]
    Parse --> Stringify[转为字符串]
    Stringify --> Read

    Read --> DocID[生成 doc_id]
    DocID --> AddKB[添加到知识库<br/>KnowledgeService.add_document]
    AddKB --> Success{添加成功?}

    Success -->|否| Failed[提示:保存失败]
    Success -->|是| Query[create_knowledge_query_node]
    Query --> Answer[返回相关回答]

    Answer --> Output[返回 messages]
    ExcelSuccess --> Output
    Failed --> Output
    NoPath --> Output
    NotFound --> Output
    TooBig --> Output
    Unsupported --> Output
    NoService --> Output

    style Excel fill:#FF69B4
    style Text fill:#87CEEB
    style Query fill:#90EE90
```

**支持的文件类型**:
- 文本: `.txt`, `.md`, `.csv`, `.log`
- JSON: `.json`
- Excel: `.xlsx`, `.xls`（需要外部 Ingest Service）

---

## 关键决策点总结

### 🎯 决策点1: 路由分类（LLM + 启发式）

| 层级 | 方法 | 输入 | 输出 |
|-----|------|------|------|
| 第1层 | LLM 分类 | 问题 + ROUTER_SYSTEM_PROMPT | Router(type, logic, question) |
| 第2层 | 启发式关键词 | 问题文本 | 匹配的路由类型 |
| 第3层 | 默认 Fallback | - | kb-query |

### 🎯 决策点2: Guardrails（Additional-Query）

| 输入 | 决策 | 输出 |
|-----|------|------|
| 菜谱相关但信息不足 | `proceed` | 询问补充信息 |
| 与菜谱无关 | `end` | 礼貌拒绝 |

### 🎯 决策点3: KB Multi-tool Router

| 问题特征 | 工具选择 | 后续处理 |
|---------|---------|---------|
| 简单查询 | `[milvus]` | 直接返回 |
| 复杂查询 | `[milvus, pgvector]` | Reranker 融合 |
| 罕见问题 | `[milvus, external]` | 外部搜索补充 |

### 🎯 决策点4: GraphRAG Planner

| 问题意图 | 工具选择 | 数据来源 |
|---------|---------|---------|
| 高频做法 | `[predefined_cypher]` | Neo4j (预定义模板) |
| 通用查询 | `[cypher_query]` | Neo4j (LLM 生成) |
| 推理技巧 | `[microsoft_graphrag_query]` | LightRAG 图推理 |
| 统计数字 | `[text2sql_query]` | MySQL |
| 复杂问题 | 多个工具组合 | 多源融合 |

### 🎯 决策点5: Cypher 生成方式

| 场景 | 方式 | 优势 |
|-----|------|------|
| 高频场景 | Predefined Cypher | 快速、准确 |
| 通用查询 | LLM 动态生成 + Few-shot | 灵活、覆盖广 |
| 语法验证失败 | 重试1次 | 容错性 |

### 🎯 决策点6: GraphRAG 模式

| 问题范围 | 模式 | 特点 |
|---------|------|------|
| 局部问题 | `local` | 快速、聚焦 |
| 全局问题 | `global` | 全面、深度 |

### 🎯 决策点7: Reranker 触发

| 条件 | 是否触发 |
|-----|---------|
| 结果来自单一来源 | ❌ 不触发 |
| 结果来自多个来源 | ✅ 触发 |

### 🎯 决策点8: Finalizer 融合

| 输入 | 处理 | 输出 |
|-----|------|------|
| 单一工具结果 | 直接格式化 | 结构化回答 |
| 多个工具结果 | 合并 + 去重 + LLM 融合 | 连贯回答 + 来源标注 |

---

## 使用说明

1. **阅读顺序**:
   - 先看"总体架构流程"了解全局
   - 再看"详细决策流程"理解每个路由
   - 最后看"关键决策点总结"掌握核心逻辑

2. **测试时对照**:
   - 运行测试脚本时，对照流程图观察日志
   - 验证实际执行路径是否与预期一致

3. **问题排查**:
   - 路由错误 → 检查"决策点1"
   - 拒答问题 → 检查"决策点2"
   - 检索质量差 → 检查"决策点3"
   - 工具选择不当 → 检查"决策点4"

4. **优化方向**:
   - 提高路由准确性 → 优化 ROUTER_SYSTEM_PROMPT
   - 提高检索质量 → 调整 Reranker 配置
   - 提高推理能力 → 优化 Planner prompt
   - 提高回答质量 → 优化 Finalizer prompt

---

**配套文档**:
- 测试问题集: `tests/test_agent_routing_questions.md`
- 测试指南: `docs/agent_routing_test_guide.md`
- 快速参考: `docs/agent_routing_quick_reference.md`
