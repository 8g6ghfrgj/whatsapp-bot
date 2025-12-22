import { db } from '../db.js';

export const LinksRepo = {
  add(accountId, groupJid, url, type, hash) {
    return new Promise((resolve, reject) => {
      db.run(
        `INSERT OR IGNORE INTO links
         (account_id, group_jid, url, type, hash)
         VALUES (?, ?, ?, ?, ?)`,
        [accountId, groupJid, url, type, hash],
        (err) => (err ? reject(err) : resolve())
      );
    });
  },

  getAllTypes() {
    return new Promise((resolve, reject) => {
      db.all(
        `SELECT DISTINCT type FROM links`,
        [],
        (err, rows) =>
          err ? reject(err) : resolve(rows.map(r => r.type))
      );
    });
  },

  getByType(type) {
    return new Promise((resolve, reject) => {
      db.all(
        `SELECT url FROM links WHERE type = ? ORDER BY id ASC`,
        [type],
        (err, rows) => (err ? reject(err) : resolve(rows))
      );
    });
  },

  count() {
    return new Promise((resolve, reject) => {
      db.get(
        `SELECT COUNT(*) as total FROM links`,
        [],
        (err, row) => (err ? reject(err) : resolve(row.total))
      );
    });
  }
};
