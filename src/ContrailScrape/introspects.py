from tqdm import tqdm
import logging
import queue
import re
import threading
import sys
from ContrailScrape import BaseClass, logger

class IntrospectClass(BaseClass):
    def __init__(self, introspect_args, num_threads, debug=False):
    # type: (List[str, str], int) -> None
        self.introspect_args = introspect_args # type: List[Dict[str, str]]
        self.num_threads = num_threads # type: int
        self.errors = False
        self.debug = debug
        self.url_filter = re.compile(r'(http.*/).*$')
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

    def parse_and_write_response(self, filename, url):
        try:
            parsed_response, next_batch = self.parse_response(url)
            self.create_and_write_files(filename, parsed_response.prettify())
            return next_batch
        except ValueError:
            self.errors = True
            return 'ValueError'

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
                    introspect_response, next_batch = self.parse_response(introspect_url)\
                        # type: bs4.BeautifulSoup
                except ValueError:
                    self.errors = True
                    continue
                self.create_and_write_files(filename, introspect_response.prettify())
                if next_batch:
                    self._fetch_batch_data(introspect_url, filename, next_batch)
                if introspect.name == 'SandeshUVETypesReq':
                    self.fetch_all_uve_types(introspect_url, tmp_dir)
                if introspect.name == 'VrfListReq':
                    vrf_indexes = list(map(lambda vrf: vrf.text, introspect_response.findAll(name='ucindex')))
                    [self.fetch_routes_per_vrf(index, introspect_url, tmp_dir) for index in vrf_indexes]
                if introspect.name == 'ShowMulticastManagerReq':
                    self.fetch_mcast_tables(introspect_url, tmp_dir)
                if introspect.name == 'IFMapXmppClientInfoShowReq':
                    self.fetch_ifmap_nodes_and_links(introspect_url, tmp_dir)
                if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                    self.fetch_sandesh_traces(introspect_response, tmp_dir, index_page_node_url)
            self.pbar.update()
            queue.task_done()
    
    def _fetch_batch_data(self, introspect_url, filepath, batch_data, batch_num=1):
        batch_url = re.sub(self.url_filter, r'\1', introspect_url) +\
            'Snh_{}?x={}'.format(batch_data['link'], batch_data['text'])
        # try:
        #     batch_response, next_batch = self.parse_response(batch_url)
        #     filename = filepath + '.{}'.format(batch_num)
        #     self.create_and_write_files(filename, batch_response.prettify())
        # except ValueError:
        #     self.errors = True
        filename = filepath + '.{}'.format(batch_num)
        next_batch = self.parse_and_write_response(filename, batch_url)
        if isinstance(next_batch, dict):
            batch_num += 1
            self._fetch_batch_data(introspect_url, filepath, next_batch, batch_num)
    
    def fetch_all_uve_types(self, uve_req_url, filepath):
        try:
            all_uve_types, _ = self.parse_response(uve_req_url)
        except ValueError:
            return
        for uve in all_uve_types.findAll('type_name'):
            uve_name = 'SandeshUVECacheReq?tname=' + uve.text
            uve_url = re.sub(r'(http.*/).*$', r'\1', uve_req_url) +\
                 'Snh_' + uve_name
            filename = filepath + '/' + uve.text
            response = self.parse_and_write_response(filename, uve_url)
            if response == 'ValueError': continue
        return

    def fetch_sandesh_traces(self, introspect_response, filepath, url):
        for sandesh_trace_buf in introspect_response.findAll\
                    (attrs={"link":"SandeshTraceRequest"}):
            filename = filepath+'/'+sandesh_trace_buf.text.replace(" ", "_")
            introspect_url = re.sub(r'(http.*/).*$', r'\1', url)+\
                'Snh_SandeshTraceRequest?x='+ "{}".format(sandesh_trace_buf.text)
            self.parse_and_write_response(filename, introspect_url)
        return

    def fetch_routes_per_vrf(self, index, url, filepath):
        inet4uc_url = re.sub(r'(http.*/).*$', r'\1', url) + \
            'Snh_Inet4UcRouteReq?vrf_index=' + index
        filename = filepath + '/Inet4UcRouteReq?vrf_index=' + index
        self.parse_and_write_response(filename, inet4uc_url)

        layer2rte_url = re.sub(r'(http.*/).*$', r'\1', url) + \
            'Snh_Layer2RouteReq?vrf_index=' + index
        filename = filepath + '/Layer2RouteReq?vrf_index=' + index
        self.parse_and_write_response(filename, layer2rte_url)
        
        inet6uc_url = re.sub(r'(http.*/).*$', r'\1', url) + \
            'Snh_Inet6UcRouteReq?vrf_index=' + index
        filename = filepath + '/Inet6UcRouteReq?vrf_index=' + index
        self.parse_and_write_response(filename, inet6uc_url)
        return

    def fetch_mcast_tables(self, url, filepath):
        mcast_tree_url = re.sub(r'(http.*/).*$', r'\1', url) +\
             'Snh_ShowMulticastManagerDetailReq?x='
        try:
            all_mcast_tables, next_batch = self.parse_response(url)
        except ValueError:
            return
        for table in all_mcast_tables.findAll('ShowMulticastManager'):
            if table.total_trees.text != '0':
                tree_name = table.find('name').text
                filename = filepath + '/ShowMulticastManagerDetailReq.'\
                     + tree_name[:200]
                self.parse_and_write_response(filename, mcast_tree_url+tree_name)
        if next_batch:
            batch_url = re.sub(self.url_filter, r'\1', url) +\
            'Snh_{}?x={}'.format(next_batch['link'], next_batch['text'])
            self.fetch_mcast_tables(batch_url, filepath)

    def fetch_ifmap_nodes_and_links(self, url, filepath):
        nodes_filename = filepath + '/IFMapPerClientNodesShow.index.'
        ifmap_nodes_url = re.sub(self.url_filter, r'\1', url) + \
            'Snh_IFMapPerClientNodesShowReq?client_index_or_name='  
        links_filename = filepath + '/IFMapPerClientLinksShow.index.'  
        ifmap_links_url = re.sub(self.url_filter, r'\1', url) + \
            'Snh_IFMapPerClientLinksShowReq?client_index_or_name='
        try:
            ifmap_clients, next_batch = self.parse_response(url)
        except ValueError:
            return
        for client in ifmap_clients.findAll('IFMapXmppClientInfo'):
            index = client.client_index.text
            nodes_url = ifmap_nodes_url + index
            filename = nodes_filename + index
            self.parse_and_write_response(filename,\
                nodes_url)
            filename = links_filename + index
            links_url = ifmap_links_url + index
            self.parse_and_write_response(filename,\
                links_url)
        if next_batch:
            batch_url = re.sub(self.url_filter, r'\1', url) +\
            'Snh_{}?x={}'.format(next_batch['link'], next_batch['text'])
            self.fetch_ifmap_nodes_and_links(batch_url, filepath)

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
            unit='thread', desc="API Scraping Progress", position=1, leave=True)
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
        self.pbar.clear()
        self.pbar.close()
        if self.errors == True:
            tqdm.write("Finishing introspection of all nodes\
            \nPlease check log file {} for details".format(self.logfile))
        else:
            tqdm.write("Finishing introspection of all nodes \
                \nNo Errors reported")
        return