"""
💾 Cache Manager - مدير التخزين المؤقت
"""

import asyncio
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class CacheType(Enum):
    """أنواع التخزين المؤقت"""
    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"

@dataclass
class CacheItem:
    """عنصر في التخزين المؤقت"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    hits: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """التحقق مما إذا انتهت صلاحية العنصر"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def ttl(self) -> Optional[float]:
        """الوقت المتبقي حتى انتهاء الصلاحية (ثانية)"""
        if self.expires_at is None:
            return None
        return (self.expires_at - datetime.now()).total_seconds()
    
    def hit(self):
        """زيادة عداد الزيارات"""
        self.hits += 1
        self.last_accessed = datetime.now()

class CacheManager:
    """مدير التخزين المؤقت"""
    
    def __init__(self, cache_type: CacheType = CacheType.MEMORY, 
                 max_size: int = 1000, default_ttl: int = 300):
        """تهيئة مدير التخزين المؤقت"""
        self.cache_type = cache_type
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # التخزين في الذاكرة
        self.memory_cache: Dict[str, CacheItem] = {}
        
        # التخزين في الملفات
        self.cache_dir = "data/cache"
        
        # إحصائيات
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'expired': 0
        }
        
        # إنشاء المجلدات
        self._setup_cache()
        
        # بدء التنظيف التلقائي
        self.cleanup_task = asyncio.create_task(self._auto_cleanup())
        
        logger.info(f"💾 تم تهيئة مدير التخزين المؤقت ({cache_type.value})")
    
    def _setup_cache(self):
        """إعداد نظام التخزين المؤقت"""
        import os
        from pathlib import Path
        
        if self.cache_type == CacheType.FILE:
            cache_path = Path(self.cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 تم إنشاء مجلد التخزين المؤقت: {cache_path}")
        
        elif self.cache_type == CacheType.REDIS:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                # اختبار الاتصال
                self.redis_client.ping()
                logger.info("✅ تم الاتصال بـ Redis بنجاح")
            except ImportError:
                logger.error("❌ مكتبة redis غير مثبتة")
                self.cache_type = CacheType.MEMORY
            except Exception as e:
                logger.error(f"❌ خطأ في الاتصال بـ Redis: {e}")
                self.cache_type = CacheType.MEMORY
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """تعيين قيمة في التخزين المؤقت"""
        try:
            # التحقق من الحد الأقصى
            if len(self.memory_cache) >= self.max_size and key not in self.memory_cache:
                await self._evict_oldest()
            
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            elif self.default_ttl:
                expires_at = datetime.now() + timedelta(seconds=self.default_ttl)
            
            cache_item = CacheItem(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            if self.cache_type == CacheType.MEMORY:
                self.memory_cache[key] = cache_item
            
            elif self.cache_type == CacheType.FILE:
                await self._save_to_file(key, cache_item)
            
            elif self.cache_type == CacheType.REDIS:
                await self._save_to_redis(key, cache_item)
            
            self.stats['sets'] += 1
            logger.debug(f"💾 تم تخزين مؤقتًا: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التخزين المؤقت: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة من التخزين المؤقت"""
        try:
            cache_item = None
            
            if self.cache_type == CacheType.MEMORY:
                cache_item = self.memory_cache.get(key)
            
            elif self.cache_type == CacheType.FILE:
                cache_item = await self._load_from_file(key)
            
            elif self.cache_type == CacheType.REDIS:
                cache_item = await self._load_from_redis(key)
            
            if cache_item:
                # التحقق من الصلاحية
                if cache_item.is_expired:
                    await self.delete(key)
                    self.stats['expired'] += 1
                    self.stats['misses'] += 1
                    logger.debug(f"⏰ انتهت صلاحية العنصر: {key}")
                    return default
                
                # تحديث الإحصائيات
                cache_item.hit()
                self.stats['hits'] += 1
                
                # تحديث في التخزين
                if self.cache_type == CacheType.MEMORY:
                    self.memory_cache[key] = cache_item
                
                logger.debug(f"✅ ضربة تخزين مؤقت: {key}")
                return cache_item.value
            else:
                self.stats['misses'] += 1
                logger.debug(f"❌ فائت تخزين مؤقت: {key}")
                return default
                
        except Exception as e:
            logger.error(f"❌ خطأ في جلب التخزين المؤقت: {e}")
            self.stats['misses'] += 1
            return default
    
    async def delete(self, key: str) -> bool:
        """حذف عنصر من التخزين المؤقت"""
        try:
            if self.cache_type == CacheType.MEMORY:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            
            elif self.cache_type == CacheType.FILE:
                await self._delete_file(key)
            
            elif self.cache_type == CacheType.REDIS:
                await self._delete_redis(key)
            
            self.stats['deletes'] += 1
            logger.debug(f"🗑️ تم حذف التخزين المؤقت: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حذف التخزين المؤقت: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """التحقق من وجود عنصر"""
        try:
            if self.cache_type == CacheType.MEMORY:
                return key in self.memory_cache
            
            elif self.cache_type == CacheType.FILE:
                return await self._file_exists(key)
            
            elif self.cache_type == CacheType.REDIS:
                return await self._redis_exists(key)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من التخزين المؤقت: {e}")
            return False
    
    async def clear(self, prefix: str = None) -> int:
        """مسح التخزين المؤقت"""
        try:
            count = 0
            
            if self.cache_type == CacheType.MEMORY:
                if prefix:
                    keys_to_delete = [k for k in self.memory_cache.keys() 
                                     if k.startswith(prefix)]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                        count += 1
                else:
                    count = len(self.memory_cache)
                    self.memory_cache.clear()
            
            elif self.cache_type == CacheType.FILE:
                count = await self._clear_files(prefix)
            
            elif self.cache_type == CacheType.REDIS:
                count = await self._clear_redis(prefix)
            
            logger.info(f"🧹 تم مسح {count} عنصر من التخزين المؤقت")
            return count
            
        except Exception as e:
            logger.error(f"❌ خطأ في مسح التخزين المؤقت: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التخزين المؤقت"""
        total_items = 0
        expired_items = 0
        
        if self.cache_type == CacheType.MEMORY:
            total_items = len(self.memory_cache)
            expired_items = len([item for item in self.memory_cache.values() 
                                if item.is_expired])
        
        elif self.cache_type == CacheType.FILE:
            # حساب العناصر في الملفات
            pass
        
        elif self.cache_type == CacheType.REDIS:
            # إحصائيات Redis
            pass
        
        hits = self.stats['hits']
        misses = self.stats['misses']
        total_requests = hits + misses
        
        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
        miss_rate = (misses / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_type': self.cache_type.value,
            'total_items': total_items,
            'expired_items': expired_items,
            'max_size': self.max_size,
            'default_ttl': self.default_ttl,
            'hits': hits,
            'misses': misses,
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'expired_deleted': self.stats['expired'],
            'hit_rate': f"{hit_rate:.1f}%",
            'miss_rate': f"{miss_rate:.1f}%",
            'memory_usage': self._get_memory_usage()
        }
    
    async def _evict_oldest(self):
        """إزالة أقدم العناصر"""
        try:
            if self.cache_type == CacheType.MEMORY:
                if not self.memory_cache:
                    return
                
                # العثور على العنصر الأقل استخدامًا
                oldest_key = min(self.memory_cache.keys(),
                               key=lambda k: self.memory_cache[k].last_accessed)
                
                del self.memory_cache[oldest_key]
                logger.debug(f"🗑️ تم إزالة أقدم عنصر: {oldest_key}")
        
        except Exception as e:
            logger.error(f"❌ خطأ في إزالة العناصر القديمة: {e}")
    
    async def _auto_cleanup(self):
        """التنظيف التلقائي للعناصر المنتهية"""
        try:
            while True:
                await asyncio.sleep(60)  # كل دقيقة
                
                if self.cache_type == CacheType.MEMORY:
                    expired_keys = []
                    
                    for key, item in self.memory_cache.items():
                        if item.is_expired:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self.memory_cache[key]
                    
                    if expired_keys:
                        logger.debug(f"🧹 تم تنظيف {len(expired_keys)} عنصر منتهي")
                        
        except asyncio.CancelledError:
            logger.info("⏹️ توقف التنظيف التلقائي")
        except Exception as e:
            logger.error(f"❌ خطأ في التنظيف التلقائي: {e}")
    
    # === دعم التخزين في الملفات ===
    
    async def _save_to_file(self, key: str, item: CacheItem):
        """حفظ العنصر في ملف"""
        try:
            from pathlib import Path
            import pickle
            
            safe_key = self._make_filename_safe(key)
            filepath = Path(self.cache_dir) / f"{safe_key}.cache"
            
            # تحويل العنصر إلى قاموس
            item_dict = {
                'value': item.value,
                'created_at': item.created_at.isoformat(),
                'expires_at': item.expires_at.isoformat() if item.expires_at else None,
                'hits': item.hits,
                'last_accessed': item.last_accessed.isoformat(),
                'metadata': item.metadata
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(item_dict, f)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الملف المؤقت: {e}")
    
    async def _load_from_file(self, key: str) -> Optional[CacheItem]:
        """تحميل العنصر من ملف"""
        try:
            from pathlib import Path
            import pickle
            
            safe_key = self._make_filename_safe(key)
            filepath = Path(self.cache_dir) / f"{safe_key}.cache"
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'rb') as f:
                item_dict = pickle.load(f)
            
            # إعادة بناء العنصر
            return CacheItem(
                key=key,
                value=item_dict['value'],
                created_at=datetime.fromisoformat(item_dict['created_at']),
                expires_at=datetime.fromisoformat(item_dict['expires_at']) 
                if item_dict['expires_at'] else None,
                hits=item_dict['hits'],
                last_accessed=datetime.fromisoformat(item_dict['last_accessed']),
                metadata=item_dict['metadata']
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الملف المؤقت: {e}")
            return None
    
    async def _delete_file(self, key: str):
        """حذف ملف التخزين المؤقت"""
        try:
            from pathlib import Path
            
            safe_key = self._make_filename_safe(key)
            filepath = Path(self.cache_dir) / f"{safe_key}.cache"
            
            if filepath.exists():
                filepath.unlink()
                
        except Exception as e:
            logger.error(f"❌ خطأ في حذف الملف المؤقت: {e}")
    
    async def _file_exists(self, key: str) -> bool:
        """التحقق من وجود ملف"""
        try:
            from pathlib import Path
            
            safe_key = self._make_filename_safe(key)
            filepath = Path(self.cache_dir) / f"{safe_key}.cache"
            
            return filepath.exists()
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الملف: {e}")
            return False
    
    async def _clear_files(self, prefix: str = None) -> int:
        """مسح ملفات التخزين المؤقت"""
        try:
            from pathlib import Path
            import os
            
            cache_path = Path(self.cache_dir)
            count = 0
            
            for filepath in cache_path.glob("*.cache"):
                filename = filepath.stem
                
                if prefix and not filename.startswith(prefix):
                    continue
                
                filepath.unlink()
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"❌ خطأ في مسح الملفات: {e}")
            return 0
    
    # === دعم Redis ===
    
    async def _save_to_redis(self, key: str, item: CacheItem):
        """حفظ العنصر في Redis"""
        try:
            import pickle
            
            item_dict = {
                'value': item.value,
                'created_at': item.created_at.isoformat(),
                'expires_at': item.expires_at.isoformat() if item.expires_at else None,
                'hits': item.hits,
                'last_accessed': item.last_accessed.isoformat(),
                'metadata': item.metadata
            }
            
            serialized = pickle.dumps(item_dict)
            ttl = item.ttl
            
            if ttl and ttl > 0:
                self.redis_client.setex(key, int(ttl), serialized)
            else:
                self.redis_client.set(key, serialized)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ Redis: {e}")
    
    async def _load_from_redis(self, key: str) -> Optional[CacheItem]:
        """تحميل العنصر من Redis"""
        try:
            import pickle
            
            serialized = self.redis_client.get(key)
            if not serialized:
                return None
            
            item_dict = pickle.loads(serialized)
            
            # إعادة بناء العنصر
            return CacheItem(
                key=key,
                value=item_dict['value'],
                created_at=datetime.fromisoformat(item_dict['created_at']),
                expires_at=datetime.fromisoformat(item_dict['expires_at']) 
                if item_dict['expires_at'] else None,
                hits=item_dict['hits'],
                last_accessed=datetime.fromisoformat(item_dict['last_accessed']),
                metadata=item_dict['metadata']
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل Redis: {e}")
            return None
    
    async def _delete_redis(self, key: str):
        """حذف من Redis"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"❌ خطأ في حذف Redis: {e}")
    
    async def _redis_exists(self, key: str) -> bool:
        """التحقق من وجود عنصر في Redis"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من Redis: {e}")
            return False
    
    async def _clear_redis(self, prefix: str = None) -> int:
        """مسح Redis"""
        try:
            if prefix:
                keys = self.redis_client.keys(f"{prefix}*")
                if keys:
                    self.redis_client.delete(*keys)
                    return len(keys)
                return 0
            else:
                self.redis_client.flushdb()
                # لا يمكن معرفة العدد في Redis بدون SCAN
                return -1  # تعني الكل
                
        except Exception as e:
            logger.error(f"❌ خطأ في مسح Redis: {e}")
            return 0
    
    # === وظائف مساعدة ===
    
    def _make_filename_safe(self, key: str) -> str:
        """إنشاء اسم ملف آمن من المفتاح"""
        import hashlib
        import re
        
        # إزالة الأحرف غير الآمنة
        safe_key = re.sub(r'[^\w\-_]', '_', key)
        
        # إذا كان طويلاً جدًا، استخدم hash
        if len(safe_key) > 100:
            safe_key = hashlib.md5(key.encode()).hexdigest()
        
        return safe_key
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """الحصول على استخدام الذاكرة"""
        try:
            import sys
            
            total_size = 0
            
            if self.cache_type == CacheType.MEMORY:
                for item in self.memory_cache.values():
                    total_size += sys.getsizeof(item.value)
            
            return {
                'items': len(self.memory_cache),
                'estimated_size_mb': total_size / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في حساب استخدام الذاكرة: {e}")
            return {'items': 0, 'estimated_size_mb': 0}
    
    async def close(self):
        """إغلاق مدير التخزين المؤقت"""
        try:
            # إلغاء مهمة التنظيف
            if hasattr(self, 'cleanup_task'):
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # إغلاق اتصال Redis
            if hasattr(self, 'redis_client'):
                self.redis_client.close()
            
            logger.info("🔒 تم إغلاق مدير التخزين المؤقت")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إغلاق مدير التخزين المؤقت: {e}")
