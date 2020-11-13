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
+ contrail-scrape requires python version 3.5 and later.
+ requires a linux system pre-installed with python3-pip.
+ runs on Ubuntu 16.04 and later
+ runs on Red Hat RHEL 7.5 and later

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
#### Example 1
```
$contrail-scrape --control 10.85.188.101 --config 10.85.188.102 --analytics 10.85.188.103 --vrouter 10.85.180.79

API Scraping Progress: 100%|████████████████████████████████████| 55/55 [01:11<00:00,  1.30s/thread]

Finishing introspection of all nodes
No Errors reported
Begining archive process..
```

#### Example 2
```
$contrail-scrape --yaml-config ~/contrail-scrape/hosts.yaml

API Scraping Progress: 100%|██████████████████████████████████| 186/186 [07:50<00:00,  2.53s/thread]

Finishing introspection of all nodes with Errors
Please check log file /var/log/scrape-2020-11-12-18:58:59-PST.log for details
Begining archive process..
```
<script src="https://gist.github.com/aniruddhamonker/f49074b50b09ec89a0aec35505204b77.js"></script>
