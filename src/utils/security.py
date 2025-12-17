"""
🔐 Security Manager - مدير الأمان والتشفير
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class SecurityManager:
    """مدير الأمان والتشفير"""
    
    def __init__(self, encryption_key: str = None):
        """تهيئة مدير الأمان"""
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.fernet = self._init_fernet()
        self.tokens = {}  # تخزين مؤقت للرموز
        self.blacklisted_tokens = set()
        
        logger.info("🔐 تم تهيئة مدير الأمان")
    
    def _generate_encryption_key(self) -> str:
        """إنشاء مفتاح تشفير عشوائي"""
        return secrets.token_urlsafe(32)
    
    def _init_fernet(self) -> Optional[Fernet]:
        """تهيئة Fernet للتشفير"""
        try:
            # تحويل المفتاح إلى تنسيق Fernet
            key = base64.urlsafe_b64encode(
                hashlib.sha256(self.encryption_key.encode()).digest()
            )
            return Fernet(key)
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة Fernet: {e}")
            return None
    
    def encrypt(self, data: Union[str, bytes]) -> Optional[str]:
        """تشفير البيانات"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            if self.fernet:
                encrypted = self.fernet.encrypt(data)
                return base64.urlsafe_b64encode(encrypted).decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"❌ خطأ في التشفير: {e}")
            return None
    
    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """فك تشفير البيانات"""
        try:
            if not encrypted_data:
                return None
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
            
            if self.fernet:
                decrypted = self.fernet.decrypt(encrypted_bytes)
                return decrypted.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"❌ خطأ في فك التشفير: {e}")
            return None
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """تجزئة كلمة المرور"""
        try:
            if salt is None:
                salt = secrets.token_hex(16)
            
            # استخدام PBKDF2 مع SHA256
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode('utf-8'),
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
            return key.decode('utf-8'), salt
            
        except Exception as e:
            logger.error(f"❌ خطأ في تجزئة كلمة المرور: {e}")
            return "", ""
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """التحقق من كلمة المرور"""
        try:
            new_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(new_hash, hashed_password)
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من كلمة المرور: {e}")
            return False
    
    def generate_token(self, user_id: str, expires_in: int = 3600) -> Optional[str]:
        """إنشاء رمز وصول"""
        try:
            token_id = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(seconds=expires_in)
            
            token_data = {
                'token_id': token_id,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': expiry.isoformat()
            }
            
            # تخزين الرمز
            self.tokens[token_id] = token_data
            
            # تشفير البيانات
            encrypted_data = self.encrypt(str(token_data))
            if encrypted_data:
                return f"{token_id}.{encrypted_data}"
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الرمز: {e}")
            return None
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """التحقق من صحة الرمز"""
        try:
            if not token or '.' not in token:
                return False, None
            
            parts = token.split('.')
            if len(parts) != 2:
                return False, None
            
            token_id, encrypted_data = parts
            
            # التحقق من القائمة السوداء
            if token_id in self.blacklisted_tokens:
                return False, None
            
            # فك التشفير
            decrypted_data = self.decrypt(encrypted_data)
            if not decrypted_data:
                return False, None
            
            # البحث عن الرمز
            if token_id not in self.tokens:
                return False, None
            
            token_data = self.tokens[token_id]
            
            # التحقق من الصلاحية
            expiry = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() > expiry:
                # حذف الرمز المنتهي
                del self.tokens[token_id]
                return False, None
            
            return True, token_data
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الرمز: {e}")
            return False, None
    
    def revoke_token(self, token_id: str) -> bool:
        """إبطال الرمز"""
        try:
            if token_id in self.tokens:
                del self.tokens[token_id]
                self.blacklisted_tokens.add(token_id)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في إبطال الرمز: {e}")
            return False
    
    def generate_2fa_code(self, length: int = 6) -> str:
        """إنشاء رمز المصادقة الثنائية"""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    def generate_csrf_token(self) -> str:
        """إنشاء رمز CSRF"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """التحقق من رمز CSRF"""
        try:
            # في الإنتاج، يجب تخزين session_token في جلسة المستخدم
            expected_token = self._generate_csrf_from_session(session_token)
            return hmac.compare_digest(token, expected_token)
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من CSRF: {e}")
            return False
    
    def _generate_csrf_from_session(self, session_token: str) -> str:
        """إنشاء رمز CSRF من رمز الجلسة"""
        secret = self.encryption_key.encode('utf-8')
        message = session_token.encode('utf-8')
        
        h = hmac.new(secret, message, hashlib.sha256)
        return h.hexdigest()
    
    def sanitize_input(self, input_str: str) -> str:
        """تعقيم إدخال المستخدم"""
        import html
        
        # إزالة HTML/JavaScript
        sanitized = html.escape(input_str)
        
        # إزالة الأحرف الخطرة
        dangerous = ['<script>', '</script>', 'javascript:', 'onload=', 'onerror=']
        for dangerous_str in dangerous:
            sanitized = sanitized.replace(dangerous_str, '')
        
        # إزالة المسافات الزائدة
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def validate_file_upload(self, filename: str, content_type: str, 
                           max_size: int, allowed_types: List[str]) -> Tuple[bool, str]:
        """التحقق من صحة ملف الرفع"""
        try:
            # التحقق من الامتداد
            ext = filename.lower().split('.')[-1]
            if ext not in allowed_types:
                return False, f"نوع الملف غير مسموح: {ext}"
            
            # التحقق من نوع المحتوى
            if content_type not in self._get_mime_types(ext):
                return False, f"نوع المحتوى غير صالح: {content_type}"
            
            # التحقق من الحجم (يتم التحقق لاحقًا)
            return True, ""
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الملف: {e}")
            return False, str(e)
    
    def _get_mime_types(self, extension: str) -> List[str]:
        """الحصول على أنواع MIME للامتداد"""
        mime_map = {
            'jpg': ['image/jpeg', 'image/jpg'],
            'jpeg': ['image/jpeg', 'image/jpg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'pdf': ['application/pdf'],
            'txt': ['text/plain'],
            'csv': ['text/csv'],
            'json': ['application/json'],
            'mp4': ['video/mp4'],
            'mp3': ['audio/mpeg'],
        }
        return mime_map.get(extension, [])
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """إنشاء اسم ملف آمن"""
        import uuid
        
        # استخراج الامتداد
        ext = original_filename.lower().split('.')[-1]
        
        # إنشاء اسم فريد
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"file_{timestamp}_{unique_id}.{ext}"
    
    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """فحص قوة كلمة المرور"""
        score = 0
        feedback = []
        
        # الطول
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            feedback.append("يجب أن تكون 8 أحرف على الأقل")
        
        # أحرف كبيرة
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("أضف حرفًا كبيرًا")
        
        # أحرف صغيرة
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("أضف حرفًا صغيرًا")
        
        # أرقام
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("أضف رقمًا")
        
        # رموز خاصة
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("أضف رمزًا خاصًا")
        
        # تحديد المستوى
        if score >= 5:
            level = "قوي جدًا"
        elif score >= 4:
            level = "قوي"
        elif score >= 3:
            level = "متوسط"
        else:
            level = "ضعيف"
        
        return {
            'score': score,
            'max_score': 6,
            'level': level,
            'feedback': feedback,
            'is_strong': score >= 4
        }
    
    def encrypt_file(self, input_path: str, output_path: str = None) -> Optional[str]:
        """تشفير ملف"""
        try:
            if output_path is None:
                output_path = input_path + '.enc'
            
            with open(input_path, 'rb') as f:
                data = f.read()
            
            if self.fernet:
                encrypted = self.fernet.encrypt(data)
                
                with open(output_path, 'wb') as f:
                    f.write(encrypted)
                
                return output_path
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشفير الملف: {e}")
            return None
    
    def decrypt_file(self, input_path: str, output_path: str = None) -> Optional[str]:
        """فك تشفير ملف"""
        try:
            if output_path is None:
                if input_path.endswith('.enc'):
                    output_path = input_path[:-4]
                else:
                    output_path = input_path + '.dec'
            
            with open(input_path, 'rb') as f:
                encrypted = f.read()
            
            if self.fernet:
                decrypted = self.fernet.decrypt(encrypted)
                
                with open(output_path, 'wb') as f:
                    f.write(decrypted)
                
                return output_path
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في فك تشفير الملف: {e}")
            return None
    
    def cleanup_expired_tokens(self):
        """تنظيف الرموز المنتهية"""
        try:
            expired_tokens = []
            
            for token_id, token_data in self.tokens.items():
                expiry = datetime.fromisoformat(token_data['expires_at'])
                if datetime.now() > expiry:
                    expired_tokens.append(token_id)
            
            for token_id in expired_tokens:
                del self.tokens[token_id]
            
            if expired_tokens:
                logger.info(f"🧹 تم تنظيف {len(expired_tokens)} رمز منتهي")
                
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف الرموز: {e}")
    
    def get_security_report(self) -> Dict[str, Any]:
        """الحصول على تقرير الأمان"""
        total_tokens = len(self.tokens)
        blacklisted = len(self.blacklisted_tokens)
        
        # حساب الرموز المنتهية
        expired = 0
        active = 0
        
        for token_data in self.tokens.values():
            expiry = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() > expiry:
                expired += 1
            else:
                active += 1
        
        return {
            'encryption_key_set': bool(self.encryption_key),
            'fernet_initialized': bool(self.fernet),
            'total_tokens': total_tokens,
            'active_tokens': active,
            'expired_tokens': expired,
            'blacklisted_tokens': blacklisted,
            'security_level': self._calculate_security_level()
        }
    
    def _calculate_security_level(self) -> str:
        """حساب مستوى الأمان"""
        factors = 0
        
        if self.encryption_key and len(self.encryption_key) >= 32:
            factors += 1
        
        if self.fernet:
            factors += 1
        
        if len(self.blacklisted_tokens) > 0:
            factors += 1
        
        if factors == 3:
            return "عالية"
        elif factors == 2:
            return "متوسطة"
        else:
            return "منخفضة"
