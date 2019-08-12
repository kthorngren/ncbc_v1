from __future__ import print_function

import pymysql.cursors

local_host = {'host' : 'localhost',
              'user': 'db_query',
              'password': 'c1sco123'}

class Sql:
    def __init__(self, host, user, password, db):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.connected = False
        self.sql_execute_result = 0
        self.sql_error = ''
        self.cursorclass = pymysql.cursors.DictCursor

    def connect(self):
        try:
            self.connection = pymysql.connect(host=self.host,
                                              user=self.user,
                                              password=self.password,
                                              db=self.db,
                                              cursorclass=self.cursorclass)
            self.connected = True
        except Exception as e:
            self.connected = False
            print('sql connect failed: {}'.format(e))
        else:
            self.cursor = self.connection.cursor()

    def disconnect(self):
        if self.connection:
            self.connection.close()
        else:
            print('SQL. disconnect - connection object is None')

    def add_log(self, table, **kwargs):
        field_list = []
        value_list = []
        for i in kwargs:
            field_list.append(i)
            value_list.append(kwargs[i])
        sql = 'INSERT INTO %s (%s) VALUES ("%s")' % (table, ','.join(field_list), '","'.join(value_list))
        sql = sql.replace('"NOW()"', 'NOW()')
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
        self.connection.commit()

    def get_log(self, table, *args):
        sql = 'SELECT * FROM %s' % table
        if args:
            sql += ' WHERE %s' % args[0]
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result


    def sql_get_one(self, sql, debug=False):
        self.sql_query(sql, debug)
        if not self.sql_error:
            result = self.fetchone()
            return result
        else:
            return {}

    def sql_get_all(self, sql, debug=False):
        self.sql_query(sql, debug)
        if not self.sql_error:
            result = self.fetchall()
            return result
        else:
            return {}

    def sql_query(self, sql, debug=False):
        self.sql_error = ''
        self.connect()
        if self.connected:
            self.sql_execute(sql, debug)
            try:
                if self.connection:
                    self.disconnect()
                else:
                    print('sql_query: self.connection is None')
                    print(sql)
            except Exception as e:
                self.sql_error = str(e)
                #print('sql_query error: {}'.format(e))
                #print(self.connection)

        else:
            result = 'Unable to connect to SQL Database'
            print('Unable to connect to SQL Database')
        return

    def sql_execute(self, sql, debug=False):
        self.sql_execute_result = 0
        self.sql_error = ''
        try:
            self.sql_execute_result = self.cursor.execute(sql)
            #print('execute result: {}, {}'.format(self.sql_execute_result, sql))
            if 'insert' in sql.lower() or 'update' in sql.lower() or 'delete' in sql.lower():
                self.connection.commit()
        except Exception as e:
            self.sql_error = str(e)
            if debug:
                print('MySql.sql_execute: {}'.format(e))
                print(sql)
            if 'total_calls' in str(e):
                print('MySql.sql_execute: {}'.format(e))
                print(sql)
        if not self.sql_execute_result and ('port=8000' in sql or 'port=7890' in sql):
            print('SQL error: {}'.format(sql))

    def fetchone(self):
        result = self.cursor.fetchone()
        return result if result else {}

    def fetchall(self):
        result = self.cursor.fetchall()
        return result if result else {}

    def rowcount(self):
        return self.cursor.rowcount

    def get_pkid(self, table, field, value):
        sql = 'select pkid from {} where {} = "{}"'.format(table, field, value)
        self.sql_query(sql)

        pkid = self.fetchone()
        if pkid:
            pkid = pkid.get('pkid', 0)
        else:
            pkid = 0
        return pkid
