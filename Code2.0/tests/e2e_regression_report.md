# 端到端回归测试报告

- Started: 1773818308175
- Duration: 1579 ms
- Pass Rate: 100.0%

## 覆盖率分析
- 端点覆盖: 7/7
- 功能覆盖: 5/5

## 性能指标
- Avg Latency: 224.86 ms
- Min Latency: 3 ms
- Max Latency: 1288 ms

## 详细结果
- ✅ [POST] /api/v1/files/upload/kb -> 201 in 157ms
- ✅ [POST] /api/v1/files/upload/staging -> 201 in 84ms
- ✅ [GET] /api/v1/files/staging/documents -> 200 in 6ms
- ✅ [POST] /api/v1/chat/search/fulltext -> 200 in 3ms
- ✅ [POST] /api/v1/chat/search/semantic -> 200 in 26ms
- ✅ [POST] /api/v1/chat/search/hybrid -> 200 in 10ms
- ✅ [POST] /api/v1/chat/qa -> 200 in 1288ms

## 问题修复验证结果
- LLM 初始化可用: True
- CrossEncoder 可用: True