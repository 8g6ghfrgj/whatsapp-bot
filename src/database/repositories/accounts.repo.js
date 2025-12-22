import { db } from '../db.js';

export const AccountsRepo = {
  create(name, chromeProfile) {
    return new Promise((resolve, reject) => {
      db.run(
        `INSERT INTO accounts (name, chrome_profile)
         VALUES (?, ?)`,
        [name, chromeProfile],
        function (err) {
          if (err) return reject(err);
          resolve(this.lastID);
        }
      );
    });
  },

  getAll() {
    return new Promise((resolve, reject) => {
      db.all(`SELECT * FROM accounts ORDER BY id ASC`, [], (err, rows) => {
        if (err) return reject(err);
        resolve(rows);
      });
    });
  },

  getById(id) {
    return new Promise((resolve, reject) => {
      db.get(
        `SELECT * FROM accounts WHERE id = ?`,
        [id],
        (err, row) => (err ? reject(err) : resolve(row))
      );
    });
  },

  deactivate(id) {
    return new Promise((resolve, reject) => {
      db.run(
        `UPDATE accounts SET is_active = 0 WHERE id = ?`,
        [id],
        (err) => (err ? reject(err) : resolve())
      );
    });
  }
};
