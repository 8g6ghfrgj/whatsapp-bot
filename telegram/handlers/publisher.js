/**
 * Handler: النشر التلقائي
 * - استقبال الإعلان من تيليجرام
 * - حفظه للحساب النشط
 * - بدء / إيقاف النشر
 */

const fs = require('fs');
const path = require('path');

const { getActiveAccountId } = require('./activeAccount');
const { getAccount } = require('../../whatsapp/accounts');
const { startPublishing, stopPublishing } = require('../../whatsapp/publisher');

/**
 * جلب الحساب النشط أو إظهار تنبيه
 */
function getActiveAccountOrFail(bot, chatId) {
  const accId = getActiveAccountId();

  if (!accId) {
    bot.sendMessage(
      chatId,
      '⚠️ لا يوجد حساب واتساب نشط\n\nيرجى اختيار حساب من زر 🔁 اختيار الحساب النشط'
    );
    return null;
  }

  const account = getAccount(accId);
  if (!account || !account.sock) {
    bot.sendMessage(chatId, '❌ الحساب النشط غير متصل حالياً');
    return null;
  }

  return account;
}

/**
 * مسار ملف الإعلان للحساب
 */
function getAdFile(accountId) {
  return path.join(
    __dirname,
    `../../storage/accounts/data/${accountId}/ads/current.json`
  );
}

/**
 * بدء النشر – استقبال الإعلان
 */
async function handleAutoPublish(bot, chatId) {
  const account = getActiveAccountOrFail(bot, chatId);
  if (!account) return;

  await bot.sendMessage(
    chatId,
    '📢 أرسل الإعلان الآن:\n\n' +
    '• نص\n' +
    '• صورة مع نص\n' +
    '• فيديو مع نص\n\n' +
    'سيتم النشر في جميع القروبات'
  );

  // نستقبل رسالة واحدة فقط
  bot.once('message', async (msg) => {
    const ad = {
      type: null,
      content: null,
      caption: null,
      createdAt: new Date().toISOString()
    };

    // نص
    if (msg.text) {
      ad.type = 'text';
      ad.content = msg.text;
    }

    // صورة
    if (msg.photo) {
      ad.type = 'image';
      ad.content = msg.photo[msg.photo.length - 1].file_id;
      ad.caption = msg.caption || '';
    }

    // فيديو
    if (msg.video) {
      ad.type = 'video';
      ad.content = msg.video.file_id;
      ad.caption = msg.caption || '';
    }

    if (!ad.type) {
      return bot.sendMessage(
        chatId,
        '❌ نوع الإعلان غير مدعوم'
      );
    }

    // حفظ الإعلان
    const adFile = getAdFile(account.id);
    fs.mkdirSync(path.dirname(adFile), { recursive: true });
    fs.writeFileSync(adFile, JSON.stringify(ad, null, 2));

    // بدء النشر
    startPublishing(account);

    await bot.sendMessage(
      chatId,
      `✅ تم حفظ الإعلان وبدء النشر التلقائي\n\n🆔 الحساب: \`${account.id}\``,
      { parse_mode: 'Markdown' }
    );
  });
}

/**
 * إيقاف النشر التلقائي
 */
async function handleStopPublish(bot, chatId) {
  const account = getActiveAccountOrFail(bot, chatId);
  if (!account) return;

  stopPublishing(account);

  await bot.sendMessage(
    chatId,
    `⛔ تم إيقاف النشر التلقائي\n\n🆔 الحساب: \`${account.id}\``,
    { parse_mode: 'Markdown' }
  );
}

module.exports = {
  handleAutoPublish,
  handleStopPublish
};
