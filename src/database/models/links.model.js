import { run, all } from '../db.js';

/**
 * إنشاء جدول الروابط
 */
export async function initLinksTable() {
  await run(`
    CREATE TABLE IF NOT EXISTS links (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      url TEXT NOT NULL UNIQUE,
      type TEXT NOT NULL,
      source_chat TEXT,
      created_at INTEGER NOT NULL
    )
  `);
}

/**
 * إضافة رابط (بدون تكرار)
 */
export async function addLink(url, type, sourceChat = null) {
  try {
    await run(
      `
      INSERT OR IGNORE INTO links (url, type, source_chat, created_at)
      VALUES (?, ?, ?, ?)
      `,
      [url, type, sourceChat, Date.now()]
    );
    return true;
  } catch (error) {
    console.error('❌ Failed to add link:', error);
    return false;
  }
}

/**
 * جلب الروابط حسب النوع
 */
export async function getLinksByType(type) {
  return await all(
    `
    SELECT url FROM links
    WHERE type = ?
    ORDER BY created_at DESC
    `,
    [type]
  );
}

/**
 * جلب كل الروابط مصنفة
 */
export async function getAllLinksGrouped() {
  const rows = await all(`
    SELECT type, url
    FROM links
    ORDER BY type, created_at DESC
  `);

  const grouped = {};
  for (const row of rows) {
    if (!grouped[row.type]) {
      grouped[row.type] = [];
    }
    grouped[row.type].push(row.url);
  }

  return grouped;
}

/**
 * عدد الروابط
 */
export async function countLinks() {
  const rows = await all(`
    SELECT COUNT(*) as total FROM links
  `);
  return rows[0]?.total || 0;
}
