import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

// تحميل ملف البيئة
dotenv.config();

// دعم __dirname في ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// دالة تحقق من القيم المطلوبة
function requireEnv(name, defaultValue = null) {
  const value = process.env[name] ?? defaultValue;
  if (value === null || value === undefined) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

// تصدير الإعدادات
const config = {
  app: {
    name: 'WhatsApp Companion Bot',
    logLevel: requireEnv('LOG_LEVEL', 'info')
  },

  session: {
    name: requireEnv('SESSION_NAME'),
    path: path.resolve(requireEnv('SESSION_PATH'))
  },

  database: {
    path: path.resolve(requireEnv('DATABASE_PATH'))
  },

  delays: {
    default: Number(requireEnv('DEFAULT_DELAY', 2000)),
    groupJoin: Number(requireEnv('GROUP_JOIN_DELAY', 120000)),
    groupJoinTimeout: Number(requireEnv('GROUP_JOIN_TIMEOUT', 86400000))
  },

  features: {
    autoReply: requireEnv('AUTO_REPLY_ENABLED', 'false') === 'true',
    autoPost: requireEnv('AUTO_POST_ENABLED', 'false') === 'true'
  },

  safety: {
    autoReconnect: requireEnv('AUTO_RECONNECT', 'true') === 'true',
    clearSessionOnLogout:
      requireEnv('CLEAR_SESSION_ON_LOGOUT', 'false') === 'true',
    maxGroupsPerCycle: Number(requireEnv('MAX_GROUPS_PER_CYCLE', 9999))
  },

  paths: {
    root: path.resolve(__dirname, '..'),
    data: path.resolve(__dirname, '..', 'data'),
    sessions: path.resolve(requireEnv('SESSION_PATH')),
    logs: path.resolve(__dirname, '..', 'data', 'logs'),
    exports: path.resolve(__dirname, '..', 'data', 'exports')
  }
};

export default config;
