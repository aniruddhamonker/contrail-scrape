# contrail-scrape
Contrail-scrape is an introspect and API scraping tool for contrail versions 3.2 and later.
It also has a built in analyzer component which is a modified IST script for offline analysis of introspect data.
contrail-scrape uses threads for concurrency and the number of threads can be adjusted based on the cluster environment and API utilization.

In the current version, contrail-scrape supports introspect data collection of the following contrail nodes
+ control(contrail-control, dns)
+ config(api, schema, discovery, svc-monitor, device-manager)
+ vrouter
+ analytics(api, collector, alarmgen, query)

Besides introspect collection, contrail-scrape also supports API scraping of analytics-api's uves, uve alarms.

## Platforms & Supportibility
+ Requires python version 3.5 and later.
+ Requires a linux system pre-installed with python3-pip.
+ Runs on Ubuntu 16.04 and later
+ Runs on Red Hat RHEL 7.5 and later

## Installation
+ contrail-scrape is packaged and available for installation using pip.

$pip install contrail-scrape

+ If installation inside virtualenv is desired:

$mkdir ~/contrail-scrape

$python3 -m venv ~/contrail-scrape --system-site-packages

$source ~/contrail-scrape/bin/activate

$pip install contrail-scrape

## Usage
### Help
```
$contrail-scrape --help

A tool to scrape APIs and Introspects of various Contrail nodes

optional arguments:
  -h, --help            show this help message and exit
  --yaml-config FILE    path to YAML configuration file
  --vrouter HOST        contrail-vrouter
  --config HOST         contrail-config
  --control HOST        contrail-control
  --analytics HOST      contrail-analytics-api introspect
  --alarmgen HOST       contrail-analytics-alarmgen
  --discovery HOST      contrail-discovery
  --schema HOST         contrail-schema
  --svc-monitor HOST    contrail-svc-monitor
  --collector HOST      contrail-analytics-collector
  --dev-mgr HOST        contrail device manager
  --dns HOST            contrail-dns
  --query HOST          contrail-query-engine
  --analytics-api HOST  contrail analytics uves and alarms
  --version             print the version number
  --debug               turn on debug mode
  --threads THREADS     control the number of threads, default=50
  --api-timeout API_TIMEOUT
                        set API requests timeout in secs, default=10sec
```

### Usage Examples
#### Usage 1
```
$contrail-scrape --control 10.85.188.101 --config 10.85.188.102 --analytics 10.85.188.103 --vrouter 10.85.180.79

API Scraping Progress: 100%|████████████████████████████████████| 55/55 [01:11<00:00,  1.30s/thread]

Finishing introspection of all nodes
No Errors reported
Begining archive process..
```

#### Usage 2 (Using YAML input)
```
$contrail-scrape --yaml-config ~/contrail-scrape/hosts.yaml

API Scraping Progress: 100%|██████████████████████████████████| 186/186 [07:50<00:00,  2.53s/thread]

Finishing introspection of all nodes with Errors
Please check log file /var/log/scrape-2020-11-12-18:58:59-PST.log for details
Begining archive process..
```

sample hosts.yaml : https://gist.github.com/aniruddhamonker/f49074b50b09ec89a0aec35505204b77

#### Usage 3 (custom introspect ports)
```
$contrail-scrape --vrouter 10.85.180.80:8096 --vrouter 10.85.180.79:8096

API Scraping Progress: 100%|████████████████████████████████████| 42/42 [01:30<00:00,  2.16s/thread]

Finishing introspection of all nodes
No Errors reported
Begining archive process..
```

#### Usage 4 (Analytics-api uves and alarms)
```
$contrail-scrape --analytics-api 10.85.188.101

Analytics-api Progress: 100%|█████████████████████████████████████| 28/28 [00:56<00:00,  2.02s/uves]

Finishing api scraping of all analytics nodes
No Errors reported
Begining archive process..
```

# Analyzing Introspect Data
All the introspect data collected by the contrail-scrape is pretty formated as xml. The data is saved into a single tar.gz archive. The file is saved under local directory from where contrail-scrape is run.
```
# ls -l contrail-scrape*
-rwxrwxrwx 1 aniruddh aniruddh 242752 Nov 12 20:00 contrail-scrape.tgz
```

Once the file is extracted, the data is saved under directory named **scrape** and structured into multiple sub-directories based on the type of introspect node.
Each of the sub-directory corresponds to introspect type for each type of node(control, config, etc..)

```
# tree -L 2 scrape/
scrape/
├── 10.85.188.101-analytics
│   ├── alarmgen_ctrl
│   ├── analytics_api_info
│   ├── cpuinfo
│   ├── redis
│   ├── sandesh_alarm
│   ├── sandesh_ctrl
│   ├── sandesh_trace
│   └── sandesh_uve
├── 10.85.188.101-config
│   ├── cpuinfo
│   ├── discovery_client_stats
│   ├── greenlets
│   ├── sandesh_alarm
│   ├── sandesh_ctrl
│   ├── sandesh_trace
│   └── sandesh_uve
------skipped----------
```
check https://gist.github.com/aniruddhamonker/81ed43dac81e77d4e7fd9be2e451b402 for the entire structure

## Contrail-scrape-ist
Although the data is pre-formatted as xml and can be directly printed from the corresponding introspect files, contrail-scrape also packages a modified IST script **contrail-scrape-ist** to assist with offline analysis and troubleshooting.

Ref IST: https://github.com/vcheny/contrail-introspect-cli/blob/master/ist.py

```
# contrail-scrape-ist --help
usage: contrail-scrape-ist [-h] [--version] [--debug]
                           {alarmgen,analytics,collector,config,control,devmgr,discovery,dns,query,schema,svc-monitor,vrouter}
                           ...

A script to make Contrail Introspect output CLI friendly.

positional arguments:
  {alarmgen,analytics,collector,config,control,devmgr,discovery,dns,query,schema,svc-monitor,vrouter}
    alarmgen            contrail-alarm-gen
    analytics           contrail-analytics-api
    collector           contrail-collector
    config              contrail-api
    control             contrail-control
    devmgr              contrail-device-manager
    discovery           contrail-discovery
    dns                 contrail-dns
    query               contrail-query-engine
    schema              contrail-schema
    svc-monitor         contrail-svc-monitor
    vrouter             contrail-vrouter-agent

optional arguments:
  -h, --help            show this help message and exit
  --version             Script version
  --debug               Verbose mode
 ```

### Usage Contrail-scrape-ist
To start analyzing data using contrail-scrape-ist, change the working directory to the introspect node that needs to be analyzed.
```
$cd scrape/
scrape$ ls -l
total 0
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.180.79-kernel
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.180.80-dpdk
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.101-analytics
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.101-config
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.101-control
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.102-analytics
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.102-config
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.102-control
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.103-analytics
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.103-config
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.103-control
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.104-kernel
drwxrwxrwx 1 root root 4096 Nov 12 20:18 10.85.188.105-kernel
```
The following example shows the usage of contrail-scrape-ist script to analyze data of a contrail control node.
The instructions to analyze the data from any other node are identical.
```
scrape$cd 10.85.188.101-control
scrape/10.85.188.101-control$contrail-scrape-ist control --help

positional arguments:
  {status,cpu,trace,uve,nei,ri,route,mcast,bgp_stats,xmpp,ifmap,sc,config,rt}
    status              Node/component status
    cpu                 CPU load info
    trace               Sandesh trace buffer
    uve                 Sandesh UVE cache
    nei                 Show BGP/XMPPP neighbors
    ri                  Show routing instances
    route               Show route info
    mcast               Show multicast managers
    bgp_stats           Show BGP server stats
    xmpp                Show XMPP info
    ifmap               Show IFMAP info
    sc                  Show ServiceChain info
    config              Show related config info
    rt                  Show RtGroup info

optional arguments:
  -h, --help            show this help message and exit

scrape/10.85.188.101-control$contrail-scrape-ist control status
Loading from introspect xml:  /mnt/c/Users/aamonker/Documents/Contrail/Repositories/contrail-introspect_scrapper/scrape/10.85.188.101-control/sandesh_uve/NodeStatus
module_id: contrail-control
state: Functional
description
+-----------+-------------+-----------------------+--------+--------------------------------------+
| type      | name        | server_addrs          | status | description                          |
+-----------+-------------+-----------------------+--------+--------------------------------------+
| IFMap     | IFMapServer |   172.18.101.101:8443 | Up     | Connection with IFMap Server (irond) |
| Collector | n/a         |   172.18.101.101:8086 | Up     | Established                          |
| Discovery | Collector   |   172.18.101.100:5998 | Up     | SubscribeResponse                    |
| Discovery | IfmapServer |   172.18.101.100:5998 | Up     | SubscribeResponse                    |
| Discovery | xmpp-server |   172.18.101.100:5998 | Up     | Publish Response - HeartBeat         |
+-----------+-------------+-----------------------+--------+--------------------------------------+
```
The output also displays the target introspect file that is being used to populate the above data. This is helpful if any data required from an introspect is missing in the output displayed by contrail-scrape-ist script.
