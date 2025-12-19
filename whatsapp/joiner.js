/**
 * WhatsApp Group Joiner Engine
 * مسؤول عن:
 * - الانضمام إلى قروبات واتساب عبر روابط الدعوة
 * - دعم طلبات الانضمام (Pending)
 * - فاصل زمني ثابت (2 دقيقة)
 * - تقارير مفصلة لكل حساب
 */

const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

const JOIN_DELAY = 2 * 60 * 1000; // 2 دقيقة

/**
 * مسارات التخزين
 */
function getAccountGroupPath(accountId) {
  return path.join(
    __dirname,
    `../storage/accounts/data/${accountId}/groups`
  );
}

function getQueueFile(accountId) {
  return path.join(getAccountGroupPath(accountId), 'queue.json');
}

function getReportFile(accountId) {
  return path.join(getAccountGroupPath(accountId), 'report.json');
}

/**
 * تحميل قائمة الروابط
 */
function loadQueue(accountId) {
  const file = getQueueFile(accountId);
  if (!fs.existsSync(file)) return { links: [] };

  try {
    return JSON.parse(fs.readFileSync(file));
  } catch {
    return { links: [] };
  }
}

/**
 * تحميل التقرير
 */
function loadReport(accountId) {
  const file = getReportFile(accountId);
  if (!fs.existsSync(file)) {
    return { joined: [], pending: [], failed: [] };
  }

  try {
    return JSON.parse(fs.readFileSync(file));
  } catch {
    return { joined: [], pending: [], failed: [] };
  }
}

/**
 * حفظ التقرير
 */
function saveReport(accountId, report) {
  const file = getReportFile(accountId);
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
}

/**
 * استخراج كود الدعوة من الرابط
 */
function extractInviteCode(link) {
  const match = link.match(
    /chat\.whatsapp\.com\/([A-Za-z0-9_-]+)/
  );
  return match ? match[1] : null;
}

/**
 * معالجة طابور الانضمام
 */
async function processGroupQueue(sock, accountId) {
  if (!sock) return;

  logger.info(`👥 بدء معالجة طابور القروبات للحساب ${accountId}`);

  const queue = loadQueue(accountId);
  if (!queue.links.length) return;

  const report = loadReport(accountId);

  for (const link of queue.links) {
    const code = extractInviteCode(link);

    if (!code) {
      report.failed.push({
        link,
        reason: 'Invalid invite link',
        time: new Date().toISOString()
      });
      saveReport(accountId, report);
      continue;
    }

    try {
      const jid = await sock.groupAcceptInvite(code);

      report.joined.push({
        link,
        jid,
        time: new Date().toISOString()
      });

      logger.info(
        `✅ [${accountId}] تم الانضمام إلى القروب: ${jid}`
      );
    } catch (err) {
      // في الغالب: يحتاج موافقة مشرف
      report.pending.push({
        link,
        reason: err?.message || 'Pending approval',
        time: new Date().toISOString()
      });

      logger.warn(
        `⏳ [${accountId}] طلب انضمام معلق للقروب`
      );
    }

    saveReport(accountId, report);
    await delay(JOIN_DELAY);
  }

  // تفريغ الطابور بعد المعالجة
  fs.writeFileSync(
    getQueueFile(accountId),
    JSON.stringify({ links: [] }, null, 2)
  );

  logger.info(`📊 انتهاء معالجة القروبات للحساب ${accountId}`);
}

/**
 * تأخير زمني
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
  processGroupQueue
};
