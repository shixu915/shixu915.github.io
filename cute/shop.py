import json
import os
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger
from sign_in_data_manager import read_user_coins, update_user_coins
from bag_manager import read_user_bag, update_user_bag

# 定义商品列表及价格
shop_items = {
    "1元优惠券": {"price": 100, "desc": "使用该优惠券，可在指定商店消费时节省1元。"},
    "5折优惠券": {"price": 500, "desc": "使用该优惠券，在指定商店购物时享受5折优惠。"},
    "小月卡": {"price": 3000, "desc": "购买小月卡后，每天可领取100金币，持续30天。"},
    "逆天改命卡": {"price": 100, "desc": "使用逆天改命卡，可以在当天重新抽取运势。"},
    "好运连连卡": {"price": 100, "desc": "使用好运连连卡，一整天都会拥有好运气。"},
}

@plugins.register(name="Shop", desc="A simple shop plugin", version="0.1", author="lanvent", desire_priority= -1)
class Shop(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Shop] inited")

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        logger.debug("[Shop] on_handle_context. content: %s" % content)
        user_id = e_context['context']['msg']['FromUserName']

        if content == "查看商店":
            shop_content = "商品列表：\n"
            for item, item_data in shop_items.items():
                shop_content += f"{item} - {item_data['price']}金币 - {item_data['desc']}\n"
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = shop_content
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

        if content.startswith("购买"):
            item_to_buy = content[2:]
            if item_to_buy not in shop_items:
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = "很抱歉，您输入的商品不存在。请检查输入并重试。"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                user_coins = read_user_coins(user_id)
                item_price = shop_items[item_to_buy]["price"]
                if user_coins < item_price:
                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = f"很抱歉，您的金币余额不足。当前余额：{user_coins}金币"
                    e_context['reply'] = reply
                    e_context.action = EventAction.BREAK_PASS
                else:
                    user_coins -= item_price
                    update_user_coins(user_id, user_coins)

                    # 更新用户背包
                    user_bag = read_user_bag(user_id)
                    user_bag[item_to_buy] = user_bag.get(item_to_buy, 0) + 1
                    update_user_bag(user_id, user_bag)

                    reply = Reply()
                    reply.type = ReplyType.TEXT
                    reply.content = f"购买成功！您已购买{item_to_buy}，当前金币余额：{user_coins}金币"
                    e_context['reply'] = reply
                    e_context.action = EventAction.BREAK_PASS

        def get_help_text(self, **kwargs):
            help_text = "发送包含“查看商店”关键词的消息，我会为您提供一首歌曲，每天第一位猜中的成员可以获得100金币奖励。\n"
            return help_text
