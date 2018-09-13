import os
import json
import datetime

import cherrypy

from MySql import local_host
from Database import Database, gen_uid
from Datatables import Datatables


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%m-%d-%Y %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class Website:
    def __init__(self):
        self.db = Database(local_host['host'], local_host['user'], local_host['password'], 'ncbc_2017')
        self.dt = Datatables(local_host['host'], local_host['user'], local_host['password'], 'ncbc_2017')


    ######################
    #
    # Index
    #
    ######################
    @cherrypy.expose
    def index(self, *args, **kwargs):
        with open('public/html/index.html') as f:
            form = f.read()
        # form = form.replace('<!-- sidebar menu -->', self.get_instructions('sidebar'))
        return form


    @cherrypy.expose
    def dt_emails(self, *args, **kwargs):

        sql = 'select * from emails'

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)

        #result = self.dt.parse_request(sql=sql, table='emails', debug=True, *args, **kwargs)
        return json.dumps({'data': result}, cls=DatetimeEncoder)


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            # 'tools.caching.on': True,
            # 'tools.caching.force' : True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            # 'tools.caching.on': True,
            # 'tools.caching.force' : True,
            'tools.staticdir.dir': './public'
        }
    }

    webapp = Website()
    cherrypy.config.update(
        {'server.socket_host': '0.0.0.0',
         'server.socket_port': 8080,
         'log.screen': True,
         'log.error_file': '',
         'log.access_file': ''
         }
    )
    cherrypy.quickstart(webapp, '/', conf)
