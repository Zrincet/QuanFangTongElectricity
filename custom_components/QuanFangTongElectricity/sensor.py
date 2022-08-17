#!/usr/bin/env python 
# -*- coding:utf-8 -*-
"""
A component which allows you to parse QuanFangTong get electricity info

For more details about this component, please refer to the documentation at
https://github.com/zrincet/QuanFangTongElectricity/

"""
import logging
import asyncio
import voluptuous as vol
from datetime import timedelta
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME)
from homeassistant.const import (CONF_CODE)
from homeassistant.const import (CONF_BASE)
from requests import request
import requests
from requests.exceptions import (
    ConnectionError as ConnectError, HTTPError, Timeout)
from bs4 import BeautifulSoup
import json

__version__ = '1.0.0'
_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['requests', 'beautifulsoup4']

COMPONENT_REPO = 'https://github.com/zrincet/QuanFangTongElectricity/'
SCAN_INTERVAL = timedelta(seconds=3600)
CONF_OPTIONS = "options"
ATTR_UPDATE_TIME = "更新时间"
# ATTR_ROOM_NAME = "房间名称"

OPTIONS = dict(ele_today=["QuanFangTong_ele_today", "今日电量", "mdi:flash", "kW·h"],
               ele_month=["QuanFangTong_ele_month", "本月电量", "mdi:flash", "kW·h"],
               balance=["QuanFangTong_balance", "剩余余额", "mdi:wallet", "￥"])

CONF_PHONE = "phone"
CONF_PASSWORD = "password"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PHONE): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_OPTIONS, default=[]): vol.All(cv.ensure_list, [vol.In(OPTIONS)]),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    _LOGGER.info("async_setup_platform sensor BeeSCRM_system electricity info Sensor")
    dev = []
    for option in config[CONF_OPTIONS]:
        dev.append(BeeSCRMElectricitySensor(config[CONF_PHONE], config[CONF_PASSWORD], option))

    async_add_devices(dev, True)


class BeeSCRMElectricitySensor(Entity):
    def __init__(self, phone, password, option):
        self._phone = phone
        self._password = password
        self._key = None
        self._state = None

        self._ele_today = None
        self._ele_month = None
        self._price = None
        self._updateTime = None
        self._roomName = None

        self._object_id = OPTIONS[option][0]
        self._friendly_name = OPTIONS[option][1]
        self._icon = OPTIONS[option][2]
        self._unit_of_measurement = OPTIONS[option][3]
        self._type = option

    def update(self):
        import time
        from datetime import datetime
        now = datetime.now()

        _LOGGER.info("QuanFangTongElectricitySensor start updating data.")
        try:
            self._key = self.login(self._phone, self._password)
        except (ConnectError, HTTPError, Timeout, ValueError) as error:
            time.sleep(0.01)
            _LOGGER.error("Unable to login to QuanFangTong. %s", error)

        try:
            url = 'https://qft.quanfangtongvip.com/api/wechat/electricity/getElectricityData'
            headers = {
                'token': self._key
            }
            re_json = requests.get(url, headers=headers).json()['data']
            self._ele_today = re_json['today']
            self._ele_month = re_json['month']
            self._price = re_json['blnance']
            self._updateTime = now.strftime("%Y-%m-%d %H:%M:%S")

            if self._type == "ele_today":
                self._state = self._ele_today
            elif self._type == "ele_month":
                self._state = self._ele_month
            elif self._type == "balance":
                self._state = self._price
        except Exception as e:
            _LOGGER.error("Something wrong in QuanFangTong. %s", e)

    def login(self, phone, password):
        url = "https://qft.quanfangtongvip.com/api/wechat/tenant/login"
        data = {
            "account": f"{phone}",
            "password": password,
            "companyUrl": "zjhj",
            "wechatTerminal": 1
        }
        a = requests.post(url, json=data)
        return a.json()['data'][0]['accessToken']

    @property
    def name(self):
        return self._friendly_name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon
    @property
    def unique_id(self):
        return self._object_id

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        return {
            ATTR_UPDATE_TIME: self._updateTime,
        }
