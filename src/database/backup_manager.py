"""
💾 Backup Manager - مدير النسخ الاحتياطي
"""

import asyncio
import json
import logging
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BackupManager:
    """مدير النسخ الاحتياطي"""
    
    def __init__(self, db_handler, backup_dir: str = "backups"):
        """تهيئة مدير النسخ الاحتياطي"""
        self.db = db_handler
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # إعدادات النسخ الاحتياطي
        self.max_backups = 30  # الحد الأقصى للنسخ المحفوظة
        self.auto_backup_interval = 24  # ساعات بين النسخ التلقائي
        self.last_backup_time = None
        
        logger.info(f"💾 مدير النسخ الاحتياطي مهيأ: {self.backup_dir}")
    
    async def create_backup(self, backup_name: str = None, include_data: bool = True) -> Optional[Path]:
        """إنشاء نسخة احتياطية"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if backup_name:
                backup_name = f"{backup_name}_{timestamp}"
            else:
                backup_name = f"whatsapp_bot_backup_{timestamp}"
            
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"💾 إنشاء نسخة احتياطية: {backup_name}")
            
            # 1. نسخ قاعدة البيانات
            if include_data and self.db.is_sqlite:
                db_backup_path = backup_path / "database.db"
                await self.db.backup_database(str(db_backup_path))
            
            # 2. حفظ ملف الإعدادات
            settings = await self._export_settings()
            settings_file = backup_path / "settings.json"
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            # 3. حفظ ملف الوضع
            state = await self._export_state()
            state_file = backup_path / "state.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            # 4. نسخ مجلد الجلسات
            sessions_dir = Path("sessions")
            if sessions_dir.exists():
                sessions_backup_dir = backup_path / "sessions"
                shutil.copytree(sessions_dir, sessions_backup_dir)
            
            # 5. نسخ مجلد البيانات
            data_dir = Path("data")
            if data_dir.exists():
                data_backup_dir = backup_path / "data"
                shutil.copytree(data_dir, data_backup_dir, ignore=shutil.ignore_patterns('*.db'))
            
            # 6. إنشاء ملف وصف النسخة
            metadata = {
                'backup_name': backup_name,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'components': ['database', 'settings', 'state', 'sessions', 'data'],
                'total_size': self._get_directory_size(backup_path)
            }
            
            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 7. ضغط النسخة الاحتياطية
            zip_path = backup_path.parent / f"{backup_name}.zip"
            self._create_zip(backup_path, zip_path)
            
            # 8. حذف المجلد المؤقت
            shutil.rmtree(backup_path)
            
            # تحديث وقت آخر نسخة
            self.last_backup_time = datetime.now()
            
            # تنظيف النسخ القديمة
            await self.cleanup_old_backups()
            
            logger.info(f"✅ تم إنشاء النسخة الاحتياطية: {zip_path.name} ({self._bytes_to_human(zip_path.stat().st_size)})")
            
            return zip_path
            
        except Exception as e:
            logger.error(f"❌ فشل في إنشاء النسخة الاحتياطية: {e}")
            return None
    
    async def _export_settings(self) -> Dict[str, Any]:
        """تصدير الإعدادات"""
        try:
            # الحصول على جميع الإعدادات
            settings = {}
            
            # هذه دالة افتراضية - تحتاج للتطبيق الفعلي
            # في الواقع ستقوم بجمع الإعدادات من قاعدة البيانات أو ملفات الإعدادات
            
            return {
                'exported_at': datetime.now().isoformat(),
                'settings': settings
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في تصدير الإعدادات: {e}")
            return {}
    
    async def _export_state(self) -> Dict[str, Any]:
        """تصدير حالة النظام"""
        try:
            # الحصول على حالة النظام الحالية
            state = {
                'exported_at': datetime.now().isoformat(),
                'system_state': {
                    'is_running': True,  # يجب الحصول من النظام
                    'connected_sessions': 0,  # يجب الحصول من النظام
                    'active_tasks': []
                },
                'database_info': await self.db.get_database_info(),
                'statistics': await self.db.get_statistics(days=7)
            }
            
            return state
            
        except Exception as e:
            logger.error(f"❌ خطأ في تصدير الحالة: {e}")
            return {}
    
    async def restore_backup(self, backup_path: Path) -> bool:
        """استعادة نسخة احتياطية"""
        try:
            if not backup_path.exists():
                logger.error(f"❌ ملف النسخة الاحتياطية غير موجود: {backup_path}")
                return False
            
            logger.info(f"🔄 استعادة النسخة الاحتياطية: {backup_path.name}")
            
            # إنشاء مجلد استخراج مؤقت
            extract_dir = self.backup_dir / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # استخراج الأرشيف
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # قراءة ملف الوصف
                metadata_file = extract_dir / "metadata.json"
                if not metadata_file.exists():
                    logger.error("❌ ملف وصف النسخة غير موجود")
                    return False
                
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                logger.info(f"📋 استعادة نسخة: {metadata['backup_name']}")
                
                # استعادة المكونات
                for component in metadata.get('components', []):
                    component_path = extract_dir / component
                    
                    if component == 'database' and component_path.exists():
                        # استعادة قاعدة البيانات
                        db_files = list(component_path.glob("*.db"))
                        if db_files:
                            await self.db.restore_database(str(db_files[0]))
                    
                    elif component == 'sessions' and component_path.exists():
                        # استعادة الجلسات
                        sessions_dir = Path("sessions")
                        if sessions_dir.exists():
                            shutil.rmtree(sessions_dir)
                        shutil.copytree(component_path, sessions_dir)
                    
                    elif component == 'data' and component_path.exists():
                        # استعادة البيانات
                        data_dir = Path("data")
                        if data_dir.exists():
                            # حذف الملفات القديمة مع الاحتفاظ على قاعدة البيانات
                            for item in data_dir.iterdir():
                                if item.is_file() and not item.name.endswith('.db'):
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item)
                        
                        # نسخ الملفات الجديدة
                        for item in component_path.iterdir():
                            if item.is_file():
                                shutil.copy2(item, data_dir / item.name)
                            elif item.is_dir():
                                shutil.copytree(item, data_dir / item.name)
                
                logger.info("✅ تم استعادة النسخة الاحتياطية بنجاح")
                return True
                
            finally:
                # تنظيف المجلد المؤقت
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
            
        except Exception as e:
            logger.error(f"❌ فشل في استعادة النسخة الاحتياطية: {e}")
            return False
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """عرض قائمة النسخ الاحتياطية"""
        backups = []
        
        try:
            for file_path in self.backup_dir.glob("*.zip"):
                try:
                    stat = file_path.stat()
                    
                    backup_info = {
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'size_human': self._bytes_to_human(stat.st_size),
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    
                    # محاولة قراءة metadata من الأرشيف
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            if 'metadata.json' in zip_ref.namelist():
                                with zip_ref.open('metadata.json') as f:
                                    metadata = json.load(f)
                                    backup_info['metadata'] = metadata
                    except:
                        pass
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    logger.debug(f"⚠️ خطأ في قراءة معلومات النسخة {file_path.name}: {e}")
            
            # ترتيب حسب تاريخ التعديل (أحدث أولاً)
            backups.sort(key=lambda x: x['modified_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض النسخ الاحتياطية: {e}")
            return []
    
    async def cleanup_old_backups(self):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            backups = await self.list_backups()
            
            if len(backups) > self.max_backups:
                backups_to_delete = backups[self.max_backups:]
                
                for backup in backups_to_delete:
                    try:
                        Path(backup['path']).unlink()
                        logger.info(f"🧹 تم حذف نسخة احتياطية قديمة: {backup['name']}")
                    except Exception as e:
                        logger.error(f"❌ فشل في حذف النسخة {backup['name']}: {e}")
                
                logger.info(f"🧹 تم تنظيف {len(backups_to_delete)} نسخة احتياطية قديمة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف النسخ القديمة: {e}")
    
    async def schedule_auto_backup(self):
        """جدولة النسخ الاحتياطي التلقائي"""
        try:
            while True:
                # التحقق مما إذا حان وقت النسخ الاحتياطي
                if self._should_create_auto_backup():
                    logger.info("🕐 إنشاء نسخة احتياطية تلقائية...")
                    await self.create_backup("auto_backup")
                
                # انتظار ساعة قبل الفحص التالي
                await asyncio.sleep(3600)
                
        except Exception as e:
            logger.error(f"❌ خطأ في جدولة النسخ الاحتياطي: {e}")
    
    def _should_create_auto_backup(self) -> bool:
        """التحقق مما إذا كان يجب إنشاء نسخة احتياطية تلقائية"""
        if self.last_backup_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_backup_time
        return time_since_last.total_seconds() >= (self.auto_backup_interval * 3600)
    
    def _create_zip(self, source_dir: Path, zip_path: Path):
        """إنشاء ملف مضغوط"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
    
    def _get_directory_size(self, directory: Path) -> int:
        """حساب حجم المجلد"""
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def _bytes_to_human(self, size_bytes: int) -> str:
        """تحويل البايتات إلى صيغة مقروءة"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    async def verify_backup(self, backup_path: Path) -> bool:
        """التحقق من صحة النسخة الاحتياطية"""
        try:
            if not backup_path.exists():
                return False
            
            # التحقق من أن الملف هو أرشيف ZIP صالح
            if not zipfile.is_zipfile(backup_path):
                return False
            
            # فتح الأرشيف والتحقق من الملفات الأساسية
            with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                required_files = ['metadata.json', 'settings.json', 'state.json']
                
                for file in required_files:
                    if file not in zip_ref.namelist():
                        logger.warning(f"⚠️ الملف المطلوب غير موجود في النسخة: {file}")
                        return False
                
                # التحقق من حجم الأرشيف
                file_size = backup_path.stat().st_size
                if file_size < 1024:  # أقل من 1KB
                    logger.warning("⚠️ حجم النسخة الاحتياطية صغير جدًا")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من النسخة: {e}")
            return False
    
    async def get_backup_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات النسخ الاحتياطية"""
        try:
            backups = await self.list_backups()
            
            total_size = sum(b['size'] for b in backups)
            oldest_backup = backups[-1]['created_at'] if backups else None
            newest_backup = backups[0]['created_at'] if backups else None
            
            return {
                'total_backups': len(backups),
                'total_size': total_size,
                'total_size_human': self._bytes_to_human(total_size),
                'oldest_backup': oldest_backup,
                'newest_backup': newest_backup,
                'max_backups': self.max_backups,
                'auto_backup_interval': self.auto_backup_interval,
                'last_backup_time': self.last_backup_time.isoformat() if self.last_backup_time else None
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب إحصائيات النسخ: {e}")
            return {}
