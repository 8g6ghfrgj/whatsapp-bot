"""
📱 WhatsApp Client - العميل الرئيسي للاتصال بواتساب
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class WhatsAppClient:
    """فئة العميل للاتصال بواتساب"""
    
    def __init__(self, session_id: str = None):
        """تهيئة العميل"""
        self.session_id = session_id or f"session_{int(time.time())}"
        self.driver: Optional[webdriver.Chrome] = None
        self.is_connected = False
        self.is_authenticated = False
        self.phone_number: Optional[str] = None
        self.profile_info: Dict[str, Any] = {}
        self.session_data: Dict[str, Any] = {}
        
        # إعدادات المتصفح
        self.chrome_options = self._setup_chrome_options()
        
        # مسارات الملفات
        self.session_dir = os.path.join("sessions", self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        logger.info(f"✅ تم إنشاء عميل واتساب جديد: {self.session_id}")
    
    def _setup_chrome_options(self):
        """إعداد خيارات متصفح Chrome"""
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        
        # إعدادات للتشغيل غير المرئي (يمكن إزالته للتصحيح)
        # options.add_argument("--headless")
        
        # إعدادات أخرى
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # إعدادات لحفظ الجلسة
        options.add_argument(f"--user-data-dir={os.path.join(self.session_dir, 'chrome_data')}")
        
        # منع الإشعارات
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 1,
        })
        
        return options
    
    async def initialize(self):
        """تهيئة المتصفح"""
        try:
            logger.info(f"🚀 تهيئة متصفح Chrome للجلسة: {self.session_id}")
            
            # استخدام ChromeDriver
            self.driver = webdriver.Chrome(options=self.chrome_options)
            
            # فتح واتساب ويب
            self.driver.get("https://web.whatsapp.com")
            
            logger.info("✅ تم تهيئة المتصفح بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة المتصفح: {e}")
            return False
    
    async def wait_for_qr_code(self, timeout: int = 300) -> Optional[str]:
        """انتظار ظهور QR Code"""
        try:
            logger.info("⏳ في انتظار ظهور QR Code...")
            
            wait = WebDriverWait(self.driver, timeout)
            
            # انتظار ظهور عنصر QR Code
            qr_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            
            # انتظار تحميل الصورة
            time.sleep(2)
            
            # حفظ صورة QR Code
            qr_path = os.path.join(self.session_dir, "qr_code.png")
            qr_element.screenshot(qr_path)
            
            logger.info(f"📱 تم حفظ QR Code في: {qr_path}")
            return qr_path
            
        except TimeoutException:
            logger.error("❌ انتهى الوقت المحدد دون ظهور QR Code")
            return None
        except Exception as e:
            logger.error(f"❌ خطأ في انتظار QR Code: {e}")
            return None
    
    async def wait_for_authentication(self, timeout: int = 300) -> bool:
        """انتظار المصادقة بعد مسح QR Code"""
        try:
            logger.info("⏳ في انتظار المصادقة...")
            
            wait = WebDriverWait(self.driver, timeout)
            
            # انتظار اختفاء QR Code وظهور واجهة المحادثات
            wait.until(
                EC.invisibility_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            
            # التحقق من ظهور واجهة المحادثات
            wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox' and @contenteditable='true']"))
            )
            
            # الحصول على معلومات الحساب
            await self._get_account_info()
            
            self.is_connected = True
            self.is_authenticated = True
            
            logger.info("✅ تمت المصادقة بنجاح!")
            logger.info(f"📞 رقم الهاتف: {self.phone_number}")
            
            return True
            
        except TimeoutException:
            logger.error("❌ انتهى الوقت المحدد دون اكتمال المصادقة")
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في المصادقة: {e}")
            return False
    
    async def _get_account_info(self):
        """الحصول على معلومات الحساب"""
        try:
            # الانتظار حتى تحميل الصفحة
            time.sleep(3)
            
            # الحصول على رقم الهاتف من الاسم الظاهر
            try:
                profile_element = self.driver.find_element(
                    By.XPATH, "//header//div[contains(@class, '_ak8l')]"
                )
                profile_text = profile_element.text
                
                if profile_text and "+" in profile_text:
                    self.phone_number = profile_text.split("\n")[-1]
                    logger.info(f"📱 تم التعرف على رقم الهاتف: {self.phone_number}")
            except:
                logger.warning("⚠️ لم يتمكن من الحصول على رقم الهاتف")
            
            # حفظ معلومات الجلسة
            self.profile_info = {
                'phone_number': self.phone_number,
                'connected_at': datetime.now().isoformat(),
                'session_id': self.session_id
            }
            
            # حفظ بيانات الجلسة
            await self._save_session_data()
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على معلومات الحساب: {e}")
    
    async def _save_session_data(self):
        """حفظ بيانات الجلسة"""
        try:
            session_file = os.path.join(self.session_dir, "session.json")
            
            session_data = {
                'session_id': self.session_id,
                'phone_number': self.phone_number,
                'profile_info': self.profile_info,
                'cookies': self.driver.get_cookies(),
                'local_storage': self._get_local_storage(),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.session_data = session_data
            logger.info(f"💾 تم حفظ بيانات الجلسة في: {session_file}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ بيانات الجلسة: {e}")
    
    def _get_local_storage(self) -> Dict[str, str]:
        """الحصول على Local Storage"""
        try:
            return self.driver.execute_script("return window.localStorage;")
        except:
            return {}
    
    async def restore_session(self, session_data: Dict[str, Any]) -> bool:
        """استعادة الجلسة من بيانات محفوظة"""
        try:
            logger.info(f"🔄 محاولة استعادة الجلسة: {self.session_id}")
            
            # تهيئة المتصفح
            if not await self.initialize():
                return False
            
            # تحميل الكوكيز
            if 'cookies' in session_data:
                for cookie in session_data['cookies']:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        continue
            
            # تحديث الصفحة
            self.driver.refresh()
            
            # التحقق من الاتصال
            time.sleep(5)
            
            # التحقق مما إذا كنا متصلين
            try:
                # البحث عن أي عنصر يدل على الاتصال
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
                )
                
                self.is_connected = True
                self.is_authenticated = True
                self.phone_number = session_data.get('phone_number')
                self.session_data = session_data
                
                logger.info("✅ تم استعادة الجلسة بنجاح")
                return True
                
            except TimeoutException:
                logger.warning("⚠️ الجلسة منتهية الصلاحية")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في استعادة الجلسة: {e}")
            return False
    
    async def get_session_data(self) -> Dict[str, Any]:
        """الحصول على بيانات الجلسة الحالية"""
        try:
            if not self.is_connected:
                return {}
            
            # تحديث بيانات الجلسة
            await self._save_session_data()
            
            return self.session_data
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على بيانات الجلسة: {e}")
            return {}
    
    async def get_account_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الحساب"""
        try:
            if not self.is_connected:
                return {}
            
            return {
                'session_id': self.session_id,
                'phone_number': self.phone_number,
                'profile_info': self.profile_info,
                'is_connected': self.is_connected,
                'connected_since': self.profile_info.get('connected_at')
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على معلومات الحساب: {e}")
            return {}
    
    async def send_message(self, to: str, message: str) -> bool:
        """إرسال رسالة"""
        try:
            if not self.is_connected:
                logger.error("❌ العميل غير متصل")
                return False
            
            logger.info(f"📤 إرسال رسالة إلى: {to}")
            
            # فتح دردشة مع المستخدم/المجموعة
            chat_url = f"https://web.whatsapp.com/send?phone={to}&text={message}"
            self.driver.get(chat_url)
            
            # الانتظار حتى تحميل الصفحة
            time.sleep(3)
            
            # إرسال الرسالة
            try:
                message_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='textbox' and @contenteditable='true']"))
                )
                
                message_box.clear()
                message_box.send_keys(message)
                
                # زر الإرسال
                send_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='إرسال']"))
                )
                send_button.click()
                
                logger.info(f"✅ تم إرسال الرسالة إلى: {to}")
                return True
                
            except TimeoutException:
                logger.error(f"❌ فشل في إرسال الرسالة إلى: {to}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الرسالة: {e}")
            return False
    
    async def send_media(self, to: str, file_path: str, caption: str = "") -> bool:
        """إرسال ملف وسائط"""
        try:
            if not self.is_connected:
                logger.error("❌ العميل غير متصل")
                return False
            
            logger.info(f"📤 إرسال وسائط إلى: {to}")
            
            # فتح الدردشة
            chat_url = f"https://web.whatsapp.com/send?phone={to}"
            self.driver.get(chat_url)
            
            time.sleep(3)
            
            # زر المرفقات
            attachment_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@title='إرفاق']"))
            )
            attachment_button.click()
            
            time.sleep(1)
            
            # اختيار نوع الملف
            file_input = self.driver.find_element(
                By.XPATH, "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']"
            )
            file_input.send_keys(os.path.abspath(file_path))
            
            time.sleep(2)
            
            # إضافة نص توضيحي إذا كان موجودًا
            if caption:
                caption_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='textbox' and @contenteditable='true']"))
                )
                caption_box.send_keys(caption)
            
            # زر الإرسال
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(@aria-label, 'إرسال')]"))
            )
            send_button.click()
            
            logger.info(f"✅ تم إرسال الوسائط إلى: {to}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الوسائط: {e}")
            return False
    
    async def get_chats(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة الدردشات"""
        try:
            if not self.is_connected:
                return []
            
            chats = []
            
            # البحث عن عناصر الدردشات
            chat_elements = self.driver.find_elements(
                By.XPATH, "//div[@role='listitem']//div[contains(@class, '_ak8l')]"
            )
            
            for element in chat_elements[:50]:  # أول 50 دردشة فقط
                try:
                    chat_info = {
                        'name': element.text.split('\n')[0] if '\n' in element.text else element.text,
                        'element': element
                    }
                    chats.append(chat_info)
                except:
                    continue
            
            logger.info(f"📋 تم العثور على {len(chats)} دردشة")
            return chats
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على الدردشات: {e}")
            return []
    
    async def join_group(self, invite_link: str) -> Dict[str, Any]:
        """الانضمام إلى مجموعة عبر رابط الدعوة"""
        try:
            logger.info(f"👥 محاولة الانضمام إلى المجموعة: {invite_link}")
            
            # فتح رابط الدعوة
            self.driver.get(invite_link)
            
            time.sleep(3)
            
            # محاولة النقر على زر الانضمام
            try:
                join_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(text(), 'انضم')]"))
                )
                join_button.click()
                
                # انتظار التأكيد
                time.sleep(3)
                
                # التحقق مما إذا كنا في المجموعة
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'أنت انضممت')]"))
                    )
                    
                    logger.info("✅ تم الانضمام إلى المجموعة بنجاح")
                    return {
                        'success': True,
                        'message': 'تم الانضمام إلى المجموعة',
                        'group_link': invite_link
                    }
                    
                except TimeoutException:
                    # قد يكون هناك حاجة للموافقة
                    logger.info("⏳ في انتظار موافقة المسؤول")
                    return {
                        'success': True,
                        'message': 'طلب الانضمام قيد الانتظار',
                        'group_link': invite_link
                    }
                    
            except TimeoutException:
                # قد يكون الرابط غير صالح أو المجموعة كاملة
                logger.error("❌ فشل في العثور على زر الانضمام")
                return {
                    'success': False,
                    'error': 'رابط غير صالح أو المجموعة كاملة',
                    'group_link': invite_link
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في الانضمام إلى المجموعة: {e}")
            return {
                'success': False,
                'error': str(e),
                'group_link': invite_link
            }
    
    async def check_health(self) -> bool:
        """فحص صحة الاتصال"""
        try:
            if not self.driver:
                return False
            
            # التحقق مما إذا كانت الصفحة لا تزال مفتوحة
            current_url = self.driver.current_url
            
            if 'web.whatsapp.com' in current_url:
                # محاولة الوصول إلى عنصر بسيط
                try:
                    self.driver.find_element(By.XPATH, "//div[@role='application']")
                    return True
                except:
                    return False
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الصحة: {e}")
            return False
    
    async def reconnect(self) -> bool:
        """إعادة الاتصال"""
        try:
            logger.info("🔄 محاولة إعادة الاتصال...")
            
            # إغلاق المتصفح الحالي
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            # إعادة التهيئة
            success = await self.initialize()
            
            if success:
                # محاولة استعادة الجلسة
                if self.session_data:
                    success = await self.restore_session(self.session_data)
            
            if success:
                logger.info("✅ تمت إعادة الاتصال بنجاح")
                return True
            else:
                logger.error("❌ فشل إعادة الاتصال")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة الاتصال: {e}")
            return False
    
    async def logout(self):
        """تسجيل الخروج"""
        try:
            logger.info(f"👋 تسجيل الخروج من الجلسة: {self.session_id}")
            
            # فتح الإعدادات
            self.driver.get("https://web.whatsapp.com/settings")
            time.sleep(2)
            
            # النقر على تسجيل الخروج
            try:
                logout_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'تسجيل الخروج')]"))
                )
                logout_button.click()
                
                # تأكيد تسجيل الخروج
                time.sleep(1)
                confirm_button = self.driver.find_element(
                    By.XPATH, "//div[@role='button' and contains(text(), 'تسجيل الخروج')]"
                )
                confirm_button.click()
                
                time.sleep(2)
                
            except:
                pass
            
            # إغلاق المتصفح
            if self.driver:
                self.driver.quit()
            
            self.is_connected = False
            self.is_authenticated = False
            
            logger.info("✅ تم تسجيل الخروج بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الخروج: {e}")
            # إغلاق المتصفح على أي حال
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
