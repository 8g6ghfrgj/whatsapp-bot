import { bot } from '../bot.js';
import { AdsRepo } from '../../database/repositories/ads.repo.js';
import {
  startPosting,
  stopPosting
} from '../../whatsapp/whatsapp.controller.js';

export async function start(chatId) {
  await startPosting();
  bot.sendMessage(chatId, '🚀 بدأ النشر التلقائي');
}

export async function stop(chatId) {
  stopPosting();
  bot.sendMessage(chatId, '🛑 تم إيقاف النشر التلقائي');
}

// إضافة إعلان نصي (أساسي – قابل للتوسعة)
export async function addTextAd(chatId, text) {
  await AdsRepo.create('text', text);
  bot.sendMessage(chatId, '✅ تم حفظ الإعلان النصي');
}
