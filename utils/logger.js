/**
 * Logger Utility
 * تسجيل الأحداث والأخطاء بشكل موحّد
 */

function getTimestamp() {
  return new Date().toISOString();
}

function info(message) {
  console.log(
    `[INFO] [${getTimestamp()}] ${message}`
  );
}

function warn(message, err = null) {
  console.warn(
    `[WARN] [${getTimestamp()}] ${message}`
  );

  if (err) {
    console.warn(err);
  }
}

function error(message, err = null) {
  console.error(
    `[ERROR] [${getTimestamp()}] ${message}`
  );

  if (err) {
    console.error(err);
  }
}

module.exports = {
  info,
  warn,
  error
};
