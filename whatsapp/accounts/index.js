/**
 * WhatsApp Accounts Manager
 * إدارة إنشاء الحسابات وحفظها واستعادتها
 * بدون اتصال تلقائي (Pairing Code only)
 */

const fs = require('fs');
const path = require('path');
const WhatsAppAccount = require('./account');
const logger = require('../../utils/logger');

const ACCOUNTS_FILE = path.join(
  __dirname,
  '../../storage/accounts/accounts.json'
);

// Map للحسابات النشطة
const accounts = new Map();

/**
 * التأكد من وجود ملف الحسابات
 */
function ensureAccountsFile() {
  const dir = path.dirname(ACCOUNTS_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  if (!fs.existsSync(ACCOUNTS_FILE)) {
    fs.writeFileSync(
      ACCOUNTS_FILE,
      JSON.stringify({ accounts: [] }, null, 2)
    );
  }
}

/**
 * استعادة الحسابات المحفوظة (بدون اتصال)
 */
function restoreLinkedAccounts() {
  ensureAccountsFile();

  let data;
  try {
    data = JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf8'));
  } catch (err) {
    logger.error('❌ فشل قراءة ملف الحسابات', err);
    return;
  }

  const list = data.accounts || [];

  for (const acc of list) {
    if (!acc.id) continue;

    const account = new WhatsAppAccount({ id: acc.id });
    accounts.set(acc.id, account);

    logger.info(`🔁 تم تحميل الحساب: ${acc.id}`);
    // ⚠️ لا يتم الاتصال هنا
  }
}

/**
 * إنشاء حساب جديد (بدون اتصال)
 */
function createAccount() {
  ensureAccountsFile();

  const id = `acc_${Date.now()}`;
  const account = new WhatsAppAccount({ id });

  accounts.set(id, account);

  let data = { accounts: [] };
  try {
    data = JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf8'));
  } catch (_) {}

  data.accounts.push({
    id,
    createdAt: new Date().toISOString()
  });

  fs.writeFileSync(
    ACCOUNTS_FILE,
    JSON.stringify(data, null, 2)
  );

  logger.info(`🆕 تم إنشاء حساب جديد: ${id}`);
  return account;
}

/**
 * حذف حساب
 */
function removeAccount(id) {
  if (!accounts.has(id)) return false;

  accounts.delete(id);

  let data = { accounts: [] };
  try {
    data = JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf8'));
  } catch (_) {}

  data.accounts = data.accounts.filter(
    (acc) => acc.id !== id
  );

  fs.writeFileSync(
    ACCOUNTS_FILE,
    JSON.stringify(data, null, 2)
  );

  logger.info(`🗑️ تم حذف الحساب: ${id}`);
  return true;
}

/**
 * جلب حساب بالمعرف
 */
function getAccount(id) {
  return accounts.get(id) || null;
}

/**
 * جلب جميع الحسابات
 */
function getAllAccounts() {
  return Array.from(accounts.values());
}

module.exports = {
  restoreLinkedAccounts,
  createAccount,
  removeAccount,
  getAccount,
  getAllAccounts
};
