

from Person import Person
from Tools import Tools
from Competitions import DATABASE
from Competitions import Competitions
from Sessions import Sessions
from Volunteers import Volunteers
from Brewers import Brewers
from Entrys import Entrys

"""
https://stackoverflow.com/questions/1210458/how-can-i-generate-a-unique-id-in-python
"""
import threading
_uid = threading.local()
def gen_uid():
    if getattr(_uid, "uid", None) is None:
        _uid.tid = threading.current_thread().ident
        _uid.uid = 0
    _uid.uid += 1
    return (_uid.tid, _uid.uid)

# create logger
import logging
import os



LEVEL = logging.INFO
logger = logging.getLogger(os.path.basename(__file__).split('.')[0] if __name__ == '__main__' else __name__.split('.')[0])
logger.setLevel(LEVEL)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(LEVEL)

# create formatter
formatter = logging.Formatter('%(asctime)s.%(msecs)03d: %(levelname)s: %(name)s.%(funcName)s(): %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
# end create logger


logging.captureWarnings(True)  #eliminate the insecure warnings on the console


from MySql import local_host
from Database import Database
from Database import escape_sql

DATABASE = ''
NCBC_DB = ''
TEST_MODE = True
#https://gist.github.com/igniteflow/1760854
try:
    # use the develop database if we are using develop
    import os
    from git import Repo
    repo = Repo(os.getcwd())
    branch = repo.active_branch
    branch = branch.name
    if branch == 'master':
        DATABASE = 'ncbc-2020'
        NCBC_DB = 'ncbc-data-2020'
        TEST_MODE = False
    else:
        DATABASE = 'comp_test'
        NCBC_DB = 'ncbc_test'
        TEST_MODE = True
except ImportError:
    pass

db = Database(local_host['host'], local_host['user'], local_host['password'], NCBC_DB)


class Import:

    def __init__(self):

        pass

    #import volunteers

    def get_ncbc_volunteers(self):

        sql = 'select * from volunteers where new = "1" or changed = "1" order by email'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result

    def get_session_mapping(self):
        sql = 'select * from session_mapping where fk_competitions = "{}"'.format(
            Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        mapping = {}

        for r in result:
            mapping[r['session']] = str(r['session_number'])

        return mapping

    def update_volunteer_fields(self, row):

        #print(row.keys())
        row_fields = ['last_name', 'first_name', 'organization',
         'home_phone', 'work_phone', 'email', 'package', 'attendee_id',
         'notes', 'certifications', 'consider_steward', 'consider_judge', 'steward_certs', 'new', 'changed', 'judge',
         'deleted', 'updated', 'fk_competitions']

        updated = {}

        row['notes'] = row['notes'].replace('"', r'\"')
        row['certifications'] = row['certifications'].replace('"', r'\"')

        updated['notes'] = 'Notes: {d[notes]}, Certs: {d[certifications]} {d[steward_certs]}, ' \
                       'Judge: {d[consider_judge]}, Steward: {d[consider_steward]}, ' \
                       'Attendee ID: {d[attendee_id]}'.format(d=row)

        updated['phone'] = 'Home: {}, Work: {}'.format(row['home_phone'], row['work_phone'])

        updated['lastname'] = row['last_name']
        updated['firstname'] = row['first_name']
        updated['email'] = row['email']
        updated['organization'] = row['organization']
        updated['judge'] = row['judge']
        updated['new'] = row['new']
        updated['changed'] = row['changed']
        updated['fk_competitions'] = row['fk_competitions']

        return updated

    def import_ncbc_volunteers(self):

        import_result = {'updated': 0, 'inserted': 0, 'errors': []}

        rows = Import().get_ncbc_volunteers()

        if len(rows) == 0:
            logger.info('No new volunteers to import')
            return import_result

        mapping = Import().get_session_mapping()
        print('mapping', mapping)

        for row in rows:
            result = Tools().find('people', ['firstname', 'nickname', 'lastname', 'alias', 'email'],
                                  name=row['last_name'], email=row['email'])

            logger.info(
                'Looking for {} {}, {} and found {} results'.format(row['first_name'], row['last_name'], row['email'],
                                                                    len(result)))

            # Get NCBC Session info from competitions DB
            session_number = mapping[row['package']]
            session = Sessions().get_session_by_number(session_number)
            logger.info('Volunteer\'s session: {}'.format(session['name']))

            # sanitize name and email values
            firstname = row['first_name'].lower()
            lastname = row['last_name'].lower()
            email = row['email'].lower()

            options = []

            for r in result:

                count = 0

                # see if registered firstname = people.firstname or nickname
                if r['firstname'].lower() == firstname or (
                        r['nickname'] is not None and r['nickname'].lower() == firstname):
                    count += 1

                if r['lastname'].lower() == lastname:
                    count += 1

                if r['email'].lower() == email:
                    count += 1

                # count of 3 means exact match
                options.append(count)

            # print(options)

            selected = []  # list of exact matches - hopefully only 1
            count = 0

            for option in options:

                if option == 3:  # get index of exact matches - is there a python method for this?
                    selected.append(result[count])

                count += 1

            fk_people = 0
            if selected:
                logger.info('Found {} records that have exact match: {}'.format(len(selected), selected))

                if len(selected) > 1:
                    logger.error('Found more than one option')

                else:
                    selected = selected[0]
                    fk_people = selected['alias'] if selected['alias'] else selected['pkid']


            elif len(result) == 0:
                logger.info('{} {} not found, inserting new record'.format(firstname, lastname))
                # todo: insert person
                # todo: then get pkid to set fk_people

            else:
                logger.info('Found {} potential options for {} {}'.format(len(result), firstname, lastname))
            
            record = Import().update_volunteer_fields(row)

            record['fk_people'] = fk_people
            record['fk_sessions'] = session['pkid']
            record['fk_competitions'] = Competitions().get_active_competition()
            print('adding record', record)
            result, inserted = Volunteers().add_record(record)

            if not result:
                logger.error('Error adding volunteer {d[firstname]} {d[lastname]} to database'.format(d=record))
                import_result['errors'].append('Error adding volunteer {d[firstname]} {d[lastname]} to database'.format(d=record))
            else:
                if inserted:
                    import_result['inserted'] += 1
                else:
                    import_result['updated'] += 1
                sql = 'update volunteers set new = "0", changed = "0" where pkid = "{}"'.format(row['pkid'])
                db.db_command(sql=sql)
            
        return import_result

    def get_brewer(self, pkid):

        sql = 'select * from people where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result



    def get_ncbc_entries(self):

        sql = 'select * from entries where imported = "0" and fk_competitions = "{}"'.format(Competitions().get_active_competition())
        print(sql)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)
        print(result)
        return result




    def import_ncbc_entries(self):
        rows = Import().get_ncbc_entries()

        import_result = {'brewers': 0, 'entries': 0, 'errors': []}

        if len(rows) == 0:
            logger.info('No new entries to import')
            return import_result

        for row in rows:

            fk_people = row['fk_people']

            ncbc_brewer = self.get_brewer(fk_people)

            row['description'] = escape_sql(row['description'])

            brewer_pkid = Brewers().find_brewer(ncbc_brewer.get('email', ''))

            if brewer_pkid == 0:

                new_brewer = {}

                new_brewer['email'] = ncbc_brewer['email']
                new_brewer['firstname'] = ncbc_brewer['first_name']
                new_brewer['lastname'] = ncbc_brewer['last_name']
                new_brewer['organization'] = ncbc_brewer['organization']
                new_brewer['address'] = ncbc_brewer['address']
                new_brewer['address_2'] = ncbc_brewer['address_2']
                new_brewer['city'] = ncbc_brewer['city']
                new_brewer['state'] = ncbc_brewer['state']
                new_brewer['zip'] = ncbc_brewer['zip']
                new_brewer['phone'] = ncbc_brewer['phone']
                new_brewer['fk_competitions'] = ncbc_brewer['fk_competitions']

                result = Brewers().insert(new_brewer)

                if not result:
                    logger.error('Unable to insert new brewer {d[firstname]} {d[lastname]}, {d[email]}'.format(d=row))

                    import_result['errors'].append('Unable to insert new brewer {d[firstname]} {d[lastname]}, {d[email]}'.format(d=row))
                else:
                    import_result['brewers'] += 1

            brewer_pkid = Brewers().find_brewer(ncbc_brewer['email'])

            if brewer_pkid == 0:
                logger.error('Unable to find brewer, skipping entry insert for pkid: {}'.format(row['pkid']))
                import_result['errors'].append('Unable to find brewer, skipping entry insert for pkid: {}'.format(row['pkid']))
                continue


            fields = ['entry_id', 'category', 'sub_category', 'name', 'description',
                      'fk_competitions']

            new_entry = {}
            for field in fields:
                new_entry[field] = row[field]

            new_entry['fk_brewers'] = brewer_pkid

            result = Entrys().insert(new_entry)

            if result:
                logger.info('Insert entry {d[category]} {d[sub_category]}, {d[name]}'.format(d=row))

                sql = 'update entries set imported = "1" where entry_id = "{}"'.format(row['entry_id'])
                db.db_command(sql=sql)
                import_result['entries'] += 1
            else:
                logger.error('Unable to insert entry {d[category]} {d[sub_category]}, {d[name]}'.format(d=row))
                import_result['errors'].append('Unable to insert entry {d[category]} {d[sub_category]}, {d[name]}'.format(d=row))

        return import_result

def test_import_volunteers():
    result = Import().import_ncbc_volunteers()
    print(result)
    #Volunteers().email_new()
    #Volunteers().email_changed()

def test_import_entries():

    result = Import().import_ncbc_entries()
    print(result)


def import_descriptions():

    sql = 'select entry_id, description from entries'

    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)

    for r in result:

        entry_id = r.pop('entry_id')

        r['description'] = escape_sql(r['description'])
        success = Entrys().update(r, entry_id, 'entry_id')

        print(success)

if __name__ == '__main__':

    #test_import_volunteers()

    test_import_entries()

    #import_descriptions()

    pass






