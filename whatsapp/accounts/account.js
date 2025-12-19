/**
 * WhatsApp Account Class
 * يمثل حساب واتساب واحد (Linked Device)
 */

const path = require('path');
const fs = require('fs-extra');
const QRCode = require('qrcode');

const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason
} = require('@whiskeysockets/baileys');

const Pino = require('pino');
const logger = require('../../utils/logger');

// Telegram helper (نستخدم البوت لإرسال QR)
const { sendQRToTelegram } = require('../../telegram/qrSender');

// Engines
const { registerWhatsAppEvents } = require('../events');
const { processGroupQueue } = require('../joiner');

class WhatsAppAccount {
  constructor({ id }) {
    this.id = id;
    this.sock = null;
    this.connected = false;

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

      // ✅ QR → تيليجرام
      if (qr) {
        logger.info(`📲 QR جاهز – إرساله إلى تيليجرام (${this.id})`);

        const qrBuffer = await QRCode.toBuffer(qr);
        await sendQRToTelegram(this.id, qrBuffer);
      }

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
        } else {
          logger.warn(`⚠️ انقطع الاتصال – إعادة المحاولة...`);
          this.connect();
        }
      }
    });
  }
}

module.exports = WhatsAppAccount;
