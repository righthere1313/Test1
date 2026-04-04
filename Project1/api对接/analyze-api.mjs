import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const filePath = path.join(__dirname, 'openapi.json');
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

console.log('=== API 接口清单 ===\n');

const paths = data.paths;
const endpoints = [];

for (const [path, methods] of Object.entries(paths)) {
    for (const [method, details] of Object.entries(methods)) {
        endpoints.push({
            method: method.toUpperCase(),
            path: path,
            summary: details.summary || '',
            operationId: details.operationId || ''
        });
    }
}

// 按标签分组
const groups = {};
for (const ep of endpoints) {
    let group = '其他';
    if (ep.path.includes('/files/')) group = '文件';
    else if (ep.path.includes('/chat/')) group = '对话';
    else if (ep.path.includes('/generate/')) group = '生成';
    else if (ep.path.includes('/templates/')) group = '模板';
    else if (ep.path.includes('/history/')) group = '历史';
    else if (ep.path.includes('/user/')) group = '用户';
    
    if (!groups[group]) groups[group] = [];
    groups[group].push(ep);
}

let output = '=== API 接口清单 ===\n\n';

for (const [group, items] of Object.entries(groups)) {
    output += `\n【${group}】\n`;
    console.log(`\n【${group}】`);
    for (const item of items) {
        const line = `  ${item.method.padEnd(6)} ${item.path}`;
        output += line + '\n';
        console.log(line);
        if (item.summary) {
            const summaryLine = `         ${item.summary}`;
            output += summaryLine + '\n';
            console.log(summaryLine);
        }
    }
}

console.log('\n=== 组件定义 ===\n');
output += '\n=== 组件定义 ===\n\n';
if (data.components && data.components.schemas) {
    for (const [name, schema] of Object.entries(data.components.schemas)) {
        console.log(`- ${name}`);
        output += `- ${name}\n`;
    }
}

// 保存到文件
fs.writeFileSync(path.join(__dirname, 'api-analysis.txt'), output);
console.log('\n分析结果已保存到 api-analysis.txt');
