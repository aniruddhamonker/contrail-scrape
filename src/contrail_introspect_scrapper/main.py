
from base import IntrospectBaseClass

class VrouterIntrospect(IntrospectBaseClass):
    def __init__(self, url):
        super().__init__(url)
    
    def fetch_all_introspects(self):
        return self.fetch_all()

    @property
    def files_to_archive(self):
        return self.files_to_compress

    def archive_introspect_output_files(self):
            return self._archive_introspect_output_files(self.files_to_archive, self.__class__.__name__)
              
class ControllerIntrospect(IntrospectBaseClass):
    def __init__(self, url):
        super().__init__(url)
    
    def fetch_all_introspects(self):
        return self.fetch_all()

    @property
    def files_to_archive(self):
        return self.files_to_compress

    def archive_introspect_output_files(self):
            return self._archive_introspect_output_files(self.files_to_archive, self.__class__.__name__)

class ConfigIntrospect(IntrospectBaseClass):
    def __init__(self, url):
        super().__init__(url)
    
    def fetch_all_introspects(self):
        return self.fetch_all()

    @property
    def files_to_archive(self):
        return self.files_to_compress

    def archive_introspect_output_files(self):
            return self._archive_introspect_output_files(self.files_to_archive, self.__class__.__name__)

def main():
    '''
    def locate_introspect_module(url):
        modules = {'8085': VrouterIntrospect(url), '8083':'control', '8084':'config-api'}
        introspect_port = url.split(":")[-1]
        assert (introspect_port in modules), "Introspect for service on port {} is not available. Check introspect port".format(introspect_port)
        module = modules.get(introspect_port, lambda: "check introspect port\n")
        return module(url)
    '''

    url = "http://10.85.188.101:8084"
    introspect = ConfigIntrospect(url)
    introspect.fetch_all_introspects()
    introspect.archive_introspect_output_files()        
    
if __name__ == '__main__':
    main()