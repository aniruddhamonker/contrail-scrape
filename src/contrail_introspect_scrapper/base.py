import requests
import logging
from bs4 import BeautifulSoup as bs
import html5lib
import queue
import re
import queue
import threading
import tarfile
import os
import time
import subprocess
from collections import defaultdict
from main_logger import logger

END_OF_TEXT = '\n'+"#"*50+'\n\n' # type: str
START_MARKER = END_MARKER = lambda introspect_name: "-"*len(introspect_name) # type: str

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
    def get_request(cls, url, retrcnt=5):
        # type: (IntrospectBaseClass, str, int) -> str
        # if 'RoutingInstanceList' in url:
        #     import pdb; pdb.set_trace()
        try:
            response = requests.get(url, timeout=5) # type: requests.models.Response
            if response:
                response.raise_for_status()
                logger.debug("Fetched url '{}' with response code: {}\n"\
                .format(url, response.status_code))
                return response.text
        except requests.exceptions.ReadTimeout:
            logger.error('Read Timeout Occurred for URL: {}'.format(url))
        except requests.exceptions.ConnectionError:
            if retrcnt >=1:
                logger.debug("Error connecting url: {}, retry attempt: {}"\
                    .format(url, 6-retrcnt))
                cls.get_request(url, retrcnt-1)
            else:
                 logger.warning("Error Connecting for url: {}\tattempts tried: 5"\
                     .format(url))
        except requests.exceptions.HTTPError:
            logger.error("introspect returned error {} for url {}"\
                .format(response.status_code, url))
        except requests.exceptions.RequestException:
            logger.error("OOps: Something Else")

    @classmethod  
    def parse_response(cls, url, attrs=None):
        # type: (IntrospectBaseClass, str, Optional[str]) -> Optional[str, Iterator[str]]
        text_response = cls.get_request(url) # type: str
        if not text_response:
            # import pdb; pdb.set_trace()
            return None
        parsed_response = bs(text_response, 'xml') # type: bs4.BeautifulSoup
        """ try:
            text_response = cls.get_request(url) # type: str
            parsed_response = bs(text_response, 'xml') # type: bs4.BeautifulSoup
        except TypeError:
            pass #handled upstream in get_request
            return None
        except UnboundLocalError:
            return None """
        if attrs is None:
            return parsed_response
        def __iter__():
            for element in parsed_response.findAll(attrs=attrs):
                yield element
        return __iter__()

    def _get_index_page_nodes_url(self):
        # type: () -> Iterator[Tuple[str, str]]
        # all_index_page_node_urls = [] # type: List[Tuple[str, str]]
        # index_page_nodes = []
        for node in self.all_nodes:
            url = node['url'] # type: str
            try:
                for element in self.parse_response(url, {'href': re.compile(r'xml')}):
                    # if element.attr:
                        # index_page_nodes.append(element.attrs)
                    yield (node['module'], url+'/'+element.attrs.get('href'))
            except TypeError:
                continue

            # index_page_nodes = [element.attrs for element in \
            #     self.parse_response(url, {'href': re.compile(r'xml')} )] # type: List[str]
            # all_index_page_node_urls.extend([(node['module'], \
            #     url+'/'+index_page_node.get('href'))\
            #                     for index_page_node in index_page_nodes])
        # yield from all_index_page_node_urls            

    def _fetch_introspect(self, queue):
        # type: (queue.Queue) -> None
        sandesh_attrs = {'type': 'sandesh'} #type: Dict[str, str]
        global END_OF_TEXT, START_MARKER, END_MARKER
        while not queue.empty():
            index_page_node = queue.get() # type: Tuple[str, str]
            index_page_node_url = index_page_node[1] # type: str
            module_ip = re.search(r'//(?P<IP>.*):', index_page_node_url).group('IP') # type: str
            module_name = index_page_node[0] # type: str
            introspect_node = re.search(r'/(\w+).xml', index_page_node_url).group(1)
            tmp_dir = "/tmp/scrape/{}-{}/{}".format(module_name, module_ip, introspect_node) # type: str
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            threading.current_thread().setName("{}-{}-{}"\
                .format(module_ip, module_name, introspect_node))
            logger.debug("Thread: {} is processing introspect: {}"\
                .format(threading.currentThread().name, index_page_node_url ))
            for introspect in self.parse_response(index_page_node_url, \
                attrs=sandesh_attrs):
                filename = tmp_dir+'/'+introspect.name
                try:
                    with open(filename, 'w') as op_file:
                        introspect_url = re.sub(r'(http.*/).*$', r'\1', \
                            index_page_node_url)+'Snh_'+introspect.name # type: str
                        introspect_response = self.parse_response(introspect_url) # type: bs4.BeautifulSoup
                        op_file.write(introspect_response.prettify())
                        if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                            for sandesh_trace_buf in introspect_response.findAll\
                                (attrs={"link":"SandeshTraceRequest"}):
                                filename = tmp_dir+'/'+sandesh_trace_buf.text
                                with open(filename, 'w') as op_file_trace:
                                    introspect_url = \
                                        re.sub(r'(http.*/).*$', r'\1', index_page_node_url)+\
                                            'Snh_SandeshTraceRequest?x='+ "{}"\
                                                .format(sandesh_trace_buf.text)
                                    op_file_trace.write(self.parse_response(introspect_url).prettify())
                                    op_file_trace.flush()                  
                        op_file.flush()
                except UnboundLocalError as uberr:
                    logger.error("{}: {} occurred for file {}".format(type(uberr), uberr, filename))
                except AttributeError:
                    pass
                except Exception as exp:
                    logger.debug("Exception {} occurred for url {}".format(type(exp), introspect_url))
                    logger.error("Unable to create output file: {}\n".format(filename))
            queue.task_done()
        return

    def fetch_all_introspects(self):
        # type: () -> None
        index_nodes_queue = queue.Queue() # type: queue.Queue
        for node in self._get_index_page_nodes_url():
            index_nodes_queue.put(node)
        logger.debug("total number of introspect urls in the queue: {}"\
            .format(index_nodes_queue.qsize()))
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