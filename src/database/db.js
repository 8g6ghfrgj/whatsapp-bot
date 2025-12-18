import sqlite3 from 'sqlite3';
import fs from 'fs';
import path from 'path';
import config from '../config.js';

// التأكد من وجود مجلد البيانات
const dbDir = path.dirname(config.database.path);
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// إنشاء الاتصال بقاعدة البيانات
const db = new sqlite3.Database(
  config.database.path,
  (err) => {
    if (err) {
      console.error('❌ Failed to connect to database:', err);
    } else {
      console.log('🗄️ SQLite database connected');
    }
  }
);

// تفعيل القيود (Foreign Keys)
db.serialize(() => {
  db.run('PRAGMA foreign_keys = ON');
});

/**
 * تشغيل استعلام بدون نتيجة
 */
export function run(query, params = []) {
  return new Promise((resolve, reject) => {
    db.run(query, params, function (err) {
      if (err) {
        return reject(err);
      }
      resolve(this);
    });
  });
}

/**
 * جلب صف واحد
 */
export function get(query, params = []) {
  return new Promise((resolve, reject) => {
    db.get(query, params, (err, row) => {
      if (err) {
        return reject(err);
      }
      resolve(row);
    });
  });
}

/**
 * جلب عدة صفوف
 */
export function all(query, params = []) {
  return new Promise((resolve, reject) => {
    db.all(query, params, (err, rows) => {
      if (err) {
        return reject(err);
      }
      resolve(rows);
    });
  });
}

export default db;
