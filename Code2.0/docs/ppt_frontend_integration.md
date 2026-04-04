# PPT 制作功能对接文档（前端）

本文档面向前端同学，描述 PPT 生成、预览切片、PPT 修改（版本化）、以及数字人按页视频的对接方式。

## 基本信息

- API 前缀：`/api/v1`
- PPT 模块路由前缀：`/api/v1/generate`
- 所有接口返回的 `download_url/pages_base_url/mp4_pages_base_url` 都是相对路径，前端需要拼接后端域名。

## 核心概念

- **Layout 模板**：布局模板名（例如 `general`），用于指定渲染时的背景与内容区。
- **Plan（渲染前 JSON）**：用于渲染 PPT 的结构化 JSON，对应后端 Schema `PPTPresentation`。
- **PPT 版本化**：
  - `ppt_id`：一个 PPT 项目的稳定 ID。
  - `version`：该项目的版本号，从 1 递增。
  - 修改时必须带 `base_version`，用于并发控制（乐观锁）。
- **数字人视频（按页）**：生成的是 `page_1.mp4/page_2.mp4/...`，不拼接完整 MP4。

## 1. 获取可用 Layout 列表

用于前端下拉选择模板。

- `GET /api/v1/templates/layouts`

返回为字符串数组（不是对象）：

```json
["general", "xxx", "yyy"]
```

### 1.1 前端推荐交互

- 首次进入“新建PPT”页面时拉取 layout 列表并缓存（内存缓存即可，必要时可在应用层做 5~30 分钟 TTL）。
- 下拉框显示建议：
  - `label`: layout 名称（当前后端没有提供更友好的 displayName）
  - `value`: layout 名称（作为接口参数直接使用）
- 选择后即写入你的生成请求：
  - `auto_layout`：`body.layout = selectedLayout`
  - `render`：`plan.layout = selectedLayout`

### 1.2 校验与兜底

- 建议前端在提交生成请求前做一次快速校验：layout 必须是列表中的一项。
- 若后端返回：
  - `400 layout is required`：前端未传或传空
  - `400 layout not found`：传入值不在模板目录中（前端可提示“模板已下线/请刷新后重试”并重新拉取列表）

### 1.3 获取模板设计规范（可选，用于“模板预览/模板说明”）

如果前端希望在选择模板时展示“模板风格说明/口吻/颜色”等，可以调用：

- `GET /api/v1/templates/layouts/design_spec?layout={layoutName}`

返回：

```json
{
  "layout": "general",
  "design_spec": "..."
}
```

前端用法建议：
- 在下拉框选中某个 layout 后，再异步拉取 design_spec 并展示为“模板说明”（无需阻塞用户点击生成）。

### 1.4 获取模板 SVG（可选，用于“模板缩略图/真实预览”）

后端也提供了按文件名获取 layout svg 的接口：

- `GET /api/v1/templates/layouts/svg?layout={layoutName}&name={svgName}`

其中 `svgName` 常用：
- `01_cover.svg`：封面
- `03_content.svg`：内容页
- `04_ending.svg`：结束页

返回：

```json
{
  "layout": "general",
  "name": "03_content.svg",
  "svg": "<svg ...>...</svg>"
}
```

前端用法建议：
- 若要做模板缩略图，可直接把 SVG 渲染到页面（或转成 canvas）。
- 若后端返回 `404 svg not found`，说明该模板缺少该 svg（前端可隐藏该预览入口）。

## 2. PPT 生成（两种方式）

### 2.1 方式 A：auto_layout（推荐给“输入一段文本自动生成课件”）

- `POST /api/v1/generate/ppt/auto_layout`
- Body（JSON）：
  - `layout`：layout 名称（必填）
  - `source_text`：源文本（必填）
  - `slides_total`：总页数（含封面，最小 2）
  - `title/subtitle`：可选（不传会使用默认）
  - `extra_instructions`：可选（额外约束，比如“第 2 页加入图表”）
  - `with_mp4`：是否生成数字人视频（默认 false）
  - `mp4_pages`：只生成前 N 页数字人（可选）
  - `mp4_portrait`：数字人头像路径（可选）
  - `mp4_max_wait_seconds`：单页视频任务最大等待秒数（可选）

请求示例：

```bash
curl -X POST "http://localhost:8000/api/v1/generate/ppt/auto_layout" \
  -H "Content-Type: application/json" \
  -d '{
    "layout":"general",
    "source_text":"请生成一份关于勾股定理的课件，包含定义、例题与总结。",
    "slides_total":6,
    "title":"勾股定理",
    "subtitle":"自动生成",
    "with_mp4":false
  }'
```

成功返回（关键字段）：

```json
{
  "status": "success",
  "ppt_id": "bf7dc35e556f4bb3a2da3e0c5196d42b",
  "version": 1,
  "filename": "xxxx.pptx",
  "download_url": "/api/v1/generate/download/ppt/xxxx.pptx"
}
```

### 2.2 方式 B：render（前端/业务方自己组装 plan 后直出 pptx）

- `POST /api/v1/generate/ppt/render`
- Query：
  - `with_mp4=true|false`
  - `mp4_pages=N`（可选，只生成前 N 页数字人）
  - `mp4_portrait=...`（可选）
  - `mp4_max_wait_seconds=...`（可选）
- Body：`PPTPresentation`（见下方 Schema 约定）

适用场景：
- 前端自己维护一份 plan（或从 DB 读取 plan）并直接渲染。
- 不依赖 LLM 生成 plan（避免不可控输出）。

## 3. PPT 下载

- `GET /api/v1/generate/download/ppt/{filename}`

前端通常通过 `download_url` 直接下载即可。

## 4. PPT 预览切片（渲染成 PNG）

用于前端预览页（分页图片 + 缩略图）。

### 4.1 创建预览任务

- `POST /api/v1/generate/ppt/preview`
- Body：

```json
{
  "filename": "xxxx.pptx",
  "options": {
    "width": 1600,
    "include_thumbnails": true,
    "thumb_width": 320,
    "format": "png"
  }
}
```

返回示例：

```json
{
  "preview_id": "pv_xxx",
  "status": "queued",
  "total_pages": 6,
  "progress": { "done_pages": 0, "total_pages": 6 }
}
```

### 4.2 轮询预览任务

- `GET /api/v1/generate/ppt/preview/{preview_id}`

当 `status` 为 `done` 后，返回中会提供：
- `pages_base_url`：大图 base url
- `thumbs_base_url`：缩略图 base url

### 4.3 获取图片

- `GET {pages_base_url}/{page}.png`（page 从 1 开始）
- `GET {thumbs_base_url}/{page}.png`

### 4.4 删除预览资源（可选）

- `DELETE /api/v1/generate/ppt/preview/{preview_id}`

## 5. PPT 修改（只改文本，不改格式）

### 5.1 修改接口（推荐用 /ppt）

项目当前约定：
- `POST /api/v1/generate/ppt`：修改入口（别名）
- `POST /api/v1/generate/ppt/edit`：同义接口

Body：
- `ppt_id`：必填（来自 auto_layout 返回）
- `base_version`：必填（必须等于当前版本，否则 409）
- `instructions`：必填（文字描述的修改需求）
- `session_id`：可选（用于引入 QA 历史作为修改上下文）
- `patch`：可选（推荐给“精确编辑”，不依赖 LLM）
- `title/subtitle`：可选（强制覆盖）
- `with_mp4/mp4_pages/mp4_portrait/mp4_max_wait_seconds`：可选（修改后也可生成按页视频）

#### A. Patch 模式（确定性、推荐）

只修改指定页的文本字段：
- `patch.slide_index`：从 1 开始
- 可选：`title/notes/content/content_blocks`

请求示例：

```json
{
  "ppt_id": "bf7dc35e556f4bb3a2da3e0c5196d42b",
  "base_version": 1,
  "instructions": "patch edit",
  "patch": {
    "slide_index": 2,
    "title": "勾股定理：经典例题（已修改）",
    "content": ["我们来做一道经典题", "已知两直角边是3和4", "斜边就是5"]
  },
  "with_mp4": false
}
```

#### B. LLM 模式（语义改写/扩写）

不传 `patch` 时，会走 LLM：服务端会把对话历史 + 原 plan + instructions 拼成 prompt，让模型输出一个“只改文本”的 JSON，然后服务端再合并回原 plan。

返回示例：

```json
{
  "status": "success",
  "ppt_id": "bf7dc35e556f4bb3a2da3e0c5196d42b",
  "version": 2,
  "filename": "yyyy.pptx",
  "download_url": "/api/v1/generate/download/ppt/yyyy.pptx"
}
```

## 6. 数字人视频（按页生成）

### 6.1 触发方式

触发入口有两类：
- `auto_layout`：Body 里传 `with_mp4=true`、`mp4_pages=N`
- `render`：Query 里传 `with_mp4=true`、`mp4_pages=N`
- `ppt/edit`：Body 里传 `with_mp4=true`、`mp4_pages=N`

返回会包含：
- `mp4_job_id`
- `mp4_status_url`：`/api/v1/generate/ppt/mp4/{job_id}`
- `mp4_pages_base_url`：`/api/v1/generate/ppt/mp4/{job_id}/pages`
- `mp4_total_pages`：本次视频生成页数（例如 2）

### 6.2 轮询任务状态

- `GET /api/v1/generate/ppt/mp4/{job_id}`

返回中包含：
- `status`：`queued | processing | done | failed`
- `progress`：`done_pages/total_pages`
- `pages`：每页状态（`queued/processing/done/failed`）与错误信息

### 6.3 下载某一页视频

- `GET /api/v1/generate/ppt/mp4/{job_id}/pages/{page}.mp4`

前端建议：
- 在预览第 `page` 页时，如果 `pages[page].status == done` 再请求该 mp4。
- 允许“边生成边播放”，不需要等整体 `status==done`。

## 7. Schema 约定（PPTPresentation 关键字段）

### 7.1 顶层字段（最小可用）

```json
{
  "title": "勾股定理",
  "subtitle": "6页测试",
  "template": null,
  "layout": "general",
  "cover_blocks": [["标题行"], ["副标题行"], ["作者/日期"]],
  "content_rect_default": { "unit": "ratio", "x": 0.08, "y": 0.22, "w": 0.84, "h": 0.58 },
  "slides": [ ... ]
}
```

### 7.2 slides[i]（最小可用）

```json
{
  "title": "公式与符号",
  "content": ["a² + b² = c²", "a、b 为直角边", "c 为斜边"],
  "content_blocks": [["a² + b² = c²", "a、b 为直角边", "c 为斜边"]],
  "notes": "",
  "layout_index": 1
}
```

### 7.3 content_rect_default 重要说明

`content_rect_default` 必须包含 `unit: "ratio"`，否则服务端会按默认 `emu` 解释并把小数截断为 0，导致正文文本框宽高为 0，看起来像“空白”。

## 8. 常见状态码与排查建议

- 400：参数校验失败（如 layout 不存在、mp4_pages<1、patch.slide_index 越界等）
- 404：资源不存在（如 preview_id/job_id 不存在、下载文件不存在）
- 409：修改冲突（`base_version` 与当前版本不一致）
- 500：服务端异常（LLM 输出非 JSON、渲染失败、外部服务失败等）

排查优先顺序：
- 先看响应体 `detail` 字段（FastAPI 默认会返回）
- 若为 mp4：优先查看 `/ppt/mp4/{job_id}` 的 `pages[*].error`
