import os
from datetime import datetime
import logging
import traceback
from tempfile import TemporaryDirectory


from flair import Flair, FlairError, FlairNotSupportedError
from launchpad import Launchpad

class Allirt():
    flair = None
    archive = None
    os_name = ''
    package_name = ''

    logger = None
    SKIPS = {'arch':['sparc', 'hppa']}
    
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
        os_dir_name = os.path.join(out_dir, os_name)
        not os.path.exists(os_dir_name) and os.mkdir(os_dir_name)
        with TemporaryDirectory() as deb_tmp_path:
            for series_idx, series  in enumerate(series_list):
                series_name, series_version = series
                print()

                series_dir_name = os.path.join(os_dir_name, '{} ({})'.format(series_version,series_name))
                not os.path.exists(series_dir_name) and os.mkdir(series_dir_name)
                self.logger.info('OS Series ({}/{}) : {} ({})'.format(series_idx+1, len(series_list), series_name, series_version) )
                archs = self.archive.get_os_architectures(os_name, series_name)
                for arch_idx, arch in enumerate(archs):
                    print()
                    self.logger.info('Architecture ({}/{}) : {}'.format(arch_idx+1, len(archs), arch))
                    if arch in self.SKIPS['arch']:
                        self.logger.warning('SKIPPED')
                        continue
                    arch_dir_name = os.path.join(series_dir_name, arch)
                    not os.path.exists(arch_dir_name) and os.mkdir(arch_dir_name)
                    package_versions = self.archive.get_pacakge_versions(os_name, series_name, arch, package_name)
                    for package_version_idx, package_version in enumerate(package_versions):
                        print()
                        self.logger.info('Package Version ({}/{}) : {}'.format(package_version_idx+1, len(package_versions), package_version))
                        self.logger.info('{} {} {} {} {} {}'.format(os_name, series_version, package_name, arch, package_version, datetime.now()))
                        info = self.archive.download_package(os_name, series_name, arch, package_name, package_version, deb_tmp_path)
                        size = info['size']
                        filename = info['filename']
                        if info['size']:
                            self.logger.info('Download Completed : {} ({} bytes)'.format(info['url'], size))
                            sig_desc = '{} {} {} ({}/{})'.format( os_name, series_version, package_name.replace('-dev',''), package_version, arch )
                            try:
                                sig_dir_name = arch_dir_name
                                sig_name = '{}.sig'.format(os.path.splitext(filename)[0])
                                sig_name = os.path.join(sig_dir_name, sig_name)
                                deb_path = os.path.join(deb_tmp_path, filename)
                                info = self.flair.deb_to_sig(deb_path, 'libc.a', sig_name, sig_desc)
                                self.logger.info('Target library : {}'.format(info['a']))
                                self.logger.info('Signature has created. -> {}'.format(info['sig']))
                            except FileExistsError as e:
                                self.logger.warning('Signature already exists.')
                            except (FlairError, FlairNotSupportedError) as e:
                                self.logger.error(e)
                            except Exception as e:
                                self.logger.error(e)
                                traceback.print_tb(e.__traceback__)
                            finally:
                                os.remove(deb_path)
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





