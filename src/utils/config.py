"""
⚙️ Config Manager - مدير إعدادات البوت
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """مستويات التسجيل"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class DatabaseType(Enum):
    """أنواع قواعد البيانات"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"

@dataclass
class WhatsAppConfig:
    """إعدادات واتساب"""
    qr_timeout: int = 300  # ثانية
    max_sessions: int = 4
    session_dir: str = "sessions"
    reconnect_attempts: int = 3
    reconnect_delay: int = 5  # ثانية
    
    # قيود
    max_messages_per_day: int = 1000
    max_groups_per_day: int = 100
    max_broadcasts_per_day: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'qr_timeout': self.qr_timeout,
            'max_sessions': self.max_sessions,
            'session_dir': self.session_dir,
            'reconnect_attempts': self.reconnect_attempts,
            'reconnect_delay': self.reconnect_delay,
            'max_messages_per_day': self.max_messages_per_day,
            'max_groups_per_day': self.max_groups_per_day,
            'max_broadcasts_per_day': self.max_broadcasts_per_day
        }

@dataclass
class DatabaseConfig:
    """إعدادات قاعدة البيانات"""
    type: DatabaseType = DatabaseType.SQLITE
    host: str = "localhost"
    port: int = 5432
    name: str = "whatsapp_bot"
    username: str = ""
    password: str = ""
    pool_size: int = 10
    echo: bool = False
    
    @property
    def url(self) -> str:
        """إنشاء عنوان قاعدة البيانات"""
        if self.type == DatabaseType.SQLITE:
            return f"sqlite:///data/{self.name}.db"
        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
        elif self.type == DatabaseType.MYSQL:
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'type': self.type.value,
            'host': self.host,
            'port': self.port,
            'name': self.name,
            'username': self.username,
            'pool_size': self.pool_size,
            'echo': self.echo,
            'url': self.url
        }

@dataclass
class AutomationConfig:
    """إعدادات الأتمتة"""
    # التجميع
    collection_interval: int = 300  # ثانية
    max_links_per_session: int = 10000
    link_categories: Dict[str, List[str]] = field(default_factory=lambda: {
        'whatsapp': ['chat.whatsapp.com'],
        'telegram': ['t.me', 'telegram.me'],
        'instagram': ['instagram.com'],
        'facebook': ['facebook.com', 'fb.com'],
        'youtube': ['youtube.com', 'youtu.be'],
        'tiktok': ['tiktok.com'],
        'twitter': ['twitter.com', 'x.com'],
        'other': []
    })
    
    # النشر
    post_interval: int = 30  # ثانية بين كل نشر
    max_posts_per_day: int = 100
    advertisement_ttl: int = 86400  # صلاحية الإعلان (ثانية)
    
    # الانظمام
    join_interval: int = 120  # ثانية بين كل انظمام
    max_joins_per_day: int = 20
    join_request_timeout: int = 86400  # 24 ساعة
    
    # الردود
    reply_cooldown: int = 30  # ثانية بين الردود لنفس المستخدم
    max_replies_per_hour: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'collection_interval': self.collection_interval,
            'max_links_per_session': self.max_links_per_session,
            'link_categories': self.link_categories,
            'post_interval': self.post_interval,
            'max_posts_per_day': self.max_posts_per_day,
            'advertisement_ttl': self.advertisement_ttl,
            'join_interval': self.join_interval,
            'max_joins_per_day': self.max_joins_per_day,
            'join_request_timeout': self.join_request_timeout,
            'reply_cooldown': self.reply_cooldown,
            'max_replies_per_hour': self.max_replies_per_hour
        }

@dataclass
class SecurityConfig:
    """إعدادات الأمان"""
    encryption_key: str = ""
    enable_2fa: bool = False
    session_timeout: int = 86400  # ثانية (24 ساعة)
    max_login_attempts: int = 5
    login_lockout_time: int = 300  # ثانية (5 دقائق)
    
    # قائمة IP المسموحة (فارغة = كل شيء مسموح)
    allowed_ips: List[str] = field(default_factory=list)
    
    # التحقق من الروابط
    validate_urls: bool = True
    block_malicious_urls: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'enable_2fa': self.enable_2fa,
            'session_timeout': self.session_timeout,
            'max_login_attempts': self.max_login_attempts,
            'login_lockout_time': self.login_lockout_time,
            'validate_urls': self.validate_urls,
            'block_malicious_urls': self.block_malicious_urls
        }

@dataclass
class BackupConfig:
    """إعدادات النسخ الاحتياطي"""
    enabled: bool = True
    interval: int = 86400  # ثانية (24 ساعة)
    max_backups: int = 30
    backup_dir: str = "backups"
    
    # ماذا يتم نسخه
    backup_database: bool = True
    backup_sessions: bool = True
    backup_media: bool = True
    backup_config: bool = True
    
    # الضغط
    compress_backups: bool = True
    compression_level: int = 6
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'enabled': self.enabled,
            'interval': self.interval,
            'max_backups': self.max_backups,
            'backup_dir': self.backup_dir,
            'backup_database': self.backup_database,
            'backup_sessions': self.backup_sessions,
            'backup_media': self.backup_media,
            'backup_config': self.backup_config,
            'compress_backups': self.compress_backups,
            'compression_level': self.compression_level
        }

class Config:
    """مدير الإعدادات الرئيسي"""
    
    _instance = None
    
    def __new__(cls):
        """نمط Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """تهيئة الإعدادات"""
        if self._initialized:
            return
        
        # المسارات
        self.base_dir = Path.cwd()
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = self.base_dir / "config"
        self.backup_dir = self.base_dir / "backups"
        
        # إنشاء المجلدات
        self._create_directories()
        
        # الملفات
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.base_dir / ".env"
        
        # التحميل
        self._load_from_env()
        self._load_from_file()
        self._set_defaults()
        
        # المكونات
        self.whatsapp = WhatsAppConfig()
        self.database = DatabaseConfig()
        self.automation = AutomationConfig()
        self.security = SecurityConfig()
        self.backup = BackupConfig()
        
        # الإعدادات العامة
        self.app_name: str = "WhatsApp Bot"
        self.version: str = "1.0.0"
        self.debug: bool = False
        self.log_level: LogLevel = LogLevel.INFO
        self.timezone: str = "Asia/Riyadh"
        self.language: str = "ar"
        self.admin_emails: List[str] = field(default_factory=list)
        
        self._initialized = True
        logger.info("⚙️ تم تحميل إعدادات البوت")
    
    def _create_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.config_dir,
            self.backup_dir,
            self.data_dir / "sessions",
            self.data_dir / "media",
            self.data_dir / "exports",
            self.data_dir / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.debug("📁 تم إنشاء المجلدات المطلوبة")
    
    def _load_from_env(self):
        """تحميل الإعدادات من ملف .env"""
        try:
            if self.env_file.exists():
                from dotenv import load_dotenv
                load_dotenv(self.env_file)
                logger.info("📄 تم تحميل الإعدادات من ملف .env")
        except ImportError:
            logger.warning("⚠️ مكتبة python-dotenv غير مثبتة، سيتم استخدام الإعدادات الافتراضية")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل ملف .env: {e}")
    
    def _load_from_file(self):
        """تحميل الإعدادات من ملف JSON"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._update_from_dict(data)
                logger.info(f"📄 تم تحميل الإعدادات من {self.config_file}")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل ملف الإعدادات: {e}")
    
    def _update_from_dict(self, data: Dict[str, Any]):
        """تحديث الإعدادات من قاموس"""
        try:
            # الإعدادات العامة
            if 'app_name' in data:
                self.app_name = data['app_name']
            if 'version' in data:
                self.version = data['version']
            if 'debug' in data:
                self.debug = data['debug']
            if 'log_level' in data:
                self.log_level = LogLevel(data['log_level'])
            if 'timezone' in data:
                self.timezone = data['timezone']
            if 'language' in data:
                self.language = data['language']
            if 'admin_emails' in data:
                self.admin_emails = data['admin_emails']
            
            # إعدادات واتساب
            if 'whatsapp' in data:
                whatsapp_data = data['whatsapp']
                self.whatsapp = WhatsAppConfig(**whatsapp_data)
            
            # إعدادات قاعدة البيانات
            if 'database' in data:
                db_data = data['database']
                if 'type' in db_data:
                    db_data['type'] = DatabaseType(db_data['type'])
                self.database = DatabaseConfig(**db_data)
            
            # إعدادات الأتمتة
            if 'automation' in data:
                auto_data = data['automation']
                self.automation = AutomationConfig(**auto_data)
            
            # إعدادات الأمان
            if 'security' in data:
                sec_data = data['security']
                self.security = SecurityConfig(**sec_data)
            
            # إعدادات النسخ الاحتياطي
            if 'backup' in data:
                backup_data = data['backup']
                self.backup = BackupConfig(**backup_data)
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث الإعدادات: {e}")
    
    def _set_defaults(self):
        """تعيين القيم الافتراضية من متغيرات البيئة"""
        # قاعدة البيانات
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            self.database.url = db_url
        
        # مفتاح التشفير
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if encryption_key:
            self.security.encryption_key = encryption_key
        
        # مستوى التسجيل
        log_level = os.getenv('LOG_LEVEL')
        if log_level:
            try:
                self.log_level = LogLevel(log_level.upper())
            except:
                pass
        
        # وضع التصحيح
        debug_mode = os.getenv('DEBUG')
        if debug_mode:
            self.debug = debug_mode.lower() == 'true'
    
    def save(self) -> bool:
        """حفظ الإعدادات إلى ملف"""
        try:
            config_data = {
                'app_name': self.app_name,
                'version': self.version,
                'debug': self.debug,
                'log_level': self.log_level.value,
                'timezone': self.timezone,
                'language': self.language,
                'admin_emails': self.admin_emails,
                'whatsapp': self.whatsapp.to_dict(),
                'database': self.database.to_dict(),
                'automation': self.automation.to_dict(),
                'security': self.security.to_dict(),
                'backup': self.backup.to_dict(),
                'last_updated': self._get_timestamp()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 تم حفظ الإعدادات إلى {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الإعدادات: {e}")
            return False
    
    def reload(self) -> bool:
        """إعادة تحميل الإعدادات"""
        try:
            self._load_from_file()
            self._load_from_env()
            logger.info("🔄 تم إعادة تحميل الإعدادات")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة تحميل الإعدادات: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """الحصول على جميع الإعدادات"""
        return {
            'general': {
                'app_name': self.app_name,
                'version': self.version,
                'debug': self.debug,
                'log_level': self.log_level.value,
                'timezone': self.timezone,
                'language': self.language,
                'base_dir': str(self.base_dir),
                'data_dir': str(self.data_dir)
            },
            'whatsapp': self.whatsapp.to_dict(),
            'database': self.database.to_dict(),
            'automation': self.automation.to_dict(),
            'security': self.security.to_dict(),
            'backup': self.backup.to_dict()
        }
    
    def update(self, section: str, updates: Dict[str, Any]) -> bool:
        """تحديث قسم معين من الإعدادات"""
        try:
            if section == 'general':
                for key, value in updates.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            
            elif section == 'whatsapp':
                for key, value in updates.items():
                    if hasattr(self.whatsapp, key):
                        setattr(self.whatsapp, key, value)
            
            elif section == 'database':
                for key, value in updates.items():
                    if hasattr(self.database, key):
                        setattr(self.database, key, value)
            
            elif section == 'automation':
                for key, value in updates.items():
                    if hasattr(self.automation, key):
                        setattr(self.automation, key, value)
            
            elif section == 'security':
                for key, value in updates.items():
                    if hasattr(self.security, key):
                        setattr(self.security, key, value)
            
            elif section == 'backup':
                for key, value in updates.items():
                    if hasattr(self.backup, key):
                        setattr(self.backup, key, value)
            
            else:
                logger.error(f"❌ قسم غير معروف: {section}")
                return False
            
            # حفظ التغييرات
            self.save()
            logger.info(f"🔄 تم تحديث قسم: {section}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث الإعدادات: {e}")
            return False
    
    def validate(self) -> List[str]:
        """التحقق من صحة الإعدادات"""
        errors = []
        
        # التحقق من مفتاح التشفير
        if not self.security.encryption_key:
            errors.append("مفتاح التشفير مطلوب")
        
        # التحقق من قاعدة البيانات
        if not self.database.url:
            errors.append("عنوان قاعدة البيانات مطلوب")
        
        # التحقق من المسارات
        if not self.data_dir.exists():
            errors.append(f"مجلد البيانات غير موجود: {self.data_dir}")
        
        # التحقق من القيم العددية
        if self.whatsapp.qr_timeout <= 0:
            errors.append("مهلة QR يجب أن تكون أكبر من صفر")
        
        if self.automation.collection_interval < 60:
            errors.append("فترة التجميع يجب أن تكون 60 ثانية على الأقل")
        
        if self.automation.post_interval < 10:
            errors.append("فترة النشر يجب أن تكون 10 ثواني على الأقل")
        
        if self.automation.join_interval < 60:
            errors.append("فترة الانظمام يجب أن تكون 60 ثانية على الأقل")
        
        return errors
    
    def export(self, filepath: Optional[Path] = None) -> Path:
        """تصدير الإعدادات إلى ملف"""
        try:
            if filepath is None:
                timestamp = self._get_timestamp()
                filepath = self.data_dir / "exports" / f"config_export_{timestamp}.json"
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'config': self.get_all(),
                'exported_at': self._get_timestamp(),
                'version': self.version
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📤 تم تصدير الإعدادات إلى: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ خطأ في تصدير الإعدادات: {e}")
            raise
    
    def import_config(self, filepath: Path) -> bool:
        """استيراد الإعدادات من ملف"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'config' not in import_data:
                logger.error("❌ تنسيق ملف غير صالح")
                return False
            
            self._update_from_dict(import_data['config'])
            self.save()
            
            logger.info(f"📥 تم استيراد الإعدادات من: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في استيراد الإعدادات: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """إعادة تعيين الإعدادات إلى القيم الافتراضية"""
        try:
            # نسخة احتياطية من الملف الحالي
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.bak')
                import shutil
                shutil.copy2(self.config_file, backup_file)
                logger.info(f"💾 تم إنشاء نسخة احتياطية: {backup_file}")
            
            # حذف الملف الحالي
            if self.config_file.exists():
                self.config_file.unlink()
            
            # إعادة التهيئة
            self._initialized = False
            self.__init__()
            
            logger.info("🔄 تم إعادة تعيين الإعدادات إلى القيم الافتراضية")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة تعيين الإعدادات: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """الحصول على طابع زمني"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @property
    def is_valid(self) -> bool:
        """التحقق من صحة الإعدادات"""
        return len(self.validate()) == 0
    
    def __str__(self) -> str:
        """تمثيل نصي للإعدادات"""
        return f"Config(app_name='{self.app_name}', version='{self.version}', valid={self.is_valid})"
