"""
🎨 Formatters - مُنسقات البيانات والعروض
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """تنسيق التاريخ والوقت"""
    return dt.strftime(format_str)

def format_date(date_obj: Union[datetime, str], 
                input_format: str = '%Y-%m-%d',
                output_format: str = '%Y-%m-%d') -> str:
    """تنسيق التاريخ"""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, input_format)
    
    return date_obj.strftime(output_format)

def format_time(time_obj: Union[datetime, str], 
                input_format: str = '%H:%M:%S',
                output_format: str = '%H:%M') -> str:
    """تنسيق الوقت"""
    if isinstance(time_obj, str):
        time_obj = datetime.strptime(time_obj, input_format)
    
    return time_obj.strftime(output_format)

def format_duration(seconds: float, precision: int = 0) -> str:
    """تنسيق المدة الزمنية"""
    if seconds < 60:
        return f"{seconds:.{precision}f} ثانية"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.{precision}f} دقيقة"
    
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.{precision}f} ساعة"
    
    days = hours / 24
    if days < 7:
        return f"{days:.{precision}f} يوم"
    
    weeks = days / 7
    if weeks < 4:
        return f"{weeks:.{precision}f} أسبوع"
    
    months = days / 30
    if months < 12:
        return f"{months:.{precision}f} شهر"
    
    years = days / 365
    return f"{years:.{precision}f} سنة"

def format_relative_time(dt: datetime) -> str:
    """تنسيق الوقت النسبي (منذ... أو بعد... )"""
    now = datetime.now()
    diff = now - dt if now > dt else dt - now
    is_past = now > dt
    
    if diff.total_seconds() < 60:
        return "الآن"
    
    if diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} دقيقة {'مضت' if is_past else 'قادمة'}"
    
    if diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} ساعة {'مضت' if is_past else 'قادمة'}"
    
    if diff.total_seconds() < 604800:
        days = int(diff.total_seconds() / 86400)
        return f"{days} يوم {'مضت' if is_past else 'قادمة'}"
    
    if diff.total_seconds() < 2592000:
        weeks = int(diff.total_seconds() / 604800)
        return f"{weeks} أسبوع {'مضت' if is_past else 'قادمة'}"
    
    if diff.total_seconds() < 31536000:
        months = int(diff.total_seconds() / 2592000)
        return f"{months} شهر {'مضت' if is_past else 'قادمة'}"
    
    years = int(diff.total_seconds() / 31536000)
    return f"{years} سنة {'مضت' if is_past else 'قادمة'}"

def format_number(number: Union[int, float], 
                  decimal_places: int = 2, 
                  use_comma: bool = True) -> str:
    """تنسيق الأرقام"""
    if isinstance(number, float):
        formatted = f"{number:,.{decimal_places}f}"
    else:
        formatted = f"{number:,}"
    
    if use_comma:
        return formatted.replace(",", "٬")  # فاصلة عربية
    return formatted

def format_percentage(value: float, total: float = 100, 
                      decimal_places: int = 1) -> str:
    """تنسيق النسبة المئوية"""
    if total == 0:
        percentage = 0
    else:
        percentage = (value / total) * 100
    
    return f"{percentage:.{decimal_places}f}%"

def format_currency(amount: float, currency: str = "ر.س", 
                   decimal_places: int = 2) -> str:
    """تنسيق العملة"""
    formatted = format_number(abs(amount), decimal_places)
    
    if amount < 0:
        return f"-{currency} {formatted}"
    return f"{currency} {formatted}"

def format_file_size(size_bytes: int, decimal_places: int = 2) -> str:
    """تنسيق حجم الملف"""
    if size_bytes < 1024:
        return f"{size_bytes} بايت"
    
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.{decimal_places}f} كيلوبايت"
    
    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.{decimal_places}f} ميجابايت"
    
    size_gb = size_mb / 1024
    if size_gb < 1024:
        return f"{size_gb:.{decimal_places}f} جيجابايت"
    
    size_tb = size_gb / 1024
    return f"{size_tb:.{decimal_places}f} تيرابايت"

def format_phone_number(phone: str, country_code: str = "+966") -> str:
    """تنسيق رقم الهاتف"""
    # إزالة كل شيء ما عدا الأرقام
    digits = ''.join(filter(str.isdigit, phone))
    
    if not digits:
        return phone
    
    # إضافة رمز الدولة إذا لم يكن موجودًا
    if not phone.startswith('+'):
        if digits.startswith('0'):
            digits = digits[1:]
        
        if len(digits) == 9:  # أرقام السعودية بدون الصفر
            return f"{country_code}{digits}"
    
    return phone

def format_json(data: Any, indent: int = 2, sort_keys: bool = False) -> str:
    """تنسيق JSON بشكل جميل"""
    return json.dumps(data, indent=indent, ensure_ascii=False, 
                      sort_keys=sort_keys)

def format_list(items: List[Any], separator: str = ", ", 
                last_separator: str = " و ") -> str:
    """تنسيق القائمة بشكل نصي"""
    if not items:
        return ""
    
    if len(items) == 1:
        return str(items[0])
    
    if len(items) == 2:
        return f"{items[0]}{last_separator}{items[1]}"
    
    all_but_last = separator.join(str(item) for item in items[:-1])
    return f"{all_but_last}{last_separator}{items[-1]}"

def format_progress_bar(percentage: float, width: int = 20, 
                       filled_char: str = "█", empty_char: str = "░") -> str:
    """تنسيق شريط التقدم"""
    filled_width = int(width * percentage / 100)
    empty_width = width - filled_width
    
    bar = filled_char * filled_width + empty_char * empty_width
    return f"[{bar}] {percentage:.1f}%"

def format_table(data: List[List[Any]], headers: List[str] = None) -> str:
    """تنسيق الجدول"""
    if not data:
        return ""
    
    # حساب أقصى عرض لكل عمود
    if headers:
        all_rows = [headers] + data
    else:
        all_rows = data
    
    col_widths = []
    for i in range(len(all_rows[0])):
        max_width = max(len(str(row[i])) for row in all_rows)
        col_widths.append(max_width)
    
    # بناء الجدول
    lines = []
    
    if headers:
        # خط الرؤوس
        header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
        lines.append(header_line)
        lines.append("-+-".join("-" * w for w in col_widths))
    
    # خطوط البيانات
    for row in data:
        line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        lines.append(line)
    
    return "\n".join(lines)

def format_markdown_table(data: List[List[Any]], headers: List[str] = None) -> str:
    """تنسيق جدول Markdown"""
    if not data:
        return ""
    
    if not headers:
        headers = [f"Column {i+1}" for i in range(len(data[0]))]
    
    # بناء الجدول
    lines = []
    
    # الرؤوس
    header_line = "| " + " | ".join(headers) + " |"
    lines.append(header_line)
    
    # الفاصل
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    lines.append(separator_line)
    
    # البيانات
    for row in data:
        row_line = "| " + " | ".join(str(cell) for cell in row) + " |"
        lines.append(row_line)
    
    return "\n".join(lines)

def format_boolean(value: bool, true_text: str = "نعم", 
                  false_text: str = "لا") -> str:
    """تنسيق القيم المنطقية"""
    return true_text if value else false_text

def format_enum(value: Any, enum_dict: Dict[Any, str]) -> str:
    """تنسيق القيم التعدادية"""
    return enum_dict.get(value, str(value))

def format_plural(count: int, singular: str, plural: str = None) -> str:
    """تنسيق صيغة الجمع"""
    if count == 1:
        return f"{count} {singular}"
    
    if plural is None:
        # محاولة إنشاء صيغة الجمع تلقائيًا للعربية
        if singular.endswith('ة'):
            plural = singular[:-1] + 'ات'
        elif singular.endswith('ي'):
            plural = singular + 'ون'
        else:
            plural = singular + 'ات'
    
    return f"{count} {plural}"

def format_time_range(start: datetime, end: datetime, 
                     format_str: str = '%H:%M') -> str:
    """تنسيق نطاق الوقت"""
    start_str = format_datetime(start, format_str)
    end_str = format_datetime(end, format_str)
    return f"{start_str} - {end_str}"

def format_date_range(start: datetime, end: datetime, 
                     format_str: str = '%Y-%m-%d') -> str:
    """تنسيق نطاق التاريخ"""
    start_str = format_datetime(start, format_str)
    end_str = format_datetime(end, format_str)
    
    if start.date() == end.date():
        return start_str
    
    return f"{start_str} إلى {end_str}"

def format_hyperlink(text: str, url: str) -> str:
    """تنسيق الارتباط التشعبي"""
    return f"[{text}]({url})"

def format_code_block(code: str, language: str = "") -> str:
    """تنسيق كتلة الكود"""
    return f"```{language}\n{code}\n```"

def format_quote(text: str, author: str = "") -> str:
    """تنسيق الاقتباس"""
    if author:
        return f"\"{text}\"\n— {author}"
    return f"\"{text}\""

def format_address(street: str = "", city: str = "", 
                  state: str = "", postal_code: str = "", 
                  country: str = "") -> str:
    """تنسيق العنوان"""
    parts = []
    
    if street:
        parts.append(street)
    
    if city:
        parts.append(city)
    
    if state:
        parts.append(state)
    
    if postal_code:
        parts.append(postal_code)
    
    if country:
        parts.append(country)
    
    return "، ".join(parts)

def format_coordinates(latitude: float, longitude: float, 
                      decimal_places: int = 6) -> str:
    """تنسيق الإحداثيات"""
    lat_dir = "شمال" if latitude >= 0 else "جنوب"
    lon_dir = "شرق" if longitude >= 0 else "غرب"
    
    lat_abs = abs(latitude)
    lon_abs = abs(longitude)
    
    return f"{lat_abs:.{decimal_places}f}° {lat_dir}، {lon_abs:.{decimal_places}f}° {lon_dir}"

def format_social_media_handle(platform: str, username: str) -> str:
    """تنسيق اسم مستخدم وسائل التواصل"""
    platforms = {
        'twitter': '@',
        'instagram': '@',
        'facebook': '',
        'telegram': '@',
        'whatsapp': '',
        'tiktok': '@',
        'youtube': '@'
    }
    
    prefix = platforms.get(platform.lower(), '@')
    return f"{prefix}{username}"

def format_rating(stars: float, max_stars: int = 5, 
                 star_char: str = "★", empty_char: str = "☆") -> str:
    """تنسيق التقييم"""
    full_stars = int(stars)
    half_star = stars - full_stars >= 0.5
    empty_stars = max_stars - full_stars - (1 if half_star else 0)
    
    result = star_char * full_stars
    
    if half_star:
        result += "½"
    
    result += empty_char * empty_stars
    
    return f"{result} ({stars:.1f}/{max_stars})"
