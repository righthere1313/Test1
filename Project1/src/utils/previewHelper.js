import { generateAPI } from '../services/api'
import apiConfig from '../config/api'

export const loadPptPreview = async (store, filename) => {
  try {
    console.log('========== 开始加载PPT预览（后台） ==========');
    console.log('PPT文件名:', filename);
    
    let pptPreviewId = null;
    
    if (!pptPreviewId) {
      console.log('创建PPT预览...');
      const previewData = await generateAPI.createPptPreview({
        filename: filename
      });
      console.log('✅ PPT预览创建成功:', previewData);
      pptPreviewId = previewData.preview_id || previewData.id;
    }
    
    console.log('开始轮询获取PPT预览状态...');
    let previewInfo = null;
    let pollCount = 0;
    const maxPollCount = 30;
    
    while (pollCount < maxPollCount) {
      pollCount++;
      console.log(`轮询第 ${pollCount} 次...`);
      
      previewInfo = await generateAPI.getPptPreview(pptPreviewId);
      console.log('当前预览状态:', previewInfo.status);
      
      if (previewInfo.status === 'done') {
        console.log('✅ PPT预览完成！');
        break;
      } else if (previewInfo.status === 'failed') {
        console.warn('⚠️ PPT预览生成失败:', previewInfo.error);
        break;
      }
      
      console.log(`等待中，当前进度: ${previewInfo.progress?.done_pages || 0}/${previewInfo.progress?.total_pages || 0}`);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    if (!previewInfo) {
      console.warn('⚠️ 无法获取预览信息');
      return false;
    }
    
    console.log('最终预览信息:', previewInfo);
    
    let pageCount = 0;
    if (previewInfo.pages) {
      pageCount = typeof previewInfo.pages === 'number' ? previewInfo.pages : previewInfo.pages.length;
    } else if (previewInfo.total_pages) {
      pageCount = previewInfo.total_pages;
    }
    
    const pages = pageCount > 0 ? Array.from({ length: pageCount }, (_, i) => i + 1) : [];
    
    store.setGeneratedFiles(
      store.generatedFiles.pptFilename,
      store.generatedFiles.docxFilename,
      pptPreviewId,
      pages,
      null,
      true
    );
    
    console.log('✅ PPT预览加载完成，已保存到store');
    return true;
  } catch (error) {
    console.error('❌ 加载PPT预览失败:', error);
    return false;
  }
};
