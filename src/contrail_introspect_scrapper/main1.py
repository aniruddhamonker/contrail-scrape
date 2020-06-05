from config_parser import ConfigParser
from base import IntrospectBaseClass

all_nodes = ConfigParser()
introspect = IntrospectBaseClass(all_nodes(), 50)
introspect.fetch_all()
introspect.archive_introspect_output_files()
