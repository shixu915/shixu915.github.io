from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger
import re
import sympy

@plugins.register(name="Calculator", desc="A plugin that calculates mathematical expressions", version="0.1", author="YourName", desire_priority= 10)
class Calculator(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Calculator] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content

        if content.startswith("计算"):
            expression = content[2:].strip()
            reply = Reply()
            reply.type = ReplyType.TEXT

            if not expression:
                reply.content = "请输入一个数学表达式。"
            else:
                try:
                    # 使用sympy库解析并计算表达式
                    result = sympy.sympify(expression)
                    reply.content = f"计算结果：{result}"
                except (sympy.SympifyError, ValueError) as e:
                    logger.error(f"计算出错：{e}")
                    reply.content = "无法计算，请检查您输入的表达式是否正确。"
                except Exception as e:
                    logger.error(f"未知错误：{e}")
                    reply.content = "发生了一个未知错误，请稍后再试。"

            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, **kwargs):
        help_text = "输入“计算 数学表达式”，我会帮您计算数学表达式的结果。\n"
        return help_text
