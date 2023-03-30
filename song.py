import random
import json
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
import plugins
from plugins import *

# 模拟歌曲库
songs = [
    {'name': '小幸运', 'lyrics': '好想再问问 你会等待还是离开'},
    {'name': '平凡之路', 'lyrics': '再一次回到 还记得的老地方'},
    {'name': '遥远的她', 'lyrics': '分手总要在雨天'},
    {'name': '岁月神偷', 'lyrics': '谁带我找回失去的勇敢'}
]

# 读取签到数据
with open("sign_in_data.json", "r") as f:
    sign_in_data = json.load(f)

@plugins.register(name="SongGuessing", desc="A song guessing game plugin", version="0.1", author="ChatGPT", desire_priority=9)
class SongGuessing(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[SongGuessing] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        user_id = e_context['context']['msg']['FromUserName']
        group_id = e_context['context']['msg']['ToUserName'] if e_context['context']['isgroup'] else e_context['context']['msg']['FromUserName']

        try:
            if "每日竞猜" in content:
                selected_song = random.choice(songs)
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"每日竞猜：\n猜猜这首歌是什么？\n歌词片段：{selected_song['lyrics']}"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS

            else:
                guessed_song = next((song for song in songs if song['name'] in content), None)
                if guessed_song:
                    group_data = sign_in_data.setdefault(group_id, {})
                    group_data[user_id] = group_data.get(user_id, 0) + 100

                    with open("sign_in_data.json", "w") as f:
                        json.dump(sign_in_data, f)

                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = f"恭喜你猜对了！获得100金币奖励！"
                    e_context['reply'] = reply
                    e_context.action = EventAction.BREAK_PASS

        except Exception as e:
            logger.error(f"[SongGuessing] Unexpected error: {e}")
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "竞猜过程中发生了错误，请稍后重试。"
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, **kwargs):
        help_text = "发送包含“每日竞猜”关键词的消息，我会为您提供一首歌曲，每天第一位猜中的成员可以获得100金币奖励。\n"
    return help_text
