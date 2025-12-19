/**
 * Handler: عرض الروابط + تصدير الروابط
 * يعمل فقط على الحساب النشط
 */

const fs = require('fs');
const path = require('path');

const { getActiveAccountId } = require('./activeAccount');
const { getAccount } = require('../../whatsapp/accounts');

const LINK_TYPES = [
  'whatsapp',
  'telegram',
  'twitter',
  'instagram',
  'tiktok',
  'others'
];

/**
 * جلب مسار روابط الحساب
 */
function getLinksDir(accountId) {
  return path.join(
    __dirname,
    `../../storage/accounts/data/${accountId}/links`
  );
}

/**
 * قراءة روابط نوع معين
 */
function readLinks(accountId, type) {
  const file = path.join(getLinksDir(accountId), `${type}.json`);
  if (!fs.existsSync(file)) return [];

  try {
    const data = JSON.parse(fs.readFileSync(file));
    return data.links || [];
  } catch {
    return [];
  }
}

/**
 * التحقق من وجود حساب نشط
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
  if (!account) {
    bot.sendMessage(chatId, '❌ الحساب النشط غير متصل');
    return null;
  }

  return account;
}

/**
 * عرض عدد الروابط المجمعة
 */
async function handleViewLinks(bot, chatId) {
  const account = getActiveAccountOrFail(bot, chatId);
  if (!account) return;

  let message = '📂 *الروابط المجمعة*\n────────────────────\n';

  let total = 0;

  for (const type of LINK_TYPES) {
    const count = readLinks(account.id, type).length;
    total += count;
    message += `🔹 ${type.toUpperCase()}: *${count}*\n`;
  }

  message += `\n📊 الإجمالي: *${total}*`;

  await bot.sendMessage(chatId, message, {
    parse_mode: 'Markdown'
  });
}

/**
 * تصدير الروابط إلى ملفات TXT
 */
async function handleExportLinks(bot, chatId) {
  const account = getActiveAccountOrFail(bot, chatId);
  if (!account) return;

  const linksDir = getLinksDir(account.id);

  let exportedAny = false;

  for (const type of LINK_TYPES) {
    const links = readLinks(account.id, type);
    if (!links.length) continue;

    const txtPath = path.join(linksDir, `${type}.txt`);
    fs.writeFileSync(txtPath, links.join('\n'), 'utf8');

    await bot.sendDocument(chatId, txtPath, {
      caption: `📤 روابط ${type.toUpperCase()}`
    });

    exportedAny = true;
  }

  if (!exportedAny) {
    await bot.sendMessage(
      chatId,
      'ℹ️ لا توجد روابط لتصديرها حالياً'
    );
  }
}

module.exports = {
  handleViewLinks,
  handleExportLinks
};
