# 低代码用例自动生成系统设计

## 需求

假如我有个低代码平台, 存储了历史上的大量低代码用例. 低代码用例是用json描述的, 构成一个
{
	name:
	desc:
	edges: [{}, ...]
	nodes: [{}, ...]
}
的图, 每个node结构非常复杂, 大致有节点名称, 请求schema参数, 响应schema, 参数提取, 设置变量, 响应断言.

举个例子, 聊天用例
1. 用户a加用户b好友, 发起个请求, 判断请求响应结果, 形成一个节点
2. 用户b确认, 也发起一个请求, 判断请求响应结果, 形成一个节点,
3. 用户a发消息给用户b, 发起个请求, 判断请求响应结果, 形成一个节点
4. 用户b拉取消息, 从响应中得到消息提取参数到变量中
5. 用户b再根据变量构造消息, 发给用户a
6. 用户a拉取消息, 提取参数, 做断言

这是一个直线流程的用例.

或者还有个视频会议的例子
1. a拉b加入视频会议
2. ....


接口的是有限的, 每个接口的url以及请求和响应的schema也是确定的; 不过它们都被包含在几千个用例的上万个节点当中了.
每个节点都有比较清晰的描述, 请求响应都是json, 并且不少json有schema说明字段含义.
发起的请求本身也包含了比较清晰的信息, 所有这些构成一个节点的json体. 多个节点再构成一个图, 用来表示整个用例

目前有数千个用例, 我想把他们放到一个知识库里, 或者某个支持搜索的库里面.
用LLM来构造一个自动编写用例的能力

比如一个新用例是, ab互加好友后, 进行视频会议. 希望大模型自动构造出一个低代码用例json.

请给出一个设计思路
1. 怎么存储历史用例, 历史用例是一个一个用例存, 还是一个一个节点存
2. 在构造低代码用例json时, agent的作用在哪里体现, 它需要参与哪些步骤?
3. 可能会遇到哪些问题?



补充
1. 我对node的结构没有写很多, 但本身非常复杂, 包含大量的嵌套的map或list, 并且格式要求非常严格, 这样才能正确解析成一个代码中的不同类.
2. 我要知道你准备用的存储架构示意, 存什么, 存在哪里, 怎么查?
3. agent需要怎么查存储的历史用例, 再构造出新用例?
4. 我理解希望大模型能够生成出一个用例的json表示, 我的低代码执行引擎就能加载这个json了.
5. 用例的json图不一定是一条直线, 也可以有循环, 分支, 这个文档考虑到了吗


## 一、存储架构设计

### 1.1 存储策略：混合存储（用例级 + 节点级）

**推荐方案：双层存储架构**

#### 第一层：用例级存储（PostgreSQL/MongoDB）
```
存储内容：
- 用例完整JSON（name, desc, edges, nodes）
- 用例元数据（用例ID、创建时间、标签、分类等）
- 用例级别的向量嵌入（基于name + desc + 所有节点描述）

存储位置：关系型数据库或文档数据库
查询方式：
- 精确查询：通过用例ID、标签等
- 语义查询：通过向量相似度搜索（用例整体语义）
```

#### 第二层：节点级存储（向量数据库 + 索引）
```
存储内容：
- 节点完整JSON（包含所有复杂嵌套结构）
- 节点元数据（节点ID、所属用例ID、节点类型、接口URL等）
- 节点级别的向量嵌入（基于节点描述 + 请求schema + 响应schema）
- 接口schema索引（URL -> 请求/响应schema映射）

存储位置：
- 向量数据库：Milvus/Chroma/Pinecone（用于语义搜索）
- 索引数据库：Elasticsearch/PostgreSQL（用于精确查询）

查询方式：
- 语义查询：通过向量相似度搜索（节点功能语义）
- 精确查询：通过接口URL、节点类型等
- Schema查询：通过请求/响应schema结构匹配
```

### 1.2 存储架构示意图

```
┌─────────────────────────────────────────────────────────┐
│                   用例级存储层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ PostgreSQL   │  │ 向量数据库    │  │ 用例元数据    │ │
│  │ (完整用例JSON)│  │ (用例向量)    │  │ (标签/分类)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 关联查询
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   节点级存储层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 向量数据库    │  │ Elasticsearch │  │ Schema索引    │ │
│  │ (节点向量)    │  │ (节点元数据)  │  │ (URL->Schema) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 1.3 具体存储内容

#### 用例表（use_cases）
```json
{
  "case_id": "uuid",
  "name": "用户互加好友并聊天",
  "desc": "用户a加用户b好友，然后进行聊天交互",
  "full_json": {...},  // 完整用例JSON
  "tags": ["好友", "聊天"],
  "category": "社交",
  "created_at": "timestamp",
  "vector_embedding": [0.1, 0.2, ...]  // 用例级向量
}
```

#### 节点表（nodes）
```json
{
  "node_id": "uuid",
  "case_id": "uuid",  // 关联到用例
  "node_name": "用户a加好友",
  "node_json": {...},  // 完整节点JSON（包含所有嵌套结构）
  "api_url": "/api/friend/add",
  "request_schema": {...},
  "response_schema": {...},
  "description": "用户a发起加好友请求",
  "vector_embedding": [0.3, 0.4, ...]  // 节点级向量
}
```

#### 接口Schema索引表（api_schemas）
```json
{
  "api_url": "/api/friend/add",
  "method": "POST",
  "request_schema": {...},
  "response_schema": {...},
  "description": "添加好友接口",
  "example_nodes": ["node_id1", "node_id2"]  // 使用该接口的节点ID列表
}
```

## 二、Agent工作流程设计

### 2.1 Agent架构：多Agent协作系统

```
┌─────────────────────────────────────────────────────────┐
│                   用户输入                               │
│  "ab互加好友后，进行视频会议"                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Agent 1: 需求理解与分解Agent                    │
│  功能：解析用户需求，分解为子任务                        │
│  输出：任务列表 ["加好友", "视频会议"]                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Agent 2: 用例检索Agent                          │
│  功能：从历史用例中检索相关用例和节点                     │
│  步骤：                                                 │
│  1. 用例级检索：找到"加好友"用例、"视频会议"用例          │
│  2. 节点级检索：找到相关节点（加好友节点、视频会议节点）  │
│  3. Schema匹配：匹配接口schema                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Agent 3: 用例组合Agent                          │
│  功能：组合检索到的用例和节点，生成新用例结构             │
│  步骤：                                                 │
│  1. 分析节点依赖关系                                     │
│  2. 确定节点执行顺序                                     │
│  3. 构建edges连接关系                                    │
│  4. 处理变量传递（从节点A提取变量，在节点B中使用）        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Agent 4: JSON生成Agent                          │
│  功能：生成符合格式要求的完整用例JSON                    │
│  步骤：                                                 │
│  1. 基于检索到的节点模板，生成新节点JSON                 │
│  2. 填充请求参数（根据schema和上下文）                   │
│  3. 设置响应断言                                         │
│  4. 配置变量提取规则                                     │
│  5. 验证JSON格式完整性                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Agent 5: 验证与优化Agent                        │
│  功能：验证生成的用例JSON，优化和修正                     │
│  步骤：                                                 │
│  1. JSON Schema验证                                      │
│  2. 节点连接性验证（edges是否正确）                       │
│  3. 变量依赖验证（变量是否正确定义和使用）                │
│  4. 逻辑合理性检查                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   输出用例JSON                           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Agent详细工作流程

#### 阶段1：需求理解与分解
```python
# Agent 1: Requirement Understanding Agent
输入: "ab互加好友后，进行视频会议"
输出: {
  "tasks": [
    {"task": "加好友", "actors": ["a", "b"]},
    {"task": "视频会议", "actors": ["a", "b"]}
  ],
  "dependencies": ["加好友 -> 视频会议"],
  "actors": ["a", "b"],
  "graph_patterns": {
    "has_branch": false,  # 是否包含分支
    "has_cycle": false,   # 是否包含循环
    "branch_type": null,  # "conditional" | "parallel" | null
    "cycle_type": null    # "retry" | "poll" | "iterate" | null
  }
}

# 示例：包含循环和分支的需求
输入: "用户登录，如果失败则重试3次，成功后并行发送消息和拉取好友列表"
输出: {
  "tasks": [
    {"task": "登录", "actors": ["user"]},
    {"task": "发送消息", "actors": ["user"]},
    {"task": "拉取好友列表", "actors": ["user"]}
  ],
  "dependencies": ["登录 -> 发送消息", "登录 -> 拉取好友列表"],
  "graph_patterns": {
    "has_branch": true,
    "has_cycle": true,
    "branch_type": "parallel",  # 并行分支
    "cycle_type": "retry",      # 重试循环
    "cycle_config": {
      "max_iterations": 3,
      "condition": "response.code != 0"
    }
  }
}
```

#### 阶段2：用例检索（核心步骤）
```python
# Agent 2: Use Case Retrieval Agent

# 2.1 用例级检索
用例级向量搜索：
- 查询向量："加好友"用例
- Top-K: 5个最相似的用例
- 返回：完整用例JSON + 相似度分数

用例级向量搜索：
- 查询向量："视频会议"用例
- Top-K: 5个最相似的用例
- 返回：完整用例JSON + 相似度分数

# 2.2 节点级检索
节点级向量搜索：
- 查询向量："用户a加用户b好友"节点
- Top-K: 10个最相似的节点
- 返回：节点JSON + 相似度分数

节点级向量搜索：
- 查询向量："拉入视频会议"节点
- Top-K: 10个最相似的节点
- 返回：节点JSON + 相似度分数

# 2.3 Schema精确匹配
Schema匹配：
- 根据接口URL查找schema
- 匹配请求/响应结构
- 返回：schema定义 + 使用示例

# 2.4 图模式检索（新增）
图模式检索：
- 识别需求中的图结构模式（分支、循环）
- 检索包含相似图模式的历史用例
- 返回：用例JSON + 图结构特征

def search_use_cases_with_patterns(query: str, graph_patterns: dict):
    # 1. 语义检索
    semantic_results = search_use_cases(query, top_k=20)
    
    # 2. 分析每个用例的图结构
    for case in semantic_results:
        case["graph_pattern"] = analyze_graph_structure(case)
    
    # 3. 根据图模式筛选
    if graph_patterns.get("has_branch"):
        semantic_results = [c for c in semantic_results 
                          if c["graph_pattern"]["has_branch"]]
    if graph_patterns.get("has_cycle"):
        semantic_results = [c for c in semantic_results 
                          if c["graph_pattern"]["has_cycle"]]
    
    return semantic_results

def analyze_graph_structure(case):
    """分析用例的图结构特征"""
    edges = case["edges"]
    nodes = case["nodes"]
    
    # 检测分支
    has_conditional = any(e.get("condition") for e in edges)
    has_parallel = any(e.get("parallel") for e in edges)
    has_branch = has_conditional or has_parallel
    
    # 检测循环
    has_cycle = detect_cycle(edges)
    cycle_type = classify_cycle(edges) if has_cycle else None
    
    return {
        "has_branch": has_branch,
        "has_conditional": has_conditional,
        "has_parallel": has_parallel,
        "has_cycle": has_cycle,
        "cycle_type": cycle_type  # "retry" | "poll" | "iterate"
    }
```

#### 阶段3：用例组合
```python
# Agent 3: Use Case Composition Agent

输入：
- 检索到的"加好友"用例节点列表
- 检索到的"视频会议"用例节点列表
- 接口schema信息
- 图结构模式（如果有分支/循环需求）

处理：
1. 节点选择：
   - 从"加好友"用例中选择：节点1（a加b好友）、节点2（b确认）
   - 从"视频会议"用例中选择：节点3（a拉b进会议）

2. 依赖分析：
   - 节点1 -> 节点2（b需要先收到好友请求）
   - 节点2 -> 节点3（需要先成为好友才能拉入会议）

3. 变量传递分析：
   - 节点1可能返回：friend_id
   - 节点3可能需要：friend_id（用于拉入会议）

4. 图结构识别与构建：
   # 4.1 线性结构（默认）
   edges = [
       {"from": "node1", "to": "node2"},
       {"from": "node2", "to": "node3"}
   ]
   
   # 4.2 条件分支结构
   # 示例：登录成功/失败走不同分支
   if has_conditional_branch:
       edges = [
           {"from": "node1", "to": "node2", "condition": "response.code == 0"},
           {"from": "node1", "to": "node3", "condition": "response.code != 0"}
       ]
   
   # 4.3 并行分支结构
   # 示例：登录成功后并行执行多个操作
   if has_parallel_branch:
       edges = [
           {"from": "node1", "to": "node2", "parallel": true},
           {"from": "node1", "to": "node3", "parallel": true},
           {"from": "node2", "to": "node4"},  # 同步点
           {"from": "node3", "to": "node4"}   # 同步点
       ]
   
   # 4.4 循环结构
   # 示例1：重试循环（失败后重试）
   if has_retry_cycle:
       edges = [
           {"from": "node1", "to": "node2"},
           {"from": "node2", "to": "node1", 
            "type": "retry", 
            "condition": "response.code != 0",
            "max_iterations": 3}
       ]
   
   # 示例2：轮询循环（等待条件满足）
   if has_poll_cycle:
       edges = [
           {"from": "node1", "to": "node2"},
           {"from": "node2", "to": "node1",
            "type": "poll",
            "condition": "response.ready != true",
            "max_iterations": 10,
            "interval": 1000}  # 轮询间隔（毫秒）
       ]
   
   # 示例3：迭代循环（处理列表）
   if has_iterate_cycle:
       edges = [
           {"from": "node1", "to": "node2"},  # 获取列表
           {"from": "node2", "to": "node3"},  # 处理单个元素
           {"from": "node3", "to": "node2",   # 循环处理下一个
            "type": "iterate",
            "condition": "has_more_items",
            "variable": "item_list"}
       ]

5. 构建完整edges列表（支持混合结构）
```

#### 阶段4：JSON生成
```python
# Agent 4: JSON Generation Agent

输入：组合后的节点列表 + edges关系（可能包含分支和循环）

处理：
1. 为每个节点生成完整JSON：
   - 复制检索到的节点模板
   - 根据新用例上下文修改：
     * 节点名称（保持或微调）
     * 请求参数（根据schema填充）
     * 响应断言（根据预期结果设置）
     * 变量提取规则（根据后续节点需求设置）

2. 生成用例级JSON（支持复杂图结构）：
   # 2.1 线性结构示例
   {
     "name": "ab互加好友后进行视频会议",
     "desc": "...",
     "nodes": [node1_json, node2_json, node3_json],
     "edges": [
       {"from": "node1", "to": "node2"},
       {"from": "node2", "to": "node3"}
     ]
   }
   
   # 2.2 条件分支结构示例
   {
     "name": "用户登录并处理结果",
     "desc": "...",
     "nodes": [node1_json, node2_json, node3_json, node4_json],
     "edges": [
       {"from": "node1", "to": "node2", "condition": "response.code == 0"},
       {"from": "node1", "to": "node3", "condition": "response.code != 0"},
       {"from": "node2", "to": "node4"},
       {"from": "node3", "to": "node4"}
     ]
   }
   
   # 2.3 并行分支结构示例
   {
     "name": "登录后并行操作",
     "desc": "...",
     "nodes": [node1_json, node2_json, node3_json, node4_json],
     "edges": [
       {"from": "node1", "to": "node2", "parallel": true},
       {"from": "node1", "to": "node3", "parallel": true},
       {"from": "node2", "to": "node4"},
       {"from": "node3", "to": "node4"}
     ]
   }
   
   # 2.4 重试循环结构示例
   {
     "name": "登录重试",
     "desc": "...",
     "nodes": [node1_json, node2_json],
     "edges": [
       {"from": "node1", "to": "node2"},
       {"from": "node2", "to": "node1", 
        "type": "retry",
        "condition": "response.code != 0",
        "max_iterations": 3,
        "on_success": "node3"}  # 成功后跳转到node3
     ]
   }
   
   # 2.5 轮询循环结构示例
   {
     "name": "等待任务完成",
     "desc": "...",
     "nodes": [node1_json, node2_json, node3_json],
     "edges": [
       {"from": "node1", "to": "node2"},  # 提交任务
       {"from": "node2", "to": "node2",    # 轮询状态
        "type": "poll",
        "condition": "response.status != 'completed'",
        "max_iterations": 10,
        "interval": 1000},
       {"from": "node2", "to": "node3",    # 完成后继续
        "condition": "response.status == 'completed'"}
     ]
   }
   
   # 2.6 混合结构示例（分支+循环）
   {
     "name": "登录重试后并行操作",
     "desc": "...",
     "nodes": [node1_json, node2_json, node3_json, node4_json, node5_json],
     "edges": [
       # 重试循环
       {"from": "node1", "to": "node2"},
       {"from": "node2", "to": "node1",
        "type": "retry",
        "condition": "response.code != 0",
        "max_iterations": 3},
       # 成功后并行分支
       {"from": "node2", "to": "node3", "parallel": true, 
        "condition": "response.code == 0"},
       {"from": "node2", "to": "node4", "parallel": true,
        "condition": "response.code == 0"},
       # 同步点
       {"from": "node3", "to": "node5"},
       {"from": "node4", "to": "node5"}
     ]
   }

3. 严格遵循JSON格式要求：
   - 所有必需字段必须存在
   - 嵌套结构必须完整
   - 类型必须正确
   - edges中的条件表达式语法正确
   - 循环结构必须有明确的退出条件
```

#### 阶段5：验证与优化
```python
# Agent 5: Validation Agent

验证项：
1. JSON Schema验证：
   - 用例JSON是否符合schema
   - 每个节点JSON是否符合节点schema
   - edges结构是否符合edge schema（包含condition、type等字段）

2. 图结构验证：
   - edges中的节点ID是否都存在
   - 是否存在孤立节点（无入边也无出边）
   - 是否存在不可达节点（从入口节点无法到达）
   
   # 2.1 循环验证（区分合法循环和错误循环）
   cycles = detect_all_cycles(edges)
   for cycle in cycles:
       cycle_type = classify_cycle_type(cycle, edges)
       
       if cycle_type == "invalid":
           # 错误循环：无退出条件的死循环
           raise Error(f"检测到死循环: {cycle}")
       elif cycle_type == "retry":
           # 重试循环：必须有max_iterations和退出条件
           if not has_exit_condition(cycle):
               raise Error("重试循环缺少退出条件")
           if not has_max_iterations(cycle):
               raise Error("重试循环缺少最大迭代次数")
       elif cycle_type == "poll":
           # 轮询循环：必须有退出条件和轮询间隔
           if not has_exit_condition(cycle):
               raise Error("轮询循环缺少退出条件")
           if not has_interval(cycle):
               raise Error("轮询循环缺少轮询间隔")
       elif cycle_type == "iterate":
           # 迭代循环：必须有迭代变量和退出条件
           if not has_iteration_variable(cycle):
               raise Error("迭代循环缺少迭代变量")
   
   # 2.2 分支结构验证
   # 条件分支：必须有完整的条件覆盖
   conditional_edges = [e for e in edges if e.get("condition")]
   if conditional_edges:
       for node_id in get_nodes_with_conditional_outgoing(edges):
           conditions = get_all_conditions(node_id, edges)
           if not is_condition_complete(conditions):
               raise Error(f"节点{node_id}的条件分支不完整")
   
   # 并行分支：必须有同步点
   parallel_edges = [e for e in edges if e.get("parallel")]
   if parallel_edges:
       sync_points = find_sync_points(edges)
       if not sync_points:
           raise Error("并行分支缺少同步点")

3. 变量依赖验证：
   - 变量是否在使用前定义
   - 变量类型是否匹配
   - 变量提取路径是否正确
   - 循环中的变量是否正确更新（避免死循环）

4. 逻辑合理性：
   - 节点顺序是否合理
   - 接口调用是否符合业务逻辑
   - 分支条件是否合理
   - 循环退出条件是否可达

如果验证失败，返回错误信息给Agent 4重新生成
```

### 2.3 Agent查询历史用例的具体方法

#### 方法1：语义向量检索
```python
# 用例级检索
def search_use_cases(query: str, top_k: int = 5):
    # 1. 将查询文本转换为向量
    query_vector = embedding_model.encode(query)
    
    # 2. 在向量数据库中搜索
    results = vector_db.search(
        collection="use_cases",
        query_vector=query_vector,
        top_k=top_k
    )
    
    # 3. 返回用例完整JSON
    return [result["full_json"] for result in results]

# 节点级检索
def search_nodes(query: str, top_k: int = 10):
    query_vector = embedding_model.encode(query)
    results = vector_db.search(
        collection="nodes",
        query_vector=query_vector,
        top_k=top_k
    )
    return [result["node_json"] for result in results]
```

#### 方法2：精确匹配检索
```python
# 通过接口URL检索
def search_nodes_by_api(api_url: str):
    nodes = db.query(
        "SELECT node_json FROM nodes WHERE api_url = ?",
        api_url
    )
    return nodes

# 通过Schema结构匹配
def search_nodes_by_schema(request_schema: dict):
    # 使用Elasticsearch的schema匹配功能
    results = es.search(
        index="nodes",
        body={
            "query": {
                "match": {
                    "request_schema": request_schema
                }
            }
        }
    )
    return results
```

#### 方法3：混合检索策略
```python
def hybrid_search(query: str):
    # 1. 语义检索（召回）
    semantic_results = search_use_cases(query, top_k=20)
    semantic_nodes = search_nodes(query, top_k=30)
    
    # 2. 精确匹配（精排）
    # 从语义结果中提取接口URL
    api_urls = extract_api_urls(semantic_results)
    exact_nodes = [search_nodes_by_api(url) for url in api_urls]
    
    # 3. 重排序（结合相似度和精确度）
    final_results = rerank(
        semantic_results + exact_nodes,
        query
    )
    
    return final_results[:10]  # 返回Top-10
```

#### 方法4：图模式检索（新增）
```python
def search_by_graph_pattern(query: str, graph_patterns: dict):
    """根据图结构模式检索用例"""
    # 1. 语义检索
    results = search_use_cases(query, top_k=50)
    
    # 2. 分析每个用例的图结构
    for case in results:
        case["graph_pattern"] = analyze_graph_structure(case)
    
    # 3. 根据图模式筛选
    filtered_results = []
    for case in results:
        pattern = case["graph_pattern"]
        
        # 检查是否匹配需求的图模式
        if graph_patterns.get("has_branch") and not pattern["has_branch"]:
            continue
        if graph_patterns.get("has_cycle") and not pattern["has_cycle"]:
            continue
        if graph_patterns.get("branch_type") and pattern.get("branch_type") != graph_patterns["branch_type"]:
            continue
        if graph_patterns.get("cycle_type") and pattern.get("cycle_type") != graph_patterns["cycle_type"]:
            continue
        
        filtered_results.append(case)
    
    # 4. 按相似度排序
    filtered_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    
    return filtered_results[:10]
```

## 三、可能遇到的问题与解决方案

### 3.1 JSON格式严格性问题

**问题描述：**
- 节点JSON结构非常复杂，包含大量嵌套的map/list
- 格式要求严格，必须完全符合schema才能被执行引擎解析
- LLM生成的JSON可能格式不完整或类型错误

**解决方案：**

#### 方案1：基于模板的生成
```python
# 不直接生成完整JSON，而是：
# 1. 检索相似节点作为模板
template_node = retrieve_similar_node(query)

# 2. 只让LLM填充关键字段
prompt = f"""
基于以下节点模板，生成新节点：
模板：{template_node}

需要修改的字段：
- node_name: 改为"用户a加用户b好友"
- request_params: 根据schema填充
- response_assertions: 设置断言规则

保持其他所有字段不变。
"""

# 3. LLM只输出需要修改的部分
modifications = llm.generate(prompt)

# 4. 程序化合并到模板
new_node = merge_template(template_node, modifications)
```

#### 方案2：JSON Schema约束生成
```python
# 使用结构化输出，让LLM严格按照schema生成
from pydantic import BaseModel

class NodeSchema(BaseModel):
    node_name: str
    request_schema: dict
    response_schema: dict
    # ... 完整定义所有字段

# LLM生成时强制遵循schema
new_node = llm.generate_structured(
    prompt=prompt,
    schema=NodeSchema
)
```

#### 方案3：多轮验证与修正
```python
def generate_with_validation():
    # 1. LLM生成初版JSON
    draft_json = llm.generate(prompt)
    
    # 2. Schema验证
    errors = validate_schema(draft_json, NodeSchema)
    
    # 3. 如果有错误，让LLM修正
    if errors:
        correction_prompt = f"""
        生成的JSON有以下错误：{errors}
        请修正这些错误，生成正确的JSON。
        """
        draft_json = llm.generate(correction_prompt)
        errors = validate_schema(draft_json, NodeSchema)
    
    # 4. 如果还有错误，使用程序化修复
    if errors:
        draft_json = programmatic_fix(draft_json, errors)
    
    return draft_json
```

### 3.2 节点组合的合理性问题

**问题描述：**
- 不同用例的节点组合时，可能存在逻辑冲突
- 变量传递可能不匹配
- 节点执行顺序可能不合理

**解决方案：**

#### 方案1：依赖图分析（支持复杂图结构）
```python
def analyze_dependencies(nodes, edges):
    # 构建依赖图（支持分支和循环）
    dependency_graph = build_graph(nodes, edges)
    
    # 检测循环（不直接报错，而是分类）
    cycles = detect_all_cycles(dependency_graph)
    
    for cycle in cycles:
        cycle_type = classify_cycle_type(cycle, edges)
        if cycle_type == "invalid":
            # 只有无效循环才报错
            raise Error(f"存在无效循环: {cycle}")
        # 合法循环（retry/poll/iterate）允许存在
    
    # 对于无循环的部分，使用拓扑排序
    # 对于有循环的部分，使用循环检测和条件验证
    execution_order = topological_sort_with_cycles(dependency_graph, edges)
    
    return execution_order

def classify_cycle_type(cycle, edges):
    """分类循环类型"""
    cycle_edges = [e for e in edges if is_edge_in_cycle(e, cycle)]
    
    # 检查是否有retry标记
    if any(e.get("type") == "retry" for e in cycle_edges):
        return "retry"
    
    # 检查是否有poll标记
    if any(e.get("type") == "poll" for e in cycle_edges):
        return "poll"
    
    # 检查是否有iterate标记
    if any(e.get("type") == "iterate" for e in cycle_edges):
        return "iterate"
    
    # 检查是否有退出条件
    if any(e.get("condition") for e in cycle_edges):
        # 有条件的循环可能是合法的
        return "conditional"
    
    # 无退出条件的循环是无效的
    return "invalid"
```

#### 方案2：变量依赖追踪（支持循环和分支）
```python
def validate_variable_flow(nodes, edges):
    # 1. 提取所有变量定义和使用
    var_definitions = {}  # {node_id: [var1, var2, ...]}
    var_usages = {}       # {node_id: [var1, var2, ...]}
    
    for node in nodes:
        var_definitions[node.id] = extract_var_definitions(node)
        var_usages[node.id] = extract_var_usages(node)
    
    # 2. 检查变量是否在使用前定义（考虑分支和循环）
    for node_id, used_vars in var_usages.items():
        # 找到该节点的所有可能前置节点（考虑分支）
        all_predecessors = find_all_predecessors(node_id, edges)
        
        # 检查使用的变量是否在前置节点中定义
        available_vars = set()
        for pred_id in all_predecessors:
            available_vars.update(var_definitions[pred_id])
        
        missing_vars = set(used_vars) - available_vars
        
        # 对于循环中的节点，变量可能在循环内定义
        if missing_vars and is_in_cycle(node_id, edges):
            # 检查变量是否在循环内定义
            cycle_nodes = get_cycle_nodes(node_id, edges)
            cycle_vars = set()
            for cycle_node_id in cycle_nodes:
                cycle_vars.update(var_definitions.get(cycle_node_id, []))
            
            # 如果变量在循环内定义，需要确保循环至少执行一次
            if missing_vars.issubset(cycle_vars):
                # 检查循环是否有初始值或前置定义
                if not has_initial_value(missing_vars, node_id, edges):
                    raise Error(f"节点{node_id}使用的变量{missing_vars}在循环内定义，但缺少初始值")
            else:
                raise Error(f"节点{node_id}使用的变量{missing_vars}未定义")
        elif missing_vars:
            raise Error(f"节点{node_id}使用的变量{missing_vars}未定义")
    
    # 3. 检查循环中的变量更新（避免死循环）
    cycles = detect_all_cycles(edges)
    for cycle in cycles:
        cycle_vars = get_cycle_variables(cycle, nodes, edges)
        # 确保循环中有变量被更新，或者有明确的退出条件
        if not has_variable_update(cycle, cycle_vars) and not has_exit_condition(cycle):
            raise Error(f"循环{cycle}可能导致死循环：无变量更新且无退出条件")
```

#### 方案3：业务逻辑验证
```python
def validate_business_logic(nodes):
    # 定义业务规则
    rules = [
        "加好友必须在聊天之前",
        "视频会议需要先成为好友",
        # ...
    ]
    
    # 检查节点序列是否符合规则
    for rule in rules:
        if not check_rule(nodes, rule):
            # 让Agent重新调整节点顺序
            nodes = agent.adjust_order(nodes, rule)
    
    return nodes
```

### 3.3 检索准确性问题

**问题描述：**
- 语义检索可能返回不相关的用例/节点
- 相似用例可能功能不同但描述相似
- 节点描述可能不够清晰

**解决方案：**

#### 方案1：多维度检索
```python
def multi_dimension_search(query):
    # 1. 语义检索（基于描述）
    semantic_results = vector_search(query)
    
    # 2. 接口URL检索（精确匹配）
    api_results = search_by_api_url(extract_api_from_query(query))
    
    # 3. Schema结构检索（结构相似）
    schema_results = search_by_schema_structure(query)
    
    # 4. 标签检索（分类匹配）
    tag_results = search_by_tags(extract_tags(query))
    
    # 5. 融合排序
    final_results = fusion_rerank(
        semantic_results,
        api_results,
        schema_results,
        tag_results
    )
    
    return final_results
```

#### 方案2：增强节点描述
```python
# 在存储节点时，生成更丰富的描述
def enrich_node_description(node):
    description = f"""
    节点名称：{node.node_name}
    功能描述：{node.description}
    接口URL：{node.api_url}
    请求参数：{summarize_schema(node.request_schema)}
    响应结构：{summarize_schema(node.response_schema)}
    业务场景：{infer_business_context(node)}
    """
    
    # 使用增强描述生成向量
    embedding = embedding_model.encode(description)
    return embedding
```

#### 方案3：交互式检索优化
```python
def interactive_retrieval(query):
    # 1. 初始检索
    results = search(query, top_k=20)
    
    # 2. 让Agent评估相关性
    relevant_results = agent.filter_relevant(results, query)
    
    # 3. 如果结果不够，Agent可以细化查询
    if len(relevant_results) < 5:
        refined_query = agent.refine_query(query, results)
        results = search(refined_query, top_k=20)
        relevant_results = agent.filter_relevant(results, query)
    
    return relevant_results
```

### 3.4 接口Schema理解问题

**问题描述：**
- 接口schema可能很复杂，LLM可能理解错误
- 请求参数如何填充可能不明确
- 响应断言如何设置可能不合理

**解决方案：**

#### 方案1：Schema示例学习
```python
# 为每个接口schema存储使用示例
def get_schema_with_examples(api_url):
    schema = get_schema(api_url)
    examples = get_node_examples(api_url)  # 历史节点中的实际使用
    
    return {
        "schema": schema,
        "examples": examples  # 让LLM学习如何填充参数
    }

# LLM生成时参考示例
prompt = f"""
接口Schema：{schema}
使用示例：
{examples}

请根据新场景填充请求参数。
"""
```

#### 方案2：Schema解析工具
```python
# 提供Schema解析工具给Agent
@tool
def parse_schema(schema: dict) -> str:
    """解析JSON Schema，返回人类可读的描述"""
    description = f"""
    接口名称：{schema.get('title')}
    必需参数：{schema.get('required', [])}
    参数说明：
    {format_properties(schema.get('properties', {}))}
    """
    return description

# Agent在生成节点时调用此工具
agent_tools = [parse_schema, ...]
```

### 3.5 变量传递的复杂性

**问题描述：**
- 节点A提取的变量，节点B如何使用
- 变量路径可能很复杂（嵌套JSON路径）
- 变量类型转换问题

**解决方案：**

#### 方案1：变量传递模式学习
```python
# 从历史用例中学习变量传递模式
def learn_variable_patterns():
    patterns = {}
    
    for case in all_cases:
        for edge in case.edges:
            from_node = get_node(edge.from_node)
            to_node = get_node(edge.to_node)
            
            # 提取变量传递模式
            extracted_vars = from_node.extract_variables
            used_vars = to_node.use_variables
            
            # 学习模式：从哪个节点提取什么变量，在哪个节点如何使用
            pattern = {
                "extract": extracted_vars,
                "use": used_vars,
                "transformation": infer_transformation(extracted_vars, used_vars)
            }
            patterns.append(pattern)
    
    return patterns

# Agent生成时参考这些模式
def generate_variable_extraction(from_node, to_node):
    # 查找相似的模式
    similar_pattern = find_similar_pattern(from_node, to_node)
    
    # 基于模式生成变量提取规则
    extraction_rule = adapt_pattern(similar_pattern, from_node, to_node)
    
    return extraction_rule
```

### 3.6 复杂图结构的处理（分支、循环）

**问题描述：**
- 用例图可能包含条件分支（if-else）
- 可能包含并行分支（并行执行多个节点）
- 可能包含循环（重试、轮询、迭代）
- Agent需要识别这些模式并正确生成
- 需要区分合法循环和错误循环

**解决方案：**

#### 方案1：图模式学习
```python
# 从历史用例中学习常见的图模式
def learn_graph_patterns():
    patterns = {
        "retry": [],      # 重试模式
        "poll": [],       # 轮询模式
        "iterate": [],    # 迭代模式
        "conditional": [], # 条件分支模式
        "parallel": []    # 并行分支模式
    }
    
    for case in all_cases:
        edges = case["edges"]
        graph_type = analyze_graph_structure(case)
        
        if graph_type["has_cycle"]:
            cycle_type = graph_type["cycle_type"]
            if cycle_type:
                # 提取循环模式
                cycle_pattern = extract_cycle_pattern(case, cycle_type)
                patterns[cycle_type].append(cycle_pattern)
        
        if graph_type["has_branch"]:
            if graph_type["has_conditional"]:
                branch_pattern = extract_conditional_pattern(case)
                patterns["conditional"].append(branch_pattern)
            if graph_type["has_parallel"]:
                parallel_pattern = extract_parallel_pattern(case)
                patterns["parallel"].append(parallel_pattern)
    
    return patterns

# Agent生成时参考这些模式
def generate_graph_structure(requirements, retrieved_cases):
    # 1. 识别需求中的图结构关键词
    graph_requirements = extract_graph_requirements(requirements)
    # 例如：{"has_retry": true, "max_iterations": 3}
    
    # 2. 从历史用例中查找相似模式
    similar_patterns = find_similar_patterns(graph_requirements, patterns)
    
    # 3. 复用图结构模式，适配到新用例
    adapted_structure = adapt_pattern(similar_patterns[0], requirements)
    
    return adapted_structure
```

#### 方案2：图结构生成策略
```python
def generate_edges_with_patterns(nodes, requirements):
    edges = []
    
    # 1. 识别需求中的图结构模式
    if requirements.get("retry"):
        # 生成重试循环
        edges.extend(generate_retry_cycle(nodes, requirements["retry"]))
    
    if requirements.get("poll"):
        # 生成轮询循环
        edges.extend(generate_poll_cycle(nodes, requirements["poll"]))
    
    if requirements.get("parallel"):
        # 生成并行分支
        edges.extend(generate_parallel_branch(nodes, requirements["parallel"]))
    
    if requirements.get("conditional"):
        # 生成条件分支
        edges.extend(generate_conditional_branch(nodes, requirements["conditional"]))
    
    # 2. 如果没有特殊模式，生成线性结构
    if not edges:
        edges = generate_linear_structure(nodes)
    
    return edges

def generate_retry_cycle(nodes, retry_config):
    """生成重试循环结构"""
    retry_node = nodes[0]  # 需要重试的节点
    check_node = nodes[1]  # 检查结果的节点
    
    edges = [
        {"from": retry_node.id, "to": check_node.id},
        {"from": check_node.id, "to": retry_node.id,
         "type": "retry",
         "condition": retry_config.get("condition", "response.code != 0"),
         "max_iterations": retry_config.get("max_iterations", 3),
         "on_success": retry_config.get("success_node")}
    ]
    return edges
```

#### 方案3：循环验证规则
```python
def validate_cycle(cycle, edges, nodes):
    """验证循环是否合法"""
    cycle_edges = [e for e in edges if is_edge_in_cycle(e, cycle)]
    
    # 规则1：必须有明确的退出条件
    has_exit_condition = any(
        e.get("condition") or e.get("max_iterations") 
        for e in cycle_edges
    )
    if not has_exit_condition:
        return False, "循环缺少退出条件"
    
    # 规则2：循环内必须有状态变化（避免死循环）
    cycle_node_ids = get_cycle_node_ids(cycle)
    cycle_nodes = [n for n in nodes if n.id in cycle_node_ids]
    
    # 检查是否有变量更新或外部状态变化
    has_state_change = any(
        has_variable_update(node) or calls_external_api(node)
        for node in cycle_nodes
    )
    if not has_state_change:
        return False, "循环内无状态变化，可能导致死循环"
    
    # 规则3：重试循环必须有最大迭代次数
    if any(e.get("type") == "retry" for e in cycle_edges):
        if not any(e.get("max_iterations") for e in cycle_edges):
            return False, "重试循环缺少最大迭代次数"
    
    # 规则4：轮询循环必须有轮询间隔
    if any(e.get("type") == "poll" for e in cycle_edges):
        if not any(e.get("interval") for e in cycle_edges):
            return False, "轮询循环缺少轮询间隔"
    
    return True, "循环合法"
```

#### 方案4：分支结构验证
```python
def validate_branch_structure(edges, nodes):
    """验证分支结构是否合理"""
    # 1. 条件分支验证
    conditional_edges = [e for e in edges if e.get("condition")]
    
    # 检查每个节点的条件分支是否完整
    for node_id in get_all_node_ids(nodes):
        outgoing_conditional = [e for e in conditional_edges 
                               if e["from"] == node_id]
        
        if outgoing_conditional:
            # 检查条件是否互斥且完整
            conditions = [e["condition"] for e in outgoing_conditional]
            if not are_conditions_complete(conditions):
                return False, f"节点{node_id}的条件分支不完整"
            
            if not are_conditions_mutually_exclusive(conditions):
                return False, f"节点{node_id}的条件分支有重叠"
    
    # 2. 并行分支验证
    parallel_edges = [e for e in edges if e.get("parallel")]
    
    if parallel_edges:
        # 检查是否有同步点
        parallel_groups = group_parallel_edges(parallel_edges)
        for group in parallel_groups:
            sync_points = find_sync_points_for_group(group, edges)
            if not sync_points:
                return False, f"并行分支组{group}缺少同步点"
    
    return True, "分支结构合法"
```

## 四、技术实现建议

### 4.1 技术栈推荐

```
向量数据库：Milvus / Chroma / Pinecone
关系数据库：PostgreSQL（存储完整JSON和元数据）
搜索引擎：Elasticsearch（用于精确查询和schema匹配）
LLM框架：LangChain / LangGraph（构建Agent系统）
嵌入模型：text-embedding-3-large / BGE-large
LLM：GPT-4 / Claude 3.5 / DeepSeek（用于生成和推理）
```

### 4.2 数据索引策略

```python
# 1. 用例级索引
index_use_case(case):
    # 生成用例向量（基于name + desc + 所有节点描述）
    text = f"{case.name} {case.desc} {extract_all_node_descriptions(case)}"
    vector = embedding_model.encode(text)
    
    # 存储到向量数据库
    vector_db.insert("use_cases", {
        "id": case.case_id,
        "vector": vector,
        "metadata": {
            "name": case.name,
            "tags": case.tags,
            "full_json": case.full_json
        }
    })

# 2. 节点级索引
index_node(node):
    # 生成节点向量（基于节点描述 + schema摘要）
    text = f"{node.description} {summarize_schema(node.request_schema)} {summarize_schema(node.response_schema)}"
    vector = embedding_model.encode(text)
    
    # 存储到向量数据库
    vector_db.insert("nodes", {
        "id": node.node_id,
        "vector": vector,
        "metadata": {
            "case_id": node.case_id,
            "api_url": node.api_url,
            "node_json": node.node_json
        }
    })
    
    # 同时索引到Elasticsearch（用于精确查询）
    es.index("nodes", {
        "node_id": node.node_id,
        "api_url": node.api_url,
        "request_schema": node.request_schema,
        "response_schema": node.response_schema
    })

# 3. Schema索引
index_schema(api_url, schema):
    # 存储接口schema映射
    db.insert("api_schemas", {
        "api_url": api_url,
        "request_schema": schema.request,
        "response_schema": schema.response,
        "example_nodes": []  # 使用该接口的节点ID列表
    })
```

### 4.3 Agent系统架构（LangGraph实现）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    user_query: str
    decomposed_tasks: list
    retrieved_cases: list
    retrieved_nodes: list
    composed_structure: dict
    generated_json: dict
    validation_errors: list

# 构建Agent工作流
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("understand", requirement_understanding_agent)
workflow.add_node("retrieve", retrieval_agent)
workflow.add_node("compose", composition_agent)
workflow.add_node("generate", json_generation_agent)
workflow.add_node("validate", validation_agent)

# 添加边
workflow.set_entry_point("understand")
workflow.add_edge("understand", "retrieve")
workflow.add_edge("retrieve", "compose")
workflow.add_edge("compose", "generate")
workflow.add_edge("generate", "validate")

# 条件边：验证失败则重新生成
workflow.add_conditional_edges(
    "validate",
    lambda x: "generate" if x["validation_errors"] else END
)

app = workflow.compile()
```

## 五、总结

### 5.1 核心设计要点

1. **双层存储**：用例级存储用于整体检索，节点级存储用于细粒度检索
2. **多Agent协作**：不同Agent负责不同阶段，各司其职
3. **模板复用**：基于历史节点模板生成，而非从零生成
4. **严格验证**：多轮验证确保JSON格式正确
5. **混合检索**：语义检索 + 精确匹配，提高检索准确性
6. **复杂图结构支持**：支持条件分支、并行分支、重试循环、轮询循环、迭代循环等复杂图结构
7. **智能循环验证**：区分合法循环（有退出条件）和错误循环（死循环），确保生成的用例可执行

### 5.2 关键成功因素

- **高质量的历史用例数据**：用例描述清晰，节点结构完整
- **准确的向量嵌入**：使用合适的嵌入模型和文本预处理
- **完善的Schema索引**：接口schema信息完整且准确
- **强大的LLM能力**：能够理解复杂结构和生成严格格式的JSON
- **持续的优化迭代**：根据生成结果不断优化检索和生成策略

