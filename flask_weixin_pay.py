# -*- coding: utf-8 -*-


import time
import string
import random
import hashlib
import urllib2

from collections import namedtuple

try:
    from flask import current_app, request
except ImportError:
    current_app = None
    request = None

try:
    from lxml import etree
except ImportError:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree


__all__ = ("WeixinPay", "WeixinPayError")
__version__ = "0.1.0"
__author__ = "Weicheng Zou <zwczou@gmail.com>"


StandaloneApplication = namedtuple('StandaloneApplication', ['config'])


class WeixinPayError(Exception):

    def __init__(self, msg):
        super(WeixinPayError, self).__init__(msg)


class WeixinPay(object):

    def __init__(self, app=None):
        self.opener = urllib2.build_opener(urllib2.HTTPSHandler())

        if isinstance(app, dict):
            app = StandaloneApplication(config=app)

        if app is None:
            self.app = current_app
        else:
            self.init_app(app)
            self.app = app

    def init_app(self, app):
        app.config.setdefault("WEIXIN_APP_ID", "")
        app.config.setdefault("WEIXIN_MCH_ID", "")
        app.config.setdefault("WEIXIN_MCH_KEY", "")
        app.config.setdefault("WEIXIN_NOTIFY_URL", "")

    def _get_app_id(self):
        return self.app.config["WEIXIN_APP_ID"]

    def _set_app_id(self, app_id):
        self.app.config["WEIXIN_APP_ID"] = app_id

    app_id = property(_get_app_id, _set_app_id)
    del _set_app_id, _get_app_id

    def _get_mch_id(self):
        return self.app.config["WEIXIN_MCH_ID"]

    def _set_mch_id(self, mch_id):
        self.app.config["WEIXIN_MCH_ID"] = mch_id

    mch_id = property(_get_mch_id, _set_mch_id)
    del _get_mch_id, _set_mch_id

    def _get_mch_key(self):
        return self.app.config["WEIXIN_MCH_KEY"]

    def _set_mch_key(self, mch_key):
        self.app.config["WEIXIN_MCH_KEY"] = mch_key

    mch_key = property(_get_mch_key, _set_mch_key)
    del _get_mch_key, _set_mch_key

    def _get_notify_url(self):
        return self.app.config["WEIXIN_NOTIFY_URL"]

    def _set_notify_url(self, notify_url):
        self.app.config["WEIXIN_NOTIFY_URL"] = notify_url

    notify_url = property(_get_notify_url, _set_notify_url)
    del _get_notify_url, _set_notify_url

    @property
    def remote_addr(self):
        if request is not None:
            return request.remote_addr
        return ""

    @property
    def nonce_str(self):
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(32))

    to_utf8 = lambda self, x: x.encode("utf-8") if isinstance(x, unicode) else x

    def sign(self, raw):
        raw = [(k, str(raw[k]) if isinstance(raw[k], int) else raw[k]) \
               for k in sorted(raw.keys())]
        s = "&".join("=".join(kv) for kv in raw if kv[1])
        s += "&key={0}".format(self.mch_key)
        return hashlib.md5(self.to_utf8(s)).hexdigest().upper()

    def verify(self, content):
        raw = self.to_dict(content)
        if raw["sign"] == self.sign(raw):
            return True
        return False

    def to_xml(self, raw):
        s = ""
        for k, v in raw.iteritems():
            s += "<{0}>{1}</{0}>".format(k, self.to_utf8(v), k)
        return "<xml>{0}</xml>".format(s)

    def to_dict(self, content):
        raw = {}
        root = etree.fromstring(content)
        for child in root:
            raw[child.tag] = child.text
        return raw

    def fetch(self, url, data):
        req = urllib2.Request(url, data=self.to_xml(data))
        try:
            resp = self.opener.open(req, timeout=20)
        except urllib2.HTTPError, e:
            resp = e
        return self.to_dict(resp.read())

    def unified_order(self, **data):
        """
        统一下单
        out_trade_no、body、total_fee、trade_type必填
        app_id, mchid, nonce_str自动填写
        user_ip 在flask框架下可以自动填写
        """
        url = "https://api.mch.weixin.qq.com/pay/unifiedorder"

        # 必填参数
        if "out_trade_no" not in data:
            raise WeixinPayError("缺少统一支付接口必填参数out_trade_no")
        if "body" not in data:
            raise WeixinPayError("缺少统一支付接口必填参数body")
        if "total_fee" not in data:
            raise WeixinPayError("缺少统一支付接口必填参数total_fee")
        if "trade_type" not in data:
            raise WeixinPayError("缺少统一支付接口必填参数trade_type")

        # 关联参数
        if data["trade_type"] == "JSAPI" and "openid" not in data:
            raise WeixinPayError("trade_type为JSAPI时，openid为必填参数")
        if data["trade_type"] == "NATIVE" and "product_id" not in data:
            raise WeixinPayError("trade_type为NATIVE时，product_id为必填参数")
        data.setdefault("appid", self.app_id)
        data.setdefault("mch_id", self.mch_id)
        data.setdefault("notify_url", self.notify_url)
        data.setdefault("nonce_str", self.nonce_str)
        data.setdefault("spbill_create_ip", self.remote_addr)
        data.setdefault("sign", self.sign(data))

        row = self.fetch(url, data)
        if row["return_code"] == "FAIL":
            raise WeixinPayError(row["return_msg"])
        err_msg = row.get("err_code_des")
        if err_msg:
            raise WeixinPayError(err_msg)
        return row["prepay_id"]

    def jsapi(self, **kwargs):
        prepay_id = self.unified_order(**kwargs)
        package = "prepay_id={0}".format(prepay_id)
        timestamp = int(time.time())
        nonce_str = self.nonce_str
        raw = dict(appId=self.app_id, timeStamp=timestamp,
                   nonceStr=nonce_str, package=package, signType="MD5")
        sign = self.sign(raw)
        return dict(package=package, appId=self.app_id,
                    timeStamp=timestamp, nonceStr=nonce_str, sign=sign)

    def order_query(self, **data):
        """
        订单查询
        out_trade_no, transaction_id至少填一个
        appid, mchid, nonce_str不需要填入
        """
        url = "https://api.mch.weixin.qq.com/pay/orderquery"

        if "out_trade_no" not in data and "transaction_id" not in data:
            raise WeixinPayError("订单查询接口中，out_trade_no、transaction_id至少填一个")
        data.setdefault("appid", self.app_id)
        data.setdefault("mch_id", self.mch_id)
        data.setdefault("nonce_str", self.nonce_str)
        data.setdefault("sign", self.sign(data))

        row = self.fetch(url, data)
        if row["return_code"] == "FAIL":
            raise WeixinPayError(row["return_msg"])
        return row

    def close_order(self, out_trade_no):
        """
        关闭订单
        transaction_id必填
        appid, mchid, nonce_str不需要填入
        """
        url = "https://api.mch.weixin.qq.com/pay/closeorder"

        data = {}
        data.setdefault("out_trace_no", out_trade_no)
        data.setdefault("appid", self.app_id)
        data.setdefault("mch_id", self.mch_id)
        data.setdefault("nonce_str", self.nonce_str)
        data.setdefault("sign", self.sign(data))

        row = self.fetch(url, data)
        if row["return_code"] == "FAIL":
            raise WeixinPayError(row["return_msg"])
        return row
