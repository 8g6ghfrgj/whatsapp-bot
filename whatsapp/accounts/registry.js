/**
 * WhatsApp Accounts Registry
 * مسؤول عن حفظ واسترجاع الحسابات المرتبطة
 */

const fs = require('fs');
const path = require('path');
const logger = require('../../utils/logger');

const REGISTRY_FILE = path.join(
  __dirname,
  '../../storage/accounts/accounts.json'
);

/**
 * التأكد من وجود ملف السجل
 */
function ensureRegistryFile() {
  if (!fs.existsSync(REGISTRY_FILE)) {
    const initialData = { accounts: [] };
    fs.mkdirSync(path.dirname(REGISTRY_FILE), { recursive: true });
    fs.writeFileSync(
      REGISTRY_FILE,
      JSON.stringify(initialData, null, 2)
    );
  }
}

/**
 * تحميل الحسابات من السجل
 */
function loadAccounts() {
  ensureRegistryFile();

  try {
    const raw = fs.readFileSync(REGISTRY_FILE, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    logger.error('❌ فشل قراءة سجل الحسابات', err);
    return { accounts: [] };
  }
}

/**
 * حفظ السجل كاملًا
 */
function saveAccounts(data) {
  ensureRegistryFile();

  try {
    fs.writeFileSync(
      REGISTRY_FILE,
      JSON.stringify(data, null, 2)
    );
  } catch (err) {
    logger.error('❌ فشل حفظ سجل الحسابات', err);
  }
}

/**
 * إضافة حساب جديد للسجل
 */
function addAccount(account) {
  const data = loadAccounts();

  const exists = data.accounts.find(
    a => a.id === account.id
  );

  if (exists) {
    logger.warn(
      `⚠️ الحساب ${account.id} موجود مسبقًا في السجل`
    );
    return false;
  }

  data.accounts.push({
    id: account.id,
    createdAt: account.createdAt || new Date().toISOString()
  });

  saveAccounts(data);
  logger.info(`📁 تم تسجيل الحساب في السجل: ${account.id}`);
  return true;
}

/**
 * إزالة حساب من السجل
 */
function removeAccount(accountId) {
  const data = loadAccounts();

  const before = data.accounts.length;
  data.accounts = data.accounts.filter(
    acc => acc.id !== accountId
  );

  if (data.accounts.length === before) {
    logger.warn(
      `⚠️ الحساب ${accountId} غير موجود في السجل`
    );
    return false;
  }

  saveAccounts(data);
  logger.info(`🗑️ تم حذف الحساب من السجل: ${accountId}`);
  return true;
}

module.exports = {
  loadAccounts,
  saveAccounts,
  addAccount,
  removeAccount
};
