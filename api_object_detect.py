#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: api_object_detect.py
Desc: 图像目标识别 API 封装
Demo: 
    nohup python api_object_detect.py > log/api_object_detect.log &
    http://www.yanjingang.com:8026/piglab/image/object_detect?img_file=/home/work/project/darknet/data/dog.jpg

    ps aux | grep api_object_detect.py |grep -v grep| cut -c 9-15 | xargs kill -9
Author: yanjingang(yanjingang@mail.com)
Date: 2019/8/2 23:08
"""

import sys
import os
import json
import logging
import tornado.ioloop
import tornado.web
import tornado.httpserver

# PATH
APP_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(APP_PATH+'/python/')
from dp import utils
import darknet


# darknet目标检测模型tiny版初始化
_cfg = str.encode(APP_PATH+"/cfg/yolov3-tiny.cfg")
_model = str.encode(APP_PATH+"/yolov3-tiny.weights")
_meta = str.encode(APP_PATH+"/cfg/coco.data")
net = darknet.load_net(_cfg, _model, 0)
meta = darknet.load_meta(_meta)


class ApiObjectDetect(tornado.web.RequestHandler):
    """API逻辑封装"""

    def get(self):
        """get请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '查询失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                      + str(result['code']) + '][' + str(result['msg']) + '][' + str(result['data']) + ']')
        self.write(json.dumps(result))

    def post(self):
        """post请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '查询失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                      + str(result['code']) + '][' + str(result['msg']) + ']')
        self.write(json.dumps(result))

    def execute(self):
        """执行业务逻辑"""
        logging.info('API REQUEST INFO[' + self.request.path + '][' + self.request.method + ']['
                      + self.request.remote_ip + '][' + str(self.request.arguments) + ']')
        img_file = self.get_argument('img_file', '')
        if img_file == '':
            return {'code': 2, 'msg': 'img_file不能为空'}
        res = []

        try:
            # 图像目标检测
            ret = darknet.detect(net, meta, str.encode(img_file))
            #print(ret)
            if not ret:
                logging.error('execute fail [' + img_file + '] ')
                return {'code': 4, 'msg': '查询失败'}
            # 数据格式化
            for o in ret:
                res.append({'label': str(o[0], 'utf-8'), 'weight': o[1], 'rect': o[2]})
            #print(res)
        except:
            logging.error('execute fail [' + img_file + '] ' + utils.get_trace())
            return {'code': 5, 'msg': '查询失败'}

        # 组织返回格式
        return {'code': 0, 'msg': 'success', 'data': res}


if __name__ == '__main__':
    """服务入口"""
    port = 8026

    # log init
    log_file = ApiObjectDetect.__name__.lower()  # + '-' + str(os.getpid())
    utils.init_logging(log_file=log_file, log_path=APP_PATH)
    print("log_file: {}".format(log_file))

    # 路由
    app = tornado.web.Application(
        handlers=[
            (r'/piglab/image/object_detect', ApiObjectDetect)
            ]
    )

    # 启动服务
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

