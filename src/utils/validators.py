"""
✅ Validators - مدققات صحة البيانات
"""

import re
import ipaddress
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

def is_valid_url(url: str, require_https: bool = False) -> bool:
    """التحقق من صحة الرابط"""
    try:
        result = urlparse(url)
        
        # يجب أن يحتوي على المخطط والنطاق
        if not all([result.scheme, result.netloc]):
            return False
        
        # إذا طلبنا HTTPS فقط
        if require_https and result.scheme != 'https':
            return False
        
        # التحقق من النطاق
        if '.' not in result.netloc:
            return False
        
        return True
        
    except:
        return False

def is_valid_email(email: str) -> bool:
    """التحقق من صحة البريد الإلكتروني"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str, country_code: str = '') -> bool:
    """التحقق من صحة رقم الهاتف"""
    # تنظيف الرقم
    phone = re.sub(r'[^\d+]', '', phone)
    
    if not phone:
        return False
    
    # إضافة رمز الدولة إذا لم يكن موجودًا
    if country_code and not phone.startswith('+'):
        phone = f"+{country_code}{phone.lstrip('0')}"
    
    # التحقق من التنسيق العام
    pattern = r'^\+?[1-9]\d{7,14}$'
    return bool(re.match(pattern, phone))

def is_valid_ip(ip: str) -> bool:
    """التحقق من صحة عنوان IP"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_valid_domain(domain: str) -> bool:
    """التحقق من صحة النطاق"""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

def is_valid_date(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """التحقق من صحة التاريخ"""
    from datetime import datetime
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def is_valid_time(time_str: str, format: str = '%H:%M') -> bool:
    """التحقق من صحة الوقت"""
    from datetime import datetime
    try:
        datetime.strptime(time_str, format)
        return True
    except ValueError:
        return False

def is_valid_datetime(datetime_str: str, format: str = '%Y-%m-%d %H:%M:%S') -> bool:
    """التحقق من صحة التاريخ والوقت"""
    from datetime import datetime
    try:
        datetime.strptime(datetime_str, format)
        return True
    except ValueError:
        return False

def is_valid_json(data: str) -> bool:
    """التحقق مما إذا كان النص JSON صالح"""
    import json
    try:
        json.loads(data)
        return True
    except json.JSONDecodeError:
        return False

def is_valid_xml(xml_str: str) -> bool:
    """التحقق مما إذا كان النص XML صالح"""
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(xml_str)
        return True
    except ET.ParseError:
        return False

def is_valid_csv_line(line: str, expected_columns: int = None) -> bool:
    """التحقق من صحة سطر CSV"""
    import csv
    from io import StringIO
    
    try:
        reader = csv.reader(StringIO(line))
        row = next(reader)
        
        if expected_columns and len(row) != expected_columns:
            return False
        
        return True
    except:
        return False

def is_valid_password(password: str, min_length: int = 8) -> Tuple[bool, List[str]]:
    """التحقق من قوة كلمة المرور"""
    errors = []
    
    if len(password) < min_length:
        errors.append(f"يجب أن تحتوي على {min_length} أحرف على الأقل")
    
    if not re.search(r'[A-Z]', password):
        errors.append("يجب أن تحتوي على حرف كبير واحد على الأقل")
    
    if not re.search(r'[a-z]', password):
        errors.append("يجب أن تحتوي على حرف صغير واحد على الأقل")
    
    if not re.search(r'\d', password):
        errors.append("يجب أن تحتوي على رقم واحد على الأقل")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("يجب أن تحتوي على رمز خاص واحد على الأقل")
    
    return len(errors) == 0, errors

def is_valid_username(username: str, min_length: int = 3, max_length: int = 20) -> Tuple[bool, List[str]]:
    """التحقق من صحة اسم المستخدم"""
    errors = []
    
    if len(username) < min_length:
        errors.append(f"يجب أن يكون {min_length} أحرف على الأقل")
    
    if len(username) > max_length:
        errors.append(f"يجب ألا يتجاوز {max_length} أحرف")
    
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        errors.append("يجب أن يحتوي على أحرف وأرقام و . _ - فقط")
    
    if re.match(r'^\d', username):
        errors.append("يجب ألا يبدأ برقم")
    
    return len(errors) == 0, errors

def is_valid_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """التحقق من امتداد الملف المسموح"""
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1]
    return ext in allowed_extensions

def is_valid_file_size(filepath: str, max_size_mb: float) -> bool:
    """التحقق من حجم الملف"""
    import os
    try:
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb <= max_size_mb
    except:
        return False

def is_valid_whatsapp_link(link: str) -> bool:
    """التحقق من صحة رابط واتساب"""
    whatsapp_patterns = [
        r'^https?://chat\.whatsapp\.com/[a-zA-Z0-9]+$',
        r'^https?://wa\.me/\d+$',
        r'^https?://whatsapp\.com/dl/[a-zA-Z0-9]+$'
    ]
    
    for pattern in whatsapp_patterns:
        if re.match(pattern, link, re.IGNORECASE):
            return True
    
    return False

def is_valid_telegram_link(link: str) -> bool:
    """التحقق من صحة رابط تلغرام"""
    telegram_patterns = [
        r'^https?://t\.me/[a-zA-Z0-9_]+$',
        r'^https?://telegram\.me/[a-zA-Z0-9_]+$'
    ]
    
    for pattern in telegram_patterns:
        if re.match(pattern, link, re.IGNORECASE):
            return True
    
    return False

def is_valid_youtube_link(link: str) -> bool:
    """التحقق من صحة رابط يوتيوب"""
    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+',
        r'^https?://youtu\.be/[a-zA-Z0-9_-]+'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, link, re.IGNORECASE):
            return True
    
    return False

def validate_required_fields(data: Dict, required_fields: List[str]) -> Tuple[bool, List[str]]:
    """التحقق من الحقول المطلوبة"""
    missing = []
    
    for field in required_fields:
        if field not in data or data[field] in [None, ""]:
            missing.append(field)
    
    return len(missing) == 0, missing

def validate_numeric_range(value: Union[int, float], min_val: float = None, 
                          max_val: float = None) -> Tuple[bool, str]:
    """التحقق من النطاق الرقمي"""
    if min_val is not None and value < min_val:
        return False, f"يجب أن يكون {min_val} على الأقل"
    
    if max_val is not None and value > max_val:
        return False, f"يجب ألا يتجاوز {max_val}"
    
    return True, ""

def validate_string_length(text: str, min_len: int = None, 
                          max_len: int = None) -> Tuple[bool, str]:
    """التحقق من طول النص"""
    length = len(text)
    
    if min_len is not None and length < min_len:
        return False, f"يجب أن يكون {min_len} أحرف على الأقل"
    
    if max_len is not None and length > max_len:
        return False, f"يجب ألا يتجاوز {max_len} أحرف"
    
    return True, ""

def validate_list_items(items: List, allowed_values: List = None, 
                       min_items: int = None, max_items: int = None) -> Tuple[bool, str]:
    """التحقق من عناصر القائمة"""
    if min_items is not None and len(items) < min_items:
        return False, f"يجب أن تحتوي على {min_items} عنصر على الأقل"
    
    if max_items is not None and len(items) > max_items:
        return False, f"يجب ألا تحتوي على أكثر من {max_items} عنصر"
    
    if allowed_values is not None:
        for item in items:
            if item not in allowed_values:
                return False, f"القيمة '{item}' غير مسموحة"
    
    return True, ""

def validate_cron_expression(cron: str) -> bool:
    """التحقق من صحة تعبير cron"""
    pattern = r'^(\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])) (\*|([0-9]|1[0-9]|2[0-3])|\*\/([0-9]|1[0-9]|2[0-3])) (\*|([1-9]|1[0-9]|2[0-9]|3[0-1])|\*\/([1-9]|1[0-9]|2[0-9]|3[0-1])) (\*|([1-9]|1[0-2])|\*\/([1-9]|1[0-2])) (\*|([0-6])|\*\/([0-6]))$'
    return bool(re.match(pattern, cron))

def validate_hex_color(color: str) -> bool:
    """التحقق من صحة لون hex"""
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, color))

def validate_base64(data: str) -> bool:
    """التحقق من صحة بيانات base64"""
    import base64
    try:
        if isinstance(data, str):
            data = data.encode('utf-8')
        base64.b64decode(data, validate=True)
        return True
    except:
        return False

def validate_mac_address(mac: str) -> bool:
    """التحقق من صحة عنوان MAC"""
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))

def validate_uuid(uuid_str: str) -> bool:
    """التحقق من صحة UUID"""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str.lower()))
