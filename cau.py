import re
import ast
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger


@plugins.register(name="Calculator", desc="A simple calculator plugin", version="0.1", author="lanvent", desire_priority= -1)
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
                result = ast.literal_eval(expression)
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"计算结果为：{result}"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑
            except:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "无法计算，请检查表达式是否正确。"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "发送包含“计算”关键词的消息，我会尝试计算表达式的结果。\n"
        return help_text
