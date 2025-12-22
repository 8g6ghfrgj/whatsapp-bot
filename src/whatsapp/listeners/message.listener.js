import { logger } from '../../logger/logger.js';

export async function listenForNewMessages(page, onMessage) {
  logger.info('Listening for new WhatsApp messages');

  // تمرير callback من Node إلى المتصفح
  await page.exposeFunction('onNewMessage', onMessage);

  await page.evaluate(() => {
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
          if (!node || node.nodeType !== 1) continue;

          const msgContainer = node.querySelector?.('[data-testid="msg-container"]');
          if (!msgContainer) continue;

          const textEl = msgContainer.querySelector('span.selectable-text');
          const text = textEl ? textEl.innerText : '';

          const links = Array.from(msgContainer.querySelectorAll('a'))
            .map(a => a.href)
            .filter(Boolean);

          const isGroup = document.title.includes('–');

          const sender =
            msgContainer.getAttribute('data-id') ||
            msgContainer.getAttribute('data-pre-plain-text') ||
            'unknown';

          window.onNewMessage({
            text,
            links,
            isGroup,
            senderId: sender,
          });
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
}
