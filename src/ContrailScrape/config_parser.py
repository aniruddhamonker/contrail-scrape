import sys
import pathlib
import argparse
import yaml
import re
from collections import namedtuple

class ConfigParser():
    def __init__(self):
        import pdb;pdb.set_trace()
        metadata_file = str(pathlib.Path(__file__).parent.parent) + "/data/metadata.yaml"
        with open(metadata_file) as meta:
            self.margs = yaml.load(meta, Loader=yaml.FullLoader) 
        self.__all_args = self.parse_all_args()
        self.__debug = True if self.__all_args.debug else False
        self.__version = True if self.__all_args.version else False

    def parse_all_args(self, args=None):
        conf_parser = argparse.ArgumentParser()
        conf_parser.add_argument("-c", "--yaml-config",
                                 help="path to YAML configuration file",
                                 metavar="FILE")                        
        for arg in self.margs['argparser'].values():
            conf_parser.add_argument(arg['short_name'], arg['option_name'], \
            action='append', metavar="<ip-addr>")
        conf_parser.add_argument('-vvv', "--debug", action='store_true', \
            help="turn on debug mode")
        conf_parser.add_argument('-v', '--version', action='store_true', \
            help="print the version number")
        all_args = conf_parser.parse_args()
        if not any(all_args.__dict__.values()):
            print("No Valid Input Arguments provided \
                \nUse \"--help\" for available options\n")
            sys.exit(1)
        return all_args
    
    def format_all_args(self):
        module_args = namedtuple("module_args","module, ip, port")
        all_formatted_args = []
        if self.__all_args.yaml_config:
            with open(self.__all_args.yaml_config) as config:
                yaml_to_dict = yaml.load(config, Loader=yaml.FullLoader)
                for mod_tuple in self.parse_yaml_config(yaml_to_dict):
                    all_formatted_args.append(module_args(*mod_tuple))
        else:
            for key, val in self.__all_args.__dict__.items():
                 if val is not None and isinstance(val, list):
                     all_formatted_args.append(module_args(key, val, \
                         self.margs['argparser'][key]['port']))
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
                if arg.module == "analytics_api_uves" else "introspect"
            for ip in arg.ip:
                module_and_url = {
                "type": mtype,
                "url": 'http://{}:{}'.format(ip, arg.port),
                "module": arg.module
                }
                introspect_urls.append(module_and_url)
        return introspect_urls
    
    @property
    def debug(self):
        return self.__debug

    @property
    def version(self):
        return self.__version

    def __call__(self):
        return self.construct_urls()