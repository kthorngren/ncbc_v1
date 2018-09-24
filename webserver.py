import os
import json
import datetime
import sys
import re

import cherrypy

from MySql import local_host
from Database import Database, gen_uid, escape_sql
from Datatables import Datatables

from Competitions import Competitions
from Styles import Style
from Brewers import Brewers
from Import import Import
from Email import Email
from Volunteers import Volunteers
from Flights import Flights
from Sessions import Sessions
from Entrys import Entrys

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

    def get_pkid(self, data):
        pkid = 0

        for field in data:
            match = re.findall(r'\[([A-Za-z0-9_\-]+)\]', field)

            # todo might need to fix loop to get multiple records
            if match:
                pkid = int(match.pop(0))
                break

        return pkid

    @cherrypy.expose
    def get_comp_names(self):

        sql = 'select pkid, name, active from competitions order by name'

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)

        return json.dumps(result)

    @cherrypy.expose
    def get_entry_id(self, entry_id):

        sql = 'select name, entry_id, category, sub_category, inventory, location_0, location_1, ' \
              'b.firstname, b.lastname, b.organization from entries ' \
              'inner join brewers as b on b.pkid = fk_brewers ' \
              'where entry_id = "{}" and entries.fk_competitions = "{}"'.format(entry_id, Competitions().get_active_competition())

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).one(uid)

        if result:
            result['inventory'] = 'Yes' if result['inventory'] == 1 else 'No'
            result['cat'] = Style('BJCP2015').get_style_name(result['category'], result['sub_category'])

        return json.dumps(result)


    @cherrypy.expose
    def update_entry_id(self, **kwargs):

        if 'entry_id' in kwargs and 'location_0' in kwargs and 'location_0' in kwargs:

            sql = 'update entries set inventory = "1", location_0 = "{d[location_0]}", location_1 = "{d[location_1]}" ' \
                  'where entry_id = "{d[entry_id]}" and fk_competitions = "{pkid}"'.format(d=kwargs, pkid=Competitions().get_active_competition())

            self.db.db_command(sql=sql)

            sql = 'select name, entry_id, category, sub_category, inventory, location_0, location_1, ' \
                  'b.firstname, b.lastname, b.organization from entries ' \
                  'inner join brewers as b on b.pkid = fk_brewers ' \
                  'where entry_id = "{}" and entries.fk_competitions = "{}"'.format(kwargs['entry_id'], Competitions().get_active_competition())

            uid = gen_uid()
            result = self.db.db_command(sql=sql, uid=uid).one(uid)

            if result:
                result['inventory'] = 'Yes' if result['inventory'] == 1 else 'No'
                result['cat'] = Style('BJCP2015').get_style_name(result['category'], result['sub_category'])

        else:
            result = {'error': 'Error updating entry'}

        return json.dumps(result)




    @cherrypy.expose
    def get_comp_stats(self):

        order = ['entries', 'checked_in', 'no_desc', 'judged', 'brewers']

        mapping = {
            'checked_in': 'Entries Checked In',
            'entries': 'Total Entries',
            'brewers': 'Brewers',
            'judged': 'Entries Judged',
            'no_desc': 'Specialty Entries W/O Description'
        }

        result = Competitions().get_comp_status()

        entries = result['entries']

        entries['no_desc'] = len(Brewers().get_specialty_wo_desc())


        temp = []
        for k in order:
            temp.append({'name': mapping.get(k, k), 'value': entries[k]})

        result['entries'] = temp


        return json.dumps(result)

    @cherrypy.expose
    def get_specialty_wo_desc(self):

        result = Brewers().get_specialty_wo_desc()

        return json.dumps(result)


    @cherrypy.expose
    def find_person(self, *args, **kwargs):

        names = []

        email = kwargs.get('email', '')
        if email == '':
            return json.dumps({'data': {}})

        firstname = kwargs.get('firstname', '')
        lastname = kwargs.get('lastname', '')

        if firstname:
            names.append(firstname)

        if lastname:
            names.append(lastname)

        display_name = kwargs.get('display_name', '')

        if display_name:

            match = re.search(r'^(.*)<.*>', display_name)

            if match:
                names = match.group(1).split(' ')


        if names:
            where = ' firstname in ("{names}") or lastname in ("{names}") or '.format(names='","'.join(names))
        else:
            where = ''


        where += ' email like "%{prefix}%" or email = "{email}" or firstname like "%{prefix}%"  or lastname like "%{prefix}%" ' \
                 ' or locate(lastname, "{prefix}")>0 or locate(firstname, "{prefix}")>0'.format(prefix=email.split('@')[0], email=email)

        sql = 'select * from people where {}'.format(where)
        
        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)


        return json.dumps(result, cls=DatetimeEncoder)

    @cherrypy.expose
    def find_bjcp_judge(self, *args, **kwargs):

        #where = [' {} = "{}" '.format(k, v) for k, v in kwargs.items()]

        where = ' (firstname like "%{d[firstname]}%" and lastname like "%{d[lastname]}%") or ' \
                'email like "%{d[email]}%"'.format(d=kwargs)

        if len(kwargs.get('bjcp_id', '')) > 0:
            where +=  'or bjcp_id like "%{d[bjcp_id]}%"'.format(d=kwargs)

        sql = 'select firstname, lastname, email, bjcp_id, level from bjcp_judges where {}'.format(where)


        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)


        return json.dumps(result, cls=DatetimeEncoder)


    @cherrypy.expose
    def bulk_find_bjcp_judge(self, *args, **kwargs):

        bjcp_result = []

        try:
            judges = json.loads(kwargs.get('data', []))
        except:
            judges = {}

        for judge in judges:

            where = ' (firstname like "%{d[firstname]}%" and lastname like "%{d[lastname]}%")'.format(d=judge)

            if len(kwargs.get('email', '')) > 0:
                where +=  'or email like "%{d[email]}%"'.format(d=judge)

            if len(kwargs.get('bjcp_id', '')) > 0:
                where +=  'or bjcp_id like "%{d[bjcp_id]}%"'.format(d=judge)

            sql = 'select firstname, lastname, email, bjcp_id, level from bjcp_judges where {}'.format(where)


            uid = gen_uid()
            result = self.db.db_command(sql=sql, uid=uid).all(uid)

            if judge['lastname'] == 'Houck':
                print(sql)

            bjcp_result.append({'pkid': judge['pkid'], 'result': result})

        return json.dumps(bjcp_result, cls=DatetimeEncoder)


    @cherrypy.expose
    def add_person(self, *args, **kwargs):

        fields = []
        values = []

        for k, v in kwargs.items():

            fields.append(k)
            values.append(v)

        sql = 'insert into people ({}, updated) values ("{}", NOW())'.format(','.join(fields), '","'.join(values))
        self.db.db_command(sql=sql)


        result = {}

        if not self.db.sql_error:

            where = [' {} = "{}" '.format(k, v) for k, v in kwargs.items()]


            sql = 'select pkid from people where {}'.format(' and '.join(where))

            uid = gen_uid()
            result = self.db.db_command(sql=sql, uid=uid).one(uid)



        return json.dumps(result.get('pkid', 0))



    @cherrypy.expose
    def add_as_alias(self, *args, **kwargs):

        fields = []
        values = []

        for k, v in kwargs.items():

            fields.append(k)
            values.append(v)

        sql = 'insert into people ({}, updated) values ("{}", NOW())'.format(','.join(fields), '","'.join(values))
        self.db.db_command(sql=sql)

        return json.dumps(self.db.row_count())


    @cherrypy.expose
    def remove_ncbc_email(self, *args, **kwargs):

        pkid = kwargs.get('pkid', 0)

        if pkid:
            sql = 'delete from ncbc_email_list where pkid = "{}"'.format(pkid)
            self.db.db_command(sql=sql)

            print(self.db.row_count())

            return json.dumps(self.db.row_count())

        return json.dumps(0)


    @cherrypy.expose
    def update_volunteer_person(self, *args, **kwargs):

        fk_people = kwargs.get('fk_people', 0)
        pkid = kwargs.get('pkid', 0)

        if pkid and fk_people:
            sql = 'update volunteers set fk_people = "{}" where pkid = "{}"'.format(fk_people, pkid)
            self.db.db_command(sql=sql)

            print(self.db.row_count())

            return json.dumps(self.db.row_count())

        return json.dumps(0)

    @cherrypy.expose
    def import_entries(self):

        result = Import().import_ncbc_entries()

        return json.dumps(result)

    @cherrypy.expose
    def import_volunteers(self):
        result = Import().import_ncbc_volunteers()

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
    #
    # ** Import section **
    #
    #
    ######################


    ######################
    #
    # Import NCBC Entries
    #
    ######################
    @cherrypy.expose
    def import_ncbc_entries(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='import_ncbc_entries.html')
        return form

    ######################
    #
    # Import NCBC Volunteers
    #
    ######################
    @cherrypy.expose
    def import_ncbc_volunteers(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='import_ncbc_volunteers.html')
        return form


    ######################
    #
    # Email new and changed volunteers
    #
    ######################
    @cherrypy.expose
    def email_volunteer_sessions(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='email_volunteer_sessions.html')
        return form

    @cherrypy.expose
    def send_volunteer_sessions(self, **kwargs):

        new_result = Volunteers().email_new()
        changed_result = Volunteers().email_changed()

        return json.dumps({'new': new_result, 'changed': changed_result})


    ######################
    #
    # Inventory
    #
    ######################
    @cherrypy.expose
    def categories(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='categories.html')
        return form

    @cherrypy.expose
    def dt_categories(self, *args, **kwargs):

        #todo: eventually start using the base guidlelines
        #result = Style().get_styles(Competitions().get_style_guidelines())

        sql = 'select * from category_strength_rating'

        result = self.dt.parse_request(sql=sql, table='category_strength_rating', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)


    @cherrypy.expose
    def save_categories(self, *args, **kwargs):

        errors = []

        result = 'Unable to process catorgories'

        try:
            categories = json.loads(kwargs.get('data', {}))
        except:
            categories = {}

        print(categories)

        if categories:

            categories = [str(x) for x in categories]

            sql = 'update competitions set fk_categories_list = "{}" ' \
                  'where pkid = "{}"'.format(','.join(categories), Competitions().get_active_competition())

            self.db.db_command(sql=sql)

            result = self.db.sql_error


        return result


    ######################
    #
    # Inventory
    #
    ######################
    @cherrypy.expose
    def inventory(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='inventory.html')
        return form

    @cherrypy.expose
    def dt_inventory(self, *args, **kwargs):

        sql = 'select * from entries'

        result = self.dt.parse_request(sql=sql, table='entries', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)


    ######################
    #
    # Description
    #
    ######################
    @cherrypy.expose
    def descriptions(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='descriptions.html')
        return form

    @cherrypy.expose
    def dt_descriptions(self, *args, **kwargs):

        sql = 'select pkid, entry_id, description from entries'

        result = self.dt.parse_request(sql=sql, table='entries', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)




    ######################
    #
    # Check in entries
    #
    ######################
    @cherrypy.expose
    def checkin(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='checkin.html')
        return form

    ######################
    #
    # Check in entries by brewer
    #
    ######################
    @cherrypy.expose
    def checkin_brewer(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='checkin_brewer.html')
        return form


    @cherrypy.expose
    def dt_checkin_brewer(self, *args, **kwargs):

        sql = 'select entries.pkid, name, entry_id, category, sub_category, inventory, location_0, location_1, ' \
              'one_bottle, comments, ' \
              'b.firstname, b.lastname, b.organization, b.email from entries ' \
              'inner join brewers as b on b.pkid = fk_brewers ' \
              'where entries.fk_competitions = "{}"'.format(Competitions().get_active_competition())

        if kwargs.get('action', '') == 'edit':

            for field in kwargs:
                match = re.findall(r'\[([A-Za-z0-9_\-]+)\]', field)

                #todo might need to fix loop to get multiple records
                if match:
                    pkid = int(match.pop(0))
                    break

            sql = 'select entries.pkid, name, entry_id, category, sub_category, inventory, location_0, location_1, ' \
                  'one_bottle, comments, ' \
                  'b.firstname, b.lastname, b.organization, b.email from entries ' \
                  'inner join brewers as b on b.pkid = fk_brewers ' \
                  'where entries.pkid = "{}" and entries.fk_competitions = "{}"'.format(pkid, Competitions().get_active_competition())

        result = self.dt.parse_request(sql=sql, table='entries', debug=True, *args, **kwargs)

        for r in result['data']:
            r['cat'] = Style('BJCP2015').get_style_name(r['category'], r['sub_category'])

        return json.dumps(result, cls=DatetimeEncoder)


    ######################
    #
    #
    # ** People section **
    #
    #
    ######################


    ######################
    #
    # NCBC Email List
    #
    ######################
    @cherrypy.expose
    def ncbc_email_list(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='ncbc_email_list.html')
        return form

    @cherrypy.expose
    def dt_ncbc_email_list(self, *args, **kwargs):

        sql = 'select * from ncbc_email_list'

        result = self.dt.parse_request(sql=sql, table='ncbc_email_list', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)


    ######################
    #
    # People Editor
    #
    ######################
    @cherrypy.expose
    def people(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='people.html')
        return form

    @cherrypy.expose
    def dt_people(self, *args, **kwargs):

        sql = 'select * from people'

        result = self.dt.parse_request(sql=sql, table='people', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)

    ######################
    #
    # Volunteer Editor
    #
    ######################
    @cherrypy.expose
    def volunteers(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='volunteers.html')
        return form

    @cherrypy.expose
    def dt_volunteers(self, *args, **kwargs):

        sql = 'select * from volunteers'

        result = self.dt.parse_request(sql=sql, table='volunteers', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)

    ######################
    #
    # Judge Maintenance
    #
    ######################
    @cherrypy.expose
    def judge_maintenance(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='judge_maintenance.html')
        return form

    @cherrypy.expose
    def dt_judge_maintenance(self, *args, **kwargs):

        sql = 'select pkid, firstname, lastname, email, bjcp_id, bjcp_rank, cicerone, ' \
              'ncbc_points, dont_pair, speed, other_cert, result from people where alias = "0"'

        if kwargs.get('action', '') == 'edit':


            pkid = self.get_pkid(kwargs)


            sql += ' and pkid = "{}"'.format(pkid)

        result = self.dt.parse_request(sql=sql, table='people', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)


    ######################
    #
    # Brewer Editor
    #
    ######################
    @cherrypy.expose
    def brewers(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='brewers.html')
        return form

    @cherrypy.expose
    def dt_brewers(self, *args, **kwargs):

        sql = 'select * from brewers'

        result = self.dt.parse_request(sql=sql, table='brewers', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)



    ######################
    #
    # Volunteer Emails
    #
    ######################
    @cherrypy.expose
    def confirmation(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='confirmation.html')
        return form

    @cherrypy.expose
    def dt_confirmation(self, *args, **kwargs):

        sql = 'select * from email_text where type = "volunteer"'

        if kwargs.get('action', '') == 'edit':

            pkid = self.get_pkid(kwargs)


            sql = 'select * from email_text where type = "volunteer" and pkid = "{}"'.format(pkid)



        result = self.dt.parse_request(sql=sql, table='email_text', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)






    ######################
    #
    #
    # ** Sessions section **
    #
    #
    ######################


    ######################
    #
    # Sessions
    #
    ######################
    @cherrypy.expose
    def sessions(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='sessions.html')
        return form

    @cherrypy.expose
    def dt_sessions(self, *args, **kwargs):

        sql = 'select * from sessions where fk_competitions = "{}"'.format(Competitions().get_active_competition())
        if kwargs.get('action', '') == 'edit':

            pkid = self.get_pkid(kwargs)


            sql += ' and pkid = "{}"'.format(pkid)



        result = self.dt.parse_request(sql=sql, table='sessions', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)




    ######################
    #
    #
    # ** Flights **
    #
    #
    ######################


    ######################
    #
    # Flights Health Check
    #
    ######################
    @cherrypy.expose
    def flights_health(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='flights_health.html')
        return form

    @cherrypy.expose
    def health_check(self, **kwargs):

        data = []

        sessions = Sessions().get_sessions(judging=True)

        for session in sorted(sessions, key=lambda k: k['session_number']):

            #['pkid', 'fk_sessions', 'head_judge', 'second_judge', 'judges']
            pairing = Flights().get_session_pairing(session['pkid'])

            all_judges = Flights().get_judges_for_session(session['pkid'])

            if len(pairing) == 0:
                data.append({'name': session['name'], 'status': 'Judge pairing not defined', 'code': 'red'})
            else:
                pairing = pairing[0]

                try:
                    judges = json.loads(pairing['judges'])
                except:
                    judges = 0
                    data.append({'name': session['name'], 'status': 'Unable to parse judges', 'code': 'red'})

                try:
                    hj_judges = json.loads(pairing['head_judge'])
                except:
                    hj_judges = 0
                    data.append({'name': session['name'], 'status': 'Unable to parse head judges', 'code': 'red'})

                try:
                    sj_judges = json.loads(pairing['second_judge'])
                except:
                    sj_judges = 0
                    data.append({'name': session['name'], 'status': 'Unable to parse second judges', 'code': 'red'})

                if len(all_judges) == 0:
                    data.append({'name': session['name'], 'status': 'No judges registerd for session', 'code': 'yellow'})
                else:
                    data.append({'name': session['name'], 'status': '{} judges registerd for session'.format(len(all_judges)), 'code': 'green'})

                difference = len(hj_judges) - len(sj_judges)

                if difference == 0:
                    data.append(
                        {'name': session['name'], 'status': 'Judge pairs are symmetrical', 'code': 'green'})
                else:
                    more = 'Head' if difference > 0 else 'Second'
                    less = 'Second' if more == 'Head' else 'Head'
                    data.append({'name': session['name'], 'status': 'More {} judges than {} judges - '
                                                                    'Head Judges: {}, Second Judges: {}'.format(more, less, len(hj_judges), len(sj_judges)),
                                 'code': 'red'})

                if len(judges) > 0:
                    data.append({'name': session['name'], 'status': '{} judges need to be assigned'.format(len(judges)), 'code': 'yellow'})

                all_pkids = [x['pkid'] for x in all_judges]
                not_in_session = []
                for judge in judges:
                    try:
                        pkid_index = all_pkids.index(judge['pkid'])
                        all_pkids.pop(pkid_index)
                    except:
                        not_in_session.append('{} {}'.format(judge['firstname'], judge['lastname']))


                for judge in hj_judges:
                    try:
                        pkid_index = all_pkids.index(judge['pkid'])
                        all_pkids.pop(pkid_index)
                    except:
                        not_in_session.append('{} {}'.format(judge['firstname'], judge['lastname']))

                for judge in sj_judges:
                    try:
                        pkid_index = all_pkids.index(judge['pkid'])
                        all_pkids.pop(pkid_index)
                    except:
                        not_in_session.append('{} {}'.format(judge['firstname'], judge['lastname']))

                if not_in_session:
                    data.append({'name': session['name'],
                                 'status': 'Judges not assigned to session: {}'.format(', '.join(not_in_session)),
                                 'code': 'red'})

                if all_pkids:
                    all_list = []

                    for judge in all_judges:
                        if judge['pkid'] in all_pkids:
                            all_list.append('{} {}'.format(judge['firstname'], judge['lastname']))

                    data.append({'name': session['name'],
                                 'status': 'Session judges not in pairing: {}'.format(', '.join(all_list)),
                                 'code': 'red'})

                else:
                    data.append({'name': session['name'],
                                 'status': 'All session judges accounted for',
                                 'code': 'green'})




        sql = 'select * from tables where fk_competitions = "{}"'.format(Competitions().get_active_competition())

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)


        if not result:
            data.append({'name': 'Tables',
                         'status': 'Tables are not defined',
                         'code': 'red'})
        else:
            pass

        flights = Flights().get_flights()

        if not flights:
            data.append({'name': 'Flights',
                         'status': 'Flights are not defined',
                         'code': 'red'})
        else:
            pass



        return json.dumps({'data': data}, cls=DatetimeEncoder)

    ######################
    #
    # Judge Pairing
    #
    ######################
    @cherrypy.expose
    def judge_pairing(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='judge_pairing.html')
        return form

    @cherrypy.expose
    def dt_judge_pairing(self, *args, **kwargs):

        sql = 'select * from sessions where judging = "1" and fk_competitions = "{}"'.format(Competitions().get_active_competition())

        result = self.dt.parse_request(sql=sql, table='sessions', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)


    @cherrypy.expose
    def auto_generate_pairs(self, *args, **kwargs):

        session_number = kwargs.get('session_number', 0)

        result = Flights().auto_assign_judges(session_number)

        return json.dumps(result, cls=DatetimeEncoder)

    @cherrypy.expose
    def get_session_judges(self, *args, **kwargs):

        result = {}

        session_number = kwargs.get('session_number', 0)

        result['all'] = Flights().get_judges_for_session(session_number)

        result['pairing'] = Flights().get_session_pairing(session_number)

        return json.dumps(result, cls=DatetimeEncoder)


    @cherrypy.expose
    def save_pairs(self, *args, **kwargs):

        errors = []

        result = ''

        try:
            session_pairs = json.loads(kwargs.get('data', {}))
        except:
            session_pairs = {}
        #print(session_pairs.keys())
        if session_pairs:
            save_result = Sessions().save_session_pairs(session_pairs)

            if save_result:
                result = 'Successfully save judge pairs'
            else:
                errors.append('Unable to save judge pairs')

        else:
            errors.append('Unable to parse judge pairs')



        return json.dumps({'data': result, 'error': ','.join(errors)}, cls=DatetimeEncoder)



    ######################
    #
    # Find judge entries
    #
    ######################
    @cherrypy.expose
    def judge_entries(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='judge_entries.html')
        return form

    @cherrypy.expose
    def dt_judge_entries(self, *args, **kwargs):

        result = Volunteers().find_volunteer_entries()

        return json.dumps({'data': result}, cls=DatetimeEncoder)


    @cherrypy.expose
    def assign_volunteers_to_brewers(self, **kwargs):

        try:
            volunteers = json.loads(kwargs.get('data', {}))
        except:
            volunteers = []

        errors = []

        for volunteer in volunteers:

            sql = 'update volunteers set fk_brewers = "{d[pkid]}" where pkid = "{d[vol_pkid]}"'.format(d=volunteer)

            self.db.db_command(sql=sql)

            if self.db.sql_error:
                errors.append(self.db.sql_error)
        return ','.join(errors)


    @cherrypy.expose
    def unassign_volunteers_to_brewers(self, **kwargs):

        try:
            volunteers = json.loads(kwargs.get('data', {}))
        except:
            volunteers = []

        errors = []

        for volunteer in volunteers:

            sql = 'update volunteers set fk_brewers = "0" where pkid = "{d[vol_pkid]}"'.format(d=volunteer)

            self.db.db_command(sql=sql)

            if self.db.sql_error:
                errors.append(self.db.sql_error)
        return ','.join(errors)


    ######################
    #
    # Table Assignments
    #
    ######################
    @cherrypy.expose
    def tables(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='tables.html')
        return form

    @cherrypy.expose
    def dt_tables(self, *args, **kwargs):

        sql = 'select tables.pkid, tables.name, tables.head_judge, tables.second_judge, ' \
              's.pkid as session_pikd, s.name as session_name from tables ' \
              'inner join sessions as s on s.pkid = fk_sessions ' \
              'where tables.fk_competitions = "{}"'.format(Competitions().get_active_competition())


        result = self.dt.parse_request(sql=sql, table='tables', debug=True, *args, **kwargs)

        for r in result['data']:
            r['head_judge'] = json.loads(r['head_judge'])
            r['second_judge'] = json.loads(r['second_judge'])
            r['total'] = 0

            brewer = r['head_judge']['fk_brewers']

            if brewer:
                r['head_judge']['categories'] = Entrys().get_brewer_categories(brewer)
            else:
                r['head_judge']['categories'] = []

            brewer = r['second_judge']['fk_brewers']

            if brewer:
                r['second_judge']['categories'] = Entrys().get_brewer_categories(brewer)
            else:
                r['second_judge']['categories'] = []


        return json.dumps(result, cls=DatetimeEncoder)


    @cherrypy.expose
    def generate_tables(self, *args, **kwargs):

        sql = 'select * from sessions where judging = "1" and fk_competitions = "{}"'.format(Competitions().get_active_competition())

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)
        session_counter = 0

        tables = {}

        for session in result:


            sql = 'select * from judge_pairing where fk_sessions = "{}"'.format(session['pkid'])

            uid = gen_uid()
            judges = self.db.db_command(sql=sql, uid=uid).all(uid)

            judges = judges[0]

            try:
                head_judge = json.loads(judges['head_judge'])
            except:
                head_judge = []

            try:
                second_judge = json.loads(judges['second_judge'])
            except:
                second_judge = []

            number_of_judges = 0

            for j in head_judge:
                if number_of_judges < j['order']:
                    number_of_judges = j['order']
                judges_table = 'Table {}'.format(str(j['order'] + session_counter))

                if judges_table not in tables:
                    tables[judges_table] = {
                        'name': judges_table,
                        'session_name': session['name'],
                        'fk_sessions': session['pkid'],
                        'head_judge': j,
                        'second_judge': {}
                    }

                tables[judges_table]['head_judge'] = j


            for j in second_judge:
                if number_of_judges < j['order']:
                    number_of_judges = j['order']
                judges_table = 'Table {}'.format(str(j['order'] + session_counter))

                if judges_table not in tables:
                    tables[judges_table] = {
                        'name': judges_table,
                        'session_name': session['name'],
                        'fk_sessions': session['pkid'],
                        'head_judge': {},
                        'second_judge': j
                    }

                tables[judges_table]['second_judge'] = j

            session_counter += number_of_judges + 5

        tables_list = []
        for t in tables:
            tables_list.append(tables[t])

        return json.dumps(tables_list, cls=DatetimeEncoder)


    @cherrypy.expose
    def save_tables(self, *args, **kwargs):

        try:
            tables = json.loads(kwargs.get('data', {}))
        except:
            tables = []

        sql = 'delete from tables where fk_competitions = "{}"'.format(Competitions().get_active_competition())
        self.db.db_command(sql=sql)

        for table in tables:

            head_judge = escape_sql(json.dumps(table['head_judge']))
            second_judge = escape_sql(json.dumps(table['second_judge']))

            sql = 'insert into tables (name, fk_sessions, fk_competitions, head_judge, second_judge) ' \
                  'values ("{}", "{}", "{}", "{}", "{}")'.format(table['name'],
                                                                 table['fk_sessions'],
                                                                 Competitions().get_active_competition(),
                                                                 head_judge,
                                                                 second_judge
                                                                 )
            self.db.db_command(sql=sql)

        return self.db.sql_error


    ######################
    #
    # Flght Assignments
    #
    ######################
    @cherrypy.expose
    def flights(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='flights.html')
        return form

    @cherrypy.expose
    def dt_flights(self, *args, **kwargs):

        sql = 'select * from flights where fk_competitions = "{}"'.format(Competitions().get_active_competition())

        result = self.dt.parse_request(sql=sql, table='flights', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)

    @cherrypy.expose
    def save_flights(self, *args, **kwargs):

        errors = []

        try:
            flights = json.loads(kwargs.get('data', {}))
        except:
            flights = []

        sql = 'delete from flights where fk_competitions = "{}"'.format(Competitions().get_active_competition())
        self.db.db_command(sql=sql)

        for flight in flights:
            flight['tables'] = escape_sql(json.dumps(flight['tables']))
            sql = 'insert into flights (number, category, style, category_id, sub_category_id, ' \
                  'tables, fk_competitions) ' \
                  'values ("{d[number]}", "{d[category]}", "{d[style]}", "{d[category_id]}", ' \
                  '"{d[sub_category_id]}", "{d[tables]}", "{fk_competitions}")'.format(d=flight,
                                                                 fk_competitions=Competitions().get_active_competition(),
                                                                 )
            self.db.db_command(sql=sql)

            if self.db.sql_error:
                errors.append(self.db.sql_error)

        return json.dumps({'error': errors})


    @cherrypy.expose
    def init_flights(self, *args, **kwargs):

        result = []

        fk_categories = Competitions().get_categories().split(',')

        sql = 'select * from category_strength_rating where pkid in ("{}")'.format('","'.join(fk_categories))

        uid = gen_uid()
        categories = self.db.db_command(sql=sql, uid=uid).all(uid)

        flight_num = 0
        for cat in categories:
            flight_num += 1
            styles = Style('BJCP2015').get_styles_for_group(int(cat['category_id']), style_type=['beer', 1])

            for style in styles:

                category_desc = '{} {}'.format(cat['category_id'], cat['category'])
                style_desc = '{}{} {}'.format(str(int(cat['category_id'])), style['style_num'], style['style_name'])


                result.append({'category': category_desc,
                               'style': style_desc,
                               'category_id': int(cat['category_id']),
                               'sub_category_id': style['style_num'],
                               'count': 0,
                               'tables': [],
                               'number': flight_num
                               })

        return json.dumps({'data': result}, cls=DatetimeEncoder)

    @cherrypy.expose
    def get_styles_count(self, *args, **kwargs):

        result = 'done'

        try:
            full_inventory = json.loads(kwargs.get('data', {}))
        except:
            full_inventory = True

        if not full_inventory:
            where = ' where inventory = "1" '
        else:
            where = ''

        print(full_inventory)

        sql = 'SELECT count(sub_category), category, sub_category FROM entries {} ' \
              'group by category, sub_category order by category, sub_category;'.format(where)

        uid = gen_uid()
        styles_count = self.db.db_command(sql=sql, uid=uid).all(uid)

        result = {}
        for style in styles_count:

            category = style['category']
            if category not in result:
                result[category] = {}

            result[category][style['sub_category']] = style['count(sub_category)']


        return json.dumps({'data': result}, cls=DatetimeEncoder)


    ######################
    #
    #
    # ** Email System **
    #
    #
    ######################


    ######################
    #
    # Email Editor
    #
    ######################
    @cherrypy.expose
    def email_editor(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='email_editor.html')
        return form

    @cherrypy.expose
    def dt_email_editor(self, *args, **kwargs):

        sql = 'select * from email_text'


        result = self.dt.parse_request(sql=sql, table='email_text', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)


    @cherrypy.expose
    def get_ncbc_email_list(self):

        result = Volunteers().get_ncbc_email_list()

        return json.dumps(result)


    @cherrypy.expose
    def send_status(self, **kwargs):

        print(kwargs)
        try:
            email_params = json.loads(kwargs['data'])
        except:
            email_params = {}

        sql = 'select count(*) from brewers where fk_competitions = "{}"'.format(Competitions().get_active_competition())

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).one(uid)

        num_brewers = result.get('count(*)', 'Not found')


        result = Competitions().get_comp_status()

        entries = result.get('entries', {})
        table = '<h3>Inventory Volunteers:</h3>'

        table += '<table border="1" style="border-collapse:collapse" cellpadding="2" >' \
                 '<thead>' \
                 '<tr>' \
                 '<th>Session</th>' \
                 '<th>Judges</th>' \
                 '<th>Stewards</th>' \
                 '</tr>' \
                 '</thead>' \
                 '<tbody>'

        count = 0
        num_judges = 0


        for sessions in result['sessions']:

            num_judges += sessions['judges']
            table += '<tr>' \
                     '<td>{}</td>' \
                     '<td>{}</td>' \
                     '<td>{}</td>' \
                     '</tr>'.format(sessions['name'], sessions['judges'], sessions['stewards'])

            if count == 3:
                table += '</tbody>' \
                         '</table>'

                table += '<h3>Competition Volunteers:</h3>'

                table += '<table border="1" style="border-collapse:collapse" cellpadding="2" >' \
                         '<thead>' \
                         '<tr>' \
                         '<th>Session</th>' \
                         '<th>Judges</th>' \
                         '<th>Stewards</th>' \
                         '</tr>' \
                         '</thead>' \
                         '<tbody>'

            count += 1

        table += '</tbody>' \
                 '</table>'

        num_entries = entries.get('entries', 0)

        beers_per_judge = round(num_entries / (num_judges / 2))



        email_params['msg'] = email_params.get('message', '').format(num_entries,  num_brewers, (datetime.date(2018, 9, 24) - datetime.date.today()).days, table, beers_per_judge)

        #email_params['msg'] = email_params['msg'].format(num_entries,  num_brewers, (datetime.date(2018, 9, 23) - datetime.date.today()).days, table, beers_per_judge)
        #email_params['msg'] = '{}{}{}{}{} '.format(num_entries,  num_brewers, (datetime.date(2018, 9, 23) - datetime.date.today()).days, table, beers_per_judge)
        print('send status', email_params)

        email_params = json.dumps(email_params)

        result = self.send_email(**{'data': email_params})

        return result




    @cherrypy.expose
    def send_email(self, *args, **kwargs):


        try:
            email_params = json.loads(kwargs['data'])
        except:
            email_params = {}

        send_to = email_params.get('to', '')
        send_bcc = email_params.get('bcc', '')
        send_cc = email_params.get('cc', '')

        errors = []
        result = {}

        sender = email_params.get('from', '')

        try:
            to = json.loads(send_to)
        except Exception as e:
            to = send_to


        try:
            cc = json.loads(send_cc)
        except Exception as e:
            cc = send_cc

        try:
            bcc = json.loads(send_bcc)
        except Exception as e:
            bcc = send_bcc


        if type(to) != type([]):
            to = [to]
        if type(cc) != type([]):
            cc = [cc]
        if type(bcc) != type([]):
            bcc = [bcc]


        subject = email_params.get('subject', '')

        msg = email_params.get('msg', '')

        email_type = email_params.get('type', 'unknown')
        content_type = email_params.get('content_type', 'text')

        file_path = email_params.get('file_path', '')
        file_list = email_params.get('file_list', [])



        #send email if all the fields are populated and the file attachment fields are populated if email_type is file
        if sender and (to or cc or bcc) and subject and msg and ((email_type == 'file' and file_path and file_list) or email_type != 'file'):
            email = Email('files/kevin.json')

            message = None

            if content_type == 'html':
                message = email.create_html_message(sender=sender,
                                            to=to,
                                            bcc=bcc,
                                            cc=cc,
                                            subject=subject,
                                            message_text=msg,
                                            )
            elif content_type == 'text':
                message = email.create_message(sender=sender,
                                            to=to,
                                            bcc=bcc,
                                            cc=cc,
                                            subject=subject,
                                            message_text=msg,
                                            )
            elif content_type == 'file':
                message = email.create_message_with_attachment(sender=sender,
                                            to=to,
                                            bcc=bcc,
                                            cc=cc,
                                            subject=subject,
                                            message_text=msg,
                                            file_dir=file_path,
                                            filename=file_list
                                            )

            if message:
                result = email.send_message(message, rcpt=to + cc + bcc)
            else:
                errors.append('Unable to create message with content type: {}'.format(content_type))

        else:
            if not sender:
                errors.append('From field is blank')
            if not to or not cc or not bcc:
                errors.append('To, CC or BCC fields are blank to: "{}", cc: "{}", bcc: "{}"'.format(to, cc, bcc))
            if not subject:
                errors.append('Subject field is blank')
            if not msg:
                errors.append('Message is blank')

            if email_type == 'file':
                if not file_path:
                    errors.append('File path is blank for "file" email type')
                if not file_list:
                    errors.append('File list is blank for "file" email type')


        return json.dumps({'data': result, 'error': errors}, cls=DatetimeEncoder)



    ######################
    #
    #
    # ** Global Settings **
    #
    #
    ######################



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

    ######################
    #
    # Certification Rankings
    #
    ######################
    @cherrypy.expose
    def cert_rank(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='cert_rank.html')
        return form

    @cherrypy.expose
    def dt_cert_rank(self, *args, **kwargs):

        sql = 'select * from cert_rank'

        result = self.dt.parse_request(sql=sql, table='cert_rank', debug=True, *args, **kwargs)
        return json.dumps(result, cls=DatetimeEncoder)



    ######################
    #
    # Category Strength Rating
    #
    ######################
    @cherrypy.expose
    def strength_rating(self, **kwargs):
        page_name = sys._getframe().f_code.co_name
        form = self.build_page(page_name, html_page='strength_rating.html')
        return form

    @cherrypy.expose
    def dt_strength_rating(self, *args, **kwargs):

        sql = 'select * from category_strength_rating'

        result = self.dt.parse_request(sql=sql, table='category_strength_rating', debug=True, *args, **kwargs)
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
