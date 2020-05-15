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

NUM_THREADS = 20
END_OF_TEXT = '\n'+"#"*50+'\n\n'
START_MARKER = END_MARKER = lambda introspect_name: "-"*len(introspect_name)
TIMEOUT = 60

class IntrospectBaseClass():
    def __init__(self):
        self.__files_to_compress = list()
        pass

    @property
    def files_to_compress(self):
        return self.__files_to_compress
    
    @staticmethod
    def get_request(url):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status
        except requests.exceptions.ReadTimeout:
            print('Read Timeout Occurred for URL: {}'.format(url))
        except Exception as err:
            print('{} Error encountered : {}\nResponse Code: {}'\
                   .format(type(err), err, response.status_code))
        return response.text

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
    
    def get_index_page_nodes(self, url):
        attrs = {'href': re.compile(r'xml')}
        yield from self.parse_response(url, attrs=attrs)

    def _get_index_page_nodes_url(self, url):
        index_page_nodes = [element.attrs for element in self.get_index_page_nodes(url)]
        index_page_nodes_urls = [url+'/'+index_page_node.get('href')\
                                for index_page_node in index_page_nodes]
        return index_page_nodes_urls

    def _fetch_introspect(self, queue, url):
        sandesh_attrs = {'type': 'sandesh'}
        global END_OF_TEXT, START_MARKER, END_MARKER
        while not queue.empty():
            index_page_node_url = queue.get()
            filename = "/tmp/"+index_page_node_url.split('/')[-1]
            threading.current_thread().setName(filename)
            print("Thread: {} started".format(threading.current_thread().getName()))
            try:
                with open(filename, 'w') as op_file:
                    for introspect in self.parse_response(index_page_node_url, \
                        attrs=sandesh_attrs):
                        try:
                            op_file.write(START_MARKER(introspect.name)+"\n"+introspect.name+"\n"+END_MARKER(introspect.name)+"\n")
                            introspect_response = self.parse_response(index_page_node_url.split('/')[0:-1]+'/'+'Snh_'+introspect.name)
                            op_file.write(introspect_response.prettify())
                            op_file.write(END_OF_TEXT)
                            if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                                for sandesh_trace_buf in introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                                    op_file.write(START_MARKER(sandesh_trace_buf.text)+"\n"+sandesh_trace_buf.text+"\n"+END_MARKER(sandesh_trace_buf)+"\n")
                                    op_file.write(self.parse_response(index_page_node_url.split('/')[0:-1]+'/'+'Snh_SandeshTraceRequest?x='+sandesh_trace_buf.text).prettify())
                                    op_file.write(END_OF_TEXT)                            
                            op_file.flush()
                        except Exception as write_exp:
                            print("Exception {} for thread {}\nUnable to write output to file {}".format(write_exp, threading.current_thread().getName(), filename))
            except Exception as exp:
                print("Exception {} occurred for {}\nUnable to create output file: {}".format(exp, threading.current_thread().getName(), filename))
            self.__files_to_compress.append(filename)
            queue.task_done()
        return

    def fetch_all(self, url):
        index_nodes_queue = queue.Queue()
        for node in self._get_index_page_nodes_url(url):
            index_nodes_queue.put(node)
        threads = list()
        for node in range(index_nodes_queue.qsize()):
            try:
                introspect_thread = threading.Thread(target=self._fetch_introspect, args=(index_nodes_queue,url))
                introspect_thread.start()
                threads.append(introspect_thread)    
            except threading.ThreadError as err:
                print("Failed to create thread {}\n{}\n{}".format(threading.current_thread.__name__, type(err), err))
        for introspect_thread in threads:
            introspect_thread.join()
    
    @classmethod
    def _archive_introspect_output_files(cls, files_to_compress, module_name, dir=None):
        if dir is None:
            dir = os.getcwd()
        tar_filename = '{}/{}-{}.tar.gz'.format(dir, module_name, time.strftime('%Y-%m-%d-%H-%M'))
        with tarfile.open(tar_filename, mode="w:gz") as tar:
            for file in files_to_compress:
                try:
                    tar.add(file, arcname=file.replace("/tmp", module_name))
                except tarfile.TarError as terr:
                    print("Failed to create a tar file archive for {} due to error:\n{}".format(module_name, terr))
                except Exception as tarexp:
                    print("Exception of type {} occurred when adding file {} to tar archive\nArchive failed for module {}\n{}".format(type(tarexp), file, module_name, tarexp))
        tar.close()
        cls.delete_tmp_files(files_to_compress)
        return

    @staticmethod
    def delete_tmp_files(files_to_delete):
        for file in files_to_delete:
            rm_file_op = subprocess.Popen('rm  {}'.format(file), shell=True, stderr=subprocess.PIPE)
            if rm_file_op.stderr.read():
                print("Failed to delete fil {} due to error:\n{}".format(file, rm_file_op.stderr.read()))
        return 