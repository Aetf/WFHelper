import os
import re
import random
import sys
import subprocess as sp

from ppadb.client import Client as AdbClient
from utils.LogUtil import Log

from collections import namedtuple

Size = namedtuple("Size", [
    'width',
    'height'
])

class CLIADB:
    def __init__(self, serial):
        self.serial = serial

    def shell(self, *cmd):
        return sp.check_output(['adb', '-s', self.serial, 'shell', *[str(c) for c in cmd]])

    def screencap(self):
        return self.shell('screencap', '-p')
    def input_tap(self, x, y):
        return self.shell('input', 'tap', x, y)
    def input_swip(self, start_x, start_y, end_x, end_y, duration):
        return self.shell('input', 'swipe', start_x, start_y, end_x, end_y, duration)

    SIZE_RE = b'Physical size:\s([\d]+)x([\d]+)'
    def wm_size(self):
        result = self.shell("wm size")
        match = re.search(self.SIZE_RE, result)

        if match:
            return Size(int(match.group(1)), int(match.group(2)))
        else:
            return None

    def get_properties(self):
        result = self.shell("getprop").decode('utf-8')
        result_pattern = r"^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"

        properties = {}
        for line in result.split('\n'):
            m = re.match(result_pattern, line)
            if m:
                properties[m.group(1)] = m.group(2)

        return properties


class ADBUtil:

    device = None
    adb = None

    def getScreen(self, savePath=None):
        currentframe = None

        if self.device is not None:
            currentframe = self.device.screencap()

        if savePath is not None and len(currentframe) != 0 and currentframe is not None:
            dirs = os.path.dirname(savePath)

            if not os.path.exists(dirs):
                os.makedirs(dirs)

            with open(savePath, "wb") as f:
                f.write(currentframe)

        return currentframe

    def touchScreen(self, area):
        if self.device is not None:
            self.device.input_tap(
                random.randrange(round(float(area[0])), round(float(area[2]))),
                random.randrange(round(float(area[1])), round(float(area[3])))
            )

    def swipeScreen(self, x1, y1, x2, y2):
        if self.device is not None:
            self.device.input_swipe(x1, y1, x2, y2, int(random.uniform(0.5, 1.0) * 1000))

    def selectSerial(self):
        devices = self.adb.devices()
        if len(devices) == 0:
            print("未检测到设备连接")
            serial = "127.0.0.1:5555"
            serial = input("请输入设备IP和端口进行连接，默认127.0.0.1:5555\n")
            ip, port = serial.split(":")
            self.adb.remote_connect(str(ip), int(port))
        elif len(devices) == 1:
            Log.info("检测到唯一已连接的设备")
            serial = devices[0].serial
        else:
            print("检测到已连接的设备，请输入序号指定要连接的设备:")
            for i in range(0, len(devices)):
                print("[{}] - {}".format(i, devices[i].serial))
            try:
                print("[-1] - 手动输入设备ip和端口进行连接")

                index = input()
                if index is None or index == "":
                    index = 0
                else:
                    index = int(index)

                if index == -1:
                    serial = "127.0.0.1:5555"
                    serial = input("请输入设备IP和端口进行连接，默认127.0.0.1:5555\n")
                    ip, port = serial.split(":")
                    self.adb.remote_connect(str(ip), int(port))
                else:
                    serial = devices[index].serial
            except ValueError:
                Log.error("请输入正确的序号!!!")
                sys.exit()
        return serial

    def setDevice(self, serial):
        # 用户没有指定设备
        if serial is None:
            return

        # self.device = self.adb.device(serial)
        self.device = CLIADB(serial)
        self.logDeviceInfo()

    def logDeviceInfo(self):
        try:
            Log.info("设备serial : {}".format(self.device.serial))
            props = self.device.get_properties()
            Log.info("设备名称 : {}".format(props["ro.product.device"]))
            Log.info("制造商 : {}".format(props["ro.product.manufacturer"]))
            Log.info("model : {}".format(props["ro.product.model"]))
            Log.info("CPU : {}".format(props["ro.product.cpu.abi"]))
            Log.info("系统版本 : {}".format(props["ro.build.version.release"]))
            size = self.device.wm_size()
            Log.info("分辨率 : {}x{}".format(size[1], size[0]))
            # print(props)
        except ValueError:
            Log.error("获取设备信息失败")
            Log.info(f"{props=}")
        except KeyError:
            Log.error("获取设备信息失败")
            Log.info(f"{props=}")

    def __init__(self):
        if getattr(sys, "frozen", None):
            basedir = sys._MEIPASS
        else:
            basedir = os.path.dirname(__file__)
        adbPath = os.path.join(basedir, "") + r"adb;"
        os.environ['PATH'] = adbPath + os.environ['PATH']
        os.system("adb start-server")
        self.adb = AdbClient(host="127.0.0.1", port=5037)


adbUtil = ADBUtil()
