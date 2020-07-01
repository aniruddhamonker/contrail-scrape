from collections import namedtuple

module = namedtuple("mod", "name, option, help, port")    
module_args = {
    "vrouter": module("--vrouter", "-vr","contrail-vrouter", "8085"),
    "cconfig": module("--cconfig", "-cfg", "contrail-config", "8084"),
    "ccontrol": module("--ccontrol", "-cnt", "contrail-control", "8083"),
    "canalytics": module("--canalytics", "-can", "contrail-analytics-api", "8090"),
    "alarm-gen": module("--alarmgen", "-alg", "contrail-analytics-alargen", "5995"),
    "discovery": module("--discovery", "-dis", "contrail-discovery", "5997"),
    "schema": module("--schema", "-sch", "contrail-schema", "8087"),
    "svc-monitor": module("--svc-mon", "-svc", "contrail-svc-monitor", "8088"),
    "collector": module("--collector", "-col", "contrail-analytics-collector", "8089")
    # "device-manager": module("--device-manager", "-dm", "contrail-device-manager", "8096"),
    # "contrail-dns": module("--contrail-dns", "-dns", "contrail-dns", "8092"),
    # "contrail-query-engine": module("--contrail-qe", "-qe", "contrail-query-engine", "8091"),
    # "contrail-analytics-nodemgr": module("--nodemgr-analytics", "-nodemgr-anal", "contrail-analytics-nodemgr", "8104"),
    # "contrail-config-nodemgr": module("--nodemgr-config", "-nodemgr-cfg", "contrail-config-nodemgr", "8100"),
    # "contrail-control-nodemgr": module("--nodemgr-control", "-nodemgr-cnt", "contrail-control-nodemgr", "8101"),
    # "contrail-database-nodemgr": module("--nodemgr-databsae", "-nodemgr-db", "contrail-database-nodemgr", "8103"),
    # "contrail-vrouter-nodemgr": module("--nodemgr-vrouter", "-nodemgr-vr", "contrail-vrouter-nodemgr", "8102")
}