import urllib2
import logging

import config
import utils
import os
import tarfile


def get_archive(target_directory, user, year, month):
    basename = '%s-%d-%d.tar.gz' % (user, year,  month)
    url = 'http://www.gokgs.com/servlet/archives/en_US/' + basename
    
    try:
        response = urllib2.urlopen(url)
    except urllib2.URLError as e:
        logging.error("Fetching the KGS archive failed: '%s'\n  %s"%(e, url))
        raise
    
    if not os.path.isdir(target_directory):
        os.mkdir(target_directory)
        
    archive_dir = os.path.join(target_directory, 'ARCHIVES')
    if not os.path.isdir(archive_dir):
        os.mkdir(archive_dir)
        
    archive_name = os.path.join(archive_dir, basename)
    with open(archive_name, 'w') as archive:
        archive.write(response.read())
        
    tf = tarfile.open(archive_name)
    tf.extractall(target_directory)
    tf.close()
    
if __name__ == '__main__':
    archive_2_osl('bronislav', 2013, 1)
    