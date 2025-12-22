import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';
import { logger } from '../logger/logger.js';
import { PATHS } from '../config/paths.js';

// ================================
// Internal State (Singleton)
// ================================
let browser = null;
let page = null;

let currentQR = null;          // Buffer
let qrListener = null;         // function
let loggedIn = false;
let sessionStarting = false;

let currentProfilePath = null;

// ================================
// Helpers
// ================================
function generateProfilePath() {
  const id = `account_${Date.now()}`;
  return path.join(PATHS.CHROME_DATA, 'accounts', id);
}

function clearQR() {
  currentQR = null;
  qrListener = null;
}

async function ensureBrowser(profilePath) {
  if (browser) return;

  browser = await puppeteer.launch({
    headless: false,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ],
    userDataDir: profilePath,
  });

  logger.info(`Launching Chrome with profile: ${profilePath}`);

  page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });
}

// ================================
// QR Watcher (FAST)
// ================================
async function watchForQR() {
  await page.exposeFunction('onQRDetected', async (dataUrl) => {
    try {
      const base64 = dataUrl.split(',')[1];
      currentQR = Buffer.from(base64, 'base64');

      logger.info('QR code captured');

      if (qrListener) {
        await qrListener(currentQR);
      }
    } catch (err) {
      logger.error('Failed to capture QR');
    }
  });

  await page.evaluate(() => {
    const observer = new MutationObserver(() => {
      const canvas = document.querySelector('canvas');
      if (canvas) {
        const dataUrl = canvas.toDataURL();
        window.onQRDetected(dataUrl);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
}

// ================================
// Login Watcher
// ================================
async function watchForLogin() {
  const check = async () => {
    try {
      const logged = await page.evaluate(() => {
        return Boolean(
          document.querySelector('[data-testid="chat-list"]')
        );
      });

      if (logged && !loggedIn) {
        loggedIn = true;
        clearQR();
        logger.info('WhatsApp login detected');
      }
    } catch (_) {}
  };

  const interval = setInterval(async () => {
    if (!page || page.isClosed()) {
      clearInterval(interval);
      return;
    }
    await check();
  }, 2000);
}

// ================================
// Public API
// ================================

/**
 * بدء جلسة واتساب
 * يلتقط QR فور ظهوره
 */
export async function startWhatsAppSession(onQR) {
  if (sessionStarting || loggedIn) {
    logger.warn('Session already running');
    return;
  }

  sessionStarting = true;
  qrListener = onQR;

  try {
    currentProfilePath = generateProfilePath();
    fs.mkdirSync(currentProfilePath, { recursive: true });

    await ensureBrowser(currentProfilePath);

    await page.goto('https://web.whatsapp.com', {
      waitUntil: 'domcontentloaded',
    });

    await watchForQR();
    await watchForLogin();

    logger.info('WhatsApp not logged in (QR visible)');
  } catch (err) {
    logger.error(`Failed to start WhatsApp session: ${err.message}`);
    sessionStarting = false;
  }
}

/**
 * هل واتساب مسجل دخول فعليًا؟
 */
export async function isWhatsAppLoggedIn() {
  return loggedIn;
}

/**
 * الحصول على آخر QR (إعادة إرسال فورية)
 */
export function getCurrentQR() {
  return currentQR;
}

/**
 * تسجيل خروج من واتساب
 */
export async function logoutWhatsApp() {
  if (!page || !loggedIn) return;

  try {
    await page.evaluate(() => {
      const menuBtn = document.querySelector('[data-testid="menu"]');
      menuBtn?.click();
    });

    await page.waitForTimeout(1000);

    await page.evaluate(() => {
      const logoutBtn = Array.from(
        document.querySelectorAll('span')
      ).find((el) => el.innerText.includes('تسجيل الخروج'));

      logoutBtn?.click();
    });

    loggedIn = false;
    clearQR();

    logger.info('WhatsApp logged out');
  } catch (err) {
    logger.error('Failed to logout WhatsApp');
  }
}

/**
 * حذف الجلسة نهائيًا
 */
export async function destroyWhatsAppSession() {
  try {
    loggedIn = false;
    clearQR();
    sessionStarting = false;

    if (page) {
      await page.close();
      page = null;
    }

    if (browser) {
      await browser.close();
      browser = null;
    }

    if (currentProfilePath && fs.existsSync(currentProfilePath)) {
      fs.rmSync(currentProfilePath, {
        recursive: true,
        force: true,
      });
    }

    currentProfilePath = null;

    logger.info('WhatsApp session destroyed');
  } catch (err) {
    logger.error('Failed to destroy WhatsApp session');
  }
}
