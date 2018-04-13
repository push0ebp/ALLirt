import os
from datetime import datetime
import logging
import traceback

from flair import Flair
from launchpad import Launchpad

class Allirt():
    flair = None
    archive = None
    os_name = ''
    package_name = ''

    logger = None
    SKIPS = {'arch':['sparc']}
    
    def __init__(self, os_name, package_name, flair='flair', log_level=logging.INFO):
        self.flair = Flair(flair)
        self.archive = Launchpad()
        self.os_name = os_name
        self.package_name = package_name
        self.logger = logging.getLogger('Allirt')
        self.logger.setLevel(log_level)
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def download(self, out_dir):
        os_name = self.os_name
        package_name = self.package_name
        self.logger.info('OS : ' + os_name)
        self.logger.info('Package : ' + package_name)
        series_list = self.archive.get_os_series(os_name)
        print()
        dir_name = os.path.join(out_dir, os_name)
        not os.path.exists(dir_name) and os.mkdir(dir_name)
        for series_idx, series  in enumerate(series_list):
            series_name, series_version = series
            print()
            
            dir_name = os.path.join(dir_name, '{} {}'.format(series_name, series_version))
            not os.path.exists(dir_name) and os.mkdir(dir_name)
            self.logger.info('OS Series ({}/{}) : {} ({})'.format(series_idx+1, len(series_list), series_name, series_version) )
            archs = self.archive.get_os_architectures(os_name, series_name)
            for arch_idx, arch in enumerate(archs):
                print()
                self.logger.info('Architecture ({}/{}) : {}'.format(arch_idx+1, len(archs), arch))
                if arch in self.SKIPS['arch']:
                    self.logger.warning('SKIPPED')
                    continue
                sig_dir_name = os.path.join(dir_name, arch)
                not os.path.exists(sig_dir_name) and os.mkdir(sig_dir_name)
                package_versions = self.archive.get_pacakge_versions(os_name, series_name, arch, package_name)
                for package_version_idx, package_version in enumerate(package_versions):
                    self.logger.info('Package Version ({}/{}) : '.format(package_version_idx+1, len(package_versions), package_version))
                    self.logger.info('{} {} {} {} {} {}'.format(os_name, series_version, package_name, arch, package_version, datetime.now()))
                    size, filename = self.archive.download_package(os_name, series_name, arch, package_name, package_version)
                    if size:
                        self.logger.info('Download Completed : {} ({} bytes)'.format(filename, size))
                        sig_desc = '{} {} {} ({}/{})'.format( os_name, series_version, package_name.replace('-dev',''), package_version, arch )
                        try:
                            sig_name = '{}.sig'.format(os.path.splitext(filename)[0])
                            sig_name = os.path.join(sig_dir_name, sig_name)
                            self.flair.deb_to_sig(filename, 'libc.a', sig_name, sig_desc)
                            self.logger.info('Signature has made.')
                        except FileExistsError:
                            self.logger.warning('Signature already exists.')
                        except Exception as e:
                            self.logger.error(e)
                            traceback.print_tb(e.__traceback__)
                        finally:
                            os.remove(filename)
                    else:
                        self.logger.warning('Package deleted')

allirt = Allirt('ubuntu', 'libc6-dev')
allirt.download('.')
#db.get()
#db.extract_a('/Users/push0ebp/Downloads/deb/libc6-dev_2.15-0ubuntu10.18_i386.deb', 'libc.a', './libc.a')
#allirt.flair.make_sig('temp/libc.a', 'temp/libc2.sig', 'Ubuntu 12.04')
#db.deb_to_sig('/Users/push0ebp/Downloads/deb/libc6-dev_2.15-0ubuntu10.18_i386.deb', 'libc.a', 'libc.sig', 'Ubuntu 12.04')
#versions = db.get_pacakge_versions('ubuntu','precise','amd64','libc6-dev')
#db.download_package('ubuntu','precise','amd64','libc6-dev',versions[1])
#series = db.launchpad.get_os_series('ubuntu')

#db.launchpad.get_os_architectures('ubuntu', series[-1][0])





