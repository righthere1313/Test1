import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const filePath = path.join(__dirname, 'openapi.json');
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

console.log('=== 具体的请求/响应格式 ===\n');

const schemas = data.components.schemas;

const importantSchemas = [
  'DocxAutoRequest',
  'PPTEditRequest',
  'PPTLayoutAutoRequest',
  'AnswerRequest',
  'AnswerResponse',
  'IntentDetectRequest',
  'IntentDetectResponse'
];

for (const name of importantSchemas) {
  if (schemas[name]) {
    console.log(`\n【${name}】`);
    console.log(JSON.stringify(schemas[name], null, 2));
  }
}

console.log('\n\n=== 生成接口的详细信息 ===\n');

const generatePaths = Object.entries(data.paths).filter(([path]) => 
  path.includes('/generate/ppt') || path.includes('/generate/docx')
);

for (const [path, methods] of generatePaths) {
  for (const [method, details] of Object.entries(methods)) {
    console.log(`\n【${method.toUpperCase()} ${path}】`);
    if (details.requestBody) {
      console.log('请求体:');
      console.log(JSON.stringify(details.requestBody, null, 2));
    }
    if (details.responses) {
      console.log('响应:');
      console.log(JSON.stringify(details.responses, null, 2));
    }
  }
}
