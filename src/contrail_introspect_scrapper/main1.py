from config_parser import ConfigParser
from base import IntrospectBaseClass

all_nodes = ConfigParser()
for node_args in all_nodes():
    introspect = IntrospectBaseClass(node_args.get('url'))
    introspect.fetch_all()
    introspect.archive_introspect_output_files(node_args)
