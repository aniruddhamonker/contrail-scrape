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
contrail-scrape is packaged and available for installation using pip.

$pip install contrail-scrape



