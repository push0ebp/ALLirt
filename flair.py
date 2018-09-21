import re
import os
import subprocess
import shutil
from tempfile import TemporaryDirectory
import logging

from patoolib import extract_archive


class FlairNotSupportedError(Exception):
    pass

class FlairError(Exception):
    pass

class FlairUtilNotFoundError(Exception):
    pass

class Flair():
    _dir_names = {}
    _logger = None
    _MESSAGES = {'reloc': 'Unknown relocation type',
                'processor': 'Unknown processor type',}
    _FILE_NAMES = {'data':'data.tar',
                  'data_gz': 'data.tar.gz'}
    def __init__(self, flair='flair', log_level=logging.WARNING):
        if not os.path.exists(flair):
            raise FlairError('flair directory not found.')
            
        self._dir_names = {'temp' : 'temp', 
                         'flair' : flair}

        self._logger = logging.getLogger('Flair')
        self._logger.setLevel(log_level)
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        stream_handler.setFormatter(formatter)
        self._logger.addHandler(stream_handler)
    
    def _clean_exc(self, exc_name):
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
        if os.path.exists(sig_name):
            raise FileExistsError(sig_name)

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
        
        flair_dir = self._dir_names['flair']
        pelf = os.path.join(flair_dir, 'pelf')
        if not os.path.exists(pelf):
            raise FlairUtilNotFoundError('pelf util not found. check your flair directory.')

        args = [pelf, lib_name, pat]
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        if self._MESSAGES['reloc'].encode() in err:
            #thanks to hstocks
            self._logger.warning(self._MESSAGES['reloc'])
            try:
                reloc_type, offset = re.findall(r'type (\d+).*?=(0x\d+)', err.decode())[0]
            except IndexError:
                raise FlairNotSupportedError('pelf: this library is not supported')

            reloc_option = '-r{}:{}:0'.format(reloc_type, offset)
            args = [pelf, reloc_option, lib_name, pat]
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            if self._MESSAGES['reloc'].encode() in err:                
                raise FlairNotSupportedError('pelf: this architecture is not supported')
        
        
        if self._MESSAGES['processor'].encode() in err:
            raise FlairNotSupportedError('pelf: this processor is not supported')
        
        if not os.path.getsize(pat):
            raise FlairError('pelf: Error {}'.format(err,))

        sigmake = os.path.join(flair_dir, 'sigmake')
        if not os.path.exists(sigmake):
            raise FlairUtilNotFoundError('sigmake util not found. check your flair directory.')

        if sig_desc:
            args = [sigmake, '-n{}'.format(sig_desc), pat, sig]
        else:
            args = [sigmake, pat, sig]
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        exit_code = process.wait()    
        if exit_code != 0 and os.path.exists(exc): #if it has collision
            self._clean_exc(exc)
            exit_code = subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if exit_code != 0:
            raise FlairError('sigmake: Unknown Error')

        if is_compress:
            zipsig = os.path.join(flair_dir, 'zipsig')
            if not os.path.exists(zipsig):
                raise FlairUtilNotFoundError('zipsig util not found. check your flair directory.')

            args = [zipsig, sig]  
            subprocess.call(args, stdout=subprocess.DEVNULL)
        
        try:
            os.remove(pat)
            os.remove(exc)
        except:
            pass
        return True

    def _extract_deb(self, deb_name, out_name):
        extract_archive(deb_name, outdir=out_name, verbosity=-1)
        if not os.path.exists(os.path.join(out_name, 'usr')): #data.tar extracted
            data = os.path.join(out_name, self._FILE_NAMES['data'])
            extract_archive(data, outdir=out_name, verbosity=-1)
            if not os.path.exists(data): #deb extract not working
                args = ['ar','x', deb_name, self._FILE_NAMES['data_gz']]
                subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                data = os.path.join(out_name, self._FILE_NAMES['data_gz'])
                if not os.path.exists(self._FILE_NAMES['data_gz']):
                    raise FlairError('deb: Extract error')
                os.rename(self._FILE_NAMES['data_gz'], data)
        return True

    def _extract_a(self, deb_name, a_name, out_name): #deb -> extract -> copy a
        if os.path.exists(out_name):
            raise FileExistsError(out_name)
        
        with TemporaryDirectory() as temp:
            self._extract_deb(deb_name, temp)
            usr = os.path.join(temp, 'usr')
            lib_name = ''
            for deb_dir in os.listdir(usr):
                if deb_dir.startswith('lib'):
                    lib_name = deb_dir
                    break
            if not lib_name:
                raise FlairError('deb: Package Error')
            
            lib = os.path.join(usr, lib_name)
            a = os.path.join(lib, a_name)
            if not os.path.exists(a): #libc.a not exists in ./usr/lib
                platforms = list(filter(lambda x: os.path.isdir(os.path.join(lib, x)), os.listdir(lib)))
                if len(platforms) >= 1:
                    if len(platforms) != 1:
                        self._logger.warning('warning: multi platforms found')

                    platform = ''
                    for relative_dir, dirs, filenames in os.walk(lib):
                        for filename in filenames:
                            if filename == a_name:
                                platform = relative_dir
                                break
                    if platform == '':
                        raise FlairError('deb: Platform not found')
                    a = os.path.join(lib, platform, a_name)
                else:
                    raise FlairError('deb: Platform not found')
            os.rename(a, out_name)
            a_lib_path = a.replace(temp, '.')
        return a_lib_path

    def deb_to_sig(self, deb_name, a_name, sig_name='', sig_desc='', is_compress=True):
        with TemporaryDirectory() as temp:
            a = os.path.join(temp, a_name)
            if not sig_name:
                sig_name = '{}.sig'.format(os.path.splitext(deb_name)[0])
            if os.path.exists(sig_name):
                raise FileExistsError(sig_name)
            
            a_lib_path = self._extract_a(deb_name, a_name, a)
            self.make_sig(a, sig_name, sig_desc=sig_desc, is_compress=is_compress)  
            
            info = {'a': a_lib_path, 
                    'sig': sig_name}
            
            return info