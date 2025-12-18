// scripts/generateExport.js
const fs = require('fs').promises;
const path = require('path');

class ExportGenerator {
    constructor() {
        this.exportDir = './exports';
        this.templates = this.getTemplates();
    }
    
    async generateLinksExport() {
        try {
            // تحميل بيانات الروابط
            const linksData = await this.loadLinksData();
            if (!linksData || !linksData.links) {
                throw new Error('لا توجد بيانات روابط للتصدير');
            }
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const fileName = `links_export_${timestamp}.txt`;
            const filePath = path.join(this.exportDir, fileName);
            
            // توليد المحتوى
            const content = this.generateContent(linksData);
            
            // حفظ الملف
            await fs.writeFile(filePath, content, 'utf8');
            
            console.log(`✅ تم إنشاء ملف التصدير: ${fileName}`);
            console.log(`📊 عدد الروابط: ${linksData.stats?.total || 0}`);
            console.log(`📁 الموقع: ${filePath}`);
            
            // تحديث سجل التصديرات
            await this.updateExportLog(fileName, linksData.stats?.total || 0);
            
            return {
                success: true,
                filePath: filePath,
                fileName: fileName,
                linksCount: linksData.stats?.total || 0,
                size: content.length
            };
            
        } catch (error) {
            console.error('❌ خطأ في إنشاء التصدير:', error);
            return { success: false, error: error.message };
        }
    }
    
    async loadLinksData() {
        try {
            const dataPath = './data/collectedLinks.json';
            const data = await fs.readFile(dataPath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            console.error('❌ خطأ في تحميل بيانات الروابط:', error);
            return null;
        }
    }
    
    generateContent(data) {
        let content = this.templates.header;
        
        const now = new Date();
        const stats = data.stats || {};
        const links = data.links || {};
        
        // تعبئة القيم الديناميكية
        content = content.replace('{date}', now.toLocaleDateString('ar-SA'))
                        .replace('{time}', now.toLocaleTimeString('ar-SA'))
                        .replace('{total}', stats.total || 0);
        
        // إضافة الروابط حسب التصنيف
        let linksContent = '';
        
        const categories = {
            whatsapp: '💚 واتساب',
            telegram: '💬 تليجرام',
            facebook: '🔵 فيسبوك',
            instagram: '📸 انستجرام',
            youtube: '🎥 يوتيوب',
            tiktok: '🎵 تيك توك',
            twitter: '🐦 تويتر',
            website: '🌐 مواقع ويب',
            other: '🔗 أخرى'
        };
        
        for (const [category, categoryName] of Object.entries(categories)) {
            if (links[category] && links[category].length > 0) {
                linksContent += `\n${categoryName} (${links[category].length} رابط)\n`;
                linksContent += '─'.repeat(50) + '\n';
                
                links[category].slice(0, 10).forEach((link, index) => {
                    linksContent += `${index + 1}. ${link.url}\n`;
                    
                    if (link.messageInfo?.sender) {
                        linksContent += `   👤 ${link.messageInfo.sender}`;
                        
                        if (link.timestamp) {
                            const date = new Date(link.timestamp);
                            linksContent += ` - 📅 ${date.toLocaleDateString('ar-SA')}`;
                        }
                        
                        linksContent += '\n';
                    }
                    
                    if (link.metadata?.title) {
                        linksContent += `   📝 ${link.metadata.title}\n`;
                    }
                    
                    linksContent += '\n';
                });
                
                if (links[category].length > 10) {
                    linksContent += `... و ${links[category].length - 10} رابط إضافي ...\n`;
                }
            }
        }
        
        content = content.replace('{links}', linksContent);
        
        // إضافة الإحصائيات
        let statsContent = '\n📈 إحصائيات التجميع\n';
        statsContent += '─'.repeat(50) + '\n';
        
        if (stats.total) {
            statsContent += `✅ إجمالي الروابط: ${stats.total}\n`;
        }
        
        if (stats.categories) {
            statsContent += '\n📊 التوزيع:\n';
            for (const [category, count] of Object.entries(stats.categories)) {
                if (count > 0) {
                    const percentage = ((count / stats.total) * 100).toFixed(1);
                    statsContent += `• ${categories[category] || category}: ${count} (${percentage}%)\n`;
                }
            }
        }
        
        if (stats.lastUpdate) {
            const lastUpdate = new Date(stats.lastUpdate);
            statsContent += `\n🕒 آخر تحديث: ${lastUpdate.toLocaleString('ar-SA')}\n`;
        }
        
        content = content.replace('{stats}', statsContent);
        
        // إضافة التذييل
        content = content.replace('{footer}', this.templates.footer);
        
        return content;
    }
    
    getTemplates() {
        return {
            header: `🔗 WhatsApp Companion Bot - تصدير الروابط
📅 التاريخ: {date} {time}
📊 إجمالي الروابط: {total}
══════════════════════════════════════════════════════════════

{links}

{stats}

{footer}
`,
            footer: `══════════════════════════════════════════════════════════════
📄 تم إنشاء هذا التقرير تلقائياً بواسطة WhatsApp Companion Bot
🤖 الإصدار: 1.0.0
📅 تم الإنشاء: ${new Date().toLocaleString('ar-SA')}
✨ "التنظيم هو مفتاح النجاح" ✨
══════════════════════════════════════════════════════════════`
        };
    }
    
    async updateExportLog(fileName, linksCount) {
        try {
            const logFile = path.join(this.exportDir, 'exports_log.json');
            let log = [];
            
            try {
                const data = await fs.readFile(logFile, 'utf8');
                log = JSON.parse(data);
            } catch {
                log = [];
            }
            
            log.push({
                fileName: fileName,
                linksCount: linksCount,
                exportedAt: new Date().toISOString(),
                size: (await fs.stat(path.join(this.exportDir, fileName))).size
            });
            
            // حفظ آخر 20 تصدير فقط
            if (log.length > 20) {
                log = log.slice(-20);
            }
            
            await fs.writeFile(logFile, JSON.stringify(log, null, 2), 'utf8');
            
        } catch (error) {
            console.error('❌ خطأ في تحديث سجل التصديرات:', error);
        }
    }
    
    async listExports() {
        try {
            const files = await fs.readdir(this.exportDir);
            const exportFiles = files.filter(file => file.startsWith('links_export_'));
            
            const exportsList = [];
            
            for (const file of exportFiles) {
                const filePath = path.join(this.exportDir, file);
                const stat = await fs.stat(filePath);
                
                exportsList.push({
                    name: file,
                    path: filePath,
                    size: stat.size,
                    created: stat.birthtime,
                    modified: stat.mtime
                });
            }
            
            // ترتيب حسب التاريخ (الأحدث أولاً)
            return exportsList.sort((a, b) => b.created - a.created);
            
        } catch (error) {
            console.error('❌ خطأ في عرض التصديرات:', error);
            return [];
        }
    }
    
    async cleanupOldExports(days = 7) {
        try {
            const exports = await this.listExports();
            const now = Date.now();
            const maxAgeMs = days * 24 * 60 * 60 * 1000;
            let deletedCount = 0;
            
            for (const exportFile of exports) {
                const fileAge = now - exportFile.created.getTime();
                
                if (fileAge > maxAgeMs) {
                    await fs.unlink(exportFile.path);
                    deletedCount++;
                    console.log(`🗑️ تم حذف: ${exportFile.name}`);
                }
            }
            
            if (deletedCount > 0) {
                console.log(`🧹 تم تنظيف ${deletedCount} ملف تصدير قديم`);
            }
            
            return deletedCount;
            
        } catch (error) {
            console.error('❌ خطأ في تنظيف التصديرات:', error);
            return 0;
        }
    }
}

// استخدام المولد مباشرة
if (require.main === module) {
    const generator = new ExportGenerator();
    
    async function main() {
        const command = process.argv[2];
        
        switch (command) {
            case 'generate':
                const result = await generator.generateLinksExport();
                if (result.success) {
                    console.log(`✅ تم إنشاء: ${result.fileName}`);
                    console.log(`📊 الروابط: ${result.linksCount}`);
                    console.log(`💾 الحجم: ${Math.round(result.size / 1024)} KB`);
                }
                break;
                
            case 'list':
                const exports = await generator.listExports();
                console.log('\n📋 آخر 5 تصديرات:');
                exports.slice(0, 5).forEach((exp, index) => {
                    const sizeKB = Math.round(exp.size / 1024);
                    console.log(`${index + 1}. ${exp.name} (${sizeKB} KB)`);
                });
                break;
                
            case 'cleanup':
                const deleted = await generator.cleanupOldExports(7);
                console.log(`🧹 تم حذف ${deleted} ملف قديم`);
                break;
                
            default:
                console.log('🔧 أوامر التصدير:');
                console.log('npm run export generate - إنشاء تصدير جديد');
                console.log('npm run export list     - عرض التصديرات');
                console.log('npm run export cleanup  - تنظيف التصديرات القديمة');
        }
    }
    
    main().catch(console.error);
}

module.exports = ExportGenerator;
