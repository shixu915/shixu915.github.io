import re
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger


@plugins.register(name="Calculator", desc="A simple calculator plugin", version="0.1", author="chenxu", desire_priority= 9)
class Calculator(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Calculator] inited")

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return
        
        content = e_context['context'].content
        logger.debug("[Calculator] on_handle_context. content: %s" % content)

        if "计算" in content:
            expression = re.sub(r'[^\d+\-*/\s().]', '', content.replace("计算", "")).strip()
            try:
                result = eval(expression)
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"计算结果为：{result}"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑
            except ZeroDivisionError:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "除数不能为零，请检查表达式是否正确。"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑
            except SyntaxError:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "表达式语法错误，请检查表达式是否正确。"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑
            except Exception as e:
                logger.error(f"[Calculator] Unexpected error: {e}")
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "计算过程中发生了错误，请稍后重试。"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "发送包含“计算”关键词的消息，我会尝试计算表达式的结果。\n"
        return help_text
