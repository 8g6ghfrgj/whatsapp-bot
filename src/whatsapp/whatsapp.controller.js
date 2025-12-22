import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';
import { logger } from '../logger/logger.js';
import { PATHS } from '../config/paths.js';

// ================================
// Internal State
// ================================
let browser = null;
let page = null;

let loggedIn = false;
let qrSent = false;

let currentProfilePath = null;

// ================================
// Helpers
// ================================
function createProfilePath() {
  const id = `account_${Date.now()}`;
  return path.join(PATHS.CHROME_DATA, 'accounts', id);
}

async function closeBrowser() {
  try {
    if (page) {
      await page.close();
      page = null;
    }
    if (browser) {
      await browser.close();
      browser = null;
    }
  } catch (_) {}
}

async function launchBrowser(profilePath) {
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

  page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });
}

// ================================
// Login Detection
// ================================
async function waitForLogin() {
  const interval = setInterval(async () => {
    try {
      const isLogged = await page.evaluate(() => {
        return Boolean(
          document.querySelector('[data-testid="chat-list"]')
        );
      });

      if (isLogged) {
        loggedIn = true;
        qrSent = false;
        clearInterval(interval);
        logger.info('WhatsApp linked successfully');
      }
    } catch (_) {}
  }, 2000);
}

// ================================
// Public API
// ================================

/**
 * بدء جلسة واتساب
 * @param {Function} onQR callback لإرسال QR
 * @param {Boolean} forceRestart هل نعيد تشغيل Chrome لإحضار QR جديد
 */
export async function startWhatsAppSession(onQR, forceRestart = false) {
  try {
    // إذا الحساب مربوط فعليًا
    if (loggedIn) {
      logger.info('WhatsApp already logged in');
      return;
    }

    // إذا نحتاج QR جديد → نغلق كل شيء ونبدأ من جديد
    if (forceRestart) {
      logger.info('Forcing new WhatsApp session');
      await closeBrowser();
      qrSent = false;
    }

    // إذا فيه QR أُرسل سابقًا ولم يُطلب إعادة
    if (qrSent && !forceRestart) {
      logger.info('QR already sent, waiting for scan');
      return;
    }

    // إنشاء بروفايل جديد
    currentProfilePath = createProfilePath();
    fs.mkdirSync(currentProfilePath, { recursive: true });

    await launchBrowser(currentProfilePath);

    logger.info(`Opening WhatsApp Web`);
    await page.goto('https://web.whatsapp.com', {
      waitUntil: 'domcontentloaded',
    });

    // ننتظر QR الرسمي الحقيقي
    const qrElement = await page.waitForSelector(
      'canvas, img[alt*="Scan"]',
      { timeout: 60000 }
    );

    // نلتقط QR مرة واحدة فقط
    const qrBuffer = await qrElement.screenshot({ type: 'png' });
    qrSent = true;

    logger.info('Valid WhatsApp QR captured');

    // نرسله للمستخدم
    await onQR(qrBuffer);

    // نبدأ مراقبة تسجيل الدخول
    await waitForLogin();
  } catch (err) {
    logger.error(`Failed to start WhatsApp session: ${err.message}`);
    await closeBrowser();
    qrSent = false;
  }
}

/**
 * هل واتساب مربوط؟
 */
export async function isWhatsAppLoggedIn() {
  return loggedIn;
}

/**
 * تسجيل خروج من واتساب
 */
export async function logoutWhatsApp() {
  try {
    if (!page || !loggedIn) return;

    await page.evaluate(() => {
      const menu = document.querySelector('[data-testid="menu"]');
      menu?.click();
    });

    await page.waitForTimeout(1000);

    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('span'))
        .find(el => el.innerText.includes('تسجيل الخروج'));
      btn?.click();
    });

    loggedIn = false;
    qrSent = false;

    logger.info('WhatsApp logged out');
  } catch (err) {
    logger.error('Logout failed');
  }
}

/**
 * حذف الجلسة نهائيًا
 */
export async function destroyWhatsAppSession() {
  try {
    loggedIn = false;
    qrSent = false;

    await closeBrowser();

    if (currentProfilePath && fs.existsSync(currentProfilePath)) {
      fs.rmSync(currentProfilePath, { recursive: true, force: true });
    }

    currentProfilePath = null;

    logger.info('WhatsApp session destroyed');
  } catch (err) {
    logger.error('Failed to destroy session');
  }
}
