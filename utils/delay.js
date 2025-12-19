/**
 * Delay Utility
 * تأخير غير متزامن (Async Delay)
 * يستخدم لتقليل الضغط وتجنب الحظر
 */

/**
 * تأخير لمدة محددة بالمللي ثانية
 * @param {number} ms
 * @returns {Promise<void>}
 */
function delay(ms = 1000) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
  delay
};
