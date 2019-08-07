#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: api_object_detect.py
Desc: 图像目标识别 API 封装
Demo: 
    nohup python api_object_detect.py > log/api_object_detect.log &
    http://www.yanjingang.com:8026/piglab/image/object_detect?img_file=/home/work/project/darknet/data/dog.jpg&tag_img=0&tts_caption=pos
    http://www.yanjingang.com:8026/piglab/image/object_detect?img_file=/home/work/odp/webroot/yanjingang/www/piglab/upload/190807/1565170604787.jpeg&tag_img=0&tts_caption=pos

    ps aux | grep api_object_detect.py |grep -v grep| cut -c 9-15 | xargs kill -9
Author: yanjingang(yanjingang@mail.com)
Date: 2019/8/2 23:08
"""

import sys
import os
import cv2
import json
import logging
import tornado.ioloop
import tornado.web
import tornado.httpserver

# PATH
APP_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(APP_PATH+'/python/')
from dp import utils,tts
from dp.darknet import Darknet
#import darknet

IMG_PATH='/home/work/odp/webroot/yanjingang/www/piglab/'
IMG_URL='http://www.yanjingang.com/piglab/'

# init darknet目标检测模型tiny版初始化
darknet = Darknet(
        so_file=APP_PATH + '/libdarknet.so',
        #cfg_file=APP_PATH + '/cfg/yolov3.cfg',
        #model_file=APP_PATH + '/yolov3.weights',
        cfg_file=APP_PATH + '/cfg/yolov3-tiny.cfg',  # tiny低性能版
        model_file=APP_PATH + '/yolov3-tiny.weights',
        meta_file=APP_PATH + '/cfg/coco.data',  # 如果命令不在darknet目录执行时，需要把coco.data里的“names = data/coco.names”改为绝对路径
    )
'''
_cfg = str.encode(APP_PATH+"/cfg/yolov3-tiny.cfg")
_model = str.encode(APP_PATH+"/yolov3-tiny.weights")
_meta = str.encode(APP_PATH+"/cfg/coco.data")
net = darknet.load_net(_cfg, _model, 0)
meta = darknet.load_meta(_meta)
'''

# init tts
# 初始化语音合成
profile = {
    'appid': '9670645',
    'api_key': 'qg4haN8b2bGvFtCbBGqhrmZy',   # 请改为自己的百度语音APP的API Key
    'secret_key': '585d4eccb50d306c401d7df138bb02e7',
    'per': 4,  # 发音人选择 0：女生；1：男生；3：度逍遥；4：度丫丫
    'lan': 'zh',
}
_tts = tts.get_engine('baidu-tts', profile, cache_path=IMG_PATH + '/upload/tts/')


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
        tag_img = int(self.get_argument('tag_img', 0))
        tts_caption = self.get_argument('tts_caption', '')
        if img_file == '':
            return {'code': 2, 'msg': 'img_file不能为空'}
        res = []
        caption = ''

        try:
            # 图像目标检测
            #ret = darknet.detect(net, meta, str.encode(img_file))
            res = darknet.detect(img_file, tag=tag_img) #tag：是否在图片上标记目标位置
            #print(res)
            # 图像描述
            caption = darknet.caption(res)
            # 图像描述语音合成
            tts_url = ''
            if tts_caption:
                s = caption[tts_caption]
                voice_file = _tts._get_cache(s)
                if not voice_file:
                    voice_file = _tts.get_speech(s)
                    cache_file = _tts._set_cache(s, voice_file)
                    if cache_file:
                        voice_file = cache_file
                    
                tts_url = voice_file.replace(IMG_PATH, IMG_URL)
        except:
            logging.error('execute fail [' + img_file + '] ' + utils.get_trace())
            return {'code': 5, 'msg': 'detect fail'}

        # 组织返回格式
        url = img_file.replace(IMG_PATH, IMG_URL)
        return {'code': 0, 'msg': 'success', 'data': {'url': url, 'objects': res, 'caption': caption, 'tts_caption': tts_url}}


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

