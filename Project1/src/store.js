import { reactive, watch } from 'vue'
import { userAPI } from './services/api'

const loadFromStorage = () => {
  try {
    const saved = localStorage.getItem('appState')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load from localStorage:', e)
  }
  return null
}

const generateSessionId = () => {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

const savedState = loadFromStorage()

const store = reactive({
  isLoggedIn: savedState?.isLoggedIn || false,
  isLoading: false,
  sessionId: savedState?.sessionId || generateSessionId(),
  user: savedState?.user || {
    id: null,
    username: '老师',
    avatar: null,
    teacherName: '',
    subject: '',
    schoolName: '',
    teachingSubject: null,
    teachingStyle: null,
    password: ''
  },
  chatHistory: [],
  temporaryDocumentIds: [],
  generatedFiles: {
    pptFilename: null,
    docxFilename: null,
    pptPreviewId: null,
    pptPreviewPages: [],
    wordContent: null,
    pptPreviewLoaded: false
  },
  selectedPptTemplate: savedState?.selectedPptTemplate || null,
  teachingRequirements: savedState?.teachingRequirements || null,
  generationHistory: savedState?.generationHistory || [],
  currentGenerationId: null,
  previewTab: 'ppt',

  init() {
    if (savedState?.isLoggedIn) {
      this.isLoggedIn = true
      this.user = { ...this.user, ...savedState.user }
    }
    if (!savedState?.sessionId) {
      this.sessionId = generateSessionId()
    }
  },

  async login(username, password) {
    try {
      const userData = await userAPI.login(username, password)
      this.isLoggedIn = true
      this.user = {
        ...this.user,
        id: userData.id,
        username: userData.username,
        teachingSubject: userData.teaching_subject,
        teachingStyle: userData.teaching_style,
        subject: userData.teaching_subject || '',
      }
      this.chatHistory = []
      this.temporaryDocumentIds = []
      this.sessionId = generateSessionId()
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  async register(username, password) {
    try {
      await userAPI.register(username, password)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  addMessage(message) {
    this.chatHistory.push(message)
  },

  addTemporaryDocument(docId) {
    if (!this.temporaryDocumentIds.includes(docId)) {
      this.temporaryDocumentIds.push(docId)
    }
  },

  clearTemporaryDocuments() {
    this.temporaryDocumentIds = []
  },

  setGeneratedFiles(pptFilename, docxFilename, pptPreviewId, pptPreviewPages, wordContent, pptPreviewLoaded) {
    if (pptFilename) this.generatedFiles.pptFilename = pptFilename
    if (docxFilename) this.generatedFiles.docxFilename = docxFilename
    if (pptPreviewId) this.generatedFiles.pptPreviewId = pptPreviewId
    if (pptPreviewPages) this.generatedFiles.pptPreviewPages = pptPreviewPages
    if (wordContent) this.generatedFiles.wordContent = wordContent
    if (typeof pptPreviewLoaded !== 'undefined') this.generatedFiles.pptPreviewLoaded = pptPreviewLoaded
  },

  clearGeneratedFiles() {
    this.generatedFiles = { 
      pptFilename: null, 
      docxFilename: null, 
      pptPreviewId: null, 
      pptPreviewPages: [], 
      wordContent: null 
    }
  },

  addGeneration(generation) {
    const newGeneration = {
      id: 'gen_' + Date.now(),
      timestamp: Date.now(),
      sessionId: this.sessionId,
      ...generation
    }
    this.generationHistory.unshift(newGeneration)
    this.currentGenerationId = newGeneration.id
    return newGeneration
  },

  updateGeneration(generationId, updates) {
    const index = this.generationHistory.findIndex(g => g.id === generationId)
    if (index !== -1) {
      this.generationHistory[index] = {
        ...this.generationHistory[index],
        ...updates
      }
    }
  },

  getGenerationById(generationId) {
    return this.generationHistory.find(g => g.id === generationId)
  },

  setCurrentGeneration(generation) {
    if (generation) {
      this.currentGenerationId = generation.id
      this.setGeneratedFiles(
        generation.pptFilename,
        generation.docxFilename,
        generation.pptPreviewId,
        generation.pptPreviewPages,
        generation.wordContent
      )
      if (generation.requirements) {
        this.setTeachingRequirements(generation.requirements)
      }
      if (generation.selectedTemplate) {
        this.setSelectedPptTemplate(generation.selectedTemplate)
      }
    }
  },

  setSelectedPptTemplate(template) {
    this.selectedPptTemplate = template
  },

  clearSelectedPptTemplate() {
    this.selectedPptTemplate = null
  },

  setTeachingRequirements(requirements) {
    this.teachingRequirements = requirements
  },

  clearTeachingRequirements() {
    this.teachingRequirements = null
  },

  setPreviewTab(tab) {
    this.previewTab = tab
  },

  updateUser(userData) {
    Object.assign(this.user, userData)
  },

  logout() {
    this.isLoggedIn = false
    this.user = {
      id: null,
      username: '老师',
      avatar: null,
      teacherName: '',
      subject: '',
      schoolName: '',
      teachingSubject: null,
      teachingStyle: null,
      password: ''
    }
    this.chatHistory = []
    this.temporaryDocumentIds = []
    this.sessionId = generateSessionId()
    this.clearGeneratedFiles()
    localStorage.removeItem('appState')
  }
})

watch(
  () => ({ 
    isLoggedIn: store.isLoggedIn, 
    user: store.user, 
    sessionId: store.sessionId,
    selectedPptTemplate: store.selectedPptTemplate,
    teachingRequirements: store.teachingRequirements,
    generationHistory: store.generationHistory
  }),
  (newState) => {
    localStorage.setItem('appState', JSON.stringify(newState))
  },
  { deep: true }
)

store.init()

export default store
