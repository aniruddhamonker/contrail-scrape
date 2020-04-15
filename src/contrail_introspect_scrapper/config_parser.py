'''
This is a third party code imported from
"https://gist.githubusercontent.com/multun/ccf5a8b855de7c50968aac127bc5605b/raw/d7554f918b8f0259220514d627dc566bd40a848e/config_parser.py"
and modified to match config parsing options for module contrail_introspect_scrapper
'''
import sys
import argparse
import yaml

class ConfigParser():
    def __init__(self, *pargs, **kwpargs):
        self.options = []
        self.pargs = pargs
        self.kwpargs = kwpargs

    def add(self, *args, **kwargs):
        self.options.append((args, kwargs))

    def parse(self, args=None):
        if args is None:
            args = sys.argv[1:]

        conf_parser = argparse.ArgumentParser(add_help=False)
        conf_parser.add_argument("-c", "--config",
                                 default="hosts.yaml",
                                 help="where to load YAML configuration",
                                 metavar="FILE")

        res, remaining_argv = conf_parser.parse_known_args(args)

        config_vars = {}
        if res.config is not None:
            with open(res.config, 'r') as stream:
                config_vars = yaml.load(stream)

        parser = argparse.ArgumentParser(
            *self.pargs,
            # Inherit options from config_parser
            parents=[conf_parser],
            # Don't mess with format of description
            formatter_class=argparse.RawDescriptionHelpFormatter,
            **self.kwpargs,
        )

        for opt_args, opt_kwargs in self.options:
            parser_arg = parser.add_argument(*opt_args, **opt_kwargs)
            if parser_arg.dest in config_vars:
                config_default = config_vars.pop(parser_arg.dest)
                expected_type = str
                if parser_arg.type is not None:
                    expected_type = parser_arg.type

                if not isinstance(config_default, expected_type):
                    parser.error('YAML configuration entry {} '
                                 'does not have type {}'.format(
                                     parser_arg.dest,
                                     expected_type))

                parser_arg.default = config_default

        if config_vars:
            parser.error('unexpected configuration entries: ' + \
                         ', '.join(config_vars))

        return parser.parse_args(remaining_argv)
    
    def get_hosts_ips_and_port(self, yaml):
        for key, value in yaml.items():
            if isinstance(value, dict):
                if 'hosts' in value and value['hosts']:
                    yield (key, value['hosts'])
                else:
                    yield from self.get_hosts_ips_and_port(value)