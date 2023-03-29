# encoding:utf-8

from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger
import random
import datetime
import json

encoding='utf-8'
def get_data():
    try:
        return json.load(open('sign_in_data.json'))
    except:
        return {}

# 存储签到数据的字典
sign_in_data = get_data()
# 记录当天首签的标志
first_sign_in_today = False

def save_data(sign_in_data):
    try:
        json.dump(sign_in_data, open('sign_in_data.json','w'))
    except:
        logger.debug('save failed')

def update_data(user, sign_in_date):
    global first_sign_in_today
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
        return f'恭喜你抢到了本群首签！额外奖励80金币。你已经连续签到 {sign_in_data[user]["days"]} 天，本次签到奖励 {coins} 金币。'
    else:
        sign_in_data[user]['coins'] += coins
        save_data(sign_in_data)
        return f'你已经连续签到 {sign_in_data[user]["days"]} 天，本次签到奖励 {coins} 金币。'


@plugins.register(name="签到", desc="这是一个签到类插件", version="0.1", author="lanvent", desire_priority= 10)
class qiandao(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Hello] inited")

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return
        
        global first_sign_in_today
        content = e_context['context'].content
        msg = e_context['context']['msg']

        if e_context['context']['isgroup']:
            user = msg['ActualNickName'] + " from " + msg['User'].get('NickName', "Group")
        else:
            user = msg['User'].get('NickName', "My friend")

        # 判断是否为新的一天，重置首签标志
        today = datetime.date.today()
        if sign_in_data and sign_in_data[next(iter(sign_in_data))]['last_sign_in_date'] != today:
            first_sign_in_today = False

        if content == '签到':
            reply = Reply()
            reply.type = ReplyType.TEXT
            # reply.content = "Hi"
            try:
                if sign_in_data[user]['last_sign_in_date'] == today:
                    reply.content = f'{user}，你今天已经签到过了，不能再签到了哦！'
                else:
                    reply.content = update_data(user, today)
            except:
                reply.content = update_data(user, today)
            # itchat.send(reply, msg['FromUserName'])
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，进入默认处理逻辑，一般会覆写reply

        if content == '查看金币':
            reply = Reply()
            reply.type = ReplyType.TEXT
            # reply.content = "Hi"
            try:
                reply.content = f"{user}，你已经连续签到{sign_in_data[user]['days']}天了，目前一共有{sign_in_data[user]['coins']}金币，呐，给你！"
            except:
                reply.content = f"{user}，查询金币失败！"
            # itchat.send(reply, msg['FromUserName'])
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，进入默认处理逻辑，一般会覆写reply
            
        logger.debug("[QD] on_handle_context. content: %s" % content)


    def get_help_text(self, **kwargs):
        help_text = "输入签到，我会进行签到\n"
        return help_text
