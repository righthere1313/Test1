# TeachingAgent 本地知识库系统

## 1. 系统概述
本系统实现了符合赛题技术规范的本地知识库能力，支持多格式文档上传、解析、双重存储、增量版本管理、全文检索、语义检索、混合检索与带引用回答生成，支持 Web 端与外部系统通过 RESTful API 集成。

## 2. 架构说明
### 2.1 双重存储机制
- 原始文档存储：`data/raw/{document_id}/v{version}/原文件`
- 结构化副本存储：`data/processed/{document_id}/v{version}.json`
- 元数据与版本记录：SQLite `data/db/metadata.db`
- 向量索引存储：Chroma `data/chroma`

### 2.2 核心模块
- 解析层：`PDFParser + DocumentParser`，支持 PDF、DOCX、TXT、Markdown
- 存储层：原文归档 + 结构化 JSON + 元数据数据库
- 索引层：Chunking + Embedding + Chroma 向量库
- 检索层：全文检索（SQLite LIKE）+ 语义检索（向量召回）+ 混合检索（加权融合）
- 生成层：基于检索结果组装可追溯回答，返回 citations

## 3. 功能清单
- 支持上传格式：`.pdf .docx .txt .md .markdown`
- 支持章节识别：PDF 基于中文章节标题规则识别章节
- 支持实时增量：同名文档自动创建新版本并更新索引
- 支持版本追溯：可查询并下载任意历史版本
- 支持检索模式：全文、语义、混合
- 支持问答：返回答案及引用来源（文档 ID、版本、chunk）

## 4. 目录结构
```text
app/
├── api/
│   ├── api.py
│   └── v1/endpoints/
│       ├── files.py
│       └── chat.py
├── core/config.py
├── schemas/
│   ├── generation.py
│   └── knowledge_base.py
├── services/
│   ├── knowledge_base_service.py
│   ├── rag_service.py
│   └── parser/
│       ├── pdf_parser.py
│       └── document_parser.py
└── main.py
```

## 5. API 文档
服务启动后访问 `/docs` 查看完整 OpenAPI 文档。

### 5.1 文档上传与管理
1) 上传文档  
- 方法：`POST /api/v1/files/upload`  
- 请求：`multipart/form-data`，字段 `file`  
- 支持扩展名：pdf/docx/txt/md/markdown  
- 响应示例：
```json
{
  "document_id": "0f8f10d3-2a3e-4d64-a9f0-2fe59afde3fd",
  "filename": "教学设计.pdf",
  "file_type": "pdf",
  "version": 2,
  "chunk_count": 18,
  "sections": [{"title": "第一章 导论", "page_number": 1}],
  "status": "processed"
}
```

2) 查询文档列表  
- 方法：`GET /api/v1/files/documents`

3) 查询单个文档  
- 方法：`GET /api/v1/files/documents/{document_id}`

4) 查询版本历史  
- 方法：`GET /api/v1/files/documents/{document_id}/versions`

5) 下载指定版本原文  
- 方法：`GET /api/v1/files/documents/{document_id}/versions/{version}/download`

### 5.2 检索接口
1) 全文检索  
- 方法：`POST /api/v1/chat/search/fulltext`

2) 语义检索  
- 方法：`POST /api/v1/chat/search/semantic`

3) 混合检索  
- 方法：`POST /api/v1/chat/search/hybrid`

请求体统一示例：
```json
{
  "query": "课堂互动设计如何安排",
  "top_k": 5,
  "document_id": null
}
```

### 5.3 带引用问答
- 方法：`POST /api/v1/chat/qa`
- 请求示例：
```json
{
  "query": "该教案的重点难点是什么？",
  "top_k": 5
}
```
- 响应示例：
```json
{
  "query": "该教案的重点难点是什么？",
  "answer": "基于知识库检索结果，建议回答如下：...",
  "citations": [
    {
      "document_id": "0f8f10d3-2a3e-4d64-a9f0-2fe59afde3fd",
      "filename": "教学设计.pdf",
      "version": 2,
      "chunk_id": "0f8f10d3_v2_3",
      "chunk_index": 3,
      "score": 0.88
    }
  ]
}
```

## 6. 用户操作手册
### 6.1 管理员/教师操作流程
1. 打开系统 Web 或 Swagger：`http://localhost:8000/docs`  
2. 调用上传接口导入 PDF、Word、TXT 或 Markdown 文档  
3. 在文档列表接口确认 `document_id` 与最新版本号  
4. 使用全文/语义/混合检索接口验证召回效果  
5. 使用问答接口获取带引用来源的回答  
6. 如文档更新，重新上传同名文件，系统自动写入新版本

### 6.2 外部系统集成流程
1. 通过 `POST /files/upload` 建立知识条目  
2. 保存返回的 `document_id`  
3. 根据业务场景调用 `search/*` 或 `qa` 接口  
4. 基于 citations 做前端溯源展示或二次审核

## 7. 部署手册
### 7.1 环境准备
```bash
conda create -n teaching_agent python=3.10 -y
conda activate teaching_agent
pip install -r requirements.txt
```

### 7.2 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.3 数据目录
- 原始文档：`data/raw`
- 结构化解析：`data/processed`
- 元数据数据库：`data/db/metadata.db`
- 向量库：`data/chroma`

### 7.4 CrossEncoder 重排序
默认启用 CrossEncoder 作为重排序器，用于在召回候选中进行精排。首次启动会自动下载模型权重，建议提前完成缓存或在有网络的环境中启动。

可配置项（环境变量或 `.env`）：
```bash
RERANKER_MODEL_NAME=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_BATCH_SIZE=16
```

性能与部署建议：
- CPU 可用但吞吐较低，建议在高并发或长文本场景使用 GPU
- 模型权重下载后会缓存到本地，避免重复下载
- 若环境内存有限，可降低 `RERANKER_BATCH_SIZE`
- 若网络无法下载模型，则可显性配置镜像，例如：

```bash
export HF_ENDPOINT="https://hf-mirror.com"
export HF_HOME="/tmp/hf_cache"

python - <<'PY'
from huggingface_hub import snapshot_download
path = snapshot_download(repo_id="cross-encoder/ms-marco-MiniLM-L-6-v2")
print("saved to:", path)
PY
```

示例代码（独立验证模型可用性）：
```python
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
pairs = [("教学目标是什么", "本课教学目标是掌握二次函数图像性质。")]
scores = model.predict(pairs)
print(scores[0])
```
