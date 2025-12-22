import { db } from '../db.js';

export const GroupsRepo = {
  add(accountId, groupName, groupJid, status = 'joined') {
    return new Promise((resolve, reject) => {
      db.run(
        `INSERT OR IGNORE INTO groups
         (account_id, group_name, group_jid, join_status, joined_at)
         VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)`,
        [accountId, groupName, groupJid, status],
        (err) => (err ? reject(err) : resolve())
      );
    });
  },

  getAll(accountId) {
    return new Promise((resolve, reject) => {
      db.all(
        `SELECT * FROM groups WHERE account_id = ?`,
        [accountId],
        (err, rows) => (err ? reject(err) : resolve(rows))
      );
    });
  }
};
