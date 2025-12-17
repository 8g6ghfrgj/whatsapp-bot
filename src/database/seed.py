"""
🌱 Database Seeder - ملقم بيانات تجريبية
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .db_handler import Database
from .models import (
    SessionStatus, MessageType, LinkCategory,
    JoinStatus, BroadcastStatus
)

class DatabaseSeeder:
    """ملقم قاعدة البيانات"""
    
    def __init__(self, database_url: str = None):
        """تهيئة الملقم"""
        self.db = Database(database_url)
    
    async def seed_all(self, clear_existing: bool = False):
        """تلقيم جميع البيانات"""
        try:
            # تهيئة قاعدة البيانات
            await self.db.initialize()
            
            if clear_existing:
                print("🗑️ مسح البيانات الحالية...")
                await self.clear_all_data()
            
            print("🌱 بدء تلقيم البيانات...")
            
            # إنشاء جلسات
            sessions = await self.seed_sessions(count=3)
            
            # إنشاء مجموعات لكل جلسة
            groups = []
            for session in sessions:
                session_groups = await self.seed_groups(session['session_id'], count=5)
                groups.extend(session_groups)
            
            # إنشاء رسائل
            messages = []
            for group in groups:
                group_messages = await self.seed_messages(
                    group['session_id'],
                    group['group_id'],
                    count=20
                )
                messages.extend(group_messages)
            
            # إنشاء روابط
            links = await self.seed_links(sessions[0]['session_id'], count=50)
            
            # إنشاء عمليات بث
            broadcasts = await self.seed_broadcasts(sessions[0]['session_id'], count=3)
            
            # إنشاء طلبات انظمام
            join_requests = await self.seed_join_requests(sessions[0]['session_id'], count=10)
            
            print(f"✅ تم تلقيم البيانات بنجاح:")
            print(f"   📱 الجلسات: {len(sessions)}")
            print(f"   👥 المجموعات: {len(groups)}")
            print(f"   💬 الرسائل: {len(messages)}")
            print(f"   🔗 الروابط: {len(links)}")
            print(f"   📢 عمليات البث: {len(broadcasts)}")
            print(f"   👤 طلبات الانظمام: {len(join_requests)}")
            
            return True
            
        except Exception as e:
            print(f"❌ فشل في تلقيم البيانات: {e}")
            return False
    
    async def clear_all_data(self):
        """مسح جميع البيانات"""
        try:
            async with self.db.get_session() as session:
                # حذف جميع السجلات بترتيب عكسي للعلاقات
                session.query(Statistics).delete()
                session.query(Setting).delete()
                session.query(User).delete()
                session.query(JoinRequest).delete()
                session.query(Broadcast).delete()
                session.query(Link).delete()
                session.query(Message).delete()
                session.query(Group).delete()
                session.query(Session).delete()
                
                print("🧹 تم مسح جميع البيانات")
                
        except Exception as e:
            print(f"❌ فشل في مسح البيانات: {e}")
    
    async def seed_sessions(self, count: int = 3) -> List[Dict[str, Any]]:
        """تلقيم جلسات"""
        sessions_data = [
            {
                'session_id': f"session_{i}",
                'name': f"الجلسة {i}",
                'phone_number': f"+9665{random.randint(10000000, 99999999)}",
                'status': random.choice(['active', 'disconnected', 'pending']),
                'connected_at': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                'metadata': {
                    'device': random.choice(['Android', 'iPhone', 'Web']),
                    'version': '2.23.1'
                }
            }
            for i in range(1, count + 1)
        ]
        
        sessions = []
        for data in sessions_data:
            success = await self.db.save_session(data)
            if success:
                sessions.append(data)
        
        return sessions
    
    async def seed_groups(self, session_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """تلقيم مجموعات"""
        group_names = [
            "مجموعة التقنية", "مجموعة الأعمال", "مجموعة التعليم",
            "مجموعة الرياضة", "مجموعة الفنون", "مجموعة الصحة",
            "مجموعة السفر", "مجموعة الطعام", "مجموعة التطوير",
            "مجموعة الاستثمار"
        ]
        
        groups = []
        for i in range(count):
            group_data = {
                'session_id': session_id,
                'group_id': f"group_{session_id}_{i}",
                'name': random.choice(group_names) + f" {i}",
                'description': f"وصف مجموعة {i}",
                'participants_count': random.randint(10, 500),
                'is_admin': random.choice([True, False]),
                'joined_at': (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
                'last_message_at': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
            }
            
            success = await self.db.save_group(group_data)
            if success:
                groups.append(group_data)
        
        return groups
    
    async def seed_messages(self, session_id: str, group_id: str, count: int = 20) -> List[Dict[str, Any]]:
        """تلقيم رسائل"""
        senders = [
            "أحمد", "محمد", "فاطمة", "سارة", "خالد",
            "نور", "علي", "مريم", "يوسف", "ليلى"
        ]
        
        message_templates = [
            "مرحبا بالجميع 👋",
            "كيف الحال؟",
            "شكرا على المشاركة",
            "أود أن أشارك هذا الرابط: https://example.com",
            "ما رأيكم في هذا الموضوع؟",
            "لدينا اجتماع غدا",
            "مبروك للجميع 🎉",
            "معلومات مفيدة جدا",
            "أحتاج إلى مساعدة",
            "تم حل المشكلة ✅"
        ]
        
        messages = []
        for i in range(count):
            message_data = {
                'session_id': session_id,
                'message_id': f"msg_{session_id}_{group_id}_{i}",
                'sender': random.choice(senders),
                'receiver': group_id,
                'content': random.choice(message_templates),
                'type': random.choice(['text', 'text', 'text', 'image', 'video']),  # معظمها نص
                'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 720))).isoformat(),
                'is_outgoing': random.choice([True, False]),
                'is_read': random.choice([True, False]),
                'group_id': group_id,
                'metadata': {
                    'length': len(random.choice(message_templates))
                }
            }
            
            success = await self.db.save_message(message_data)
            if success:
                messages.append(message_data)
        
        return messages
    
    async def seed_links(self, session_id: str, count: int = 50) -> List[Dict[str, Any]]:
        """تلقيم روابط"""
        domains = {
            'whatsapp': ['chat.whatsapp.com/ABC123', 'chat.whatsapp.com/DEF456'],
            'telegram': ['t.me/group1', 'telegram.me/channel1'],
            'instagram': ['instagram.com/p/ABC123', 'instagram.com/reel/DEF456'],
            'facebook': ['facebook.com/groups/123', 'facebook.com/page/456'],
            'youtube': ['youtube.com/watch?v=ABC123', 'youtu.be/DEF456'],
            'tiktok': ['tiktok.com/@user/video/123', 'vm.tiktok.com/ABC123'],
            'other': ['example.com', 'github.com/project']
        }
        
        links = []
        for i in range(count):
            category = random.choice(list(domains.keys()))
            domain = random.choice(domains[category])
            
            link_data = {
                'session_id': session_id,
                'url': f"https://{domain}",
                'found_in': f"مجموعة {random.randint(1, 10)}",
                'group_id': f"group_{session_id}_{random.randint(0, 4)}",
                'message_id': f"msg_{session_id}_group_{random.randint(0, 4)}_{i}",
                'title': f"عنوان الرابط {i}",
                'description': f"وصف الرابط {i}",
                'metadata': {
                    'category': category,
                    'domain': domain
                }
            }
            
            success = await self.db.save_link(link_data)
            if success:
                links.append(link_data)
        
        return links
    
    async def seed_broadcasts(self, session_id: str, count: int = 3) -> List[Dict[str, Any]]:
        """تلقيم عمليات بث"""
        broadcast_names = [
            "إعلان المنتجات الجديدة",
            "تحديث النظام",
            "ترقية الخدمة",
            "عرض خاص",
            "إشعار مهم"
        ]
        
        broadcasts = []
        for i in range(count):
            broadcast_id = f"bcast_{session_id}_{i}"
            
            broadcast_data = {
                'session_id': session_id,
                'name': random.choice(broadcast_names),
                'content': f"هذا محتوى الإعلان رقم {i}. يرجى الاطلاع على التفاصيل.",
                'content_type': random.choice(['text', 'image', 'video']),
                'target_type': 'groups',
                'target_ids': [f"group_{session_id}_{j}" for j in range(5)],
                'scheduled_for': (datetime.now() + timedelta(hours=random.randint(1, 24))).isoformat(),
                'total_targets': 5,
                'status': random.choice(['scheduled', 'sending', 'completed'])
            }
            
            try:
                broadcast_id = await self.db.save_broadcast(broadcast_data)
                
                # تحديث حالة البث
                await self.db.update_broadcast_status(
                    broadcast_id,
                    broadcast_data['status'],
                    sent_count=random.randint(3, 5) if broadcast_data['status'] == 'completed' else 0,
                    failed_count=random.randint(0, 2) if broadcast_data['status'] == 'completed' else 0
                )
                
                broadcasts.append(broadcast_data)
                
            except Exception as e:
                print(f"⚠️ فشل في تلقيم البث {i}: {e}")
        
        return broadcasts
    
    async def seed_join_requests(self, session_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """تلقيم طلبات انظمام"""
        group_names = [
            "مجموعة المطورين", "مجموعة المستثمرين", "مجموعة المسافرين",
            "مجموعة الطهاة", "مجموعة الرياضيين", "مجموعة الفنانين"
        ]
        
        requests = []
        for i in range(count):
            status = random.choice(['pending', 'joined', 'rejected'])
            
            request_data = {
                'session_id': session_id,
                'invite_link': f"https://chat.whatsapp.com/INVITE{i}",
                'group_name': random.choice(group_names),
                'status': status,
                'requested_at': (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
                'error_message': "المجموعة كاملة" if status == 'rejected' else None
            }
            
            if status == 'joined':
                request_data['joined_at'] = (datetime.now() - timedelta(days=random.randint(0, 3))).isoformat()
            elif status == 'rejected':
                request_data['rejected_at'] = (datetime.now() - timedelta(days=random.randint(1, 2))).isoformat()
            
            success = await self.db.save_group_join(request_data)
            if success:
                requests.append(request_data)
        
        return requests
    
    async def generate_test_report(self):
        """إنشاء تقرير اختبار"""
        print("\n📊 تقرير البيانات التجريبية:")
        
        # الحصول على الإحصائيات
        stats = await self.db.get_statistics(days=30)
        
        print(f"\n📈 الإحصائيات (آخر 30 يوم):")
        for metric, value in stats['totals'].items():
            print(f"   {metric}: {value}")
        
        # الحصول على عدد السجلات
        info = await self.db.get_database_info()
        
        print(f"\n🗃️ إجمالي السجلات في كل جدول:")
        for table, count in info['tables'].items():
            print(f"   {table}: {count}")
        
        print(f"\n💾 حجم قاعدة البيانات: {info.get('database_size', 'غير متوفر')}")

# دالة تشغيل
async def main():
    """الدالة الرئيسية للتلقيم"""
    print("🌱 ملقم قاعدة البيانات التجريبية")
    
    # إنشاء الملقم
    seeder = DatabaseSeeder()
    
    # تلقيم البيانات
    await seeder.seed_all(clear_existing=True)
    
    # إنشاء تقرير
    await seeder.generate_test_report()
    
    print("\n✅ اكتمل تلقيم البيانات التجريبية!")

if __name__ == "__main__":
    asyncio.run(main())
