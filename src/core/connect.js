import makeWASocket, {
  DisconnectReason,
  Browsers
} from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import Pino from 'pino';

import config from '../config.js';
import {
  loadAuthState,
  getBaileysVersion,
  clearSession
} from './session.js';

let sock = null;

/**
 * إنشاء اتصال واتساب
 */
export async function connectWhatsApp() {
  const { authState, saveCreds } = await loadAuthState();
  const { version } = await getBaileysVersion();

  sock = makeWASocket({
    version,
    auth: authState,
    logger: Pino({ level: config.app.logLevel }),
    browser: Browsers.macOS('WhatsApp Companion Bot'),
    printQRInTerminal: false,
    syncFullHistory: true
  });

  // حفظ بيانات الجلسة
  sock.ev.on('creds.update', saveCreds);

  // استقبال QR Code
  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log('\n📱 امسح رمز QR لربط الحساب:\n');
      qrcode.generate(qr, { small: true });
    }

    if (connection === 'open') {
      console.log('✅ تم ربط واتساب بنجاح كجهاز مصاحب');
    }

    if (connection === 'close') {
      const reason =
        lastDisconnect?.error?.output?.statusCode;

      console.log('❌ تم قطع الاتصال:', reason);

      if (
        reason === DisconnectReason.loggedOut &&
        config.safety.clearSessionOnLogout
      ) {
        console.log('🧹 حذف الجلسة بسبب تسجيل الخروج');
        clearSession();
      }

      if (config.safety.autoReconnect) {
        console.log('🔄 إعادة الاتصال...');
        connectWhatsApp();
      }
    }
  });

  return sock;
}

/**
 * الحصول على الاتصال الحالي
 */
export function getSocket() {
  if (!sock) {
    throw new Error('WhatsApp socket not initialized');
  }
  return sock;
}
