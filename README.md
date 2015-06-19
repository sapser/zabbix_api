#Python调用zabbix api

### 介绍
调用zabbix提供的api，实现自动化操作zabbix监控系统，目前只实现了几个基本功能，如获取host、group、template和proxy的信息，还有添加新的host。
该脚本需要argparse(python2.7及以上默认已装)和requests模块，不支持python3。
该脚本支持zabbix2.2和zabbix2.4的api接口。

用法：
```bash
shell> python zabbix_api.py -h
usage: zabbix_api.py [-h] {host,template,hostgroup,proxy} ...

Interact with zabbix.

positional arguments:
  {host,template,hostgroup,proxy}
                        子命令：
    host                host manipulate
    hostgroup           hostgroup manipulate
    template            template manipulate
    proxy               proxy manipulate

optional arguments:
  -h, --help            show this help message and exit
shell> 
shell> python zabbix_api.py hostgroup -h
usage: zabbix_api.py hostgroup [-h] -a {get} [-g GROUPS]

optional arguments:
  -h, --help            show this help message and exit
  -a {get}, --action {get}
                        指定对主机组执行什么操作
  -g GROUPS, --groups GROUPS
                        获取指定host group的信息

shell> python zabbix_api.py hostgroup -a get -g "Linux servers"
[{u'groupid': u'2', u'name': u'Linux servers'}]
```

