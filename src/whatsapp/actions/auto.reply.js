import { AutoRepliesRepo } from '../../database/repositories/autoReplies.repo.js';
import { RuntimeState } from '../../state/runtime.state.js';
import { delay } from '../../utils/delay.js';
import { logger } from '../../logger/logger.js';

function matchRule(text, rule) {
  if (!rule.keyword) return true;
  return text.toLowerCase().includes(rule.keyword.toLowerCase());
}

export async function handleAutoReply(page, message) {
  if (!RuntimeState.autoReply) return;

  const { text, isGroup, senderId } = message;
  if (!text) return;

  // منع تكرار الرد في الخاص
  if (!isGroup && RuntimeState.repliedUsers.has(senderId)) return;

  const scope = isGroup ? 'group' : 'private';
  const rules = await AutoRepliesRepo.getAll(scope);

  for (const rule of rules) {
    if (matchRule(text, rule)) {
      try {
        await delay(1500 + Math.random() * 2000);
        await page.keyboard.type(rule.reply_text, { delay: 40 });
        await page.keyboard.press('Enter');

        logger.info(`Auto reply sent (${scope})`);

        if (!isGroup) {
          RuntimeState.repliedUsers.add(senderId);
        }
      } catch {
        logger.warn('Failed to send auto reply');
      }
      break;
    }
  }
}
