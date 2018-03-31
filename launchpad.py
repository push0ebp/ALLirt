import os

from requests import Session, get as req_get
from bs4 import BeautifulSoup


class Launchpad():
    session = None
    
    ARCHIVE_HOST = 'launchpad.net'
    ARCHIVE_PAGE = {'suffix':{'os':'+series',
                              'arch':'+builds'},
                    'selector':{'os':'#maincontent .series strong a',
                                'arch':'#arch_tag option',
                                'file_url':'#downloadable-files li a'}
                   }

    def __init__(self):
        self.session = Session()

    def download_package(self, os_name, os_series, arch, package, package_version, filename=''):
        package_info_url = 'https://{}/{}/{}/{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, os_series, arch, package, package_version)    
        res = self.session.get(package_info_url)
        
        bs = BeautifulSoup(res.content, 'html.parser')
        download_url = bs.select_one(self.ARCHIVE_PAGE['selector']['file_url'])
        if not download_url:
            return (0, '')
        download_url = download_url.get('href')
        if not filename:
            filename = os.path.basename(download_url).replace('-dev','')
        res = req_get(download_url, stream=True) #using requests because of unknown error
        with open(filename, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
            size = f.tell()
        return size, filename
        
    def get_pacakge_versions(self, os_name, os_series, arch, package):
        path = '/{}/{}/{}/{}'.format(os_name, os_series, arch, package)
        url = 'https://{}{}'.format(self.ARCHIVE_HOST, path)    
        
        res = self.session.get(url)
        bs = BeautifulSoup(res.content, 'html.parser')
        
        links = bs.find_all('a', href=True)
        package_versions = []
        for link in links:
            href = link.get('href')
            if href.startswith(path):
                package_versions.append(href.split('/')[-1])
        package_versions.sort()
        return package_versions
    
    def get_os_series(self, os_name):
        url = 'https://{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, self.ARCHIVE_PAGE['suffix']['os'])
        res = self.session.get(url)
        bs = BeautifulSoup(res.content, 'html.parser')
        series_list = bs.select(self.ARCHIVE_PAGE['selector']['os'])
        
        result_series_list = []
        for series in series_list:
            name = series.get('href').split('/')[-1]
            version = series.text.split('(')[1].split(')')[0]

            result_series_list.append((name,version))
        return result_series_list[::-1]

    def get_os_architectures(self, os_name, os_series):
        url = 'https://{}/{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, os_series, self.ARCHIVE_PAGE['suffix']['arch'])
        res = self.session.get(url)
        bs = BeautifulSoup(res.content, 'html.parser')
        
        archs = []
        element_archs = bs.select(self.ARCHIVE_PAGE['selector']['arch'])
        for element_arch in element_archs:
            if not element_arch.get('value') == 'all':
                archs.append(element_arch.get('value'))
        return archs

