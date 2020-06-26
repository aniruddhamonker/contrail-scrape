from config_parser import ConfigParser
from base import IntrospectBaseClass
import sys

version = '0.1.0'

all_nodes = ConfigParser()
# import pdb; pdb.set_trace()
if all_nodes.version:
    print("CONTRAIL-INTROSPECT-SCRAPE\nVERSION: {}".format(version))
    sys.exit()
introspect = IntrospectBaseClass(all_nodes(), 50, debug=all_nodes.debug)
introspect.fetch_all_introspects()
introspect.archive_all_files()
