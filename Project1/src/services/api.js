import apiConfig from '../config/api'

const request = async (url, options = {}) => {
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  }

  try {
    console.log('========== 发送API请求 ==========');
    console.log('URL:', url);
    console.log('方法:', defaultOptions.method || 'GET');
    if (defaultOptions.body) {
      console.log('请求体:', defaultOptions.body);
    }
    const response = await fetch(url, defaultOptions)
    const text = await response.text()
    
    console.log('响应状态:', response.status);
    console.log('响应内容:', text);
    
    let data
    try {
      data = text ? JSON.parse(text) : {}
    } catch (e) {
      data = {}
    }
    
    if (!response.ok) {
      let errorMessage = '请求失败'
      if (data.detail) {
        const errorTranslations = {
          'Incorrect username or password': '用户名或密码错误',
          'Username already exists': '用户名已被注册',
          'User not found': '用户不存在',
          'Invalid credentials': '凭据无效',
          'Authentication failed': '认证失败',
          'Unauthorized': '未授权访问',
          'Forbidden': '禁止访问',
          'Not found': '资源未找到',
          'Internal server error': '服务器内部错误',
          'Bad request': '请求参数错误',
          'Validation error': '数据验证失败'
        }
        if (typeof data.detail === 'string') {
          errorMessage = errorTranslations[data.detail] || data.detail
        } else if (Array.isArray(data.detail)) {
          errorMessage = data.detail.map((e) => {
            if (typeof e === 'string') return e
            if (e.msg) return e.msg
            return JSON.stringify(e)
          }).join('; ')
        } else {
          errorMessage = JSON.stringify(data.detail)
        }
      } else if (response.status === 404) {
        errorMessage = '接口不存在'
      }
      console.error('请求失败:', response.status, errorMessage, data)
      throw new Error(errorMessage)
    }
    
    return data
  } catch (error) {
    console.error('API 请求错误:', error)
    throw error
  }
}

const formDataRequest = async (url, formData, options = {}) => {
  try {
    console.log('发送FormData请求到:', url)
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      ...options,
    })
    const text = await response.text()
    
    let data
    try {
      data = text ? JSON.parse(text) : {}
    } catch (e) {
      data = {}
    }
    
    if (!response.ok) {
      let errorMessage = '请求失败'
      if (data.detail) {
        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (Array.isArray(data.detail)) {
          errorMessage = data.detail.map((e) => {
            if (typeof e === 'string') return e
            if (e.msg) return e.msg
            return JSON.stringify(e)
          }).join('; ')
        } else {
          errorMessage = JSON.stringify(data.detail)
        }
      } else if (response.status === 404) {
        errorMessage = '接口不存在'
      }
      console.error('FormData请求失败:', response.status, errorMessage, data)
      throw new Error(errorMessage)
    }
    
    return data
  } catch (error) {
    console.error('API 请求错误:', error)
    throw error
  }
}

const downloadRequest = async (url, filename) => {
  try {
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error('下载失败')
    }
    
    const blob = await response.blob()
    const urlObject = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = urlObject
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(urlObject)
  } catch (error) {
    console.error('下载错误:', error)
    throw error
  }
}

export const userAPI = {
  login: async (username, password) => {
    return request(apiConfig.USER.LOGIN, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },

  register: async (username, password) => {
    return request(apiConfig.USER.REGISTER, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },
}

export const filesAPI = {
  uploadStaging: async (file, sessionId, ttlMinutes = 120) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    formData.append('ttl_minutes', ttlMinutes.toString())
    return formDataRequest(apiConfig.FILES.UPLOAD_STAGING, formData)
  },

  getStagingDocuments: async (sessionId, includeExpired = false) => {
    const params = new URLSearchParams()
    if (sessionId) params.append('session_id', sessionId)
    if (includeExpired) params.append('include_expired', 'true')
    return request(`${apiConfig.FILES.STAGING_DOCUMENTS}?${params.toString()}`)
  },

  deleteStagingDocument: async (tempDocumentId) => {
    return request(apiConfig.FILES.STAGING_DOCUMENT(tempDocumentId), {
      method: 'DELETE',
    })
  },
}

export const chatAPI = {
  qa: async (query, options = {}) => {
    const { top_k = 5, document_id, temporary_document_ids, session_id } = options
    const requestBody = { query: query || '', top_k }
    if (document_id) requestBody.document_id = document_id
    if (temporary_document_ids && temporary_document_ids.length > 0) {
      requestBody.temporary_document_ids = temporary_document_ids
    }
    if (session_id) requestBody.session_id = session_id
    return request(apiConfig.CHAT.QA, {
      method: 'POST',
      body: JSON.stringify(requestBody),
    })
  },

  intentDetect: async (query) => {
    return request(apiConfig.CHAT.INTENT_DETECT, {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
  },
}

export const generateAPI = {
  createPptPreview: async (requestData) => {
    return request(apiConfig.GENERATE.PPT_PREVIEW, {
      method: 'POST',
      body: JSON.stringify(requestData),
    })
  },

  getPptPreview: async (previewId) => {
    return request(apiConfig.GENERATE.PPT_PREVIEW_GET(previewId))
  },

  generatePptAutoLayout: async (requestData) => {
    return request(apiConfig.GENERATE.PPT_AUTO_LAYOUT, {
      method: 'POST',
      body: JSON.stringify(requestData),
    })
  },

  generateDocxAuto: async (requestData) => {
    return request(apiConfig.GENERATE.DOCX_AUTO, {
      method: 'POST',
      body: JSON.stringify(requestData),
    })
  },

  downloadFile: async (fileType, filename) => {
    return downloadRequest(apiConfig.GENERATE.DOWNLOAD(fileType, filename), filename)
  },

  downloadPpt: async (filename) => {
    return downloadRequest(apiConfig.GENERATE.DOWNLOAD('ppt', filename), filename)
  },

  downloadDocx: async (filename) => {
    return downloadRequest(apiConfig.GENERATE.DOWNLOAD('docx', filename), filename)
  },
}

export const templatesAPI = {
  getLayouts: async () => {
    console.log('========== 调用getLayouts API ==========');
    console.log('API URL:', apiConfig.TEMPLATES.LAYOUTS);
    const result = await request(apiConfig.TEMPLATES.LAYOUTS);
    console.log('✅ getLayouts API返回结果:', result);
    console.log('返回结果类型:', typeof result);
    return result;
  },

  getCovers: async () => {
    console.log('========== 调用getCovers API ==========');
    console.log('API URL:', apiConfig.TEMPLATES.COVERS);
    const result = await request(apiConfig.TEMPLATES.COVERS);
    console.log('✅ getCovers API返回结果:', result);
    return result;
  },

  getLayoutDesignSpec: async (layout) => {
    const params = new URLSearchParams()
    params.append('layout', layout)
    return request(`${apiConfig.TEMPLATES.LAYOUT_DESIGN_SPEC}?${params.toString()}`)
  },

  getLayoutSvg: async (layout, name) => {
    const params = new URLSearchParams()
    params.append('layout', layout)
    params.append('name', name)
    return request(`${apiConfig.TEMPLATES.LAYOUT_SVG}?${params.toString()}`)
  },
}

export const documentsAPI = {
  getList: async () => {
    return request(apiConfig.FILES.DOCUMENTS)
  },
  
  upload: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return formDataRequest(apiConfig.FILES.UPLOAD_KB, formData)
  },
  
  getDetail: async (documentId) => {
    return request(apiConfig.FILES.DOCUMENT_DETAIL(documentId))
  },
  
  getVersions: async (documentId) => {
    return request(apiConfig.FILES.DOCUMENT_VERSIONS(documentId))
  },
  
  downloadVersion: async (documentId, version) => {
    const response = await fetch(apiConfig.FILES.DOWNLOAD_VERSION(documentId, version))
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `document_${documentId}_v${version}.pdf`
    a.click()
    window.URL.revokeObjectURL(url)
  },
  
  delete: async (documentId) => {
    return request(apiConfig.FILES.DOCUMENT_DETAIL(documentId), {
      method: 'DELETE',
    })
  },
}

export const searchAPI = {
  fulltext: async (query, options = {}) => {
    const { top_k = 5, document_id } = options;
    const requestBody = {
      query,
      top_k,
      ...(document_id && { document_id })
    };
    return request(apiConfig.SEARCH.FULLTEXT, {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  },
  
  semantic: async (query, options = {}) => {
    const { top_k = 5, document_id } = options;
    const requestBody = {
      query,
      top_k,
      ...(document_id && { document_id })
    };
    return request(apiConfig.SEARCH.SEMANTIC, {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  },
  
  hybrid: async (query, options = {}) => {
    const { top_k = 5, document_id } = options;
    const requestBody = {
      query,
      top_k,
      ...(document_id && { document_id })
    };
    return request(apiConfig.SEARCH.HYBRID, {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  },
}

export default {
  user: userAPI,
  files: filesAPI,
  chat: chatAPI,
  generate: generateAPI,
  documents: documentsAPI,
  search: searchAPI,
  templates: templatesAPI,
}
