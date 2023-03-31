import random
import json
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
import plugins
from plugins import *
from sign_in_data_manager import SignInDataManager

@plugins.register(name="SongGuessing", desc="A song guessing game plugin", version="0.1", author="chenxu", desire_priority=9)
class SongGuessing(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[SongGuessing] inited")

        self.songs = [
            {'name': '小幸运', 'lyrics': '好想再问问 你会等待还是离开'},
            {'name': '平凡之路', 'lyrics': '再一次回到 还记得的老地方'},
            {'name': '遥远的她', 'lyrics': '分手总要在雨天'},
            {'name': '岁月神偷', 'lyrics': '谁带我找回失去的勇敢'}
        ]
        self.sign_in_data_manager = SignInDataManager()

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content

        try:
            if "每日竞猜" in content:
                self.handle_daily_quiz(e_context)

            else:
                self.handle_guess(e_context)

        except Exception as e:
            logger.error(f"[SongGuessing] Unexpected error: {e}")
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "竞猜过程中发生了错误，请稍后重试。"
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

    def handle_daily_quiz(self, e_context: EventContext):
        selected_song = random.choice(self.songs)
        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = f"每日竞猜：\n猜猜这首歌是什么？\n歌词片段：{selected_song['lyrics']}"
        e_context['reply'] = reply
        e_context.action = EventAction.BREAK_PASS

    def handle_guess(self, e_context: EventContext):
        content = e_context['context'].content
        user_id = e_context['context']['msg']['FromUserName']
        group_id = e_context['context']['msg']['ToUserName'] if e_context['context']['isgroup'] else e_context['context']['msg']['FromUserName']
        guessed_song = next((song for song in self.songs if song['name'] in content), None)

        if guessed_song:
            group_data = self.sign_in_data_manager.get_group_data(group_id)

            if not group_data.get('daily_winner'):
                group_data['daily_winner'] = user_id
                self.sign_in_data_manager.add_user_gold(group_id, user_id, 100)

                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"恭喜你猜对了！获得100金币奖励！"
            else:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "竞猜已结束，请明天再来吧，刚把爹~"

            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, **kwargs):
        help_text = "发送包含“每日竞猜”关键词的消息，我会为您提供一首歌曲，每天第一位猜中的成员可以获得100金币奖励。\n"
        return help_text
