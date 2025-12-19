/**
 * WhatsApp Account
 * Pairing Code (Phone Number) – FINAL
 */

const path = require('path');
const fs = require('fs-extra');
const Pino = require('pino');

const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason
} = require('@whiskeysockets/baileys');

const logger = require('../../utils/logger');
const { registerWhatsAppEvents } = require('../events');
const { processGroupQueue } = require('../joiner');

class WhatsAppAccount {
  constructor({ id }) {
    this.id = id;
    this.sock = null;
    this.connected = false;
    this.phoneNumber = null;

    // 👇 Pairing Code الحقيقي
    this.pairingCode = null;

    this.sessionPath = path.join(
      __dirname,
      `../../storage/accounts/sessions/${id}`
    );

    this.dataPath = path.join(
      __dirname,
      `../../storage/accounts/data/${id}`
    );

    this._ensureStorage();
  }

  _ensureStorage() {
    fs.ensureDirSync(this.sessionPath);
    fs.ensureDirSync(this.dataPath);

    fs.ensureDirSync(path.join(this.dataPath, 'links'));
    fs.ensureDirSync(path.join(this.dataPath, 'ads'));
    fs.ensureDirSync(path.join(this.dataPath, 'replies'));
    fs.ensureDirSync(path.join(this.dataPath, 'groups'));

    this._ensureFile('ads/current.json', {
      type: null,
      content: null,
      caption: ''
    });

    this._ensureFile('replies/config.json', {
      enabled: false,
      private_reply: 'مرحباً 👋\nتم استلام رسالتك.',
      group_reply: '📌 للتواصل يرجى مراسلتنا خاص'
    });

    this._ensureFile('groups/queue.json', { links: [] });
    this._ensureFile('groups/report.json', {
      joined: [],
      pending: [],
      failed: []
    });
  }

  _ensureFile(relativePath, content) {
    const file = path.join(this.dataPath, relativePath);
    if (!fs.existsSync(file)) {
      fs.writeFileSync(file, JSON.stringify(content, null, 2));
    }
  }

  /**
   * الاتصال باستخدام Pairing Code
   */
  async connectWithPairing(phoneNumber) {
    this.phoneNumber = phoneNumber;

    logger.info(
      `🔗 بدء ربط حساب واتساب (${this.id}) برقم الهاتف: ${phoneNumber}`
    );

    const { state, saveCreds } = await useMultiFileAuthState(
      this.sessionPath
    );

    this.sock = makeWASocket({
      auth: state,
      logger: Pino({ level: 'silent' }),
      browser: ['WhatsApp Companion', 'Chrome', '120.0'],
      printQRInTerminal: false
    });

    this.sock.ev.on('creds.update', saveCreds);

    try {
      const code = await this.sock.requestPairingCode(phoneNumber);

      // 👇 حفظ الرمز الحقيقي
      this.pairingCode = code;

      logger.info(`🔐 Pairing Code للحساب ${this.id}: ${code}`);
    } catch (err) {
      logger.error('❌ فشل إنشاء Pairing Code', err);
      throw err;
    }

    this.sock.ev.on('connection.update', (update) => {
      const { connection, lastDisconnect } = update;

      if (connection === 'open') {
        this.connected = true;
        logger.info(`✅ تم ربط الحساب بنجاح: ${this.id}`);

        registerWhatsAppEvents(this.sock, this.id);
        processGroupQueue(this.sock, this.id);
      }

      if (connection === 'close') {
        this.connected = false;

        const reason =
          lastDisconnect?.error?.output?.statusCode;

        if (reason === DisconnectReason.loggedOut) {
          logger.warn(`🚪 تم تسجيل خروج الحساب: ${this.id}`);
          return;
        }

        logger.warn(`⚠️ انقطع الاتصال (${this.id}) – إعادة المحاولة`);

        setTimeout(() => {
          this.connectWithPairing(this.phoneNumber);
        }, 5000);
      }
    });
  }

  async logout() {
    try {
      if (this.sock) {
        await this.sock.logout();
        this.sock = null;
        this.connected = false;
        logger.info(`🚪 تم تسجيل خروج الحساب: ${this.id}`);
      }
    } catch (err) {
      logger.error(
        `❌ خطأ أثناء تسجيل خروج الحساب ${this.id}`,
        err
      );
    }
  }
}

module.exports = WhatsAppAccount;
