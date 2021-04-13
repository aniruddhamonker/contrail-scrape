from ContrailScrape import base
from bs4 import BeautifulSoup as bs
import pytest

base_obj = base.BaseClass()
base_class = base.BaseClass

def test_timeout():
    assert base_obj.timeout == 10
    
def test_get_request(monkeypatch, capsys, sample_xml_response):
    test_url = 'http://<introspect-node-ip-address:introspect-port>'
    assert base_class.get_request(test_url) == sample_xml_response
    monkeypatch.undo()
    test_connectionError_url = 'http://8.8.8.8:8085'
    
    base_class.get_request(test_connectionError_url)
    output = capsys.readouterr()
    assert output.out == "Error Connecting node: {}\nHint: Check if introspect port is correct\n"\
            .format(test_connectionError_url)

def test_parse_response(monkeypatch, mock_requests, sample_xml_response):
    test_url = 'http://<introspect-node-ip-address:introspect-port>'
    assert base_class.parse_response(test_url)[0] == bs(sample_xml_response, 'xml')

    text_response = base_class.parse_response(test_url)
    monkeypatch.setattr(text_response, "len", 200000001)
    assert base_class.parse_response(test_url) == bs(sample_xml_response, 'xml')

    monkeypatch.undo()
    with pytest.raises(Exception):
        assert base_class.parse_response(test_url)
    
    





