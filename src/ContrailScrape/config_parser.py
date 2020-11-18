import sys
import pathlib
import argparse
import yaml
import re
from collections import namedtuple

class ConfigParser():
    def __init__(self):
        metadata_file = str(pathlib.Path(__file__).parent) + "/data/metadata.yaml"
        with open(metadata_file) as meta:
            self.margs = yaml.safe_load(meta) 
        self.__all_args = self.parse_all_args()
        self.__debug = True if self.__all_args.debug else False
        self.__version = True if self.__all_args.version else False

    def parse_all_args(self, args=None):
        conf_parser = argparse.ArgumentParser(description="A tool to scrape APIs and Introspects of various Contrail nodes")
        conf_parser.add_argument("--yaml-config", metavar='FILE',
                                 help="path to YAML configuration file")                        
        for arg in self.margs['argparser'].values():
            conf_parser.add_argument(arg['option_name'], \
            action='append', metavar='HOST', help=arg['help'])
        conf_parser.add_argument('--version', action='store_true', \
            help="print the version number")
        conf_parser.add_argument("--debug", action='store_true', \
            help="turn on debug mode")
        conf_parser.add_argument('--threads', type=int, default=50,\
            help="control the number of threads, default=50")
        conf_parser.add_argument('--api-timeout', type=int, default=10,\
            help='set API requests timeout in secs, default=10sec')
        all_args = conf_parser.parse_args()
        arg_list = list(all_args.__dict__.values())
        if not list(filter(lambda x: isinstance(x, (list, str)) or x is True, arg_list)):
            print("No Valid Input Arguments provided \
                \nUse \"--help\" for available options\n")
            sys.exit(1)
        return all_args
    
    def format_all_args(self):
        module_args = namedtuple("module_args","module, ip, port")
        all_formatted_args = []
        if self.__all_args.yaml_config:
            with open(self.__all_args.yaml_config) as config:
                yaml_to_dict = yaml.safe_load(config)
                for mod_tuple in self.parse_yaml_config(yaml_to_dict):
                    all_formatted_args.append(module_args(*mod_tuple))
        else:
            for key, val in self.__all_args.__dict__.items():
                if val is not None and isinstance(val, list):
                    #  if map(lambda host_ip: True if ':' in host_ip else None, val):
                    if ':' in val[0]:
                        port = re.split(':', val[0])[-1]
                        val = list(map(lambda host: host.split(':')[0], val))
                    else:
                        port = self.margs['argparser'][key]['port']
                    all_formatted_args.append(module_args(key, val, port))
        yield from all_formatted_args
    
    @classmethod
    def parse_yaml_config(cls, config_dict):
        for key, value in config_dict.items():
            if isinstance(value, dict):
                if 'hosts' in value and value['hosts']:
                    yield (key, value['hosts'], value['port'])
                else:
                    yield from cls.parse_yaml_config(value)
    
    def construct_urls(self):
        introspect_urls = []
        for arg in self.format_all_args():
            mtype = "analytics-api" \
                if arg.module == "analytics_api" else "introspect"
            for ip in arg.ip:
                module_and_url = {
                "type": mtype,
                "url": 'http://{}:{}'.format(ip, arg.port),
                "module": arg.module
                }
                introspect_urls.append(module_and_url)
        return introspect_urls
    
    @property
    def all_args(self):
        return self.__all_args
    
    @property
    def debug(self):
        return self.__debug

    @property
    def version(self):
        return self.__version

    def __call__(self):
        return self.construct_urls()