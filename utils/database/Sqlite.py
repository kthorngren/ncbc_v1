
from Database.Database import Database

import sqlite3
from pathlib import Path
from shutil import copyfile

from competition import logger

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Sqlite(Database):



    def __init__(self, host='', user='', password='', db=''):
        logger.debug('Sqlite.__init__')
        super().__init__(host, user, password, db)

        self.conn = None

    #todo: to make more generic find a way to pass the path along with the DB when initing Sqlite()
    def connect(self, reconnect=False):

        if self.conn is None:
            cwd = Path.cwd()
            schema = cwd / 'public/database' / self._db

            try:
                self.conn = sqlite3.connect(str(schema))
            except Exception as e:
                logger.error('Error connection to Database: {}'.format(str(e)))
                self.cursor = None
            else:
                self.cursor = self.conn.cursor()
                self.cursor.row_factory = dict_factory

    def disconnect(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
        self.conn = None
        self.connection = None


    def sql_query(self, sql, uid=''):
        logger.debug('sql_query() - {}'.format(sql))
        #print(sql)
        get_context = False
        #print('sql_query uid', uid)
        if not self.conn:
            self.connect()
        with self.conn:
            logger.debug('Using self.conn context: {}'.format(self.conn))
            get_context = True
            self.sql_error = ''
            #logger.debug('Using cursor object: {}'.format(self.cursor))
            try:
                #print(sql)
                self.cursor.execute(sql)
            except Exception as e:
                self.sql_error = str(e)
                self.set_status(status='error', error=self.sql_error)
                logger.warning('sql_execute() error: {}'.format(e))
                logger.warning('  sql: {}'.format(sql))
                #self.mysql.close_cursor()  # make sure to clear cursor and remove lock
                self.result = []  # clear out any remaininig SQL responses
            else:
                self.result = self.cursor.fetchall()
                #print('sql result:', self.result)
                self.set_status()

                if 'insert' in sql.lower() or 'update' in sql.lower() or 'delete' in sql.lower():
                    #self.conn.commit()
                    logger.debug('Rows affected: {}'.format(self.row_count()))
                else:
                    logger.debug('Rows returned: {}'.format(len(self.result)))
                if self.sql_error:
                    logger.error('Rows returned: {} for error: "{}"sql:\n{}'.format(self.row_count(), self.sql_error, sql))


        if get_context == False:
            logger.error('Unable to get with context for sql: {}'.format(sql))
        self.disconnect()
        return self

    def one(self):

        result = self.result

        return result.pop(0) if result else {}

    def all(self):
        result = self.result

        return result if result else []


    def fetchone(self):
        result = self.cursor.fetchone()
        return result if result else {}

    def fetchall(self):
        result = self.cursor.fetchall()
        return result if result else {}

    def row_count(self):
        #if self.status == 'error':
        #    return 0
        if self.cursor:
            return self.cursor.rowcount
        else:
            return 0

    def db_command(self, *args, **kwargs):
        #logger.debug('sql_get() - args: {}'.format(args))
        #logger.debug('sql_get() - kwargs: {}'.format(kwargs))
        data = {}
        errors = []
        self.error = ''
        self.status = ''
        self.sql = ''
        self.validated = False
        sql = kwargs.get('sql', '')

        #print (uid)
        if sql and type(sql) == type(' '):
            if ';' != sql[-1]:
                sql = sql + ';'
            self.sql_query(sql)
            self.sql = sql
        else:
            if 'select' in kwargs:
                command = 'select'
            elif 'insert' in kwargs:
                command = 'insert'
            elif 'delete' in kwargs:
                command = 'delete'
            elif 'update' in kwargs:
                command = 'update'
            else:
                command = 'unknown'
            self.validate_query(*args, **kwargs)
            #logger.debug ('{}, {}'.format(self.validated, command))
            if self.validated and command != 'unknown':
                result = {'status': 'error'}
                if command == 'select':
                    result = self.parse_select(**kwargs)
                elif command == 'insert':
                    result = self.parse_insert(**kwargs)
                elif command == 'delete':
                    result = self.parse_delete(**kwargs)
                elif command == 'update':
                    result = self.parse_update(**kwargs)
                if result['status'] == 'success':
                    self.sql_query(result['sql'])
                    self.sql = result['sql']
                else:
                    self.set_status(status=result['status'], error=result['error'])
            else:
                self.set_status(status='error', error='{} query not validated with error(s): {}'.format(command.title(), self.error))

        return self


    def backup(self, path):

        error = ''
        data = ''
        self.disconnect()

        cwd = Path.cwd()
        schema = cwd / 'public/database' / self._db

        if path[0] == '~':
            path = '{}{}'.format(str(Path.home()), path[1:])

        target = Path(path)
        target = target / self._db

        logger.info('Backing up "{}" to "{}"'.format(schema, target))

        try:
            copyfile(schema, target)
        except IOError as e:
            error = 'Unable to copy file. {}'.format(e)
            logger.error(error)
        except:
            error = 'Unexpected error: {}'.format(sys.exc_info())
            logger.error(error)
        else:
            data = 'Backup successful to "{}"'.format(target)
            logger.info(data)

        return {'data': data, 'error': error}


    def restore(self, path):

        error = ''
        data = ''
        self.disconnect()

        cwd = Path.cwd()
        schema = cwd / 'public/database' / self._db

        if path[0] == '~':
            path = '{}{}'.format(str(Path.home()), path[1:])

        target = Path(path)
        target = target / self._db

        logger.info('Restoring "{}" to "{}"'.format(target, schema))

        try:
            copyfile(target, schema)
        except IOError as e:
            error = 'Unable to copy file. {}'.format(e)
            logger.error(error)
        except:
            error = 'Unexpected error: {}'.format(sys.exc_info())
            logger.error(error)
        else:
            data = 'Restore successful to "{}"'.format(schema)
            logger.info(data)

        return {'data': data, 'error': error}

    def clear_tables(self, tables=''):

        data = ''
        error = ''

        if tables:

            if type(tables) != type([]):

                tables = [tables]

            for table in tables:

                sql = 'DELETE FROM {};'.format(table)
                self.sql_query(sql)

            sql = 'VACUUM;'
            self.sql_query(sql)
            data = 'Tables successfully cleared'
        else:
            error = 'No tables supplied to empty'

        return {'data': data, 'error': error}
