"""
💬 Message Handler - معالج الرسائل
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)

class MessageHandler:
    """فئة معالجة الرسائل"""
    
    def __init__(self, whatsapp_client, database_handler=None):
        """تهيئة معالج الرسائل"""
        self.client = whatsapp_client
        self.db = database_handler
        self.is_listening = False
        self.message_callbacks = []
        self.last_message_time = {}
        self.message_buffer = []
        
    async def get_messages(self, chat_id: str, limit: int = 100, include_old: bool = False) -> List[Dict[str, Any]]:
        """الحصول على الرسائل من دردشة"""
        try:
            if not self.client.is_connected:
                logger.error("❌ العميل غير متصل")
                return []
            
            logger.info(f"📨 جلب الرسائل من الدردشة: {chat_id}")
            
            # هذه وظيفة افتراضية - تحتاج للتعديل حسب واجهة واتساب
            messages = []
            
            # فتح الدردشة
            await self.client.open_chat(chat_id)
            time.sleep(2)
            
            # تنفيذ جافا سكريبت لجلب الرسائل
            # هذا مثال افتراضي - يحتاج للتعديل الفعلي
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الرسائل: {e}")
            return []
    
    async def get_group_messages(self, group_id: str, include_old: bool = True) -> List[Dict[str, Any]]:
        """الحصول على رسائل المجموعة"""
        try:
            logger.info(f"👥 جلب رسائل المجموعة: {group_id}")
            
            # في هذه المرحلة، سنستخدم نفس دالة get_messages
            messages = await self.get_messages(group_id, include_old=include_old)
            
            # تصفية وتحسين بيانات الرسائل
            processed_messages = []
            
            for msg in messages:
                processed_msg = {
                    'id': msg.get('id', f"{group_id}_{time.time()}"),
                    'from': msg.get('from', 'unknown'),
                    'body': msg.get('body', ''),
                    'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                    'type': msg.get('type', 'text'),
                    'group_id': group_id,
                    'has_links': self._contains_links(msg.get('body', ''))
                }
                processed_messages.append(processed_msg)
            
            logger.info(f"✅ تم جلب {len(processed_messages)} رسالة من المجموعة")
            return processed_messages
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب رسائل المجموعة: {e}")
            return []
    
    def _contains_links(self, text: str) -> bool:
        """التحقق مما إذا كان النص يحتوي على روابط"""
        url_pattern = r'https?://[^\s]+'
        return bool(re.search(url_pattern, text))
    
    async def send_reply(self, to: str, message: str, quoted_msg_id: str = None) -> bool:
        """إرسال رد"""
        try:
            logger.info(f"↪️ إرسال رد إلى: {to}")
            
            # إضافة علامة الاقتباس إذا كان هناك رسالة مرجعية
            if quoted_msg_id:
                message = f"رد على الرسالة السابقة:\n{message}"
            
            # استخدام دالة الإرسال في العميل
            success = await self.client.send_message(to, message)
            
            if success and self.db:
                # تسجيل الرد في قاعدة البيانات
                await self.db.save_message({
                    'to': to,
                    'message': message,
                    'type': 'reply',
                    'timestamp': datetime.now().isoformat(),
                    'quoted_msg_id': quoted_msg_id
                })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الرد: {e}")
            return False
    
    async def send_bulk_messages(self, recipients: List[str], message: str, delay: int = 2) -> Dict[str, Any]:
        """إرسال رسائل جماعية"""
        try:
            logger.info(f"📤 إرسال رسائل جماعية إلى {len(recipients)} مستلم")
            
            results = {
                'total': len(recipients),
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for recipient in recipients:
                try:
                    success = await self.client.send_message(recipient, message)
                    
                    if success:
                        results['success'] += 1
                        logger.debug(f"✅ تم الإرسال إلى: {recipient}")
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"فشل الإرسال إلى: {recipient}")
                    
                    # تأخير بين الرسائل
                    if delay > 0:
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"خطأ في الإرسال إلى {recipient}: {str(e)}")
                    logger.error(f"❌ خطأ في الإرسال إلى {recipient}: {e}")
            
            logger.info(f"📊 نتائج الإرسال الجماعي: {results['success']} نجاح، {results['failed']} فشل")
            return results
            
        except Exception as e:
            logger.error(f"❌ خطأ في الإرسال الجماعي: {e}")
            return {'total': 0, 'success': 0, 'failed': 0, 'errors': [str(e)]}
    
    async def start_listening(self, callback: Callable = None):
        """بدء الاستماع للرسائل الجديدة"""
        try:
            if not self.client.is_connected:
                logger.error("❌ العميل غير متصل")
                return False
            
            self.is_listening = True
            
            if callback:
                self.message_callbacks.append(callback)
            
            logger.info("👂 بدء الاستماع للرسائل الجديدة...")
            
            # بدء حلقة الاستماع
            asyncio.create_task(self._listening_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء الاستماع: {e}")
            return False
    
    async def _listening_loop(self):
        """حلقة الاستماع للرسائل"""
        try:
            while self.is_listening and self.client.is_connected:
                # الحصول على أحدث الرسائل
                new_messages = await self._get_new_messages()
                
                for message in new_messages:
                    # استدعاء callback functions
                    for callback in self.message_callbacks:
                        try:
                            await callback(message)
                        except Exception as e:
                            logger.error(f"❌ خطأ في callback: {e}")
                    
                    # تخزين في buffer
                    self.message_buffer.append(message)
                    
                    # حفظ في قاعدة البيانات إذا كان متاحًا
                    if self.db:
                        await self.db.save_incoming_message(message)
                
                # تقليل حجم buffer إذا أصبح كبيرًا
                if len(self.message_buffer) > 1000:
                    self.message_buffer = self.message_buffer[-500:]
                
                # انتظار قبل التكرار التالي
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حلقة الاستماع: {e}")
            self.is_listening = False
    
    async def _get_new_messages(self) -> List[Dict[str, Any]]:
        """الحصول على الرسائل الجديدة"""
        # هذه دالة افتراضية - تحتاج للتطبيق الفعلي
        # تعتمد على كيفية جلب الرسائل الجديدة من واتساب
        
        new_messages = []
        
        try:
            # تنفيذ JavaScript لجلب الرسائل الجديدة
            # هذا مثال افتراضي
            
            return new_messages
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الرسائل الجديدة: {e}")
            return []
    
    async def stop_listening(self):
        """إيقاف الاستماع"""
        self.is_listening = False
        self.message_callbacks.clear()
        logger.info("⏹️ توقف الاستماع للرسائل")
    
    async def search_messages(self, keyword: str, chat_id: str = None) -> List[Dict[str, Any]]:
        """بحث في الرسائل"""
        try:
            logger.info(f"🔍 البحث عن: '{keyword}'")
            
            messages = []
            
            if chat_id:
                # البحث في دردشة محددة
                messages = await self.get_messages(chat_id, limit=200)
            else:
                # البحث في جميع الدردشات (أول 10 دردشات)
                chats = await self.client.get_chats()
                for chat in chats[:10]:
                    chat_messages = await self.get_messages(chat['name'], limit=50)
                    messages.extend(chat_messages)
            
            # تصفية الرسائل التي تحتوي على الكلمة المفتاحية
            results = []
            
            for msg in messages:
                if keyword.lower() in msg.get('body', '').lower():
                    results.append(msg)
            
            logger.info(f"✅ تم العثور على {len(results)} رسالة تحتوي على '{keyword}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ خطأ في البحث: {e}")
            return []
    
    async def delete_message(self, message_id: str, chat_id: str) -> bool:
        """حذف رسالة"""
        try:
            logger.info(f"🗑️ محاولة حذف رسالة: {message_id}")
            
            # هذه وظيفة افتراضية - تحتاج للتطبيق الفعلي
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حذف الرسالة: {e}")
            return False
    
    async def forward_message(self, message_id: str, from_chat: str, to_chat: str) -> bool:
        """إعادة توجيه رسالة"""
        try:
            logger.info(f"↪️ إعادة توجيه رسالة من {from_chat} إلى {to_chat}")
            
            # الحصول على الرسالة
            messages = await self.get_messages(from_chat, limit=50)
            target_message = None
            
            for msg in messages:
                if msg.get('id') == message_id:
                    target_message = msg
                    break
            
            if not target_message:
                logger.error(f"❌ لم يتم العثور على الرسالة: {message_id}")
                return False
            
            # إرسال الرسالة إلى الدردشة الجديدة
            success = await self.client.send_message(
                to_chat, 
                f"رسالة محولة:\n{target_message.get('body', '')}"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة التوجيه: {e}")
            return False
