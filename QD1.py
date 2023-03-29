from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger
import random
import datetime
import json

encoding = 'utf-8'


def get_data():
    try:
        return json.load(open('sign_in_data.json'))
    except:
        return {}


def save_data(sign_in_data):
    try:
        json.dump(sign_in_data, open('sign_in_data.json', 'w'))
    except:
        logger.debug('save failed')


def update_data(user, sign_in_date, sign_in_data, first_sign_in_today):
    if user not in sign_in_data:
        sign_in_data[user] = {'days': 0, 'last_sign_in_date': None, 'coins': 0}

    # 更新连续签到天数
    if sign_in_data[user]['last_sign_in_date'] == sign_in_date - datetime.timedelta(days=1):
        sign_in_data[user]['days'] += 1
    else:
        sign_in_data[user]['days'] = 1

    # 更新最后签到日期
    sign_in_data[user]['last_sign_in_date'] = sign_in_date

    # 奖励金币
    coins = random.randint(20, 80)
    if not first_sign_in_today:
        first_sign_in_today = True
        coins += 80  # 首签奖励
    sign_in_data[user]['coins'] += coins
    save_data(sign_in_data)
    if not first_sign_in_today:
        return f'你已经连续签到 {sign_in_data[user]["days"]} 天，本次签到奖励 {coins} 金币。'
    else:
        return f'恭喜你抢到了本群首签！额外奖励80金币。你已经连续签到 {sign_in_data[user]["days"]} 天，本次签到奖励 {coins} 金币。'


@plugins.register(name="签到", desc="这是一个签到类插件", version="0.1", author="lanvent", desire_priority= 10)
class qiandao(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.sign_in_data = get_data()
        self.first_sign_in_today = False
        logger.info("[Hello] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        msg = e_context['context']['msg']

        if e_context['context']['isgroup']:
            user = msg['ActualNickName'] + " from " + msg['User'].get('NickName', "Group")
        else:
            user = msg['User'].get('NickName', "My friend")

        # 判断是否为新的一天，重置首签标志
        today = datetime.date.today()
        if self.sign_in_data and self.sign_in_data.get(user, {}).get('last_sign_in_date') != today:
            self.first_sign_in_today = False

        if content == '签到':
            reply = Reply()
            reply.type = ReplyType.TEXT
            try:
                if self.sign_in_data.get(user, {}).get('last_sign_in_date') == today:
                    reply.content = f'{user}，你今天已经签到过了，不能再签到了哦！'
                else:
                    reply.content = update_data(user, today, self.sign_in_data, self.first_sign_in_today)
            except:
                reply.content = update_data(user, today, self.sign_in_data, self.first_sign_in_today)
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

        if content == '查看金币':
            reply = Reply()
            reply.type = ReplyType.TEXT
            try:
                reply.content = f"{user}，你已经连续签到{self.sign_in_data.get(user, {}).get('days', 0)}天了，目前一共有{self.sign_in_data.get(user, {}).get('coins', 0)}金币，呐，给你！"
            except:
                reply.content = f"{user}，查询金币失败！"
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

        logger.debug("[QD] on_handle_context. content: %s" % content)

    def get_help_text(self, **kwargs):
        help_text = "输入签到，我会进行签到\n"
        return help_text

    def on_stop(self):
        save_data(self.sign_in_data)
        logger.info("[Goodbye] QD plugin stopped.") 

