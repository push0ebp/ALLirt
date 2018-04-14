import os

from requests import Session, get as req_get
from bs4 import BeautifulSoup


class Launchpad():
    session = None
    
    ARCHIVE_HOST = 'https://launchpad.net'
    ARCHIVE_PAGE = {'suffix':{'os':'+series',
                              'arch':'+builds'},
                    'selector':{'os':'#maincontent .series strong a',
                                'arch':'#arch_tag option',
                                'file_url':'#downloadable-files li a'}
                   }

    def __init__(self):
        self.session = Session()

    #https://launchpad.net/ubuntu/lucid/i386/libc6-dev
    def get_download_info(self, os_name, os_series, arch, package, package_version):        
        package_info_url = '{}/{}/{}/{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, os_series, arch, package, package_version)    
        res = self.session.get(package_info_url)
        
        bs = BeautifulSoup(res.content, 'html.parser')
        bs_download_url = bs.select_one(self.ARCHIVE_PAGE['selector']['file_url'])
        
        filename = ''
        download_url = ''
    
        if bs_download_url:
            download_url = bs_download_url.get('href')
            filename = os.path.basename(download_url.replace('-dev',''))
            
        info = {'url' : download_url,
                'filename': filename}
        return info

    def download_package(self, os_name, os_series, arch, package, package_version, out_dir='.', filename=''):
        info = self.get_download_info(os_name, os_series, arch, package, package_version)
        if info['url']:
            if not filename:
                filename = info['filename']
            out = os.path.join(out_dir, filename)
            size = self.download_file(info['url'], out)
        else:
            size = 0
        info['size'] = size
        return info
    
    
    def download_file(self, download_url, filename):
        res = req_get(download_url, stream=True) #using requests because of unknown error
        with open(filename, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
            size = f.tell()
        return size
    
    def get_pacakge_versions(self, os_name, os_series, arch, package):
        path = '/{}/{}/{}/{}'.format(os_name, os_series, arch, package)
        url = '{}{}'.format(self.ARCHIVE_HOST, path)    
        
        res = self.session.get(url)
        bs = BeautifulSoup(res.content, 'html.parser')
        
        links = bs.find_all('a', href=True)
        package_versions = []
        for link in links:
            href = link.get('href')
            if href.startswith(path):
                package_versions.append(href.split('/')[-1])
        package_versions = list(set(package_versions))
        package_versions.sort()
        return package_versions
    
    def get_os_series(self, os_name):
        url = '{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, self.ARCHIVE_PAGE['suffix']['os'])
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
        url = '{}/{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, os_series, self.ARCHIVE_PAGE['suffix']['arch'])
        res = self.session.get(url)
        bs = BeautifulSoup(res.content, 'html.parser')
        
        archs = []
        element_archs = bs.select(self.ARCHIVE_PAGE['selector']['arch'])
        for element_arch in element_archs:
            if not element_arch.get('value') == 'all':
                archs.append(element_arch.get('value'))
        return archs

