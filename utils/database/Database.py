#import threading
import time
import re
import sys
import codecs
from random import randint

import os
from competition import get_logger, set_log_level
logger = get_logger(os.path.basename(__file__).split('.')[0])


from pymysql import converters



"""
https://stackoverflow.com/questions/1210458/how-can-i-generate-a-unique-id-in-python
"""
import threading
_uid = threading.local()
def gen_uid():
    if getattr(_uid, "uid", None) is None:
        _uid.tid = threading.current_thread().ident
        #_uid.uid = 0  #auto increment from original code
    #_uid.uid += 1
    _uid.uid = randint(0, 99999)  # not guaranteed unique but should be different for each run
    return (_uid.tid, _uid.uid)





#global lock variable
#_lock = threading.Lock()
#print(_lock)

TEST_CASE = '** '

def escape_sql(data):
    """
    Escape the " that might be in a string before creating sql string
    :param data: dictionary or string to escape "
    :return: updated data
    """

    result = converters.escape_item(data, 'utf-8')

    if result[0] == "'":
        result = result[1:]
    if result[-1] == "'":
        result = result[:-1]

    return result




class Database:

    def __init__(self, host='', user='', password='', db=''):
        logger.info(f'Initializing using Server: {host} and DB: {db}')
        self.host = host
        self.user = user
        self.password = password
        self._db = db
        self.conn = None  #DB conneciton object
        self.result = {}
        self.connected = None
        self.error = ''
        self.status = ''
        self.sql = ''
        self.validated = False
        self.validation_error = ''
        self.cursor = None
        self.result = {}

    def run_sql(self, sql, get=None):
        """Executes SQL query using the MySql class of the Database package.

        :Parameters:
            - sql (str) - The sql query string.
            - get (str) - (one | all | None) String specifying the number of results to return.

        :Returns:
            - (dict | list(dict, dict, ...) | object) - dictionary if `one` result is requested or an array of dictionaries of `all` results are requested.
                    If the result set is empty or generates an error the dictionary or array will be empty.
                    The self.db object can be queried for the errors.
                    If `get` is None then the self.db object is returned.
        """
        logger.debug('Executing SQL query: {} {}'.format(sql, get))

        get = get.lower() if type(get) is str else get

        if get == 'one':
            uid = gen_uid()
            result = self.db_command(sql=sql, uid=uid).one(uid)
        elif get == 'all':
            uid = gen_uid()
            result = self.db_command(sql=sql, uid=uid).all(uid)
        else:
            result = self.db_command(sql=sql)

        if self.get_error():
            result = [] if get == 'all' else {} if get == 'one' else self._db

        #logger.debug('Sql query result: {}'.format(result))
        return result

    def connect(self, reconnect=False):
        pass

    def disconnect(self):
        pass

    def set_status(self, status='success', error=''):
        pass

    def get_result(self):
        return self.status

    def get_error(self):
        return self.error

    def sql_query(self, sql, uid=''):
        pass

    def sql_execute(self, sql):
        pass


    def one(self):
        pass


    def all(self):
        pass

    def one_orig(self):
        if self.status == 'success':
            return self.fetchone()   #fetchone pops first record
        return {}

    def all_orig(self):
        if self.status == 'success':
            return self.fetchall()
        return []

    def fetchone(self):
        pass

    def fetchall(self):
        pass

    def row_count(self):
        pass



    def parse_select(self, **kwargs):
        pass

    def parse_insert(self, **kwargs):
        pass

    def parse_delete(self, **kwargs):
        pass

    def parse_update(self, **kwargs):
        pass

    def db_command(self, *args, **kwargs):
        pass


    def validate_query(self, *args, **kwargs):
        """
        Method to be sub classed
        :param args:
        :param kwargs:
        :return:
        """
        self.error = ''
        self.validated = True

    def get_list(self, uid, field):

        pass




"""
mysql DB test functions
"""
def get_all(db):
    fn = sys._getframe().f_code.co_name
    logger.info('{}Test case: {} start'.format(TEST_CASE, fn))
    sql = 'select * from test_table'
    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)
    logger.info('select result: {}'.format(result))
    logger.info('{}Test case: {} end\n'.format(TEST_CASE, fn))

def get_one(db):
    fn = sys._getframe().f_code.co_name
    logger.info('{}Test case: {} start'.format(TEST_CASE, fn))
    sql = 'select * from test_table where name = "name1"'
    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).one(uid)
    logger.info('select result: {}'.format(result))
    logger.info('{}Test case: {} end\n'.format(TEST_CASE, fn))

def sql_error(db):
    fn = sys._getframe().f_code.co_name
    logger.info('{}Test case: {} start'.format(TEST_CASE, fn))
    sql = 'select * error from test_table where name = "name1"'
    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).one(uid)
    logger.info('select result: {}'.format(result))
    logger.info('{}Test case: {} end\n'.format(TEST_CASE, fn))

def reconnect(db):
    fn = sys._getframe().f_code.co_name
    logger.info('{}Test case: {} start'.format(TEST_CASE, fn))
    db.disconnect()
    db.connect()
    logger.info('{}Test case: {} end\n'.format(TEST_CASE, fn))

def connect(db, reconnect=False):
    fn = sys._getframe().f_code.co_name
    logger.info('{}Test case: {} start'.format(TEST_CASE, fn))
    db.connect(reconnect=reconnect)
    logger.info('{}Test case: {} end\n'.format(TEST_CASE, fn))

def disconnect(db):
    fn = sys._getframe().f_code.co_name
    logger.info('{}Test case: {} start'.format(TEST_CASE, fn))
    db.disconnect()
    logger.info('{}Test case: {} end\n'.format(TEST_CASE, fn))


def test_mysql():
    db = Database(local_host['host'], local_host['user'], local_host['password'], 'db_test')

    #get_all()

    #get_one()

    sql_error()

    #reconnect()
    get_one()

    #connect()
    #connect(reconnect=True)
    #get_one()

    #disconnect()
    #get_one()

def test_sqlite():
    db = Sqlite(db='test')

    db.connect()


    sql = 'drop table if  exists names'
    result = db.db_command(sql=sql).row_count()


    sql = 'create table if not exists names (pkid integer primary key AUTOINCREMENT, name text unique not null)'
    result = db.db_command(sql=sql).row_count()

    if result == -1:
        print('Table already exits', result)
    else:
        print('Table created', result)


    sql = 'insert or ignore into names (name) values ("kevin")'
    db.db_command(sql=sql)


    sql = 'select * from names;'
    result = db.db_command(sql=sql).all()

    print(result)


def reset_graph_table():
    graph_table = '''CREATE TABLE IF NOT EXISTS `graph` (
  `pkid` integer UNIQUE NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar(45) DEFAULT NULL,
  `description` varchar(100) DEFAULT NULL,
  `fk_graph_files` integer DEFAULT NULL,
  `fk_graph_sources` integer DEFAULT NULL,
  `fk_textfsm` integer DEFAULT NULL,
  `fk_perfmon_counters` integer DEFAULT NULL,
  `graph_options` varchar(1000) DEFAULT NULL)
  '''

    graph_files = '''CREATE TABLE IF NOT EXISTS `graph_files` (
  `pkid` integer UNIQUE NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar(45) DEFAULT NULL,
  `uploaded_files` varchar(1000) DEFAULT NULL)
  '''

    graph_sources = '''CREATE TABLE IF NOT EXISTS `graph_sources` (
  `pkid` integer UNIQUE NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar(45) UNIQUE DEFAULT NULL,
  `title` varchar(45) DEFAULT NULL,
  `field` varchar(45) DEFAULT NULL,
  `description` varchar(100) DEFAULT NULL)
  '''

    perfmon_counters = '''CREATE TABLE IF NOT EXISTS `perfmon_counters` (
  `pkid` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar(200) UNIQUE DEFAULT NULL)
  '''

    perfmon_templates = '''CREATE TABLE IF NOT EXISTS `perfmon_templates` (
  `pkid` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar(45) UNIQUE DEFAULT NULL,
  `fk_perfmon_counters` int(11) DEFAULT NULL,
  `options` varchar(300) DEFAULT NULL)
  '''

    textfsm = '''CREATE TABLE IF NOT EXISTS `textfsm` (
  `pkid` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar(45) DEFAULT NULL,
  `script` varchar(1000) DEFAULT NULL)
  '''

    uploads = '''CREATE TABLE IF NOT EXISTS `uploads` (
  `pkid` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `id` integer DEFAULT 0 ,
  `filename` varchar(45) UNIQUE DEFAULT NULL,
  `timestamp` DATETIME DEFAULT NULL,
  `filesize` varchar(45) DEFAULT NULL,
  `web_path` varchar(2000) DEFAULT NULL,
  `system_path` varchar(2000) DEFAULT NULL)
  '''

    table_list = [graph_table, graph_sources, graph_files, perfmon_counters, perfmon_templates, textfsm, uploads]
    table_names = ['graph', 'graph_sources', 'graph_files', 'perfmon_counters', 'perfmon_templates', 'textfsm', 'uploads']

    db = Sqlite(db='graphs.sqlite')






    db.connect()

    drop = True

    count = 0
    for t in table_list:
        t_name  = table_names[count]
        count += 1

        if drop:
            sql = 'drop table if exists {}'.format(t_name)
            result = db.db_command(sql=sql).row_count()


        sql = escape_sql(t.replace(r'`', ''))
        sql = sql.replace('\n', '')
        result = db.db_command(sql=sql).row_count()


    sql = 'insert into graph_sources (pkid, name, title, field, description) values ("1", "Text File", "TextFSM Script", "fk_textfsm", "TestFSM Script")'
    db.db_command(sql=sql)

    sql = 'insert into graph_sources (pkid, name, title, field, description) values ("2", "Perfmon", "TPerfmon Counter", "fk_perfmon_counters", "Perfmon Counter")'
    db.db_command(sql=sql)

def test_graphs_sql():

    sql = 'insert  into uploads (filename) values ("CS_vz0cube1.txt")'

    db = Sqlite(db='graphs.sqlite')

    db.connect()

    #db.db_command(sql=sql)


    sql = 'select filename from uploads;'
    result = db.db_command(sql=sql).all()

    print('test result', result)


if __name__ == '__main__':
    LEVEL = logging.DEBUG
    logger.setLevel(LEVEL)
    ch.setLevel(LEVEL)
    #db = Database('1.1.1.1', local_host['user'], local_host['password'], 'db_test')


    #test_sqlite()
    #reset_graph_table()
    #test_graphs_sql()



    db = Sqlite(db='graphs.sqlite')

    db.connect()

    #result = db.backup('~/temp')
    #print(result)

    result = db.restore('~/temp')
    print(result)

    db.clear_tables(['graph', 'graph_files', 'graph_sources', 'perfmon_counters', 'perfmon_templates', 'textfsm', 'uploads'])
