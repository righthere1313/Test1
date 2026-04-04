import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const filePath = path.join(__dirname, 'openapi.json');
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

const schemas = data.components.schemas;

console.log('=== DocxAutoRequest ===');
console.log(JSON.stringify(schemas.DocxAutoRequest, null, 2));

console.log('\n\n=== PPTLayoutAutoRequest ===');
console.log(JSON.stringify(schemas.PPTLayoutAutoRequest, null, 2));

console.log('\n\n=== PPTEditRequest ===');
console.log(JSON.stringify(schemas.PPTEditRequest, null, 2));

console.log('\n\n=== PPTPresentation ===');
console.log(JSON.stringify(schemas.PPTPresentation, null, 2));

console.log('\n\n=== PPTPreviewRequest ===');
console.log(JSON.stringify(schemas.PPTPreviewRequest, null, 2));

console.log('\n\n=== SlideContent ===');
console.log(JSON.stringify(schemas.SlideContent, null, 2));

console.log('\n\n=== DocxDocument ===');
console.log(JSON.stringify(schemas.DocxDocument, null, 2));

console.log('\n\n=== DocxElement ===');
console.log(JSON.stringify(schemas.DocxElement, null, 2));
