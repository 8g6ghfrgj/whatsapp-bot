import fs from 'fs';
import path from 'path';
import { PATHS } from '../config/paths.js';

export function exportTxt(filename, lines = []) {
  const exportDir = path.join(PATHS.EXPORTS, 'links');

  if (!fs.existsSync(exportDir)) {
    fs.mkdirSync(exportDir, { recursive: true });
  }

  const filePath = path.join(exportDir, filename);

  const uniqueLines = [...new Set(lines)].filter(Boolean);

  fs.writeFileSync(
    filePath,
    uniqueLines.join('\n'),
    'utf8'
  );

  return filePath;
}
