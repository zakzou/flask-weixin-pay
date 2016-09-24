# 微信支付

参考文档 [https://pay.weixin.qq.com/wiki/doc/api/jsapi.php](https://pay.weixin.qq.com/wiki/doc/api/jsapi.php)

## 安装

使用pip安装

    pip install flask-weixin-pay

使用easy_install安装

    easy_install flask-weixin-pay

## 开始

首先引入库

    from flask_weixin_pay import WeixinPay, WeixinPayError

如果使用flask，需要依赖flask配置文件

    wxpay = WeixinPay()
    wxpay.init(app)

如果单独使用，需要传入配置文件

    config = {
        "WEIXIN_APP_ID": "wxapp_id",
        "WEIXIN_MCH_ID": "100000010",
        "WEIXIN_MCH_KEY": "128bad2e99a79312e25b2c162c9bab34",
        "WEIXIN_NOTIFY_URL": "http://www.example.com/pay/weixin/notify",
    }
    wxpay = WeixinPay(config)

创建订单

    out_trade_no = wx_pay.nonce_str
    try:
        raw = wx_pay.unified_order(openid="orU79wrXdrgNRNEZmoFD97rxGkb0", trade_type="JSAPI", body=u"测试", out_trade_no=out_trade_no, total_fee=1)
        print raw["prepay_id"]
    except WeixinPayError, e:
        print e.message

查询订单

    raw = wx_pay.order_query(out_trade_no=out_trade_no)

关闭订单

    raw = wx_pay.close_order(out_trade_no)

生成JSAPI需要调用的参数

    // total_fee 单位为分
    print wx_pay.jsapi(openid="orU79wrXdrgNRNEZmoFD97rxGkb0", body=u"测试", out_trade_no=out_trade_no, total_fee=1)

## 工具函数

签名

    wx_pay.sign(dict(openid="123"))

32位随机字符串

    wx_pay.nonce_str


验证签名

    wx_pay.check(dict(openid="123", sign="SIGN"))
