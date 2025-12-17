"""
📝 Logger Configuration - إعدادات مسجل الأحداث
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColorFormatter(logging.Formatter):
    """مُنسق الألوان للسجلات"""
    
    COLORS = {
        'DEBUG': '\033[94m',     # أزرق
        'INFO': '\033[92m',      # أخضر
        'WARNING': '\033[93m',   # أصفر
        'ERROR': '\033[91m',     # أحمر
        'CRITICAL': '\033[41m'   # خلفية حمراء
    }
    
    RESET = '\033[0m'
    
    def format(self, record):
        """تنسيق السجل مع الألوان"""
        # إضافة اللون
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # تنسيق الرسالة
        if record.levelno >= logging.ERROR:
            record.msg = f"❌ {record.msg}"
        elif record.levelno >= logging.WARNING:
            record.msg = f"⚠️  {record.msg}"
        elif record.levelno >= logging.INFO:
            record.msg = f"✅ {record.msg}"
        elif record.levelno >= logging.DEBUG:
            record.msg = f"🔍 {record.msg}"
        
        return super().format(record)

class ArabicFormatter(logging.Formatter):
    """مُنسق عربي للسجلات"""
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        if fmt is None:
            fmt = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
        super().__init__(fmt, datefmt, style)
    
    def format(self, record):
        """تنسيق السجل بالعربية"""
        # تحويل مستوى السجل إلى عربي
        level_translations = {
            'DEBUG': 'تصحيح',
            'INFO': 'معلومات',
            'WARNING': 'تحذير',
            'ERROR': 'خطأ',
            'CRITICAL': 'حرج'
        }
        
        record.levelname = level_translations.get(record.levelname, record.levelname)
        
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_arabic: bool = False,
    enable_colors: bool = True
) -> None:
    """
    إعداد نظام تسجيل الأحداث
    
    Args:
        log_level: مستوى السجل (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: اسم ملف السجل (إذا كان None، سيتم إنشاء اسم تلقائي)
        log_dir: مجلد السجلات
        max_bytes: الحد الأقصى لحجم ملف السجل
        backup_count: عدد ملفات النسخ الاحتياطي
        enable_console: تفعيل السجل في الكونسول
        enable_file: تفعيل السجل في الملف
        enable_arabic: استخدام التنسيق العربي
        enable_colors: استخدام الألوان في الكونسول
    """
    
    # إنشاء مجلد السجلات
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # إنشاء اسم ملف السجل
    if log_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = f"whatsapp_bot_{timestamp}.log"
    
    log_file_path = log_path / log_file
    
    # الحصول على مستوى السجل
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # تكوين السجل الأساسي
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[]
    )
    
    # إزالة جميع المعالجات الحالية
    logging.getLogger().handlers.clear()
    
    # معالج الكونسول
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        if enable_colors and sys.stdout.isatty():
            formatter = ColorFormatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                '%Y-%m-%d %H:%M:%S'
            )
        elif enable_arabic:
            formatter = ArabicFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                '%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
    
    # معالج الملف
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logging.getLogger().addHandler(file_handler)
    
    # تعيين مستوى سجل لبعض المكتبات
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # رسالة بدء التشغيل
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 بدء تشغيل نظام تسجيل الأحداث")
    logger.info(f"📝 مستوى السجل: {log_level}")
    logger.info(f"💾 مجلد السجلات: {log_path}")
    logger.info(f"📄 ملف السجل: {log_file_path}")

def get_logger(name: str) -> logging.Logger:
    """
    الحصول على مسجل أحداث
    
    Args:
        name: اسم المسجل
        
    Returns:
        كائن مسجل الأحداث
    """
    return logging.getLogger(name)

def log_exception(logger: logging.Logger, exception: Exception, 
                  context: str = "", include_traceback: bool = True):
    """
    تسجيل استثناء مع السياق
    
    Args:
        logger: مسجل الأحداث
        exception: الاستثناء
        context: سياق الخطأ
        include_traceback: تضمين تتبع المكالمات
    """
    try:
        error_msg = f"{context}: {type(exception).__name__}: {str(exception)}"
        
        if include_traceback:
            import traceback
            tb_str = traceback.format_exc()
            error_msg += f"\n{traceback}"
        
        logger.error(error_msg)
        
    except Exception as e:
        print(f"❌ فشل في تسجيل الاستثناء: {e}")

def log_performance(logger: logging.Logger, operation: str, 
                   start_time: float, end_time: float = None):
    """
    تسجيل أداء العملية
    
    Args:
        logger: مسجل الأحداث
        operation: اسم العملية
        start_time: وقت البدء
        end_time: وقت الانتهاء (إذا كان None، يستخدم الوقت الحالي)
    """
    if end_time is None:
        import time
        end_time = time.time()
    
    duration = end_time - start_time
    
    if duration > 5.0:
        level = logging.WARNING
        emoji = "🐢"
    elif duration > 1.0:
        level = logging.INFO
        emoji = "⏱️"
    else:
        level = logging.DEBUG
        emoji = "⚡"
    
    message = f"{emoji} {operation} استغرق {duration:.3f} ثانية"
    logger.log(level, message)

def get_log_files(log_dir: str = "logs", pattern: str = "*.log") -> list:
    """
    الحصول على قائمة ملفات السجلات
    
    Args:
        log_dir: مجلد السجلات
        pattern: نمط البحث
        
    Returns:
        قائمة بمسارات ملفات السجلات
    """
    log_path = Path(log_dir)
    
    if not log_path.exists():
        return []
    
    log_files = sorted(log_path.glob(pattern), key=os.path.getmtime, reverse=True)
    return [str(file) for file in log_files]

def clear_old_logs(log_dir: str = "logs", days: int = 30):
    """
    حذف السجلات القديمة
    
    Args:
        log_dir: مجلد السجلات
        days: عدد الأيام للاحتفاظ بالسجلات
    """
    try:
        import time
        from pathlib import Path
        
        log_path = Path(log_dir)
        if not log_path.exists():
            return
        
        cutoff_time = time.time() - (days * 86400)
        deleted_count = 0
        
        for log_file in log_path.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1
        
        logger = get_logger(__name__)
        logger.info(f"🧹 تم حذف {deleted_count} ملف سجل قديم")
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"❌ خطأ في حذف السجلات القديمة: {e}")

def setup_structured_logging(logger_name: str = "whatsapp_bot"):
    """
    إعداد السجل المنظم (Structured Logging)
    
    Args:
        logger_name: اسم المسجل
        
    Returns:
        كائن السجل المنظم
    """
    try:
        import structlog
        
        # تكوين structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()  # إخراج JSON
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        return structlog.get_logger(logger_name)
        
    except ImportError:
        logger = get_logger(logger_name)
        logger.warning("⚠️ مكتبة structlog غير مثبتة، استخدام السجل العادي")
        return logger

# اختصارات للاستخدام السريع
def debug(msg: str, *args, **kwargs):
    """سجل تصحيح"""
    logger = get_logger(kwargs.pop('logger_name', __name__))
    logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    """سجل معلومات"""
    logger = get_logger(kwargs.pop('logger_name', __name__))
    logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    """سجل تحذير"""
    logger = get_logger(kwargs.pop('logger_name', __name__))
    logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    """سجل خطأ"""
    logger = get_logger(kwargs.pop('logger_name', __name__))
    logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    """سجل حرج"""
    logger = get_logger(kwargs.pop('logger_name', __name__))
    logger.critical(msg, *args, **kwargs)
