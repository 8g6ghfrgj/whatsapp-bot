import { delay } from '../../utils/delay.js';
import { RuntimeState } from '../../state/runtime.state.js';
import { AdsRepo } from '../../database/repositories/ads.repo.js';
import { logger } from '../../logger/logger.js';

export async function startAutoPosting(page) {
  const ad = await AdsRepo.getLatest();
  if (!ad) throw new Error('No ad found');

  RuntimeState.autoPosting = true;
  logger.info('Auto posting started');

  const chats = await page.$$('div[role="row"]');

  // ترتيب عشوائي
  const shuffled = chats.sort(() => Math.random() - 0.5);

  for (const chat of shuffled) {
    if (!RuntimeState.autoPosting) break;

    try {
      await chat.click();
      await delay(2000 + Math.random() * 3000);

      if (ad.type === 'text' && ad.content) {
        await page.keyboard.type(ad.content, { delay: 40 });
        await page.keyboard.press('Enter');
      }

      await delay(30000 + Math.random() * 60000); // 30–90 ثانية
    } catch {
      logger.warn('Failed to post in a chat');
    }
  }

  RuntimeState.autoPosting = false;
  logger.info('Auto posting finished');
}

export function stopAutoPosting() {
  RuntimeState.autoPosting = false;
}
