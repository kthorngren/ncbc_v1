import re

from Competitions import DATABASE
from Competitions import Competitions
from Entrys import Entrys
from Styles import  Style


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

db = Database(local_host['host'], local_host['user'], local_host['password'], DATABASE)


class Brewers:

    def __init__(self):

        pass


    def find_brewer(self, email):

        sql = 'select pkid from brewers where email = "{}"'.format(email)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('pkid', 0)

    def get_brewer(self, pkid):

        sql = 'select * from brewers where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result

    def get_brewers(self, order_by=''):

        if order_by:
            order_by = 'order by {}'.format(order_by)

        sql = 'select * from brewers where fk_competitions = "{}" {}'.format(Competitions().get_active_competition(), order_by)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


    def insert(self, record):

        success = True
        fields = []
        values = []

        for k, v in record.items():
            fields.append(str(k))
            values.append(str(v))

        sql = 'insert into brewers ({}, updated) values ("{}", NOW())'.format(','.join(fields), '","'.join(values))
        db.db_command(sql=sql)

        if (db.row_count() > 0):
            logger.info('Insert brewer {d[firstname]} {d[lastname]}'.format(d=record))
        else:
            logger.error(
                'Unable to insert brewer {d[firstname]} {d[lastname]}'.format(d=record))
            success = False

        return success


    def get_entries(self, pkid):
        pass


def print_entries(order_by=''):

    result = Brewers().get_brewers(order_by=order_by)

    count = 0

    for r in result:

        entries = Entrys().get_entries_by_brewer(r['pkid'], order_by='category')
        if order_by == 'organization':
            print('{d[organization]} {d[firstname]} {d[lastname]} - {d[email]} - '
                  '# of entries: {num}'.format(d=r, num=len(entries)))
        elif order_by == 'email' :
            print('{d[email]} {d[firstname]} {d[lastname]} - {d[organization]} - '
                  '# of entries: {num}'.format(d=r, num=len(entries)))
        elif order_by == 'lastname' :
            print('{d[firstname]} {d[lastname]} {d[email]} - {d[organization]} - '
                  '# of entries: {num}'.format(d=r, num=len(entries)))
        else:
            print('{d[email]} {d[firstname]} {d[lastname]} - {d[organization]} - '
                  '# of entries: {num}'.format(d=r, num=len(entries)))

        for entry in entries:
            count += 1
            print('   {d[entry_id]:05}: {d[category]}{d[sub_category]} {cat_name}: '
                  'Name: {d[name]}'.format(d=entry,
                                           cat_name=Style(Competitions().get_style_guidelines()).get_style_name(entry['category'], entry['sub_category'])))
            if Style(Competitions().get_style_guidelines()).is_specialty(entry['category'], entry['sub_category']):
                print('      Desc: {}'.format(entry['description']))
                if not re.sub(r'\s', '', entry['description']):
                    print('**Error no descrition for specialty beer')
    print('Total Brewers: {}'.format(len(result)))
    print('Total Entries: {}'.format(count))


def list_specialty_wo_desc():

    print('Specialty entries without descriptions')
    result = Brewers().get_brewers(order_by='organization')

    for r in result:
        entries = Entrys().get_entries_by_brewer(r['pkid'], order_by='category')

        for entry in entries:

            if Style(Competitions().get_style_guidelines()).is_specialty(entry['category'], entry['sub_category']) and not re.sub(r'\s', '', entry['description']):
                print('{d[organization]} {d[firstname]} {d[lastname]} - {d[email]}: No descrption for Entry ID: '
                      '{e[entry_id]:05}: {e[category]}{e[sub_category]} {cat_name}'.format(d=r, e=entry,
                                            cat_name=Style(Competitions().get_style_guidelines()).get_style_name(entry['category'], entry['sub_category'])))


if __name__ == '__main__':

    print_entries(order_by='organization')

    list_specialty_wo_desc()

    pass