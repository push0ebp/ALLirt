import re
import os
import subprocess
import shutil
import tempfile
import logging

from patoolib import extract_archive


class Flair():
    dir_names = {}
    logger = None

    def __init__(self, flair='flair'):
        self.dir_names = {'temp' : 'temp', 
                         'flair' : flair}
        self.logger = logging.getLogger('Flair')
        self.logger.setLevel(logging.WARNING)

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
        
        flair_dir = self.dir_names['flair']
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
            if len(platforms) >= 1:
                if len(platforms) == 1:
                    self.logger.warning('warning: multi platforms found')
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
