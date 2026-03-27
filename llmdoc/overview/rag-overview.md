# RAG 检索增强生成系统概览

## 1. 身份

- **定义**: RAG (Retrieval-Augmented Generation) 是一种将外部知识库检索与大语言模型生成能力相结合的技术架构。
- **目的**: 解决大语言模型知识时效性不足、幻觉问题，以及私有数据安全访问的需求，为 AI 对话提供精准的上下文知识支撑。

## 2. 高层描述

HaloWebUI 的 RAG 系统是一个完整的检索增强生成解决方案，支持从文档上传、向量嵌入、知识库检索到结果重排序的全流程处理。系统采用模块化设计，向量数据库、嵌入引擎、重排序引擎均可独立配置替换，适应不同的部署场景。

### 核心能力

| 能力 | 描述 |
|------|------|
| **多向量库支持** | ChromaDB、Qdrant、Milvus、pgvector、OpenSearch、Elasticsearch |
| **多嵌入引擎** | 本地模型 (sentence-transformers)、Ollama、OpenAI 兼容 API |
| **多检索模式** | 纯向量搜索、混合搜索 (BM25+向量)、带重排序的检索 |
| **多文档解析器** | Tika、Docling、Azure Document Intelligence、Mistral OCR |
| **Web 搜索集成** | DuckDuckGo、Tavily、Bing、Brave、Google PSE、SerpAPI |

### 技术架构要点

- **距离度量**: 统一使用余弦相似度 (Cosine Similarity)，分数归一化至 [0, 1]
- **混合搜索**: BM25 关键词检索与向量语义检索加权融合 (默认 BM25 权重 0.5)
- **重排序**: 支持 CrossEncoder 本地模型、ColBERT、Jina API 三种方案

### 配置入口

核心配置项位于 `backend/open_webui/config.py:2334-2432`:
- `VECTOR_DB`: 向量数据库选择
- `RAG_EMBEDDING_ENGINE/MODEL`: 嵌入引擎与模型
- `RAG_RERANKING_ENGINE/MODEL`: 重排序引擎与模型
