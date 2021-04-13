import pytest
import requests

class MockResponse():
        def __init__(self, sample_xml_fixture):
            self.text = sample_xml_fixture
            self.status_code = '200'

        def raise_for_status(self):
            return None

@pytest.fixture(autouse=True)
def mock_requests(monkeypatch, sample_xml_response):
    #setting mock object
    def mock_requests_get(*args, **kwargs):
        return MockResponse(sample_xml_response)
    monkeypatch.setattr(requests, "get", mock_requests_get)

@pytest.fixture(autouse=True)
def sample_xml_response():
    response = '''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head><link href="css/style.css" rel="stylesheet" type="text/css"/><title>contrail-vrouter-agent</title></head><body>
    <h1>Modules for contrail-vrouter-agent</h1>
    <a href="agent.xml">agent.xml</a><br/>
    <a href="agent_profile.xml">agent_profile.xml</a><br/>
    <a href="agent_stats_interval.xml">agent_stats_interval.xml</a><br/>
    <a href="cfg.xml">cfg.xml</a><br/>
    <a href="controller.xml">controller.xml</a><br/>
    <a href="cpuinfo.xml">cpuinfo.xml</a><br/>
    <a href="diag.xml">diag.xml</a><br/>
    <a href="discovery_client_stats.xml">discovery_client_stats.xml</a><br/>
    <a href="flow_stats.xml">flow_stats.xml</a><br/>
    <a href="ifmap_agent.xml">ifmap_agent.xml</a><br/>
    <a href="kstate.xml">kstate.xml</a><br/>
    <a href="multicast.xml">multicast.xml</a><br/>
    <a href="pkt.xml">pkt.xml</a><br/>
    <a href="port_ipc.xml">port_ipc.xml</a><br/>
    <a href="sandesh_trace.xml">sandesh_trace.xml</a><br/>
    <a href="sandesh_uve.xml">sandesh_uve.xml</a><br/>
    <a href="services.xml">services.xml</a><br/>
    <a href="stats.xml">stats.xml</a><br/>
    <a href="stats_interval.xml">stats_interval.xml</a><br/>
    <a href="task.xml">task.xml</a><br/>
    <a href="xmpp_server.xml">xmpp_server.xml</a><br/>
    </body></html>
    '''
    return response
