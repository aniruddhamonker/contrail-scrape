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
        #self.__output_files = defaultdict(list)
        self.__output_files = []
    
    @classmethod
    def get_request(cls, url, retrcnt=5):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status
        except requests.exceptions.ReadTimeout:
            print('Read Timeout Occurred for URL: {}'.format(url))
        except requests.exceptions.ConnectionError:
            print ("Error Connecting for url: {}".format(url))
            print("Retrying {}: retry attempt {}".format(url, retrcnt))
            if retrcnt >=1:
                cls.get_request(url, retrcnt-1)
            else:
                 print("All retry attempts failed for url: {} , moving on..".format(url))
        except requests.exceptions.RequestException as err:
            print ("OOps: Something Else",err)
        #except Exception as err:
         #   print('{} Error encountered : {}\n'\
           #        .format(type(err), err))
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

    def _get_index_page_nodes_url(self):
        all_index_page_node_urls = []
        for node in self.all_nodes:
            url = node['url']
            index_page_nodes = [element.attrs for element in \
                self.parse_response(url, {'href': re.compile(r'xml')} )]
            all_index_page_node_urls.extend([(node['module'], url+'/'+index_page_node.get('href'))\
                                for index_page_node in index_page_nodes])
        #import pdb; pdb.set_trace()
        yield from all_index_page_node_urls            

    def _fetch_introspect(self, queue):
        sandesh_attrs = {'type': 'sandesh'}
        global END_OF_TEXT, START_MARKER, END_MARKER
        while not queue.empty():
            index_page_node = queue.get()
            index_page_node_url = index_page_node[1]
            module_ip = re.search(r'//(?P<IP>.*):', index_page_node_url).group('IP')
            module_name = index_page_node[0]
            tmp_dir = "/tmp/{}-{}".format(module_name, module_ip)
            if not os.path.exists(tmp_dir):
                os.mkdir(tmp_dir)
            filename = "{}/{}".format(tmp_dir, index_page_node_url.split('/')[-1])
            threading.current_thread().setName(filename)
            #print("Thread: {} started".format(threading.current_thread().getName()))
            try:
                with open(filename, 'w') as op_file:
                    for introspect in self.parse_response(index_page_node_url, \
                        attrs=sandesh_attrs):
                        op_file.write(START_MARKER(introspect.name)+"\n"\
                            +introspect.name+"\n"+END_MARKER(introspect.name)+"\n")
                        introspect_url = re.sub(r'(http.*/).*$', r'\1', \
                            index_page_node_url)+'Snh_'+introspect.name
                        introspect_response = self.parse_response(introspect_url)
                        op_file.write(introspect_response.prettify())
                        op_file.write(END_OF_TEXT)
                        if introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                            for sandesh_trace_buf in introspect_response.findAll(attrs={"link":"SandeshTraceRequest"}):
                                op_file.write(START_MARKER(sandesh_trace_buf.text)+"\n"+sandesh_trace_buf.text+"\n"+END_MARKER(sandesh_trace_buf)+"\n")
                                sandesh_trace_url = re.sub(r'(http.*/).*$', r'\1', index_page_node_url)+'Snh_SandeshTraceRequest?x='+ "{}".format(sandesh_trace_buf.text)
                                op_file.write(self.parse_response(sandesh_trace_url).prettify())
                                op_file.write(END_OF_TEXT)                            
                        op_file.flush()
            except UnboundLocalError:
                pass
            except Exception as exp:
                #import pdb; pdb.set_trace()
                print("Exception {} occurred for {}\nUnable to create output file: {}\n".format(type(exp), threading.current_thread().getName(), filename))
            self.__output_files.append(filename)
            queue.task_done()
        return

    def fetch_all_introspects(self):
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
        print("Current active thread count is {}\n".format(threading.active_count()))
        for introspect_thread in threads:
            introspect_thread.join()

    def archive_all_files(self):
        with tarfile.open("all_introspects.tgz", mode="w:gz") as tar:
            for file in self.__output_files:
                try:
                    archive_name = "all-introspects/"+file.strip("/tmp/")
                    tar.add(file, arcname=archive_name)
                except tarfile.TarError as terr:
                    print("Failed to create a tar file archive due to error:\n{}".format(type(terr)))
                except Exception as tarexp:
                    print("Exception of type {} occurred when adding file {} to tar archive\n{}".format(type(tarexp), file, tarexp))
        tar.close()
        self.delete_tmp_files(self.__output_files)
        return

    @staticmethod
    def delete_tmp_files(files_to_delete):
        for file in files_to_delete:
            rm_file_op = subprocess.Popen('rm  {}'.format(file), shell=True, stderr=subprocess.PIPE)
            if rm_file_op.stderr.read():
                print("Failed to delete file {} due to error:\n{}".format(file, rm_file_op.stderr.read()))
        return