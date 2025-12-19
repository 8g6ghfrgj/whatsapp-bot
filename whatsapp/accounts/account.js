/**
 * WhatsApp Account Class (FINAL – QR via Telegram)
 */

const path = require('path');
const fs = require('fs-extra');
const QRCode = require('qrcode');
const TelegramBot = require('node-telegram-bot-api');

const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason
} = require('@whiskeysockets/baileys');

const Pino = require('pino');
const logger = require('../../utils/logger');

const { registerWhatsAppEvents } = require('../events');
const { processGroupQueue } = require('../joiner');

// Telegram bot (لا polling)
const tgBot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, {
  polling: false
});

class WhatsAppAccount {
  constructor({ id }) {
    this.id = id;
    this.sock = null;
    this.connected = false;
    this.isLinking = true; // ⛔ مهم جدًا لمنع loop

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

  async connect() {
    logger.info(`🔗 بدء ربط حساب واتساب: ${this.id}`);

    const { state, saveCreds } = await useMultiFileAuthState(
      this.sessionPath
    );

    this.sock = makeWASocket({
      auth: state,
      logger: Pino({ level: 'silent' }),
      generateHighQualityLinkPreview: true
    });

    this.sock.ev.on('creds.update', saveCreds);

    this.sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;

      // =========================
      // إرسال QR إلى تيليجرام (نهائي)
      // =========================
      if (qr) {
        try {
          const adminId = process.env.ADMIN_TELEGRAM_ID;
          if (!adminId) {
            logger.error('❌ ADMIN_TELEGRAM_ID غير موجود في .env');
            return;
          }

          const qrImage = await QRCode.toBuffer(qr);

          await tgBot.sendPhoto(
            adminId,
            qrImage,
            {
              caption:
                '📲 امسح رمز QR لربط حساب واتساب\n\n' +
                'واتساب → الأجهزة المرتبطة → ربط جهاز\n\n' +
                '⏱️ الرمز صالح لفترة قصيرة'
            }
          );

          logger.info(`📸 تم إرسال QR إلى تيليجرام للحساب ${this.id}`);
        } catch (err) {
          logger.error('❌ فشل إرسال QR إلى تيليجرام', err);
        }
        return;
      }

      // =========================
      // تم الربط بنجاح
      // =========================
      if (connection === 'open') {
        this.connected = true;
        this.isLinking = false;

        logger.info(`✅ تم ربط الحساب بنجاح: ${this.id}`);

        registerWhatsAppEvents(this.sock, this.id);
        processGroupQueue(this.sock, this.id);
        return;
      }

      // =========================
      // إغلاق الاتصال
      // =========================
      if (connection === 'close') {
        this.connected = false;

        // ⛔ لا تعيد الاتصال أثناء الربط
        if (this.isLinking) {
          logger.warn('❌ تم إغلاق الاتصال قبل مسح QR');
          return;
        }

        const reason =
          lastDisconnect?.error?.output?.statusCode;

        if (reason === DisconnectReason.loggedOut) {
          logger.warn(`🚪 تم تسجيل خروج الحساب: ${this.id}`);
          return;
        }

        logger.warn('⚠️ انقطع الاتصال – إعادة المحاولة');
        this.reconnect();
      }
    });
  }

  async reconnect() {
    try {
      await this.connect();
    } catch (err) {
      logger.error(`❌ فشل إعادة الاتصال للحساب ${this.id}`, err);
    }
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
      logger.error(`❌ خطأ أثناء تسجيل خروج الحساب ${this.id}`, err);
    }
  }
}

module.exports = WhatsAppAccount;
