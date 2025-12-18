import { getSocket } from '../core/connect.js';

/**
 * إرسال رسالة نصية
 */
export async function sendTextMessage(chatId, text, options = {}) {
  const sock = getSocket();

  if (!chatId || !text) return;

  try {
    await sock.sendMessage(chatId, {
      text,
      ...options
    });
  } catch (error) {
    console.error('❌ Failed to send text message:', error);
  }
}

/**
 * إرسال رسالة مع أزرار
 */
export async function sendButtonsMessage(chatId, text, buttons = []) {
  const sock = getSocket();

  if (!chatId || !text || !Array.isArray(buttons)) return;

  const formattedButtons = buttons.map((btn, index) => ({
    buttonId: btn.id || `btn_${index}`,
    buttonText: { displayText: btn.text },
    type: 1
  }));

  try {
    await sock.sendMessage(chatId, {
      text,
      buttons: formattedButtons,
      headerType: 1
    });
  } catch (error) {
    console.error('❌ Failed to send buttons message:', error);
  }
}

/**
 * إرسال رسالة رد (Reply)
 */
export async function replyToMessage(chatId, text, quotedMessage) {
  const sock = getSocket();

  if (!chatId || !text || !quotedMessage) return;

  try {
    await sock.sendMessage(
      chatId,
      { text },
      { quoted: quotedMessage }
    );
  } catch (error) {
    console.error('❌ Failed to reply to message:', error);
  }
}
