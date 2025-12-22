import { logger } from '../../logger/logger.js';

export async function isSessionAlive(page) {
  try {
    // وجود QR يعني الجلسة انتهت
    const qrExists = await page.$('canvas[aria-label]');
    if (qrExists) {
      logger.warn('WhatsApp session expired (QR detected)');
      return false;
    }

    // التأكد من تحميل واجهة واتساب
    await page.waitForSelector('div[role="application"]', {
      timeout: 5000,
    });

    return true;
  } catch (err) {
    logger.warn('WhatsApp session check failed');
    return false;
  }
}

export async function waitUntilLoggedOut(page) {
  logger.info('Waiting for WhatsApp logout');

  await page.waitForSelector('canvas[aria-label]', {
    timeout: 0,
  });

  logger.warn('WhatsApp logged out');
}
