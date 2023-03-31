from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger
import random
import datetime
from sign_in_data_manager import SignInDataManager

data_manager = SignInDataManager()

@plugins.register(name="签到", desc="这是一个签到类插件", version="0.1", author="晨旭", desire_priority=10)
class SignIn(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.sign_in_data = data_manager.get_data()
        logger.info("[SignIn] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        msg = e_context['context']['msg']

        user = msg['ActualNickName']

        if content == '签到':
            reply = Reply()
            reply.type = ReplyType.TEXT
            try:
                today = datetime.date.today()
                last_sign_in_date = self.sign_in_data.get(user, {}).get('last_sign_in_date')

                if last_sign_in_date and datetime.date.fromisoformat(last_sign_in_date) == today:
                    reply.content = f'{user}，你今天已经签到过了，不能再签到了哦！'
                else:
                    reply.content = self.update_data(user, today)
            except Exception as e:
                logger.error(f"签到异常: {str(e)}")
                reply.content = f"{user}，签到失败，请稍后再试。"

            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

        if content == '查看金币余额':
            reply = Reply()
            reply.type = ReplyType.TEXT
            try:
                sign_in_data = data_manager.get_data()
                days = sign_in_data.get(user, {}).get('days', 0)
                coins = sign_in_data.get(user, {}).get('coins', 0)
                reply.content = f"{user}，你已经连续签到{days}天了，目前一共有{coins}金币，呐，给你！"
            except Exception as e:
                logger.error(f"查看金币余额异常: {str(e)}")
                reply.content = f"{user}，查询金币余额失败，请稍后再试。"

                        e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

    def update_data(self, user, sign_in_date):
        if user not in self.sign_in_data:
            self.sign_in_data[user] = {'days': 0, 'last_sign_in_date': None, 'coins': 0, 'first_sign_in': True}

        # 更新连续签到天数和最后签到日期
        last_sign_in_date = self.sign_in_data[user]['last_sign_in_date']
        if last_sign_in_date and datetime.date.fromisoformat(last_sign_in_date) == sign_in_date - datetime.timedelta(days=1):
            self.sign_in_data[user]['days'] += 1
        else:
            self.sign_in_data[user]['days'] = 1

        self.sign_in_data[user]['last_sign_in_date'] = sign_in_date.isoformat()

        # 奖励金币
        coins = random.randint(10, 60)

        if self.sign_in_data[user]['first_sign_in']:
            self.sign_in_data[user]['first_sign_in'] = False
            coins += 40  # 首签奖励
            response = f'恭喜你抢到了首签！额外奖励40金币。你已经连续签到 {self.sign_in_data[user]["days"]} 天，本次签到奖励 {coins} 金币。'
        else:
            response = f'你已经连续签到 {self.sign_in_data[user]["days"]} 天，本次签到奖励 {coins} 金币。'

        self.sign_in_data[user]['coins'] += coins
        data_manager.save_data(self.sign_in_data)

        return response

    def get_help_text(self, **kwargs):
        help_text = "输入签到，我会进行签到\n输入查看金币余额，我会告诉你目前的金币总数\n"
        return help_text

    def on_stop(self):
        data_manager.save_data(self.sign_in_data)
        logger.info("[Goodbye] SignIn plugin stopped.")

