import sys
import argparse
import yaml
import re
from collections import namedtuple

class ConfigParser():
    module = namedtuple("mod", "name, option, help, port")    
    args = {
        "vrouter": module("--vrouter", "-vr","contrail-vrouter", "8085"),
        "cconfig": module("--cconfig", "-cfg", "contrail-config", "8084"),
        "ccontrol": module("--ccontrol", "-cnt", "contrail-control", "8083"),
        "canalytics": module("--canalytics", "-can", "contrail-analytics", "8090")
    }
    @classmethod
    def parse_all_args(cls, args=None):
        conf_parser = argparse.ArgumentParser()
        conf_parser.add_argument("-c", "--config",
                                 help="path to YAML configuration file",
                                 metavar="FILE")                                       
        for arg_opts in cls.args.values():
            conf_parser.add_argument(arg_opts.option, arg_opts.name, \
                action='append', metavar="<ip-addr>", help="IP address or hostname to fetch introspect from \
                    {} module".format(arg_opts.help))
        all_args = conf_parser.parse_args()
        module_args = namedtuple("module_args","module, ip, port")
        all_modules = []
        if all_args.config:
            with open(all_args.config) as config:
                yaml_to_dict = yaml.load(config, Loader=yaml.FullLoader)
                for mod_tuple in cls.parse_yaml_config(yaml_to_dict):
                    all_modules.append(module_args(*mod_tuple))
        else:
            for module, ip in all_args.__dict__.items():
                 if ip is not None:
                     all_modules.append(module_args(module, ip, cls.args.get(module).port))
        return all_modules
    
    @classmethod
    def parse_yaml_config(cls, config_dict):
        for key, value in config_dict.items():
            if isinstance(value, dict):
                if 'hosts' in value and value['hosts']:
                    yield (key, value['hosts'], value['port'])
                else:
                    yield from cls.parse_yaml_config(value)
    
    @classmethod
    def construct_urls(cls):
        all_args = cls.parse_all_args()
        introspect_urls = []
        for module in all_args:
            for ip in module.ip:
                module_and_url = {
                "url": 'http://{}:{}'.format(ip, module.port),
                "module": module.module
                }
                introspect_urls.append(module_and_url)
        return introspect_urls

    def __call__(self):
        return self.construct_urls()