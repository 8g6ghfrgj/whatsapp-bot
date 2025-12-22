import { db } from '../db.js';

export const AdsRepo = {
  create(type, content = null, filePath = null) {
    return new Promise((resolve, reject) => {
      db.run(
        `INSERT INTO ads (type, content, file_path)
         VALUES (?, ?, ?)`,
        [type, content, filePath],
        function (err) {
          if (err) return reject(err);
          resolve(this.lastID);
        }
      );
    });
  },

  getLatest() {
    return new Promise((resolve, reject) => {
      db.get(
        `SELECT * FROM ads ORDER BY id DESC LIMIT 1`,
        [],
        (err, row) => (err ? reject(err) : resolve(row))
      );
    });
  }
};
