"""
🔧 WhatsApp Utilities - أدوات مساعدة
"""

import base64
import hashlib
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

def generate_session_id() -> str:
    """إنشاء معرف جلسة فريد"""
    timestamp = int(time.time())
    random_hash = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
    return f"session_{timestamp}_{random_hash}"

def validate_phone_number(phone: str) -> bool:
    """التحقق من صحة رقم الهاتف"""
    # نموذج بسيط للتحقق - يمكن تحسينه
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, phone.replace(" ", "")))

def extract_whatsapp_link_info(link: str) -> Dict[str, Any]:
    """استخراج معلومات من رابط واتساب"""
    try:
        parsed = urlparse(link)
        
        # لروابط المجموعات
        if 'chat.whatsapp.com' in parsed.netloc:
            path = parsed.path.strip('/')
            query_params = parse_qs(parsed.query)
            
            return {
                'type': 'group',
                'invite_code': path,
                'params': query_params,
                'full_link': link
            }
        
        # لروابط الاتصال
        elif 'wa.me' in parsed.netloc:
            path = parsed.path.strip('/')
            
            return {
                'type': 'contact',
                'phone_number': path,
                'full_link': link
            }
        
        else:
            return {'type': 'unknown', 'full_link': link}
            
    except Exception:
        return {'type': 'unknown', 'full_link': link}

def save_session_to_file(session_data: Dict[str, Any], file_path: str) -> bool:
    """حفظ بيانات الجلسة إلى ملف"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception:
        return False

def load_session_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """تحميل بيانات الجلسة من ملف"""
    try:
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception:
        return None

def encrypt_data(data: str, key: str) -> str:
    """تشفير البيانات"""
    try:
        # تشفير بسيط (يفضل استخدام مكتبة تشفير أقوى في الإنتاج)
        from cryptography.fernet import Fernet
        
        if len(key) < 32:
            key = key.ljust(32, '0')[:32]
        
        fernet_key = base64.urlsafe_b64encode(key.encode())
        fernet = Fernet(fernet_key)
        
        encrypted = fernet.encrypt(data.encode())
        return encrypted.decode()
        
    except ImportError:
        # تشفير بدائي إذا لم تكن مكتبة cryptography مثبتة
        import hashlib
        from base64 import b64encode
        
        hash_object = hashlib.sha256(key.encode() + data.encode())
        return b64encode(hash_object.digest()).decode()
    except Exception:
        return data

def decrypt_data(encrypted_data: str, key: str) -> str:
    """فك تشفير البيانات"""
    try:
        from cryptography.fernet import Fernet
        
        if len(key) < 32:
            key = key.ljust(32, '0')[:32]
        
        fernet_key = base64.urlsafe_b64encode(key.encode())
        fernet = Fernet(fernet_key)
        
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
        
    except ImportError:
        # لا يمكن فك التشفير البدائي
        return encrypted_data
    except Exception:
        return encrypted_data

def format_timestamp(timestamp: str) -> str:
    """تنسيق الطابع الزمني"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

def calculate_interval_delay(base_delay: int, jitter: int = 0) -> int:
    """حساب تأخير مع تباين عشوائي"""
    import random
    
    if jitter > 0:
        return base_delay + random.randint(0, jitter)
    return base_delay

def safe_filename(filename: str) -> str:
    """إنشاء اسم ملف آمن"""
    # إزالة الأحرف غير الآمنة
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = safe_name.strip('. ')
    
    # تحديد الطول
    if len(safe_name) > 200:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:200-len(ext)] + ext
    
    return safe_name

def bytes_to_human_readable(size_bytes: int) -> str:
    """تحويل البايتات إلى صيغة مقروءة"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
