#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import datetime
import logging
import subprocess
import sys
import os
import zlib
import shutil

from multiprocessing import Process


'''
backup to

    <dest>/<date>/<database_name>_<timestamp>.sql.gz
'''


LOG = logging.getLogger(__name__)

SKIP_DATABASES = ['information_schema', 'performance_schema']

IGNORE_TABLES = {
    'keystone': ['token'],
    'zabbix': ['alerts',
               'history',
               'history_uint',
               'history_str',
               'history_text',
               'history_log',
               'trends.ibd',
               'trends_unit.ibd']
}

DATE_FORMAT = '%Y%m%d'
DATETIME_FORMAT = '%Y%m%d_%H%M'


class MySQLDump(object):

    def __init__(self, conf):
        self.conf = conf
        foldername = datetime.datetime.now().strftime(DATE_FORMAT)
        self.dest = os.path.join(self.conf.dest, foldername)
        if not os.path.exists(self.dest):
            os.makedirs(self.dest)

    def run(self, cmds):
        try:
            LOG.debug ('Runing cmd: %s', cmds)
            return subprocess.check_output(cmds)
        except subprocess.CalledProcessError:
            LOG.exception ('Run command failed: %s', cmds)
            return ''

    def _backup(self, database):
        if database in SKIP_DATABASES:
            LOG.debug ('Skip database: %s', database)
            return
        dumpdata = self.dump(database)
        now = datetime.datetime.now().strftime(DATETIME_FORMAT)
        filename = '%s_%s.sql.gz' % (database, now)
        self.save(filename, dumpdata)
        LOG.info ('Backup "%s" successfully.', database)

    def backup(self):
        for database in self.get_databases():
            self._backup(database)

    def save(self, filename, data):
        with open(os.path.join(self.dest, filename), 'w') as f:
            f.write(zlib.compress(data))

    def dump(self, database):
        cmds = ['mysqldump', '--single-transaction', '--user', self.conf.username,
                '--password=%s' % self.conf.password, '--host',
                self.conf.host, '--databases', database]
        ignore_tables = IGNORE_TABLES.get(database, [])
        for ignore_table in ignore_tables:
            cmds += ['--ignore-table', '%s.%s' % (database, ignore_table)]
        return self.run(cmds)

    def get_databases(self):
        cmds = ['mysql', '--skip-column-names', '--silent',
                '--user', self.conf.username,
                '--password=%s' % self.conf.password,
                '--host', self.conf.host,
                '--execute', 'show databases;']
        databases = self.run(cmds)
        return databases.split()

def clean_old_files(conf): 
    now = datetime.datetime.now() 
    before = now - datetime.timedelta(days=conf.keep) 
    LOG.info ('Start cleaning older backups before: %s', before)
    for folder in os.listdir(conf.dest): 
        path = os.path.join(conf.dest, folder) 
        LOG.info ('path:%s', path)
        if not os.path.isdir(path): 
            continue 
        try: 
            backup_date = datetime.datetime.strptime(folder, DATE_FORMAT) 
        except ValueError: 
            LOG.exception ('Can not parse %s', path) 
            continue 
        if backup_date < before:
            LOG.info ('Cleaning folder %s', path) 
            shutil.rmtree(path)
        else:
            LOG.debug ('folder %s is OK', path) 

def main():
    parser = argparse.ArgumentParser()
    # basic info
    parser.add_argument('-D', '--debug', action='store_true')
    # save info
    parser.add_argument('-k', '--keep', type=int, default=30)
    parser.add_argument('-d', '--dest', default='/data/backup')
    # database info
    parser.add_argument('-u', '--username', default='root')
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-H', '--host', required=True)

    conf = parser.parse_args(sys.argv[1:])

    log_level = logging.INFO
    if conf.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    # backup
    mysqldump = MySQLDump(conf)
    back_obj = Process(target=mysqldump.backup)
    back_obj.start()
    # clean old files
    clean_obj = Process(target=clean_old_files, args=(conf, ))
    clean_obj.start()
    # wait
    back_obj.join()
    clean_obj.join()

if __name__ == "__main__":
    main()

