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

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
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
function watchForLogin() {
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
        logger.info('WhatsApp device linked successfully');
      }
    } catch (_) {}
  }, 2000);
}

// ================================
// Public API
// ================================
export async function startWhatsAppSession(onQR, forceRestart = false) {
  try {
    if (loggedIn) {
      logger.info('WhatsApp already linked');
      return;
    }

    if (forceRestart) {
      logger.info('Forcing new WhatsApp session');
      await closeBrowser();
      qrSent = false;
    }

    if (qrSent && !forceRestart) {
      logger.info('QR already sent, waiting for scan');
      return;
    }

    currentProfilePath = createProfilePath();
    fs.mkdirSync(currentProfilePath, { recursive: true });

    await launchBrowser(currentProfilePath);

    logger.info('Opening WhatsApp Web');
    await page.goto('https://web.whatsapp.com', {
      waitUntil: 'domcontentloaded',
    });

    // ================================
    // Detect OFFICIAL WhatsApp QR
    // ================================
    const qrSelectors = [
      '[data-testid="qrcode"]',
      'canvas[aria-label]',
      'canvas',
      'img[src^="data:image"]',
    ];

    let qrElement = null;

    for (const selector of qrSelectors) {
      try {
        qrElement = await page.waitForSelector(selector, { timeout: 15000 });
        if (qrElement) {
          logger.info(`QR found using selector: ${selector}`);
          break;
        }
      } catch (_) {}
    }

    if (!qrElement) {
      throw new Error('Failed to detect WhatsApp QR element');
    }

    // انتظار تثبيت الـ QR (بدون waitForTimeout)
    await delay(1500);

    const qrBuffer = await qrElement.screenshot({ type: 'png' });

    qrSent = true;
    logger.info('Official WhatsApp linking QR captured');

    await onQR(qrBuffer);

    watchForLogin();
  } catch (err) {
    logger.error(`Failed to start WhatsApp session: ${err.message}`);
    await closeBrowser();
    qrSent = false;
  }
}

export async function isWhatsAppLoggedIn() {
  return loggedIn;
}

export async function logoutWhatsApp() {
  try {
    if (!page || !loggedIn) return;

    await page.evaluate(() => {
      document.querySelector('[data-testid="menu"]')?.click();
    });

    await delay(1000);

    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('span'))
        .find(el => el.innerText.includes('تسجيل الخروج'));
      btn?.click();
    });

    loggedIn = false;
    qrSent = false;

    logger.info('WhatsApp logged out');
  } catch (_) {}
}

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
  } catch (_) {}
}
