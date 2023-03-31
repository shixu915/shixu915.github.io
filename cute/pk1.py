import os
import json
import random
import plugins
from plugins import *
from common.log import logger
from bridge.reply import Reply, ReplyType
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType


@plugins.register(name="抽取角色", desc="A plugin for extracting a random role", version="0.1", author="chenxu", desire_priority=10)
class RoleExtraction(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        self.img_path = os.path.join(current_file_directory, "img")
        self.roles = ["穹妹", "猫娘", "公主", "战斗女仆", "神里绫华"]
        self.required_gold = 200
        logger.info("[RoleExtraction] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        if content == "抽取角色":
            user_id = e_context['context']['msg']['User']['Uin']

            # Read user data
            with open('sign_in_data.json', 'r') as f:
                user_data = json.load(f)

            # Check if user has enough gold
            if user_data[user_id]['gold'] >= self.required_gold:
                user_data[user_id]['gold'] -= self.required_gold

                # Save user data
                with open('sign_in_data.json', 'w') as f:
                    json.dump(user_data, f)

                chosen_role = self.extract_role(user_id)

                # Prepare and send reply
                reply = Reply()
                reply.type = ReplyType.TEXT_IMAGE
                reply.content = f"恭喜你获得了{chosen_role}角色!"
                reply.image_path = os.path.join(self.img_path, f"{chosen_role}.jpg")
                e_context['reply'] = reply
            else:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "对不起，你的金币不足，无法抽取角色。"
                e_context['reply'] = reply
            e_context.action = EventAction.BREAK

    def extract_role(self, user_id):
        # Read role data
        with open('role.json', 'r') as f:
            role_data = json.load(f)

        # Check if user already has a role
        if user_id not in role_data:
            chosen_role = random.choice(self.roles)
            role_data[user_id] = {
                "name": chosen_role,
                "attack": random.randint(10, 100),
                "defense": random.randint(10, 100),
                "speed": random.randint(10, 100)
            }

            # Save role data
            with open('role.json', 'w') as f:
                json.dump(role_data, f)
            return chosen_role
        else:
            return None

    def get_help_text(self, **kwargs):
        help_text = f"发送包含“抽取角色”关键词的消息，我会随机抽取一名角色为您效忠\n"
        return help_text
