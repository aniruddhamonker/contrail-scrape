import requests
from bs4 import BeautifulSoup as bs
import html5lib
import re
import tarfile
import os
import time
import subprocess
from collections import defaultdict
from main_logger import logger

class BaseClass:
    def __init__(self):
        pass

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
        logger.info("begining archive process..\n")
        with tarfile.open("contrail-scrape.tgz", mode="w:gz") as tar:
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