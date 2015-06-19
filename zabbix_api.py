#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import json
import argparse
import requests


class ZABBIX_API(object):
    """zabbix api调用类"""
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def call_api(self, data):
        headers = {'content-type': 'application/json'}
        res = requests.post(self.url, data=json.dumps(data), headers=headers)
        return res.json()

    def auth(self):
        """调用其他接口前先验证，获取token"""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "user.login",
            "params": {
                "user": self.user,
                "password": self.password, 
            },
            "auth": None,
        }
        res = self.call_api(data)
        if res.get("result"):
            return res["result"]

    def host_create(self, host, groups=u"Linux servers", templates="Template OS Linux", proxy=None):
        """
        添加一个监控主机
        @params
          groups: 该主机所属主机组，可以添加多个，以逗号隔开
          templates: 该主机链接的模板，可以添加多个模板，以逗号隔开
        """
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "auth": self.auth(),
            "method": "host.create",
            "params": {
                "host": host,
                "interfaces": [{
                    "type": 1,
                    "main": 1,
                    "useip": 1,
                    "ip": host,
                    "dns": "",
                    "port": "10050",
                }],
            },
        }
        params = data["params"]
        #指定主机所属组
        groupids = self.hostgroup_get(groups)
        if groupids:
            groupids = [{"groupid": g["groupid"]} for g in groupids]
            params["groups"] = groupids
        #指定主机链接的模板
        templateids = self.template_get(templates)
        if templateids:
            templateids = [{"templateid": t["templateid"]} for t in templateids]
            params["templates"] = templateids
        #是否通过zabbix proxy监控
        if proxy:
            proxyid = self.proxy_get(proxy)
            if proxyid:
                proxyid = proxyid[0]["proxyid"]
                params["proxy_hostid"] = proxyid

        res = self.call_api(data)
        if res.get("error"):
            faild("%s: %s" % (host, res["error"]["data"]))
        else:
            success("%s: create success!" % host)

    def host_get(self):
        """获取所有主机及其监控状态"""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "auth": self.auth(),
            "method": "host.get",
            "params": {
                "output": [
                    "host",
                    "available",
                ],
            },
        }
        res = self.call_api(data)
        if res.get("result"):
            #以字典格式返回主机IP和对应监控状态：0为unknown、1为正常、2为异常
            hosts = dict([(h["host"],h["available"]) for h in res["result"]])
            return hosts
        else:
            faild("Error: %s" % res["error"]["data"])

    def hostgroup_get(self, groups=None):
        """获取主机组及其对应id"""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "auth": self.auth(),
            "method": "hostgroup.get",
            "params": {
                "output": [
                    "name",
                    "groupid",
                ],
            },
        }
        if groups:
            filter = data["params"]["filter"] = {}
            filter["name"] = groups.split(",") 
        res = self.call_api(data)
        if 'result' in res:
            #主机组不存在，返回空列表，不会报错！
            return res["result"]
        else:
            faild("Error: %s" % res["error"]["data"])

    def proxy_get(self, proxies=None):
        """获取zabbix proxy对应id"""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "auth": self.auth(),
            "method": "proxy.get",
            "params": {
                "output": [
                    "host",
                    "proxyid",
                ],
            },
        }
        if proxies:
            filter = data["params"]["filter"] = {}
            filter["host"] = proxies.split(",") 
        res = self.call_api(data)
        if 'result' in res:
            #代理不存在，返回空列表，不会报错！
            return res["result"]
        else:
            faild("Error: %s" % res["error"]["data"])

    def template_get(self, templates=None):
        """获取模板及对应模板id"""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "auth": self.auth(),
            "method": "template.get",
            "params": {
                "output": [
                    "name",
                    "templateid",
                ],
            },
        }
        if templates:
            filter = data["params"]["filter"] = {}
            filter["host"] = templates.split(",") 
        res = self.call_api(data)
        if 'result' in res:
            #模板不存在，返回空列表，不会报错！
            return res["result"]
        else:
            faild("Error: %s" % res["error"]["data"])


def success(msg):
    print "\033[32m%s\033[0m" % msg

def faild(msg):
    sys.stderr.write("\033[31m%s\033[0m\n" % msg)
    #sys.exit(1)

def cmdline_parse():
    parser = argparse.ArgumentParser(description=u"Interact with zabbix.")
    subparsers = parser.add_subparsers(help=u"子命令：")
    #host
    host_parser = subparsers.add_parser('host', help='host manipulate')
    host_parser.add_argument('-a', "--action", action='store', default="get", dest="host_action",
                             choices=("get", "create"), required=True, help=u"指定对主机执行什么操作")
    host_parser.add_argument('-i', "--hosts", action='store', default=None, dest="hosts",
                             help=u"要添加的主机，多个值以逗号分隔，和\"-a create\"一起使用")
    host_parser.add_argument('-g', "--groups", action='store', default=u"Linux servers", dest="groups",
                             help=u"添加主机时，指定主机所属的组，多个组以逗号分隔")
    host_parser.add_argument('-t', "--templates", action='store', default="Template OS Linux", dest="templates",
                             help=u"添加主机时，指定主机要链接的模板，多个模板以逗号分隔")
    host_parser.add_argument('-p', "--proxy", action='store', default=None, dest="proxy",
                             help=u"添加主机时，主机是否通过给定的zabbix proxy监控")
    #host group
    hostgroup_parser = subparsers.add_parser('hostgroup', help='hostgroup manipulate')
    hostgroup_parser.add_argument('-a', "--action", action='store', default="get", dest="hostgroup_action",
                             choices=("get",), required=True, help=u"指定对主机组执行什么操作")
    hostgroup_parser.add_argument('-g', "--groups", action='store', default=None, dest="groups",
                             help=u"获取指定host group的信息")
    #template
    template_parser = subparsers.add_parser('template', help='template manipulate')
    template_parser.add_argument('-a', "--action", action='store', default="get", dest="template_action",
                             choices=("get",), required=True, help=u"指定对模板执行什么操作")
    template_parser.add_argument('-t', "--templates", action='store', default=None, dest="templates",
                             help=u"获取指定模板的信息")
    #proxy
    proxy_parser = subparsers.add_parser('proxy', help='proxy manipulate')
    proxy_parser.add_argument('-a', "--action", action='store', default="get", dest="proxy_action",
                             choices=("get",), required=True, help=u"指定对proxy执行什么操作")
    proxy_parser.add_argument('-p', "--proxies", action='store', default=None, dest="proxies",
                             help=u"获取指定zabbix proxy的信息")

    args = parser.parse_args()
    return args

def main(url, user="admin", password="zabbix"):
    zbxapi = ZABBIX_API(url, user, password)
    args = cmdline_parse()
    if hasattr(args, "host_action"):
        if args.host_action == "create":
            if not args.hosts:
                faild("Error: Must provide an ip(-i HOSTS) with \"-a create\" option!")
            for host in args.hosts.split(","):
                zbxapi.host_create(host.strip(), args.groups, args.templates, args.proxy)
        elif args.host_action == "get":
            print zbxapi.host_get()
    elif hasattr(args, "hostgroup_action"):
        print zbxapi.hostgroup_get(args.groups)
    elif hasattr(args, "template_action"):
        print zbxapi.template_get(args.templates)
    elif hasattr(args, "proxy_action"):
        print zbxapi.proxy_get(args.proxies)


if __name__ == "__main__":
    #不设置默认编码为utf8，argparse处理中文会出现编码问题
    reload(sys)
    sys.setdefaultencoding('utf-8')

    main("http://zabbixpt.uuzu.com/api_jsonrpc.php")

