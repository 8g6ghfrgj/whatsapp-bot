import fs from 'fs';
import { bot } from '../bot.js';
import { SettingsRepo } from '../../database/repositories/settings.repo.js';
import { LinksRepo } from '../../database/repositories/links.repo.js';
import { exportTxt } from '../../utils/file.exporter.js';

export async function start(chatId) {
  await SettingsRepo.set('links_collecting', '1');
  bot.sendMessage(chatId, '▶️ تم تشغيل تجميع الروابط');
}

export async function stop(chatId) {
  await SettingsRepo.set('links_collecting', '0');
  bot.sendMessage(chatId, '⏹️ تم إيقاف تجميع الروابط');
}

export async function show(chatId) {
  const types = await LinksRepo.getAllTypes();

  if (!types.length) {
    return bot.sendMessage(chatId, '❌ لا توجد روابط مخزنة');
  }

  bot.sendMessage(
    chatId,
    `📂 أقسام الروابط:\n\n${types.join('\n')}`
  );
}

export async function exportLinks(chatId) {
  const types = await LinksRepo.getAllTypes();

  if (!types.length) {
    return bot.sendMessage(chatId, '❌ لا توجد روابط للتصدير');
  }

  for (const type of types) {
    const rows = await LinksRepo.getByType(type);
    if (!rows.length) continue;

    const filePath = exportTxt(
      `${type}.txt`,
      rows.map(r => r.url)
    );

    await bot.sendDocument(
      chatId,
      fs.createReadStream(filePath),
      { caption: `📄 روابط ${type}` }
    );
  }
}
