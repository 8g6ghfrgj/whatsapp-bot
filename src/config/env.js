import dotenv from 'dotenv';

dotenv.config();

const REQUIRED_VARS = [
  'TELEGRAM_BOT_TOKEN',
  'TELEGRAM_ADMIN_ID',
];

for (const key of REQUIRED_VARS) {
  if (!process.env[key]) {
    console.error(`❌ Missing required environment variable: ${key}`);
    process.exit(1);
  }
}

export const ENV = {
  NODE_ENV: process.env.NODE_ENV || 'production',
  APP_NAME: process.env.APP_NAME || 'WhatsApp Telegram Controller',

  TELEGRAM: {
    TOKEN: process.env.TELEGRAM_BOT_TOKEN,
    ADMIN_ID: Number(process.env.TELEGRAM_ADMIN_ID),
  },

  PATHS: {
    CHROME_DATA: process.env.CHROME_DATA_PATH || './chrome-data',
    EXPORTS: process.env.EXPORT_PATH || './exports',
  },

  LOG_LEVEL: process.env.LOG_LEVEL || 'info',
};
