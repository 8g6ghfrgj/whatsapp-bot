"""
🤖 أنظمة الأتمتة - التحكم التلقائي في البوت
"""

__version__ = "1.0.0"
__author__ = "WhatsApp Bot Team"

from .auto_poster import AutoPoster
from .auto_joiner import AutoJoiner
from .auto_replier import AutoReplier
from .auto_collector import AutoCollector
from .scheduler import Scheduler
from .monitor import SystemMonitor

__all__ = [
    "AutoPoster",
    "AutoJoiner", 
    "AutoReplier",
    "AutoCollector",
    "Scheduler",
    "SystemMonitor"
]
