import requests
from bs4 import BeautifulSoup as bs
import html5lib
import re
import tarfile
import os
import time
import subprocess
from collections import defaultdict
from ContrailScrape import logger

class BaseClass:
    def __init__(self):
        self.__timeout = 10
        pass
    
    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, secs):
        self.__timeout = secs

    @classmethod
    def get_request(cls, url, retrcnt=3):
        # type: (IntrospectBaseClass, str, int) -> str
        try:
            response = requests.get(url, timeout=BaseClass().timeout) # type: requests.models.Response
            response.raise_for_status()
            logger.debug("Fetched url '{}' with response code: {}"\
            .format(url, response.status_code))
            return response.text
        except requests.exceptions.ReadTimeout:
            if retrcnt >=1:
                cls.get_request(url, retrcnt-1)
            else:
                logger.error("Skipping url: {}; Multiple Read Timeouts Occurred, attempts tried: 3"\
                     .format(url))
        except requests.exceptions.ConnectionError:
            if len(url.split('/')) == 3:
                print("Error Connecting node: {}".format(url))
                print("Hint: Check if introspect port is correct")
                logger.error("Error Connecting node: {}".format(url))
            else:
                if retrcnt >=1:   
                    cls.get_request(url, retrcnt-1)
                else:                
                    logger.error("Error Connecting node: {} for introspect {}"\
                    .format(url.split('/')[2], url.split('/')[-1]))
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
            raise ValueError
        #handling memory leak in Beautifulsoup xml parser with large payload
        #using lxml parser for large payloads
        if len(text_response) > 200000000:
            logger.debug("{} has payload larger than 200MB, using lxml parser".format(url))
            parsed_response = bs(text_response, 'lxml')
        else:
            parsed_response = bs(text_response, 'xml') # type: bs4.BeautifulSoup
        if attrs is None:
            if 'Snh_PageReq?x=' not in url and parsed_response.find("PageReqData"):
                if parsed_response.find("PageReqData").find("next_page").text:
                    all_pages = parsed_response.find("PageReqData").find("all").text
                    url = re.sub(r'(http:.*/).*$',r'\1Snh_PageReq?x=', url) + all_pages
                    parsed_response, next_batch = cls.parse_response(url)
            if parsed_response.find("next_batch"):
                next_batch = {
                    'link': parsed_response.find("next_batch").attrs['link'],
                    'text': parsed_response.find("next_batch").text
                    }
                # url = 'Snh_{}?x={}'.format(link, text)
                return parsed_response, next_batch
            else:
                return parsed_response, None
        def __iter__():
            for element in parsed_response.findAll(attrs=attrs):
                yield element
        return __iter__()

    @staticmethod
    def _get_output_dir(*index_node_args):
        tmp_dir = "/tmp/scrape/{}-{}/{}".format(index_node_args[0], \
            index_node_args[1], index_node_args[2]) # type: str
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        return tmp_dir

    @staticmethod
    def create_and_write_files(filename, file_content):
        try:
            with open(filename, 'w') as op_file:
                op_file.write(file_content)
                op_file.flush()
        except Exception as exp:
            logger.error("Exception {} occurred\n".format(exp))
            logger.error("Failed to create output file {}".format(filename))
        return

    def archive_all_files(self):
        # type: () -> None
        print("Begining archive process..\n")
        with tarfile.open("contrail-scrape.tgz", mode="w:gz") as tar:
            try:
                tar.add('/tmp/scrape', arcname='scrape')
            except tarfile.TarError as terr:
                logger.error("Failed to create a tar file archive due to error: {}"\
                    .format(type(terr)))
            except Exception as tarexp:
                logger.error("Exception of type {} occurred when archiving files {}"\
                    .format(type(tarexp), tarexp))
        tar.close()
        self.delete_tmp_files()
        return

    @staticmethod
    def delete_tmp_files():
        rm_file_op = subprocess.Popen('rm  -rf {}'\
            .format('/tmp/scrape'), shell=True, stderr=subprocess.PIPE)
        if rm_file_op.stderr.read():
            logger.error("Failed to perform cleanup due to error: {}"\
                .format(rm_file_op.stderr.read()))
        return