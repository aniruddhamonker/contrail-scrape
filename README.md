# contrail-scrape
Contrail-scrape is an introspect and API scraping tool for contrail versions 3.2 and later.
It uses threads for concurrency and the number of threads can be adjusted based on the cluster environment and API utilization.
In the current version, contrail-scrape supports introspect data collection for the following contrail nodes
+ control(contrail-control, dns)
+ config(api, schema, discovery, svc-monitor, device-manager)
+ vrouter
+ analytics(api, collector, alarmgen, query)

contrail-scrape also supports API scraping of analytics-api uve-alarms and queries.
