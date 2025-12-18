// scripts/initData.js
const fs = require('fs').promises;
const path = require('path');

async function initDataDirectory() {
    const directories = [
        './data',
        './exports', 
        './logs',
        './backups',
        './scripts'
    ];
    
    console.log('🚀 بدء تهيئة نظام البوت...');
    console.log('📁 جاري إنشاء المجلدات والملفات...');
    
    try {
        // إنشاء جميع المجلدات
        for (const dir of directories) {
            await fs.mkdir(dir, { recursive: true });
            console.log(`✅ تم إنشاء: ${dir}/`);
        }
        
        // قائمة بجميع الملفات المطلوبة
        const filesToCreate = [
            // ملفات data/
            {
                path: './data/auth_info_multi.json',
                content: JSON.stringify({
                    state: { creds: {}, keys: {} },
                    sessionInfo: {},
                    version: "1.0.0"
                }, null, 2)
            },
            {
                path: './data/collectedLinks.json',
                content: JSON.stringify({
                    links: {
                        whatsapp: [], telegram: [], facebook: [],
                        instagram: [], youtube: [], tiktok: [],
                        twitter: [], website: [], other: []
                    },
                    stats: { total: 0, categories: {}, lastUpdate: null },
                    processedMessageIds: [],
                    savedAt: new Date().toISOString(),
                    version: "1.0.0"
                }, null, 2)
            },
            {
                path: './data/adsContent.json',
                content: JSON.stringify({
                    campaigns: [],
                    templates: [],
                    schedule: [],
                    history: [],
                    settings: {},
                    version: "1.0.0"
                }, null, 2)
            },
            {
                path: './data/autoReplies.json',
                content: JSON.stringify({
                    replies: [],
                    patterns: [],
                    savedAt: new Date().toISOString(),
                    version: "1.0.0"
                }, null, 2)
            },
            {
                path: './data/groupJoinQueue.json',
                content: JSON.stringify({
                    queue: [],
                    pending: {},
                    joined: [],
                    failed: [],
                    savedAt: new Date().toISOString()
                }, null, 2)
            },
            
            // ملفات logs/
            {
                path: './logs/bot.log',
                content: '📝 سجل البوت - بدء التشغيل: ' + new Date().toLocaleString() + '\n' +
                        '='.repeat(60) + '\n\n'
            },
            {
                path: './logs/error.log',
                content: '❌ سجل الأخطاء\n' +
                        '='.repeat(60) + '\n\n'
            },
            
            // ملفات exports/ (مثال)
            {
                path: './exports/README.txt',
                content: '📁 مجلد التصديرات\n' +
                        '='.repeat(40) + '\n\n' +
                        'يتم حفظ جميع ملفات التصدير هنا تلقائياً.\n' +
                        'التنسيقات المتاحة: TXT, JSON, CSV\n\n' +
                        '📅 الملفات تحوي التاريخ في أسمائها:\n' +
                        '- links_export_20240119_143000.txt\n' +
                        '- links_export_20240119_143000.json\n' +
                        '- links_export_20240119_143000.csv\n'
            },
            
            // ملفات backups/ (مثال)
            {
                path: './backups/README.txt',
                content: '💾 مجلد النسخ الاحتياطي\n' +
                        '='.repeat(40) + '\n\n' +
                        'يتم حفظ النسخ الاحتياطية هنا تلقائياً كل 24 ساعة.\n' +
                        'يمكن استعادة البيانات من أي نسخة احتياطية.\n'
            }
        ];
        
        // إنشاء جميع الملفات
        for (const file of filesToCreate) {
            await fs.writeFile(file.path, file.content, 'utf8');
            console.log(`✅ تم إنشاء: ${file.path}`);
        }
        
        // إنشاء ملف .env إذا لم يكن موجوداً
        try {
            await fs.access('./.env');
            console.log('⚠️ ملف .env موجود بالفعل');
        } catch {
            const envContent = `# WhatsApp Companion Bot - Configuration
BOT_NAME=WhatsApp Companion Bot
ADMIN_JID=491234567890@s.whatsapp.net
SESSION_ENCRYPTION_KEY=change-this-to-a-strong-key-32-chars

# إعدادات الأداء
MAX_GROUPS_PER_HOUR=50
JOIN_INTERVAL_MS=120000
REPLY_COOLDOWN_MS=30000

# إعدادات السجلات
LOG_LEVEL=info
LOG_TO_FILE=true

# ملاحظة: قم بتعديل هذه القيم حسب احتياجاتك
`;
            await fs.writeFile('./.env', envContent, 'utf8');
            console.log('✅ تم إنشاء: .env (تعديل الإعدادات المهمة!)');
        }
        
        console.log('\n🎉 ' + '='.repeat(50));
        console.log('✅ تمت تهيئة النظام بنجاح!');
        console.log('='.repeat(50));
        console.log('\n📋 الملفات التي تم إنشاؤها:');
        console.log('├── 📂 data/ (5 ملفات بيانات)');
        console.log('├── 📂 logs/ (2 ملف سجلات)');
        console.log('├── 📂 exports/ (مجلد التصدير)');
        console.log('├── 📂 backups/ (مجلد النسخ)');
        console.log('├── 📂 scripts/ (مجلد السكريبتات)');
        console.log('└── 📄 .env (ملف الإعدادات)');
        console.log('\n🚀 الخطوات التالية:');
        console.log('1. قم بتعديل ملف .env بإعداداتك');
        console.log('2. قم بتثبيت الحزم: npm install');
        console.log('3. ابدأ البوت: npm start');
        console.log('4. امسح QR Code بحساب واتساب');
        console.log('\n💡 ملاحظة: البوت سيعمل تلقائياً بعد التهيئة!');
        
    } catch (error) {
        console.error('❌ خطأ في التهيئة:', error);
        process.exit(1);
    }
}

// إذا تم تشغيل الملف مباشرة
if (require.main === module) {
    initDataDirectory();
} else {
    module.exports = { initDataDirectory };
}
