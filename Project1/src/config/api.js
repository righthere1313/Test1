const getApiBaseUrl = () => {
  if (typeof window !== 'undefined' && window.__APP_CONFIG__ && window.__APP_CONFIG__.API_BASE) {
    return window.__APP_CONFIG__.API_BASE;
  }
  return 'http://localhost:8000/api/v1';
}

const getApiOrigin = () => {
  const baseUrl = getApiBaseUrl();
  const url = new URL(baseUrl);
  return url.origin;
}

const API_BASE_URL = getApiBaseUrl();
const API_ORIGIN = getApiOrigin();

export default {
  API_BASE_URL,
  API_ORIGIN,
  
  USER: {
    LOGIN: `${API_BASE_URL}/user/login`,
    REGISTER: `${API_BASE_URL}/user/register`,
  },
  
  FILES: {
    UPLOAD_STAGING: `${API_BASE_URL}/files/upload/staging`,
    STAGING_DOCUMENTS: `${API_BASE_URL}/files/staging/documents`,
    STAGING_DOCUMENT: (tempDocumentId) => `${API_BASE_URL}/files/staging/documents/${tempDocumentId}`,
    DOCUMENTS: `${API_BASE_URL}/files/documents`,
    UPLOAD_KB: `${API_BASE_URL}/files/upload/kb`,
    DOCUMENT_DETAIL: (documentId) => `${API_BASE_URL}/files/documents/${documentId}`,
    DOCUMENT_VERSIONS: (documentId) => `${API_BASE_URL}/files/documents/${documentId}/versions`,
    DOWNLOAD_VERSION: (documentId, version) => `${API_BASE_URL}/files/documents/${documentId}/versions/${version}/download`,
  },
  
  CHAT: {
    FULLTEXT: `${API_BASE_URL}/chat/search/fulltext`,
    SEMANTIC: `${API_BASE_URL}/chat/search/semantic`,
    HYBRID: `${API_BASE_URL}/chat/search/hybrid`,
    QA: `${API_BASE_URL}/chat/qa`,
    INTENT_DETECT: `${API_BASE_URL}/chat/intent/detect`,
  },
  
  GENERATE: {
    PPT_PREVIEW: `${API_BASE_URL}/generate/ppt/preview`,
    PPT_PREVIEW_GET: (previewId) => `${API_BASE_URL}/generate/ppt/preview/${previewId}`,
    PPT_PREVIEW_PAGE: (previewId, page) => `${API_BASE_URL}/generate/ppt/preview/${previewId}/pages/${page}.png`,
    PPT_PREVIEW_THUMB: (previewId, page) => `${API_BASE_URL}/generate/ppt/preview/${previewId}/thumbs/${page}.png`,
    PPT_AUTO_LAYOUT: `${API_BASE_URL}/generate/ppt/auto_layout`,
    DOCX_AUTO: `${API_BASE_URL}/generate/docx/auto`,
    DOWNLOAD: (fileType, filename) => `${API_BASE_URL}/generate/download/${fileType}/${filename}`,
  },

  TEMPLATES: {
    LAYOUTS: `${API_BASE_URL}/templates/layouts`,
    LAYOUT_DESIGN_SPEC: `${API_BASE_URL}/templates/layouts/design_spec`,
    LAYOUT_SVG: `${API_BASE_URL}/templates/layouts/svg`,
    COVERS: `${API_BASE_URL}/templates/covers`,
  },
}
