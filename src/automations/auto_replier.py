"""
💬 AutoReplier - نظام الرد التلقائي على الرسائل
"""

import asyncio
import logging
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Pattern
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ReplyType(Enum):
    """أنواع الردود"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    CONTACT = "contact"
    BUTTONS = "buttons"
    LIST = "list"

class TriggerType(Enum):
    """أنواع المحفزات"""
    KEYWORD = "keyword"
    REGEX = "regex"
    CONTAINS = "contains"
    EXACT = "exact"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"

@dataclass
class ReplyRule:
    """قاعدة رد"""
    id: str
    name: str
    trigger_type: TriggerType
    trigger_value: str
    reply_type: ReplyType
    reply_content: Any
    is_active: bool = True
    priority: int = 0
    cooldown: int = 0  # ثانية بين الردود للمستخدم نفسه
    match_count: int = 0
    last_used: Optional[datetime] = None
    
    def matches(self, message: str) -> bool:
        """التحقق مما إذا كانت الرسالة تطابق القاعدة"""
        try:
            message_lower = message.lower()
            trigger_lower = self.trigger_value.lower()
            
            if self.trigger_type == TriggerType.KEYWORD:
                return any(keyword.strip() in message_lower 
                          for keyword in trigger_lower.split(','))
            
            elif self.trigger_type == TriggerType.REGEX:
                return bool(re.search(self.trigger_value, message, re.IGNORECASE))
            
            elif self.trigger_type == TriggerType.CONTAINS:
                return trigger_lower in message_lower
            
            elif self.trigger_type == TriggerType.EXACT:
                return message_lower == trigger_lower
            
            elif self.trigger_type == TriggerType.STARTS_WITH:
                return message_lower.startswith(trigger_lower)
            
            elif self.trigger_type == TriggerType.ENDS_WITH:
                return message_lower.endswith(trigger_lower)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في مطابقة القاعدة: {e}")
            return False

class AutoReplier:
    """نظام الرد التلقائي"""
    
    def __init__(self, database_handler=None):
        """تهيئة نظام الرد التلقائي"""
        self.db = database_handler
        self.is_replying = False
        self.reply_rules: Dict[str, ReplyRule] = {}
        self.user_cooldowns: Dict[str, datetime] = {}  # تبريد للمستخدمين
        self.default_replies = []
        self.learning_enabled = False
        self.learned_responses = {}
        
        # تحميل القواعد الافتراضية
        self._load_default_rules()
        
        logger.info("💬 تم تهيئة نظام الرد التلقائي")
    
    def _load_default_rules(self):
        """تحميل قواعد الرد الافتراضية"""
        default_rules = [
            ReplyRule(
                id="welcome",
                name="رسالة ترحيب",
                trigger_type=TriggerType.CONTAINS,
                trigger_value="مرحبا,اهلا,السلام عليكم",
                reply_type=ReplyType.TEXT,
                reply_content="مرحباً بك! 👋\nكيف يمكنني مساعدتك؟",
                priority=10
            ),
            ReplyRule(
                id="help",
                name="طلب مساعدة",
                trigger_type=TriggerType.CONTAINS,
                trigger_value="مساعدة,مساعدة,help,مساعده",
                reply_type=ReplyType.TEXT,
                reply_content="يمكنني مساعدتك في:\n✅ تجميع الروابط\n✅ الانظمام للمجموعات\n✅ النشر التلقائي\n\nما الذي تحتاج إليه؟",
                priority=10
            ),
            ReplyRule(
                id="thank_you",
                name="شكر",
                trigger_type=TriggerType.CONTAINS,
                trigger_value="شكرا,مشكور,جزاك الله خيرا,thanks",
                reply_type=ReplyType.TEXT,
                reply_content="العفو! 😊\nسعيد لأنني استطعت المساعدة.",
                priority=5
            ),
            ReplyRule(
                id="bot_info",
                name="معلومات البوت",
                trigger_type=TriggerType.CONTAINS,
                trigger_value="من انت,ما هو البوت,معلومات,info,about",
                reply_type=ReplyType.TEXT,
                reply_content="أنا بوت واتساب متطور 🤖\nأقوم بتجميع الروابط والنشر التلقائي والانظمام للمجموعات.",
                priority=8
            )
        ]
        
        for rule in default_rules:
            self.reply_rules[rule.id] = rule
        
        logger.info(f"📋 تم تحميل {len(default_rules)} قاعدة رد افتراضية")
    
    async def set_reply_rules(self, rules_data: List[Dict[str, Any]]) -> bool:
        """تعيين قواعد الرد"""
        try:
            logger.info(f"🔄 تعيين {len(rules_data)} قاعدة رد جديدة")
            
            for rule_data in rules_data:
                try:
                    rule = ReplyRule(
                        id=rule_data.get('id', f"rule_{datetime.now().timestamp()}"),
                        name=rule_data.get('name', 'قاعدة بدون اسم'),
                        trigger_type=TriggerType(rule_data.get('trigger_type', 'keyword')),
                        trigger_value=rule_data.get('trigger_value', ''),
                        reply_type=ReplyType(rule_data.get('reply_type', 'text')),
                        reply_content=rule_data.get('reply_content', ''),
                        is_active=rule_data.get('is_active', True),
                        priority=rule_data.get('priority', 0),
                        cooldown=rule_data.get('cooldown', 0)
                    )
                    
                    self.reply_rules[rule.id] = rule
                    
                    # حفظ في قاعدة البيانات
                    if self.db:
                        await self._save_rule_to_db(rule)
                    
                    logger.debug(f"✅ تم إضافة قاعدة: {rule.name}")
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في معالجة قاعدة: {e}")
                    continue
            
            logger.info(f"✅ تم تعيين {len(rules_data)} قاعدة رد")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تعيين قواعد الرد: {e}")
            return False
    
    async def _save_rule_to_db(self, rule: ReplyRule):
        """حفظ قاعدة في قاعدة البيانات"""
        try:
            # هذه دالة افتراضية - تحتاج للتطبيق الفعلي
            # ستحفظ القاعدة في جدول مخصص للردود
            pass
            
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ القاعدة: {e}")
    
    async def should_reply(self, message_data: Dict[str, Any]) -> Tuple[bool, Optional[ReplyRule]]:
        """التحقق مما إذا يجب الرد على الرسالة"""
        try:
            message = message_data.get('body', '').strip()
            sender = message_data.get('sender', '')
            
            if not message or not sender:
                return False, None
            
            # التحقق من تبريد المستخدم
            if sender in self.user_cooldowns:
                last_reply = self.user_cooldowns[sender]
                time_diff = (datetime.now() - last_reply).total_seconds()
                
                # البحث عن القاعدة المناسبة للمستخدم
                matching_rule = None
                for rule in self.reply_rules.values():
                    if rule.is_active and rule.matches(message):
                        if rule.cooldown > 0 and time_diff < rule.cooldown:
                            continue
                        matching_rule = rule
                        break
                
                if matching_rule and matching_rule.cooldown > 0:
                    if time_diff < matching_rule.cooldown:
                        logger.debug(f"⏳ تبريد نشط للمستخدم {sender}")
                        return False, None
            else:
                # البحث عن القاعدة المناسبة
                matching_rule = None
                highest_priority = -1
                
                for rule in self.reply_rules.values():
                    if rule.is_active and rule.matches(message):
                        if rule.priority > highest_priority:
                            highest_priority = rule.priority
                            matching_rule = rule
            
            if matching_rule:
                # تحديث عداد الاستخدام
                matching_rule.match_count += 1
                matching_rule.last_used = datetime.now()
                
                # تحديث تبريد المستخدم
                if matching_rule.cooldown > 0:
                    self.user_cooldowns[sender] = datetime.now()
                
                logger.debug(f"✅ تطابق مع قاعدة: {matching_rule.name}")
                return True, matching_rule
            
            return False, None
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الرد: {e}")
            return False, None
    
    async def generate_reply(self, message_data: Dict[str, Any], rule: ReplyRule) -> Dict[str, Any]:
        """توليد رد"""
        try:
            reply_data = {
                'type': rule.reply_type.value,
                'content': rule.reply_content,
                'rule_id': rule.id,
                'rule_name': rule.name
            }
            
            # معالجة محتوى الرد حسب النوع
            if rule.reply_type == ReplyType.TEXT:
                # يمكن إضافة متغيرات ديناميكية
                sender_name = message_data.get('sender', 'صديقي')
                reply_data['content'] = rule.reply_content.replace('{name}', sender_name)
            
            elif rule.reply_type == ReplyType.IMAGE:
                # تأكد من وجود مسار الصورة
                reply_data['media_path'] = rule.reply_content
            
            elif rule.reply_type == ReplyType.VIDEO:
                reply_data['media_path'] = rule.reply_content
            
            elif rule.reply_type == ReplyType.DOCUMENT:
                reply_data['media_path'] = rule.reply_content
            
            elif rule.reply_type == ReplyType.CONTACT:
                reply_data['contact_info'] = rule.reply_content
            
            elif rule.reply_type == ReplyType.BUTTONS:
                reply_data['buttons'] = json.loads(rule.reply_content) if isinstance(rule.reply_content, str) else rule.reply_content
            
            elif rule.reply_type == ReplyType.LIST:
                reply_data['list_items'] = json.loads(rule.reply_content) if isinstance(rule.reply_content, str) else rule.reply_content
            
            logger.debug(f"🤖 تم توليد رد من نوع: {rule.reply_type.value}")
            return reply_data
            
        except Exception as e:
            logger.error(f"❌ خطأ في توليد الرد: {e}")
            return {'type': 'text', 'content': 'حدث خطأ في توليد الرد.'}
    
    async def start_auto_replying(self, message_handler) -> bool:
        """بدء الرد التلقائي"""
        try:
            if self.is_replying:
                logger.warning("⚠️ الرد التلقائي يعمل بالفعل")
                return False
            
            self.is_replying = True
            
            # بدء الاستماع للرسائل
            await message_handler.start_listening(
                callback=self._handle_incoming_message
            )
            
            logger.info("👂 بدء الرد التلقائي على الرسائل")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء الرد التلقائي: {e}")
            self.is_replying = False
            return False
    
    async def _handle_incoming_message(self, message: Dict[str, Any]):
        """معالجة الرسائل الواردة"""
        try:
            if not self.is_replying:
                return
            
            # التحقق مما إذا كانت الرسالة تحتاج إلى رد
            should_reply, rule = await self.should_reply(message)
            
            if should_reply and rule:
                # توليد الرد
                reply_data = await self.generate_reply(message, rule)
                
                # إرسال الرد
                if hasattr(self, 'client'):
                    await self._send_reply(message, reply_data)
                
                # تسجيل في قاعدة البيانات
                await self._log_reply(message, rule, reply_data)
                
                logger.info(f"💬 تم الرد على رسالة من: {message.get('sender')}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
    
    async def _send_reply(self, message: Dict[str, Any], reply_data: Dict[str, Any]):
        """إرسال الرد"""
        try:
            # هذه دالة افتراضية - تحتاج للتطبيق الفعلي حسب واجهة API
            # سترسل الرد باستخدام WhatsAppClient
            pass
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الرد: {e}")
    
    async def _log_reply(self, message: Dict[str, Any], rule: ReplyRule, reply_data: Dict[str, Any]):
        """تسجيل الرد في قاعدة البيانات"""
        try:
            if self.db:
                log_entry = {
                    'message_id': message.get('id'),
                    'sender': message.get('sender'),
                    'original_message': message.get('body', '')[:500],
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'reply_content': str(reply_data.get('content', ''))[:500],
                    'reply_type': rule.reply_type.value,
                    'timestamp': datetime.now().isoformat()
                }
                
                # حفظ في قاعدة البيانات
                await self.db.save_message({
                    'session_id': 'auto_replier',
                    'message_id': f"reply_{message.get('id', 'unknown')}",
                    'sender': 'bot',
                    'receiver': message.get('sender', 'unknown'),
                    'content': reply_data.get('content', ''),
                    'type': 'text',
                    'is_outgoing': True,
                    'is_read': True,
                    'metadata': log_entry
                })
                
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الرد: {e}")
    
    async def stop_auto_replying(self) -> bool:
        """إيقاف الرد التلقائي"""
        try:
            if not self.is_replying:
                return True
            
            self.is_replying = False
            
            # إيقاف الاستماع للرسائل
            # تحتاج للتطبيق حسب واجهة message_handler
            
            logger.info("⏹️ تم إيقاف الرد التلقائي")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف الرد التلقائي: {e}")
            return False
    
    async def add_reply_rule(self, rule_data: Dict[str, Any]) -> str:
        """إضافة قاعدة رد جديدة"""
        try:
            rule_id = rule_data.get('id', f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            rule = ReplyRule(
                id=rule_id,
                name=rule_data['name'],
                trigger_type=TriggerType(rule_data['trigger_type']),
                trigger_value=rule_data['trigger_value'],
                reply_type=ReplyType(rule_data['reply_type']),
                reply_content=rule_data['reply_content'],
                is_active=rule_data.get('is_active', True),
                priority=rule_data.get('priority', 0),
                cooldown=rule_data.get('cooldown', 0)
            )
            
            self.reply_rules[rule_id] = rule
            
            # حفظ في قاعدة البيانات
            if self.db:
                await self._save_rule_to_db(rule)
            
            logger.info(f"➕ تم إضافة قاعدة رد جديدة: {rule.name}")
            return rule_id
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة قاعدة رد: {e}")
            return ""
    
    async def update_reply_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """تحديث قاعدة رد"""
        try:
            if rule_id not in self.reply_rules:
                logger.error(f"❌ القاعدة غير موجودة: {rule_id}")
                return False
            
            rule = self.reply_rules[rule_id]
            
            # تحديث الحقول
            if 'name' in updates:
                rule.name = updates['name']
            
            if 'trigger_type' in updates:
                rule.trigger_type = TriggerType(updates['trigger_type'])
            
            if 'trigger_value' in updates:
                rule.trigger_value = updates['trigger_value']
            
            if 'reply_type' in updates:
                rule.reply_type = ReplyType(updates['reply_type'])
            
            if 'reply_content' in updates:
                rule.reply_content = updates['reply_content']
            
            if 'is_active' in updates:
                rule.is_active = updates['is_active']
            
            if 'priority' in updates:
                rule.priority = updates['priority']
            
            if 'cooldown' in updates:
                rule.cooldown = updates['cooldown']
            
            # تحديث في قاعدة البيانات
            if self.db:
                await self._save_rule_to_db(rule)
            
            logger.info(f"🔄 تم تحديث قاعدة: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث قاعدة: {e}")
            return False
    
    async def delete_reply_rule(self, rule_id: str) -> bool:
        """حذف قاعدة رد"""
        try:
            if rule_id in self.reply_rules:
                rule_name = self.reply_rules[rule_id].name
                del self.reply_rules[rule_id]
                
                logger.info(f"🗑️ تم حذف قاعدة: {rule_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في حذف قاعدة: {e}")
            return False
    
    async def get_reply_rules(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """الحصول على قائمة قواعد الرد"""
        rules_list = []
        
        for rule in self.reply_rules.values():
            if active_only and not rule.is_active:
                continue
            
            rules_list.append({
                'id': rule.id,
                'name': rule.name,
                'trigger_type': rule.trigger_type.value,
                'trigger_value': rule.trigger_value,
                'reply_type': rule.reply_type.value,
                'reply_content': str(rule.reply_content)[:100] + '...' if len(str(rule.reply_content)) > 100 else str(rule.reply_content),
                'is_active': rule.is_active,
                'priority': rule.priority,
                'cooldown': rule.cooldown,
                'match_count': rule.match_count,
                'last_used': rule.last_used.isoformat() if rule.last_used else None
            })
        
        # ترتيب حسب الأولوية
        rules_list.sort(key=lambda x: (-x['priority'], x['name']))
        
        return rules_list
    
    async def get_reply_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الردود"""
        total_rules = len(self.reply_rules)
        active_rules = len([r for r in self.reply_rules.values() if r.is_active])
        total_matches = sum(r.match_count for r in self.reply_rules.values())
        
        # القواعد الأكثر استخدامًا
        top_rules = sorted(
            [r for r in self.reply_rules.values() if r.match_count > 0],
            key=lambda x: x.match_count,
            reverse=True
        )[:5]
        
        return {
            'total_rules': total_rules,
            'active_rules': active_rules,
            'total_matches': total_matches,
            'active_users': len(self.user_cooldowns),
            'top_rules': [
                {
                    'name': rule.name,
                    'match_count': rule.match_count,
                    'last_used': rule.last_used.isoformat() if rule.last_used else 'لم يستخدم'
                }
                for rule in top_rules
            ]
        }
    
    async def clear_user_cooldowns(self) -> int:
        """مسح تبريد جميع المستخدمين"""
        try:
            count = len(self.user_cooldowns)
            self.user_cooldowns.clear()
            
            logger.info(f"🧹 تم مسح تبريد {count} مستخدم")
            return count
            
        except Exception as e:
            logger.error(f"❌ خطأ في مسح تبريد المستخدمين: {e}")
            return 0
    
    async def export_rules(self, format: str = 'json') -> Optional[str]:
        """تصدير قواعد الرد"""
        try:
            import json
            from datetime import datetime
            
            rules_data = []
            for rule in self.reply_rules.values():
                rules_data.append({
                    'id': rule.id,
                    'name': rule.name,
                    'trigger_type': rule.trigger_type.value,
                    'trigger_value': rule.trigger_value,
                    'reply_type': rule.reply_type.value,
                    'reply_content': rule.reply_content,
                    'is_active': rule.is_active,
                    'priority': rule.priority,
                    'cooldown': rule.cooldown
                })
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_rules': len(rules_data),
                'rules': rules_data
            }
            
            if format == 'json':
                filename = f"reply_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = f"data/exports/{filename}"
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                return filepath
            
            else:
                logger.error(f"❌ تنسيق غير مدعوم: {format}")
                return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في تصدير القواعد: {e}")
            return None
    
    async def import_rules(self, filepath: str) -> Tuple[int, int]:
        """استيراد قواعد الرد من ملف"""
        try:
            import json
            
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            rules_data = import_data.get('rules', [])
            
            added = 0
            updated = 0
            
            for rule_data in rules_data:
                rule_id = rule_data.get('id')
                
                if rule_id in self.reply_rules:
                    # تحديث قاعدة موجودة
                    await self.update_reply_rule(rule_id, rule_data)
                    updated += 1
                else:
                    # إضافة قاعدة جديدة
                    await self.add_reply_rule(rule_data)
                    added += 1
            
            logger.info(f"📥 تم استيراد {added} قاعدة جديدة و {updated} قاعدة محدثة")
            return added, updated
            
        except Exception as e:
            logger.error(f"❌ خطأ في استيراد القواعد: {e}")
            return 0, 0
