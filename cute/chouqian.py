from datetime import datetime
import random

from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger

fortune_descriptions = [
    "今天运势非常好，适合出门旅行、投资和尝试新事物哦~",
    "今天运势还不错，适合处理日常事务，注意保持良好的心态。",
    "今天运势一般，可能会遇到一些小麻烦，不过只要冷静应对就没问题。",
    "今天运势较差，最好避免重要决策和冒险行为，以免造成损失。",
    "今天运势很差，小心谨慎，尽量避免外出和参与重要活动。"
]

emoji_list = ['(＾▽＾)', '(￣▽￣)', '(*^▽^*)', '(╹◡╹)', 'ヾ(≧▽≦*)o']

user_draw_history = {}


@plugins.register(name="FortuneTeller", desc="A simple fortune teller plugin", version="0.1", author="chenxu", desire_priority=9)
class FortuneTeller(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[FortuneTeller] inited")

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        logger.debug("[FortuneTeller] on_handle_context. content: %s" % content)

        try:
            if "抽签" in content:
                user_id = e_context['context']['msg']['FromUserName']
                today = datetime.now().date().isoformat()

                if user_id in user_draw_history and user_draw_history[user_id] == today:
                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = f"你今天已经抽签过了，不要妄图逆天改命哟~ {random.choice(emoji_list)}"
                else:
                    user_draw_history[user_id] = today
                    fortune = random.choice(fortune_descriptions)
                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = f"今日运势：{fortune} {random.choice(emoji_list)}"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
        except Exception as e:
            logger.error(f"[FortuneTeller] Unexpected error: {e}")
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "抽签过程中发生了错误，请稍后重试。"
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "发送包含“抽签”关键词的消息，我会为您抽取今日运势。\n"
        return help_text

