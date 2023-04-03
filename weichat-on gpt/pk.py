import json
import os
import random
import datetime
from typing import Dict
import re
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType, ReplyImage
import plugins
from plugins import *
from common.log import logger
from json import JSONDecodeError

image_folder_path = "path/to/your/image/folder"

class DataHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_data(self):
        if not os.path.exists(self.file_path):
            return {}

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {self.file_path}")
            return {}
        except JSONDecodeError as e:
            logger.error(f"Error decoding JSON data from {self.file_path}: {e}")
            return {}
        return data

    def save_data(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

gold_data_handler = DataHandler("sign_in_data.json")
role_data_handler = DataHandler("role.json")
train_record_data_handler = DataHandler("train_record.json")

# 读取培养记录文件
def read_train_record_data() -> Dict[str, str]:
    return train_record_data_handler.read_data()

# 保存培养记录文件
def save_train_record_data(data: Dict[str, str]):
    train_record_data_handler.save_data(data)

# 检查用户今天是否已经培养过角色
def check_train_today(user_id: str) -> bool:
    train_record_data = read_train_record_data()
    today = datetime.date.today().strftime('%Y-%m-%d')
    return train_record_data.get(user_id) == today

# 保存用户培养角色的记录
def save_train_record(user_id: str, date: str):
    train_record_data = read_train_record_data()
    train_record_data[user_id] = date
    save_train_record_data(train_record_data)

role_names = [
    '穹妹',
    '猫娘',
    '公主',
    '战斗女仆',
    '神里绫华'
]

attributes = ["攻击", "防御", "速度"]

def create_random_role(name):
    role = {
        "name": name,
        "攻击": random.randint(10, 100),
        "防御": random.randint(10, 100),
        "速度": random.randint(10, 100),
    }
    return role

# 获取当前擂台上的最强角色
def get_top_role() -> Dict:
    role_data = role_data_handler.read_data()
    top_role = None
    max_score = -1
    for role in role_data.values():
        score = role['攻击'] + role['防御'] + role['速度']
        if score > max_score:
            max_score = score
            top_role = role
    return top_role

# 获取最强角色的拥有者
def get_top_role_owner(top_role: Dict) -> str:
    role_data = role_data_handler.read_data()
    for user_id, role in role_data.items():
        if role == top_role:
            return user_id
    return "未知"

@plugins.register(name="RoleGame", desc="A simple role game plugin", version="0.1", author="Assistant", desire_priority=9)
class RoleGame(Plugin):
    def init(self):
        super().init()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[RoleGame] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

    content = e_context['context'].content
    logger.debug("[RoleGame] on_handle_context. content: %s" % content)

    user_id = e_context['context']['msg']['FromUserName']
    group_id = e_context['context']['msg']['ToUserName'] if e_context['context']['isgroup'] else e_context['context']['msg']['FromUserName']

    gold_data = read_gold_data()
    role_data = read_role_data()

    try:
        # 抽取角色
        if "抽取角色" in content:
            if gold_data[user_id] < 200:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "您的金币不足以抽取角色，请先签到或完成其他任务赚取金币。"
            else:
                gold_data[user_id] -= 200
                save_gold_data(gold_data)

                role_name = random.choice(role_names)
                role = create_random_role(role_name)
                role_data[user_id] = role
                save_role_data(role_data)

                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"恭喜您抽取到了 {role_name} 角色！"
                e_context['reply'] = reply

                # 发送角色图片
                image_reply = ReplyImage()
                image_reply.path = os.path.join(image_folder_path, f"{role_name}.jpg")
                e_context['reply_images'] = [image_reply]

        # 查看角色
        elif "查看角色" in content:
            if user_id not in role_data:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "您还没有抽取到任何角色，请先抽取角色。"
            else:
                role = role_data[user_id]
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"您的角色：{role['name']}，攻击：{role['攻击']}，防御：{role['防御']}，速度：{role['速度']}"
            e_context['reply'] = reply

       # 决斗
        elif "决斗" in content:
            # 解析出对方用户ID
            target_user_id = re.search(r'@(\w+)', content)
            if target_user_id:
                target_user_id = target_user_id.group(1)
            else:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "请@一个对方用户来发起决斗。"
                e_context['reply'] = reply
                return

            else:
                my_role = role_data[user_id]
                target_role = role_data[target_user_id]

                result = (my_role["攻击"] + my_role["速度"] * 0.2) - target_role["防御"]

                if result > 0:
                    gold_stolen = random.randint(50, 150)
                    gold_data[user_id] += gold_stolen
                    gold_data[target_user_id] -= gold_stolen
                    save_gold_data(gold_data)
                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = f"抢夺成功，获得对方 {gold_stolen} 金币！"
                elif result == 0:
                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = "别打撩，你们这样子是打不死人的！"
                else:
                    gold_data[user_id] -= 50
                    save_gold_data(gold_data)
                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = "你被对方痛扁了一顿，损失了 50 金币。"

            e_context['reply'] = reply

        # 培养角色
        elif "培养角色" in content:
            if check_train_today(user_id):
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "您今天已经培养过角色了，请明天再来。"
            elif gold_data[user_id] < 20:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "您的金币不足以培养角色，请先签到或完成其他任务赚取金币。"
            else:
                gold_data[user_id] -= 20
                save_gold_data(gold_data)
                role = role_data[user_id]
                attr_to_increase = random.choice(attributes)
                role[attr_to_increase] += random.randint(1, 10)
                save_role_data(role_data)
                save_train_record(user_id, datetime.date.today().strftime('%Y-%m-%d'))

                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"培养成功！您的 {role['name']} 角色的 {attr_to_increase} 增加了。"
            e_context['reply'] = reply

        # 查看擂台
        elif "查看擂台" in content:
            top_role = get_top_role()
            top_role_owner = get_top_role_owner(top_role)
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = f"当前擂台上的最强角色是：{top_role['name']}，攻击：{top_role['攻击']}，防御：{top_role['防御']}，速度：{top_role['速度']}。拥有者：{top_role_owner}"
            e_context['reply'] = reply

            # 发送角色图片
            image_reply = ReplyImage()
            image_reply.path = os.path.join(image_folder_path, f"{top_role['name']}.jpg")
            e_context['reply_images'] = [image_reply]    
        except Exception as e:
            logger.error(f"[RoleGame] Unexpected error: {e}")
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "游戏过程中发生了错误，请稍后重试。"
            e_context['reply'] = reply

    def get_help_text(self, **kwargs):
        help_text = ("发送包含“抽取角色”关键词的消息，我会为您抽取一个角色；\n"
                     "发送包含“查看角色”关键词的消息，我会为您展示您当前的角色；\n"
                     "发送包含“决斗”关键词的消息并@对方，我会根据您和对方的角色属性进行决斗，并返回结果；\n"
                     "发送包含“培养角色”关键词的消息，我会为您随机增加角色的攻击、防御或速度属性；\n"
                     "发送包含“查看擂台”关键词的消息，我会为您展示当前擂台上的最强角色及其拥有者。")
        return help_text

