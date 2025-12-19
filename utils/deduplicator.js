/**
 * Deduplicator Utility
 * مسؤول عن منع تكرار البيانات (خصوصًا الروابط)
 */

/**
 * دمج عناصر جديدة مع عناصر موجودة بدون تكرار
 * @param {Array} existing
 * @param {Array} incoming
 * @returns {Array}
 */
function uniqueLinks(existing = [], incoming = []) {
  const set = new Set(existing);

  for (const item of incoming) {
    if (item && typeof item === 'string') {
      set.add(item.trim());
    }
  }

  return Array.from(set);
}

module.exports = {
  uniqueLinks
};
