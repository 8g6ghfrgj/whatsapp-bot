/**
 * WhatsApp Links Scraper
 * مسؤول عن:
 * - تشغيل / إيقاف التجميع لكل حساب
 * - استخراج الروابط من النص
 * - تصنيف الروابط
 * - منع التكرار
 * - حفظ الروابط في تخزين معزول لكل حساب
 */

const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');
const { uniqueLinks } = require('../utils/deduplicator');
const { classifyLink } = require('../utils/linkClassifier');

// حالة التجميع لكل حساب
// { accId: true/false }
const scrapingState = {};

/**
 * مسارات التخزين
 */
function getLinksDir(accountId) {
  return path.join(
    __dirname,
    `../storage/accounts/data/${accountId}/links`
  );
}

function getLinksFile(accountId, type) {
  return path.join(getLinksDir(accountId), `${type}.json`);
}

/**
 * تفعيل تجميع الروابط لحساب معيّن
 */
function enableScraping(accountId) {
  scrapingState[accountId] = true;
  logger.info(`▶️ تم تشغيل تجميع الروابط للحساب ${accountId}`);
}

/**
 * إيقاف تجميع الروابط لحساب معيّن
 */
function disableScraping(accountId) {
  scrapingState[accountId] = false;
  logger.info(`⏹️ تم إيقاف تجميع الروابط للحساب ${accountId}`);
}

/**
 * هل التجميع مفعّل للحساب؟
 */
function isScrapingEnabled(accountId) {
  return scrapingState[accountId] === true;
}

/**
 * استخراج الروابط من نص
 */
function extractLinks(text) {
  if (!text || typeof text !== 'string') return [];
  const regex = /(https?:\/\/[^\s]+)/gi;
  return text.match(regex) || [];
}

/**
 * التأكد من وجود ملف التخزين
 */
function ensureLinksFile(filePath) {
  if (!fs.existsSync(filePath)) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(
      filePath,
      JSON.stringify({ links: [] }, null, 2)
    );
  }
}

/**
 * حفظ الروابط (مع تصنيف + منع تكرار)
 */
function saveLinks(accountId, links = []) {
  if (!links.length) return;

  for (const link of links) {
    const type = classifyLink(link);
    const filePath = getLinksFile(accountId, type);

    ensureLinksFile(filePath);

    try {
      const data = JSON.parse(fs.readFileSync(filePath));
      data.links = uniqueLinks(data.links, [link]);

      fs.writeFileSync(
        filePath,
        JSON.stringify(data, null, 2)
      );
    } catch (err) {
      logger.error(
        `❌ خطأ حفظ رابط للحساب ${accountId}`,
        err
      );
    }
  }
}

module.exports = {
  enableScraping,
  disableScraping,
  isScrapingEnabled,
  extractLinks,
  saveLinks
};
