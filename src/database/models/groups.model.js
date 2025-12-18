import { run, get, all } from '../db.js';

/**
 * إنشاء جدول المجموعات
 */
export async function initGroupsTable() {
  await run(`
    CREATE TABLE IF NOT EXISTS groups (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      invite_link TEXT NOT NULL UNIQUE,
      group_name TEXT,
      status TEXT NOT NULL,
      requested_at INTEGER NOT NULL,
      joined_at INTEGER,
      last_update INTEGER
    )
  `);
}

/**
 * إضافة رابط مجموعة جديد
 * status:
 * pending | joined | rejected | expired
 */
export async function addGroupInvite(inviteLink, groupName = null) {
  try {
    await run(
      `
      INSERT OR IGNORE INTO groups
      (invite_link, group_name, status, requested_at, last_update)
      VALUES (?, ?, 'pending', ?, ?)
      `,
      [
        inviteLink,
        groupName,
        Date.now(),
        Date.now()
      ]
    );
    return true;
  } catch (error) {
    console.error('❌ Failed to add group invite:', error);
    return false;
  }
}

/**
 * تحديث حالة المجموعة
 */
export async function updateGroupStatus(inviteLink, status) {
  await run(
    `
    UPDATE groups
    SET status = ?, last_update = ?
    WHERE invite_link = ?
    `,
    [status, Date.now(), inviteLink]
  );
}

/**
 * تسجيل نجاح الانضمام
 */
export async function markGroupJoined(inviteLink, groupName) {
  await run(
    `
    UPDATE groups
    SET status = 'joined',
        group_name = ?,
        joined_at = ?,
        last_update = ?
    WHERE invite_link = ?
    `,
    [
      groupName,
      Date.now(),
      Date.now(),
      inviteLink
    ]
  );
}

/**
 * جلب المجموعات حسب الحالة
 */
export async function getGroupsByStatus(status) {
  return await all(
    `
    SELECT * FROM groups
    WHERE status = ?
    ORDER BY requested_at ASC
    `,
    [status]
  );
}

/**
 * جلب كل المجموعات
 */
export async function getAllGroups() {
  return await all(`
    SELECT * FROM groups
    ORDER BY requested_at DESC
  `);
}

/**
 * جلب مجموعة واحدة
 */
export async function getGroupByInvite(inviteLink) {
  return await get(
    `
    SELECT * FROM groups
    WHERE invite_link = ?
    `,
    [inviteLink]
  );
}

/**
 * إنهاء الطلبات المنتهية (بعد 24 ساعة)
 */
export async function expireOldPendingGroups(timeoutMs) {
  const now = Date.now();

  await run(
    `
    UPDATE groups
    SET status = 'expired', last_update = ?
    WHERE status = 'pending'
      AND (? - requested_at) > ?
    `,
    [now, now, timeoutMs]
  );
}
