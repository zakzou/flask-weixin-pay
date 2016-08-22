# -*- coding: utf-8 -*-


import json

from flask import Flask, request

from flask.ext.weixin_pay import WeixinPay, WeixinPayError


app = Flask(__name__)


config = {
    "WEIXIN_APP_ID": "wxapp_id",
    "WEIXIN_MCH_ID": "100000010",
    "WEIXIN_MCH_KEY": "138bad2e99a79312e25b2c162c9bab34",
    "WEIXIN_NOTIFY_URL": "http://www.example.com/pay/weixin/notify",
}
app.config.update(config)


wx_pay = WeixinPay()
wx_pay.init_app(app)


@app.route("/pay/create")
def pay_create():
    """
    微信JSAPI创建统一订单，并且生成参数给JS调用
    """
    try:
        out_trade_no = wx_pay.nonce_str
        raw = wx_pay.jsapi(openid="openid", body=u"测试", out_trade_no=out_trade_no, total_fee=1)
        return json.loads(raw)
    except WeixinPayError, e:
        print e.message
        return e.message, 400


@app.route("/pay/notify")
def pay_notify():
    """
    微信异步通知
    """
    data = wx_pay.to_dict(request.data)
    if not wx_pay.check(data):
        return wx_pay.reply("签名验证失败", False)
    # 处理业务逻辑
    return wx_pay.reply("OK", True)


if __name__ == '__main__':
    app.run()
