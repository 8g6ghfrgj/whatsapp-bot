import { db } from '../db.js';

// ================================
// Create Account (AFTER LOGIN ONLY)
// ================================
export async function create({ name, is_active = 0 }) {
  return new Promise((resolve, reject) => {
    const stmt = `
      INSERT INTO accounts (name, is_active, created_at)
      VALUES (?, ?, datetime('now'))
    `;

    db.run(stmt, [name, is_active], function (err) {
      if (err) return reject(err);
      resolve({
        id: this.lastID,
        name,
        is_active,
      });
    });
  });
}

// ================================
// Get All Accounts
// ================================
export async function getAll() {
  return new Promise((resolve, reject) => {
    db.all(
      `SELECT * FROM accounts ORDER BY created_at DESC`,
      [],
      (err, rows) => {
        if (err) return reject(err);
        resolve(rows || []);
      }
    );
  });
}

// ================================
// Get Active Account (ONLY ONE)
// ================================
export async function getActive() {
  return new Promise((resolve, reject) => {
    db.get(
      `SELECT * FROM accounts WHERE is_active = 1 LIMIT 1`,
      [],
      (err, row) => {
        if (err) return reject(err);
        resolve(row || null);
      }
    );
  });
}

// ================================
// Set Account Active / Inactive
// ================================
export async function updateStatus(id, isActive) {
  return new Promise((resolve, reject) => {
    const stmt = `
      UPDATE accounts
      SET is_active = ?
      WHERE id = ?
    `;

    db.run(stmt, [isActive ? 1 : 0, id], function (err) {
      if (err) return reject(err);
      resolve(true);
    });
  });
}

// ================================
// Set ALL Accounts Inactive
// (Safety: only one active allowed)
// ================================
export async function setAllInactive() {
  return new Promise((resolve, reject) => {
    db.run(
      `UPDATE accounts SET is_active = 0`,
      [],
      function (err) {
        if (err) return reject(err);
        resolve(true);
      }
    );
  });
}

// ================================
// Set One Account Inactive
// ================================
export async function setInactive(id) {
  return updateStatus(id, false);
}

// ================================
// Delete Account by ID
// ================================
export async function deleteById(id) {
  return new Promise((resolve, reject) => {
    db.run(
      `DELETE FROM accounts WHERE id = ?`,
      [id],
      function (err) {
        if (err) return reject(err);
        resolve(true);
      }
    );
  });
}
