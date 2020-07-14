from base import BaseClass
import logging
from main_logger import logger
import queue
import re
import threading
import sys

class IntrospectClass(BaseClass):
    def __init__(self, all_nodes, num_threads, debug=False):
    # type: (List[str, str], int) -> None
        self.all_nodes = all_nodes # type: List[Dict[str, str]]
        self.num_threads = num_threads # type: int
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)

    def _get_index_page_nodes_url(self):
    # type: () -> Iterator[Tuple[str, str]]
        for node in self.all_nodes:
            url = node['url'] # type: str
            try:
                for element in self.parse_response(url, {'href': re.compile(r'xml')}):
                    yield (node['module'], url+'/'+element.attrs.get('href'))
            except ValueError:
                continue

    def _fetch_introspect(self, queue):
        # type: (queue.Queue) -> None
        sandesh_attrs = {'type': 'sandesh'} #type: Dict[str, str]
        while not queue.empty():
            index_page_node = queue.get() # type: Tuple[str, str]
            tmp_dir, index_page_node_url = self.get_output_dir(index_page_node)
            for introspect in self.parse_response(index_page_node_url, \
                attrs=sandesh_attrs):
                filename = tmp_dir+'/'+introspect.name
                introspect_url = re.sub(r'(http.*/).*$', r'\1', \
                    index_page_node_url)+'Snh_'+introspect.name # type: str
                try:                 
                    introspect_response = self.parse_response(introspect_url) # type: bs4.BeautifulSoup
                except ValueError:
                    logger.error("Failed to create output file for introspect: {}\n"\
                        .format(introspect.name))
                    continue
                self.create_and_write_files(filename, introspect_response)
                if introspect.name == 'SandeshUVETypesReq':
                    self.fetch_all_uve_types(introspect_url, tmp_dir)
                if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                    self.fetch_sandesh_traces(introspect_response, tmp_dir, index_page_node_url)
            queue.task_done()
    
    def fetch_all_uve_types(self, introspect_url, filepath):
        all_uve_types = self.parse_response(introspect_url)
        for uve in all_uve_types.findAll('type_name'):
            uve_name = 'SandeshUVECacheReq?tname=' + uve.text
            uve_url = re.sub(r'(http.*/).*$', r'\1', introspect_url) + 'Snh_' + uve_name
            uve_response = self.parse_response(uve_url)
            filename = filepath + '/' + uve_name
            self.create_and_write_files(filename, uve_response)
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
                logger.error("Failed to create output file for introspect: {}\n"\
                        .format(sandesh_trace_buf.text.replace(" ", "_")))
            self.create_and_write_files(filename, sandesh_trace)
        return

    def fetch_all_introspects(self):
        # type: () -> None
        index_nodes_queue = queue.Queue() # type: queue.Queue
        for node in self._get_index_page_nodes_url():
            index_nodes_queue.put(node)
        logger.debug("total number of introspect urls in the queue: {}"\
            .format(index_nodes_queue.qsize()))
        if index_nodes_queue.empty():
            logger.error("No nodes found in the queue. check connectivity to introspect nodes\n")
            sys.exit(0)
        threads = [] # type: List[threading.Thread]
        logger.debug("Initiating threads to fetch {} introspects from the queue"\
            .format(index_nodes_queue.qsize()))
        for _ in range(self.num_threads):
            try:
                introspect_thread = threading.Thread\
                    (target=self._fetch_introspect, args=(index_nodes_queue,)) # type: threading.Thread
                introspect_thread.start() 
                threads.append(introspect_thread)    
            except threading.ThreadError as err:
                logger.error("Failed to create thread {}\n{}\n{}"\
                    .format(threading.current_thread.__name__, type(err), err))
        logger.info("Current active thread count is {}\n"\
            .format(threading.active_count()))
        for introspect_thread in threads:
            introspect_thread.join()
        logger.info("Finishing introspection of all nodes\n")
        return