import re
import os
import subprocess
import shutil
import tempfile
import logging

from patoolib import extract_archive
from requests_html import HTMLSession, requests

class Launchpad():
    session = None
    
    ARCHIVE_HOST = 'launchpad.net'
    ARCHIVE_PAGE = {'suffix':{'os':'+series',
                              'arch':'+builds'},
                    'selector':{'os':'#maincontent .series strong a:first-child',
                                'arch':'#arch_tag option',
                                'file_url':'#downloadable-files li a'}
                   }

    def __init__(self):
        self.session = HTMLSession()

    def download_package(self, os_name, os_series, arch, package, package_version, filename=''):
        package_info_url = 'https://{}/{}/{}/{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, os_series, arch, package, package_version)    
        print(package_info_url)
        res = self.session.get(package_info_url)
        
        download_url = res.html.find(self.ARCHIVE_PAGE['selector']['file_url'], first=True).attrs['href']
        if not filename:
            filename = os.path.basename(download_url).replace('-dev','')
        res = requests.get(download_url, stream=True) #using requests because of unknown error
        with open(filename, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
            size = f.tell()
        return size
        
    def get_pacakge_versions(self, os_name, os_series, arch, package):
        path = '/{}/{}/{}/{}'.format(os_name, os_series, arch, package)
        url = 'https://{}{}'.format(self.ARCHIVE_HOST, path)    
        #url = 'https://launchpad.net/ubuntu/precise/amd64/libc6-dev'
        res = self.session.get(url)
        #open('1.html', 'w').write(res.content.decode())
        #html = open('1.html', 'r').read()
        
        #links = re.findall(r'link="(.*?)"', html)
        links = res.html.links
        package_versions = []
        for link in links:
            if link.startswith(path):
                package_versions.append(link.split('/')[-1])
        package_versions.sort()
        return package_versions
    
    def get_os_series(self, os_name):
        url = 'https://{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, self.ARCHIVE_PAGE['suffix']['os'])
        res = self.session.get(url)
        series_list = res.html.find(self.ARCHIVE_PAGE['selector']['os'])
        result_series_list = []
        for series in series_list:
            name = series.attrs['href'].split('/')[-1]
            version = series.text.split('(')[1].split(')')[0]

            result_series_list.append((name,version))
        return result_series_list[::-1]

    def get_os_architectures(self, os_name, os_series):
        url = 'https://{}/{}/{}/{}'.format(self.ARCHIVE_HOST, os_name, os_series, self.ARCHIVE_PAGE['suffix']['arch'])
        res = self.session.get(url)
        archs = []
        element_archs = res.html.find(self.ARCHIVE_PAGE['selector']['arch'])
        for element_arch in element_archs:
            if not element_arch.attrs['value'] == 'all':
                archs.append(element_arch.attrs['value'])
        return archs


class Flair():
    DIR_NAMES = {'temp' : 'temp', 
                 'flair' : 'flair70',}
    
    def get(self):
        #url = 'http://ftp.ubuntu.com/ubuntu/pool/main/e/eglibc/'
        url = 'http://turul.canonical.com/pool/main/g/glibc/'
        res = requests.get(url)
        s = res.content.decode() 
        #open('g.html','w').write(s)
        
        #s = open('e.html','r').read()
        debs = re.findall(r'"([\w\-\._]+\.deb)"',s)
        packages = []
        #r = re.compile(r'"(.+?)_(.+?)_(.+?)\.deb"')
        r = re.compile(r'"(?P<name>[\w-]+)_(?P<version>[\d.-]+)-(?P<os>[\w.]+)_(?P<arch>[\w\-_]+).deb"')
        m = r.match('"{}"'.format(debs[0]))
        #map(lambda deb: packages.append(r.findall(deb)), debs)
        archs = []
        for m in r.finditer(s):
            packages.append(m.groupdict())
        #list(map(lambda x: archs.append(x['arch']), packages))
        #print(set(archs))

    
    def __clean_exc(self, exc_name):
        with open(exc_name, 'r') as f:
            s = f.read()
            
        with open(exc_name, 'w') as f:   
            cleaned_funcs = []
            s = re.sub(r';.+', '', s).strip()
            funcs_pairs = s.split(os.linesep*2)
            for funcs_pair in funcs_pairs:
                funcs = funcs_pair.splitlines()
                start = 0
                if len(funcs) > 1: #if only one collision, not add '+' 
                    cleaned_funcs.append('+' + funcs[0])
                    start +=1 
                funcs.append('') #double linesep
                cleaned_funcs.extend(funcs[start:])
            s = os.linesep.join(cleaned_funcs)
            f.write(s)
        return True

    def make_sig(self, lib_name, sig_name, sig_desc='', is_compress=True):
        
        lib, ext = os.path.splitext(lib_name)
        pat = lib + '.pat'
        sig_base, ext = os.path.splitext(sig_name)
        exc = sig_base + '.exc'
        sig = sig_name
        
        try: #clean
            os.remove(pat)
            os.remove(sig)
            os.remove(exc)
        except:
            pass
        
        flair_dir = self.DIR_NAMES['flair']
        pelf = os.path.join(flair_dir, 'pelf')
        args = [pelf, lib_name, pat]
        subprocess.call(args, stderr=subprocess.DEVNULL)
        
        if not os.path.exists(pat):
            raise 'pelf: Error'

        sigmake = os.path.join(flair_dir, 'sigmake')
        args = [sigmake]
        if sig_desc:
            args.append('-n{}'.format(sig_desc))
        args += [pat, sig]
        exit_code = subprocess.call(args, stderr=subprocess.DEVNULL)
        
        if exit_code != 0 and os.path.exists(exc): #if it has collision
            self.__clean_exc(exc)
            exit_code = subprocess.call(args, stderr=subprocess.DEVNULL)
        if exit_code != 0:
            raise 'sigmake: Unknown Error'

        if is_compress:
            zipsig = os.path.join(flair_dir, 'zipsig')
            args = [zipsig, sig]  
            subprocess.call(args, stdout=subprocess.DEVNULL)
        
        try:
            os.remove(pat)
            os.remove(exc)
        except:
            pass
        return True

    def __extract_deb(self, deb_name, out_name):
        extract_archive(deb_name, outdir=out_name, verbosity=-1)
        data = os.path.join(out_name, 'data.tar')
        extract_archive(data, outdir=out_name, verbosity=-1)
        return True

    def __extract_a(self, deb_name, a_name, out_name): #deb -> extract -> copy a
        temp = tempfile.mkdtemp()
        self.__extract_deb(deb_name, temp)
    
        usr = os.path.join(temp, 'usr')
        lib_name = ''
        for deb_dir in os.listdir(usr):
            if deb_dir.startswith('lib'):
                lib_name = deb_dir
                break
        if not lib_name:
            raise 'deb: Package Error'
        
        lib = os.path.join(usr, lib_name)
        a = os.path.join(lib, a_name)
        if not os.path.exists(a):
            platforms = os.listdir(lib)
            if len(platforms) > 1:
                self.logger.warning('warning: multi platforms found')
            elif len(platforms) == 1:
                a = os.path.join(lib, platforms[0], a_name)
            else:
                raise 'deb: Platform not found'
        
        os.rename(a, out_name)
        shutil.rmtree(temp)
        return True

    def deb_to_sig(self, deb_name, a_name, sig_name, sig_desc=''):
        temp = tempfile.mkdtemp()
        a = os.path.join(temp, a_name)
        self.__extract_a(deb_name, a_name, a)
        self.make_sig(a, sig_name, sig_desc=sig_desc)  
        shutil.rmtree(temp)      

class Allirt():
    flair = None
    archive = None
    os_name = ''
    package_name = ''

    def __init__(self, os_name, package_name):
        self.flair = Flair()
        self.archive = Launchpad()
        self.os_name = os_name
        self.package_name = package_name

    def download(self):
        os_name = self.os_name
        series_list = self.archive.get_os_series(os_name)
        for series_name, series_version  in series_list:
            archs = self.archive.get_os_architectures(os_name, series_name)
            for arch in archs:
                package_versions = self.archive.get_pacakge_versions(os_name, series_name, arch, self.package_name)
                print(series_version, arch, package_versions)
                
allirt = ALLirt('ubuntu', 'libc6-dev')
allirt.download()
#db.get()
#db.extract_a('/Users/push0ebp/Downloads/deb/libc6-dev_2.15-0ubuntu10.18_i386.deb', 'libc.a', './libc.a')
#db.make_sig('libc.a', 'libc2.sig', 'Ubuntu 12.04')
#db.deb_to_sig('/Users/push0ebp/Downloads/deb/libc6-dev_2.15-0ubuntu10.18_i386.deb', 'libc.a', 'libc.sig', 'Ubuntu 12.04')
#versions = db.get_pacakge_versions('ubuntu','precise','amd64','libc6-dev')
#db.download_package('ubuntu','precise','amd64','libc6-dev',versions[1])
#series = db.launchpad.get_os_series('ubuntu')

#db.launchpad.get_os_architectures('ubuntu', series[-1][0])





