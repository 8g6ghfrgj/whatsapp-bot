import fs from 'fs';
import path from 'path';
import {
  useMultiFileAuthState,
  fetchLatestBaileysVersion
} from '@whiskeysockets/baileys';
import config from '../config.js';

/**
 * التأكد من وجود مجلد
 */
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

/**
 * تهيئة مجلدات الجلسة
 */
function prepareSessionDirectories() {
  ensureDir(config.paths.data);
  ensureDir(config.paths.sessions);
  ensureDir(config.paths.logs);
  ensureDir(config.paths.exports);
}

/**
 * تحميل حالة المصادقة (Auth State)
 */
export async function loadAuthState() {
  prepareSessionDirectories();

  const sessionDir = path.join(
    config.session.path,
    config.session.name
  );

  ensureDir(sessionDir);

  const { state, saveCreds } = await useMultiFileAuthState(sessionDir);

  return {
    authState: state,
    saveCreds
  };
}

/**
 * جلب نسخة Baileys المتوافقة
 */
export async function getBaileysVersion() {
  const { version, isLatest } = await fetchLatestBaileysVersion();

  return {
    version,
    isLatest
  };
}

/**
 * حذف الجلسة (عند الحاجة)
 */
export function clearSession() {
  const sessionDir = path.join(
    config.session.path,
    config.session.name
  );

  if (fs.existsSync(sessionDir)) {
    fs.rmSync(sessionDir, {
      recursive: true,
      force: true
    });
  }
}
