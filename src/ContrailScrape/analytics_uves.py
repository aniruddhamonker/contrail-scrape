import requests
from tqdm import tqdm
import logging
import json
import os
import re
import queue
import threading
from bs4 import BeautifulSoup as bs
from ContrailScrape import BaseClass, logger

class AnalyticsApiClass(BaseClass):
    def __init__(self, debug=False):
        self.errors = False
        self.logfile = logger.handlers[0].__dict__['baseFilename']
        if debug:
            self.debug = debug
            logger.setLevel(logging.DEBUG)

    def get_api_nodes(self, queue):
        while not queue.empty():
            api_arg = queue.get()
            for node in ['uves', 'queries', 'alarms']:
                node_dir_path = self.get_output_dir(api_arg['url'], node)
                api_node_url = api_arg['url']+'/analytics/'+ node
                # yield (api_node_url, node_dir_path)
                api_response_txt = self.get_request(api_node_url)
                self.pbar.update()
                api_response_json = json.loads(api_response_txt)
                self.parse_json(api_response_json, node_dir_path)
            queue.task_done()
    
    def get_output_dir(self,api_node_url, analytics_api_node):
        module_ip = re.search(r'//(?P<IP>.*):', api_node_url).group('IP') # type: str
        module_name = "analytics_api" # type: str
        return self._get_output_dir(module_ip, module_name, analytics_api_node)

    def parse_json(self, json_payload, dir_path, filename=None):
        if isinstance(json_payload, list):
            for obj in json_payload:
                self.parse_json(obj, dir_path)
        elif isinstance(json_payload, dict):
            if not json_payload.get('href'):
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                filename = dir_path + '/' + (filename or dir_path.split("/")[-1])
                self.create_and_write_files(filename, json.dumps(json_payload, indent=4))
            else:
                branch_url = json_payload['href']
                if re.search(r'\?flat$', branch_url):
                    filename = re.search(r'http://.*/(.+)\?flat', branch_url).group(1)
                else:
                    branch_sub_dir = re.search(r'/([\w\-]+)$', branch_url).group(1)
                    dir_path = dir_path + '/{}'.format(branch_sub_dir)
                    self.pbar.update()
                api_response_txt = self.get_request(branch_url)
                api_response_json = json.loads(api_response_txt)
                self.parse_json(api_response_json, dir_path, filename)

    def fetch_all_analytics_apis(self, api_args):
        analytics_api_queue = queue.Queue()
        for arg in api_args:
            analytics_api_queue.put(arg)
        logger.debug("total number of analytics api nodes in the queue: {}"\
            .format(analytics_api_queue.qsize()))
        threads = [] # type: List[threading.Thread]
        logger.debug("Initiating threads to fetch apis of {} analytics nodes from the queue"\
            .format(analytics_api_queue.qsize()))
        self.pbar = tqdm(total=28*len(api_args), ncols=100, \
            unit='uves', desc="Analytics-api Progress", position=1)
        for _ in range(analytics_api_queue.qsize()):
            try:
                analytics_api_thread = threading.Thread\
                    (target=self.get_api_nodes, args=(analytics_api_queue,)) # type: threading.Thread
                threads.append(analytics_api_thread) 
                analytics_api_thread.start()    
            except threading.ThreadError as err:
                logger.error("Failed to create thread {}\n{}\n{}"\
                    .format(threading.current_thread.__name__, type(err), err))
                self.errors = True
        logger.debug("Current active thread count is {}\n"\
            .format(threading.active_count()))
        for analytics_api_thread in threads:
            analytics_api_thread.join()
        self.pbar.clear()
        self.pbar.close()
        if self.errors == True:
            tqdm.write("Finishing api scraping of all analytics nodes with errors \
            \nPlease check log file {} for details".format(self.logfile))
        else:
            tqdm.write("Finishing api scraping of all analytics nodes \
            \nNo Errors reported")
        return



