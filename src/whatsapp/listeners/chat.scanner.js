import { logger } from '../../logger/logger.js';
import { delay } from '../../utils/delay.js';

export async function scanAllChats(page, onMessage) {
  logger.info('Scanning existing chats');

  // جلب قائمة المحادثات
  const chats = await page.$$('div[role="row"]');

  for (const chat of chats) {
    try {
      await chat.click();
      await delay(1500);

      // تمرير للأعلى لجلب رسائل قديمة
      for (let i = 0; i < 5; i++) {
        await page.evaluate(() => {
          const container = document.querySelector('[role="application"]');
          if (container) container.scrollTop = 0;
        });
        await delay(1200);
      }

      const messages = await page.evaluate(() => {
        return Array.from(
          document.querySelectorAll('[data-testid="msg-container"]')
        ).map((msg) => {
          const textEl = msg.querySelector('span.selectable-text');
          const text = textEl ? textEl.innerText : '';

          const links = Array.from(msg.querySelectorAll('a'))
            .map(a => a.href)
            .filter(Boolean);

          return { text, links };
        });
      });

      for (const msg of messages) {
        onMessage(msg);
      }
    } catch (err) {
      logger.warn('Failed to scan a chat');
    }
  }

  logger.info('Chat scan completed');
}
