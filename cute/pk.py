import os
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger
from role_manager import RoleManager
from sign_in_data_manager import SignInDataManager

@plugins.register(name="抽取角色", desc="A plugin for extracting a random role", version="0.1", author="chenxu", desire_priority=10)
class RoleExtraction(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        self.img_path = os.path.join(current_file_directory, "img")
        self.roles = ["穹妹", "猫娘", "公主", "战斗女仆", "神里绫华"]
        self.required_gold = 200
        self.role_manager = RoleManager(self.roles)
        self.sign_in_data_manager = SignInDataManager()
        logger.info("[RoleExtraction] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        if content == "抽取角色":
            user_id = e_context['context']['msg'].get('User', {}).get('Uin', None)
            user_gold = self.sign_in_data_manager.get_gold(user_id)

            if user_gold >= self.required_gold:
                self.sign_in_data_manager.set_gold(user_id, user_gold - self.required_gold)
                chosen_role = self.role_manager.extract_random_role(user_id)
                e_context['reply'] = self.generate_reply(chosen_role)
            else:
                e_context['reply'] = self.generate_insufficient_gold_reply()

            e_context.action = EventAction.BREAK

    def generate_reply(self, chosen_role):
        if chosen_role is not None:
            reply = Reply()
            reply.type = ReplyType.TEXT_IMAGE
            reply.content = f"恭喜你获得了{chosen_role}角色!"
            reply.image_path = os.path.join(self.img_path, f"{chosen_role}.jpg")
            return reply
        else:
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "对不起，你已经拥有一个角色，无法再次抽取。"
            return reply

    def generate_insufficient_gold_reply(self):
        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = "对不起，你的金币不足，无法抽取角色。"
        return reply

    def get_help_text(self, **kwargs):
        help_text = f"发送包含“抽取角色”关键词的消息，我会随机抽取一名角色为您效忠\n"
        return help_text
