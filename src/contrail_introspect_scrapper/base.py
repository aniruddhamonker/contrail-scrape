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

END_OF_TEXT = '\n'+"#"*50+'\n\n'
START_MARKER = END_MARKER = lambda introspect_name: "-"*len(introspect_name)
TIMEOUT = 60

class IntrospectBaseClass():
    def __init__(self, all_nodes, num_threads):
        self.all_nodes = all_nodes
        self.num_threads = num_threads
        self.__output_files = defaultdict(list)
    
    @staticmethod
    def get_request(url):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status
        except requests.exceptions.ReadTimeout:
            print('Read Timeout Occurred for URL: {}'.format(url))
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:",errc)
        except requests.exceptions.RequestException as err:
            print ("OOps: Something Else",err)
        except Exception as err:
            print('{} Error encountered : {}\nResponse Code: {}'\
                   .format(type(err), err, response.status_code))
        return response.text if isinstance(response, requests.models.Response)\
             else None

    @classmethod
    def parse_response(cls, url, attrs=None):
        text_response = cls.get_request(url)
        parsed_response = bs(text_response, 'xml')
        if attrs is None:
            return parsed_response
        def __iter__():
            for element in parsed_response.findAll(attrs=attrs):
                yield element
        return __iter__()

    '''
    def get_index_page_nodes(self):
        attrs = {'href': re.compile(r'xml')}
        yield from self.parse_response(self.root_url, attrs=attrs)
    '''
    def _get_index_page_nodes_url(self):
        all_index_page_node_urls = []
        for node in self.all_nodes:
            url = node['url']
            index_page_nodes = [element.attrs for element in \
                self.parse_response(url, {'href': re.compile(r'xml')} )]
            all_index_page_node_urls.extend([url+'/'+index_page_node.get('href')\
                                for index_page_node in index_page_nodes])
        yield from all_index_page_node_urls            

    def _fetch_introspect(self, queue):
        sandesh_attrs = {'type': 'sandesh'}
        global END_OF_TEXT, START_MARKER, END_MARKER
        while not queue.empty():
            index_page_node_url = queue.get()
            filename = "/tmp/{}-{}".format(index_page_node_url.split('/')[-2], index_page_node_url.split('/')[-1])
            threading.current_thread().setName(filename)
            print("Thread: {} started".format(threading.current_thread().getName()))
            try:
                with open(filename, 'w') as op_file:
                    for introspect in self.parse_response(index_page_node_url, \
                        attrs=sandesh_attrs):
                        try:
                            op_file.write(START_MARKER(introspect.name)+"\n"+introspect.name+"\n"+END_MARKER(introspect.name)+"\n")
                            introspect_url = re.sub(r'(http.*/).*$', r'\1', index_page_node_url)+'Snh_'+introspect.name
                            introspect_response = self.parse_response(introspect_url)
                            op_file.write(introspect_response.prettify())
                            op_file.write(END_OF_TEXT)
                            if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                                for sandesh_trace_buf in introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                                    op_file.write(START_MARKER(sandesh_trace_buf.text)+"\n"+sandesh_trace_buf.text+"\n"+END_MARKER(sandesh_trace_buf)+"\n")
                                    op_file.write(self.parse_response(re.sub(r'(http.*/).*$', r'\1', index_page_node_url)+'/'+'Snh_SandeshTraceRequest?x='+sandesh_trace_buf.text).prettify())
                                    op_file.write(END_OF_TEXT)                            
                            op_file.flush()
                        except Exception as write_exp:
                            print("Exception {} for thread {}\nUnable to write output to file {}\n".format(write_exp, threading.current_thread().getName(), filename))
            except Exception as exp:
                print("Exception {} occurred for {}\nUnable to create output file: {}\n".format(exp, threading.current_thread().getName(), filename))
            self.__output_files[index_page_node_url.split('/')[-2]].append(filename)
            queue.task_done()
        return

    def fetch_all(self):
        index_nodes_queue = queue.Queue()
        for node in self._get_index_page_nodes_url():
            index_nodes_queue.put(node)
        threads = []
        for _ in range(self.num_threads):
            try:
                introspect_thread = threading.Thread(target=self._fetch_introspect, args=(index_nodes_queue,))
                introspect_thread.start()
                threads.append(introspect_thread)    
            except threading.ThreadError as err:
                print("Failed to create thread {}\n{}\n{}".format(threading.current_thread.__name__, type(err), err))
        for introspect_thread in threads:
            introspect_thread.join()
    
    def archive_introspect_output_files(self, dir=None):
        if dir is None:
            dir = os.getcwd()
        for node in self.all_nodes:
            module_ip = node['url'].split('/')[-1]
            module_name = node['module']
            tar_filename = '{}/{}-{}-{}.tar.gz'.format(dir, module_name, module_ip, time.strftime('%Y-%m-%d-%H-%M'))
            with tarfile.open(tar_filename, mode="w:gz") as tar:
                try:
                    for file in self.__output_files[module_ip]:
                        tar.add(file, arcname=file.replace("/tmp", module_name))
                except tarfile.TarError as terr:
                    print("Failed to create a tar file archive for {} due to error:\n{}".format(module_name, terr))
                except Exception as tarexp:
                    print("Exception of type {} occurred when adding file {} to tar archive\nArchive failed for module {}\n{}".format(type(tarexp), file, module_name, tarexp))
        tar.close()
        self.delete_tmp_files(self.__output_files)
        print("archive complete for node {} and module {}\n".format(module_ip, module_name))
        return

    @staticmethod
    def delete_tmp_files(files_to_delete):
        for files in files_to_delete.values():
            for file in files:
                rm_file_op = subprocess.Popen('rm  {}'.format(file), shell=True, stderr=subprocess.PIPE)
            if rm_file_op.stderr.read():
                print("Failed to delete fil {} due to error:\n{}".format(file, rm_file_op.stderr.read()))
        return