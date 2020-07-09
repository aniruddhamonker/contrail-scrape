import requests
import logging
from bs4 import BeautifulSoup as bs
import html5lib
import queue
import re
import threading
import tarfile
import os
import sys
import time
import subprocess
from collections import defaultdict
from main_logger import logger

class IntrospectBaseClass:
    def __init__(self, all_nodes, num_threads, debug=False):
        # type: (List[str, str], int) -> None
        self.all_nodes = all_nodes # type: List[Dict[str, str]]
        self.num_threads = num_threads # type: int
        self.output_files = [] # type: List[str]
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)

    @classmethod
    def get_request(cls, url, retrcnt=3):
        # type: (IntrospectBaseClass, str, int) -> str
        try:
            response = requests.get(url, timeout=5) # type: requests.models.Response
            response.raise_for_status()
            logger.debug("Fetched url '{}' with response code: {}\n"\
            .format(url, response.status_code))
            return response.text
        except requests.exceptions.ReadTimeout:
            logger.error('Read Timeout Occurred for URL: {}'.format(url))
        except requests.exceptions.ConnectionError:
            if retrcnt >=1:
                logger.error("Error connecting url: {}, retry attempt: {}"\
                    .format(url, 4-retrcnt))
                cls.get_request(url, retrcnt-1)
            else:
                logger.error("Error Connecting for url: {}\tattempts tried: 3"\
                     .format(url))
                logger.error("Check if introspect port is correct\n")
        except requests.exceptions.HTTPError:
            logger.error("introspect returned error response {} for url {}"\
                .format(response.status_code, url))
        except requests.exceptions.RequestException:
            logger.error("OOps: Something Else")

    @classmethod  
    def parse_response(cls, url, attrs=None):
        # type: (IntrospectBaseClass, str, Optional[str]) -> Optional[str, Iterator[str]]
        text_response = cls.get_request(url) # type: str
        if not text_response:
            # import pdb; pdb.set_trace()
            raise ValueError
        parsed_response = bs(text_response, 'xml') # type: bs4.BeautifulSoup
        if attrs is None:
            return parsed_response
        def __iter__():
            for element in parsed_response.findAll(attrs=attrs):
                yield element
        return __iter__()

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
                if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                    self.fetch_sandesh_traces(introspect_response, tmp_dir, index_page_node_url)
            queue.task_done()

    def fetch_sandesh_traces(self, introspect_response, filepath, url):
        for sandesh_trace_buf in introspect_response.findAll\
                    (attrs={"link":"SandeshTraceRequest"}):
            filename = filepath+'/'+sandesh_trace_buf.text.replace(" ", "_")
            introspect_url = re.sub(r'(http.*/).*$', r'\1', url)+\
                'Snh_SandeshTraceRequest?x='+ "{}".format(sandesh_trace_buf.text)
            sandesh_trace = self.parse_response(introspect_url)
            self.create_and_write_files(filename, sandesh_trace)
        return

    @staticmethod
    def get_output_dir(index_page_node):
        index_page_node_url = index_page_node[1] # type: str
        module_ip = re.search(r'//(?P<IP>.*):', index_page_node_url).group('IP') # type: str
        module_name = index_page_node[0] # type: str
        introspect_node = re.search(r'/(\w+).xml', index_page_node_url).group(1)
        tmp_dir = "/tmp/scrape/{}-{}/{}".format(module_name, module_ip, introspect_node) # type: str
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        return (tmp_dir, index_page_node_url)

    @staticmethod
    def create_and_write_files(filename, introspect_response):
        try:
            with open(filename, 'w') as op_file:
                op_file.write(introspect_response.prettify())
                op_file.flush()
        except Exception as exp:
            logger.error("Exception {} occurred\n".format(type(exp)))
            logger.error("Failed to create output file {}".format(filename))
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

    def archive_all_files(self):
        # type: () -> None
        logger.info("begining archive process..\n")
        with tarfile.open("all-introspects.tgz", mode="w:gz") as tar:
            try:
                tar.add('/tmp/scrape', arcname='scrape')
            except tarfile.TarError as terr:
                logger.error("Failed to create a tar file archive due to error:\n{}"\
                    .format(type(terr)))
            except Exception as tarexp:
                logger.error("Exception of type {} occurred when archiving files\n{}"\
                    .format(type(tarexp), tarexp))
        tar.close()
        self.delete_tmp_files()
        return

    @staticmethod
    def delete_tmp_files():
        rm_file_op = subprocess.Popen('rm  -rf {}'\
            .format('/tmp/scrape'), shell=True, stderr=subprocess.PIPE)
        if rm_file_op.stderr.read():
            logger.error("Failed to perform cleanup due to error:\n{}"\
                .format(rm_file_op.stderr.read()))
        return