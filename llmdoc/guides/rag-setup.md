# 如何配置 RAG 系统

本指南介绍如何配置 HaloWebUI 的 RAG (检索增强生成) 系统，包括嵌入模型、向量数据库和知识库设置。

## 1. 配置嵌入模型

嵌入模型负责将文本转换为向量表示，是 RAG 系统的核心组件。

### 1.1 选择嵌入引擎

在环境变量或管理面板中设置:

```bash
# 引擎类型: "" (本地)、"ollama"、"openai"
RAG_EMBEDDING_ENGINE=openai
```

### 1.2 本地模型配置

使用 sentence-transformers 本地模型:

```bash
RAG_EMBEDDING_ENGINE=
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# 或其他 HuggingFace 模型，如:
# RAG_EMBEDDING_MODEL=BAAI/bge-m3
```

需要安装依赖: `pip install sentence-transformers transformers accelerate`

### 1.3 Ollama 嵌入配置

```bash
RAG_EMBEDDING_ENGINE=ollama
RAG_EMBEDDING_MODEL=nomic-embed-text
RAG_OLLAMA_BASE_URL=http://localhost:11434
```

### 1.4 OpenAI 兼容 API 配置

```bash
RAG_EMBEDDING_ENGINE=openai
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_OPENAI_API_BASE_URL=https://api.openai.com/v1
RAG_OPENAI_API_KEY=sk-xxx
```

### 1.5 可选参数

```bash
# 批处理大小 (减少 API 调用次数)
RAG_EMBEDDING_BATCH_SIZE=50

# 查询/内容前缀 (某些模型需要)
RAG_EMBEDDING_QUERY_PREFIX="search_query: "
RAG_EMBEDDING_CONTENT_PREFIX="search_document: "
```

## 2. 配置向量数据库

向量数据库存储文档向量并支持相似性搜索。

### 2.1 ChromaDB (默认)

```bash
VECTOR_DB=chroma
# 本地存储路径
CHROMA_DATA_PATH=./data/chroma
# 或 HTTP 模式
CHROMA_HTTP_HOST=localhost
CHROMA_HTTP_PORT=8000
```

### 2.2 Qdrant

```bash
VECTOR_DB=qdrant
QDRANT_URI=http://localhost:6333
QDRANT_API_KEY=your-api-key  # 可选
```

### 2.3 Milvus

```bash
VECTOR_DB=milvus
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=your-token  # 可选
```

### 2.4 pgvector

```bash
VECTOR_DB=pgvector
PGVECTOR_DB_URL=postgresql://user:pass@localhost:5432/vectordb
```

### 2.5 OpenSearch / Elasticsearch

```bash
VECTOR_DB=opensearch
OPENSEARCH_URI=http://localhost:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
```

## 3. 配置重排序模型 (可选)

重排序模型对检索结果进行二次排序，提升相关性。

### 3.1 本地 CrossEncoder

```bash
RAG_RERANKING_ENGINE=local
RAG_RERANKING_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

### 3.2 ColBERT 本地模型

```bash
RAG_RERANKING_ENGINE=local
RAG_RERANKING_MODEL=jinaai/jina-colbert-v2
```

需要安装: `pip install colbert-ai`

### 3.3 Jina API

```bash
RAG_RERANKING_ENGINE=jina
RAG_RERANKING_MODEL=jina-reranker-m0
RAG_RERANKING_API_BASE_URL=https://api.jina.ai/v1
RAG_RERANKING_API_KEY=jina-xxx
```

## 4. 创建知识库

### 4.1 通过 Web 界面

1. 登录管理面板，进入 "知识库" 页面
2. 点击 "创建知识库"，输入名称
3. 上传文档文件 (支持 PDF、DOCX、TXT、MD 等格式)
4. 系统自动解析文档并生成向量索引

### 4.2 文档解析器配置

```bash
# 内容提取引擎: "" (默认)、"tika"、"docling"
CONTENT_EXTRACTION_ENGINE=docling

# Tika 配置
TIKA_SERVER_URL=http://localhost:9998

# Docling 配置 (本地)
DOCLING_SERVER_URL=http://localhost:5001
```

## 5. 验证配置

### 5.1 检查运行时能力

访问 API 端点查看 RAG 能力:

```bash
curl http://localhost:8080/api/v1/retrieval/config
```

响应示例:

```json
{
	"local_embedding_available": true,
	"local_reranking_available": true,
	"colbert_reranking_available": false
}
```

### 5.2 测试检索功能

在聊天界面中，选择已创建的知识库进行对话测试，验证检索结果是否准确返回。

## 6. 常见问题

| 问题           | 解决方案                                             |
| -------------- | ---------------------------------------------------- |
| 嵌入生成失败   | 检查 API 密钥和网络连接，或切换到本地模型            |
| 向量库连接失败 | 确认数据库服务已启动，检查 URI 和认证信息            |
| 检索结果不准确 | 尝试启用混合搜索或配置重排序模型                     |
| 内存不足       | 减小 `RAG_EMBEDDING_BATCH_SIZE` 或使用更小的嵌入模型 |
