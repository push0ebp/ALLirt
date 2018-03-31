from datetime import datetime
import logging


from flair import Flair
from launchpad import Launchpad

class Allirt():
    flair = None
    archive = None
    os_name = ''
    package_name = ''

    logger = None

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

    def download(self):
        os_name = self.os_name
        package_name = self.package_name
        self.logger.info('OS : ' + os_name)
        self.logger.info('Package : ' + package_name)
        series_list = self.archive.get_os_series(os_name)
        for series_idx, series  in enumerate(series_list):
            series_name, series_version = series
            print()
            self.logger.info('OS Series ({}/{}) : {} ({})'.format(series_idx+1, len(series_list), series_name, series_version) )
            archs = self.archive.get_os_architectures(os_name, series_name)
            for arch_idx, arch in enumerate(archs):
                print()
                self.logger.info('Architecture ({}/{}) : {}'.format(arch_idx+1, len(archs), arch))
                package_versions = self.archive.get_pacakge_versions(os_name, series_name, arch, package_name)
                for package_version_idx, package_version in enumerate(package_versions):
                    print()
                    self.logger.info('Package Version ({}/{}) : '.format(package_version_idx+1, len(package_versions), package_version))
                    size, filename = self.archive.download_package(os_name, series_name, arch, package_name, package_version)
                    if size:
                        self.logger.info('Download Completed : {} ({} bytes)'.format(filename, size))
                    else:
                        self.logger.warning('Package deleted')
                    self.logger.info(datetime.now())
                    print()
allirt = Allirt('ubuntu', 'libc6-dev')
allirt.download()
#db.get()
#db.extract_a('/Users/push0ebp/Downloads/deb/libc6-dev_2.15-0ubuntu10.18_i386.deb', 'libc.a', './libc.a')
#db.make_sig('libc.a', 'libc2.sig', 'Ubuntu 12.04')
#db.deb_to_sig('/Users/push0ebp/Downloads/deb/libc6-dev_2.15-0ubuntu10.18_i386.deb', 'libc.a', 'libc.sig', 'Ubuntu 12.04')
#versions = db.get_pacakge_versions('ubuntu','precise','amd64','libc6-dev')
#db.download_package('ubuntu','precise','amd64','libc6-dev',versions[1])
#series = db.launchpad.get_os_series('ubuntu')

#db.launchpad.get_os_architectures('ubuntu', series[-1][0])





