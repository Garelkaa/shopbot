import datetime
import logging
import string
import secrets
import aiohttp
from models import *

session = aiohttp.ClientSession()  # Спрятать в функцию/класс


async def get_btc_price(amount):
    req = await session.get("https://blockchain.com/tobtc?currency=RUB&value=" + str(amount))
    return await req.text()


# async def makeQiwiInvoice(amount):
#     billId = random.randrange(1, 10000000000000000)
#     dateNow = datetime.datetime.now() + datetime.timedelta(hours=3)
#     expirationDateTime = dateNow.strftime('%Y-%m-%dT%H:%M:%S+03:00')
#     amount = str(round(Decimal(float(amount)), 2))  # прости меня, господи
#     secret_key = (await paySystemConfig.get(key="secret_key")).value
#     theme_code = (await paySystemConfig.get(key="theme_code")).value
#     data = {"amount": {"currency": "RUB", "value": amount}, "comment": "Оплата товара",
#             "expirationDateTime": expirationDateTime, "customFields": {"themeCode": theme_code}}
#     headers = {"Authorization": "Bearer " + secret_key, "Accept": "application/json",
#                "Content-Type": "application/json"}
#     req = await session.put("https://api.qiwi.com/partner/bill/v1/bills/{0}".format(str(billId)), data=json.dumps(data),
#                             headers=headers)
#     if req.status == 200:
#         result = await req.json()
#         return (result["payUrl"], result["billId"])
#     else:
#         await bot.send_message(admin, "Отпиши ТСу! Ошибка при создании счета. Код ошибки: " + str(req.status))
#         return False

# async def getStats(time):
#     timedict = {"час": 60 * 60, "день": 60 * 60 * 24, "неделя": 60 * 60 * 24 * 7, "месяц": 60 * 60 * 24 * 31,
#                 "все": 1000000000}
#     timestamp = await getTimestamp() - timedict[time]
#     registered = await User.filter(timestamp__gt=timestamp)
#     return len(registered)


    # TODO разобраться с этим
    # async def order_text(self, user, method, position, order):
    #     text = await get_text("orderMsg")
    #     positiontext = await position_text(position)
    #     price = int(position.price)
    #     if user.workerid:
    #         worker = await Worker.get(id=user.workerid)
    #         price = int(position.price * (100 - worker.discount) / 100)
    #         await Order.filter(id=order.id).update(price=price)
    #     # if method == 1:
    #     # 	paymsg = (await paySystemConfig.get(key="qiwi_pay_msg")).value
    #     # 	paystr = (await paySystemConfig.get(key="qiwi_pay_str")).value
    #     # 	invoice = await makeQiwiInvoice(price)
    #     # 	topay = invoice[0]
    #     # 	await Order.filter(id = order.id).update(invoiceid = invoice[1])
    #     if method in [1, 2, 3]:
    #         # manualMethods = {2: "card", 3: "btc"}
    #         manualMethods = {1: "qiwi", 2: "card", 3: "btc"}
    #         methodstr = manualMethods[method]
    #         paymsg = (await paySystemConfig.get(key=f"{methodstr}_pay_msg")).value.format(price)
    #     # paystr = (await paySystemConfig.get(key=f"{methodstr}_pay_str")).value
    #     # topay = "<code>" + (await paySystemConfig.get(key=f"{methodstr}_to_pay")).value + "</code>"
    #     else:
    #         return
    #     # if method == 3: price = await getBtcPrice(price)
    #     # paystr = paystr + " " + topay
    #     # text = text.format(positiontext, order.id, paymsg, paystr, price)
    #     text = text.format(positiontext, order.id, paymsg)
    #     return text



    # async def order_message(self, user, event):
    #     method_id = event.data.replace(b'method_', b'')
    #     if method_id not in ['1', '2', '3']:
    #         return
    #     position_id = user.laststep.replace('methods_', '')
    #     if '_' in position_id:
    #         return
    #     position = await Position.filter(id=position_id).first()
    #     worker_id = user.workerid
    #     # TODO разобраться с этим
    #     # worker = await Position.filter(id=worker_id).first() # ЧО ЭТО
    #     # method = awai paySystem.filter(id=methodid).first() # Нахуя это
    #     order = await Order.create(id=''.join(secrets.choice(string.digits) for _ in range(10)),
    #                                userid=user.id,
    #                                workerid=worker_id,
    #                                positionid=position_id,
    #                                price=position.price,
    #                                paysystemid=method_id)
    #     text = await order_text()
    #     keyboard = await kb.generate_order_inline(user)
    #     await event.edit(text, buttons=keyboard)
    # 
