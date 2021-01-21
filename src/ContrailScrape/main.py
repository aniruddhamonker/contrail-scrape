import sys
import ContrailScrape

version = "0.1.13"

def get_version():
    print("CONTRAIL-SCRAPE\nVERSION: {}".format(version))
    sys.exit()

def fetch_all_introspects(introspect_args, thread_count, debug):
    if introspect_args:
        introspect = ContrailScrape.IntrospectClass(introspect_args, thread_count, debug)
        return introspect.fetch_all_introspects()

def fetch_analytics_api(api_args, debug):
    if api_args:
        analytics_api = ContrailScrape.AnalyticsApiClass(debug)
        return analytics_api.fetch_all_analytics_apis(api_args)

def main():
    config_parser = ContrailScrape.ConfigParser()
    all_urls = config_parser()
    all_args = config_parser.all_args
    base = ContrailScrape.BaseClass()
    base.timeout = all_args.api_timeout
    if config_parser.version:
        get_version()
    try:
        introspect_args = list(filter(lambda arg: arg.get('type') == "introspect", all_urls))
        fetch_all_introspects(introspect_args, all_args.threads, config_parser.debug)
        analytics_api_args = list(filter(lambda arg: arg.get('type') == "analytics-api", all_urls))
        fetch_analytics_api(analytics_api_args, config_parser.debug)
        base.archive_all_files()
    except KeyboardInterrupt:
        print("Interrupted\n")
        print("Performing Cleanup...")
        base.delete_tmp_files()
        sys.exit(0)

if __name__ == "__main__":
    main()
