import os
import json
import datetime
import sys

import cherrypy

from MySql import local_host
from Database import Database, gen_uid
from Datatables import Datatables

from Competitions import Competitions

DATABASE = ''
#https://gist.github.com/igniteflow/1760854
try:
    # use the develop database if we are using develop
    import os
    from git import Repo
    repo = Repo(os.getcwd())
    branch = repo.active_branch
    branch = branch.name
    if branch == 'master':
        DATABASE = 'competitions'
    else:
        DATABASE = 'comp_test'
except ImportError:
    pass


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
        self.db = Database(local_host['host'], local_host['user'], local_host['password'], DATABASE)
        self.dt = Datatables(local_host['host'], local_host['user'], local_host['password'], DATABASE)


    def get_instructions(self, page_name):
        """
        Get the web page instrauctions stored in instructions table.
        :param page_name: instructions name in table
        :return: text found in table or ''
        """
        sql = 'select instructions from instructions where name = "{}"'.format(page_name)
        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).one(uid)
        if result:
            return result['instructions']
        else:
            return ''

    def build_page(self, page_name, html_page=''):

        """

        :param page_name:
        :param libraries: Dictionary containing DT libraries based on Download bulder page and none DT libraries such as select2, quill
            {'styling': 'Bootstrap 3',   #string containing lib - DataTables, Bootstrap 3, Bootstrap 4, Foundation, jQuery UI, Semantic UI
                         'packages': [],  #list of packages - jQuery, DataTables, Editor, Select2, Quill, etc
                         'extensions': []  #list of DT extension like Buttons, Select
                         }
        :param css_styles:
        :param child_name: string or list containing child tables in order of display
        :param datatables:
        :param editors:
        :return:
        """

        with open('public/html/{}'.format(html_page if html_page else 'template.html')) as f:
            form = f.read()

        if html_page and '_template' not in html_page:
            form = form.replace('Place instructions here', self.get_instructions(page_name))


        form = form.replace('<!-- sidebar menu -->', self.get_instructions('sidebar'))

        return form




    @cherrypy.expose
    def get_comp_names(self):

        sql = 'select pkid, name, active from competitions order by name'

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)

        return json.dumps(result)

    @cherrypy.expose
    def get_comp_stats(self):

        order = ['entries', 'checked_in', 'brewers']

        mapping = {
            'checked_in': 'Entries Checked In',
            'entries': 'Total Entries',
            'brewers': 'Brewers'
        }

        result = Competitions().get_comp_status()

        entries = result['entries']

        temp = []
        for k in order:
            temp.append({'name': mapping.get(k, k), 'value': entries[k]})

        result['entries'] = temp


        return json.dumps(result)



    ######################
    #
    # Index
    #
    ######################
    @cherrypy.expose
    def index(self, *args, **kwargs):
        page_name = sys._getframe().f_code.co_name

        #with open('public/html/index.html') as f:
        #    form = f.read()
        # form = form.replace('<!-- sidebar menu -->', self.get_instructions('sidebar'))

        form = self.build_page(page_name, html_page='index.html')
        return form


    @cherrypy.expose
    def dt_competitions(self, *args, **kwargs):

        sql = 'select * from competitions'

        result = self.dt.parse_request(sql=sql, table='competitions', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)




    ######################
    #
    # web page instructions
    #
    ######################
    @cherrypy.expose
    def instructions(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='instructions.html')
        return form

    @cherrypy.expose
    def dt_instructions(self, *args, **kwargs):

        sql = 'select * from instructions'

        result = self.dt.parse_request(sql=sql, table='instructions', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)



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
