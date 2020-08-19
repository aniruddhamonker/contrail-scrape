from ContrailScrape.base import BaseClass
from tqdm import tqdm
import logging
from ContrailScrape.main_logger import logger
import queue
import re
import threading
import sys

class IntrospectClass(BaseClass):
    def __init__(self, introspect_args, num_threads, debug=False):
    # type: (List[str, str], int) -> None
        self.introspect_args = introspect_args # type: List[Dict[str, str]]
        self.num_threads = num_threads # type: int
        self.errors = False
        self.debug = debug
        self.logfile = logger.handlers[0].__dict__['baseFilename']
        if self.debug:
            logger.setLevel(logging.DEBUG)

    def _get_index_page_nodes_url(self):
    # type: () -> Iterator[Tuple[str, str]]
        for node in self.introspect_args:
            url = node['url'] # type: str
            try:
                for element in self.parse_response(url, {'href': re.compile(r'xml')}):
                    yield (node['module'], url+'/'+element.attrs.get('href'))
            except ValueError:
                self.errors = True
                continue
    
    def get_output_dir(self, index_page_node):
        module_ip = re.search(r'//(?P<IP>.*):', index_page_node[1]).group('IP') # type: str
        module_name = index_page_node[0] # type: str
        introspect_node = re.search(r'/(\w+).xml', index_page_node[1]).group(1)
        return self._get_output_dir(module_ip, module_name, introspect_node)

    def _fetch_introspect(self, queue):
        # type: (queue.Queue) -> None
        sandesh_attrs = {'type': 'sandesh'} #type: Dict[str, str]
        while not queue.empty():
            index_page_node = queue.get() # type: Tuple[str, str]
            index_page_node_url = index_page_node[1] # type: str
            tmp_dir = self.get_output_dir(index_page_node)
            for introspect in self.parse_response(index_page_node_url, \
                attrs=sandesh_attrs):
                filename = tmp_dir+'/'+introspect.name
                introspect_url = re.sub(r'(http.*/).*$', r'\1', \
                    index_page_node_url)+'Snh_'+introspect.name # type: str
                try:                 
                    introspect_response = self.parse_response(introspect_url) # type: bs4.BeautifulSoup
                except ValueError:
                    logger.error("Failed to create output file for introspect: {}"\
                        .format(introspect.name))
                    self.errors = True
                    continue
                self.create_and_write_files(filename, introspect_response.prettify())
                if introspect.name == 'SandeshUVETypesReq':
                    self.fetch_all_uve_types(introspect_url, tmp_dir)
                if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                    self.fetch_sandesh_traces(introspect_response, tmp_dir, index_page_node_url)
            self.pbar.update()
            queue.task_done()
    
    def fetch_all_uve_types(self, introspect_url, filepath):
        all_uve_types = self.parse_response(introspect_url)
        for uve in all_uve_types.findAll('type_name'):
            uve_name = 'SandeshUVECacheReq?tname=' + uve.text
            uve_url = re.sub(r'(http.*/).*$', r'\1', introspect_url) + 'Snh_' + uve_name
            uve_response = self.parse_response(uve_url)
            filename = filepath + '/' + uve_name
            self.create_and_write_files(filename, uve_response.prettify())
        return

    def fetch_sandesh_traces(self, introspect_response, filepath, url):
        for sandesh_trace_buf in introspect_response.findAll\
                    (attrs={"link":"SandeshTraceRequest"}):
            filename = filepath+'/'+sandesh_trace_buf.text.replace(" ", "_")
            introspect_url = re.sub(r'(http.*/).*$', r'\1', url)+\
                'Snh_SandeshTraceRequest?x='+ "{}".format(sandesh_trace_buf.text)
            try:
                sandesh_trace = self.parse_response(introspect_url)
            except ValueError:
                logger.error("Failed to create output file for introspect: {}"\
                        .format(sandesh_trace_buf.text.replace(" ", "_")))
                self.errors = True
            self.create_and_write_files(filename, sandesh_trace.prettify())
        return

    def fetch_all_introspects(self):
        # type: () -> None
        index_nodes_queue = queue.Queue() # type: queue.Queue
        for node in self._get_index_page_nodes_url():
            index_nodes_queue.put(node)
        logger.debug("total number of introspect urls in the queue: {}"\
            .format(index_nodes_queue.qsize()))
        if index_nodes_queue.empty():
            print("No introspect nodes found. Check connectivity to introspect nodes\n")
            sys.exit(0)
        threads = [] # type: List[threading.Thread]
        logger.debug("Initiating threads to fetch {} introspects from the queue"\
            .format(index_nodes_queue.qsize()))
        self.pbar = tqdm(total=index_nodes_queue.qsize(), ncols=100, \
            unit='thread', desc="Introspection Progress", position=1)
        for _ in range(self.num_threads):
            try:
                introspect_thread = threading.Thread\
                    (target=self._fetch_introspect, args=(index_nodes_queue,)) # type: threading.Thread
                introspect_thread.start() 
                threads.append(introspect_thread)    
            except threading.ThreadError as err:
                logger.error("Failed to create thread {}\n{}\n{}"\
                    .format(threading.current_thread.__name__, type(err), err))
        logger.debug("Current active thread count is {}"\
            .format(threading.active_count()))
        for introspect_thread in threads:
            introspect_thread.join()
        self.pbar.close()
        if self.errors == True:
            print("Finishing introspection of all nodes with Errors")
            print("Please check log file {} for details".format(self.logfile))
        else:
            print("Finishing introspection of all nodes")
            print("No Errors reported")
        return