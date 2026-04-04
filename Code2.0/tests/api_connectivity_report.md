# API 连通性测试报告

- Base URL: http://localhost:8000
- Started: 2026-03-12 15:43:34
- Elapsed: 7 ms

## 总览
- 端点总数: 12
- 成功: 0
- 失败: 12

## 详细结果
- ❌ [POST] /api/v1/chat/search/fulltext -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/chat/search/fulltext (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc8262fd0>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [POST] /api/v1/chat/search/semantic -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/chat/search/semantic (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc821e3f0>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [POST] /api/v1/chat/search/hybrid -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/chat/search/hybrid (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc821e780>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [POST] /api/v1/chat/qa -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/chat/qa (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc84ad6d0>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [POST] /api/v1/files/upload -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/upload (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc82c1040>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [POST] /api/v1/files/upload/kb -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/upload/kb (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc846bce0>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [POST] /api/v1/files/upload/staging -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/upload/staging (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc82c0f30>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [GET] /api/v1/files/staging/documents -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/staging/documents (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc82c1040>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [GET] /api/v1/files/documents -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/documents (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc82c0d10>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [GET] /api/v1/files/documents/{document_id} -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/documents/nonexistent (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc82c0af0>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [GET] /api/v1/files/documents/{document_id}/versions -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/documents/nonexistent/versions (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc82c08d0>: Failed to establish a new connection: [Errno 111] Connection refused'))
- ❌ [GET] /api/v1/files/documents/{document_id}/versions/{version}/download -> None in 0ms
  - 错误: RequestError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/files/documents/nonexistent/versions/1/download (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x782fc82c07c0>: Failed to establish a new connection: [Errno 111] Connection refused'))

## 排查建议
- 连接失败(RequestError): 检查服务是否已启动、地址/端口是否正确、网络是否可达
- 404: 路由可能不存在或删除，请核对 chat.py/files.py 是否提供该端点，或路径参数是否有效
- 405: 方法不匹配，核对实际端点允许的方法
- 422: 入参不符合 Schema，请对照 OpenAPI 的请求体字段与类型
- 500: 服务内部错误，建议查看应用日志并定位对应服务实现
- SchemaError: 返回结构与 OpenAPI 定义不一致，需检查响应模型或文档