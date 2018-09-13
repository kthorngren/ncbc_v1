from Competitions import DATABASE
from Competitions import Competitions

import json
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


class Entrys:

    def __init__(self):

        pass


    def find_entry(self, entry_id=0):
        #todo: define what this function should do

        sql = 'select pkid from entries where entry_id = "{}"'.format(entry_id)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('pkid', 0)

    def get_entry(self, pkid):

        sql = 'select * from entries where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result


    def get_entries_by_brewer(self, pkid, order_by=''):

        sql = 'select * from entries where fk_brewers = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        if order_by == 'category':
            result = sorted(result, key=lambda k: '{:02d}{}'.format(int(k['category']), k['sub_category']))

        return result

    def get_specialty_entries_wo_desc(self):

        sql = 'select * from entries where '


    def insert(self, record):

        success = True
        fields = []
        values = []

        for k, v in record.items():
            fields.append(str(k))
            values.append(str(v))

        sql = 'insert into entries ({}, updated) values ("{}", NOW())'.format(','.join(fields), '","'.join(values))
        db.db_command(sql=sql)

        if (db.row_count() > 0):
            logger.info('Insert entry {d[category]} {d[sub_category]}, {d[name]}'.format(d=record))
        else:
            logger.error(
                'Unable to insert entry {d[category]} {d[sub_category]}, {d[name]}'.format(d=record))
            success = False

        return success


    def update(self, record, where_value, where_field='entry_id'):

        success = True

        set_command = ['{} = "{}"'.format(k, v) for k, v in record.items()]

        sql = 'update entries set {} where {} = "{}"'.format(','.join(set_command), where_field, where_value)

        db.db_command(sql=sql)

        if db.sql_error:
            logger.error('Unable to update entry with where clause: where {} = "{}"'.format(where_field, where_value))
            success = False
        else:
            logger.info('Row Count - row info changed: {}'.format(db.row_count()))

        return success


    def inventory_status(self):

        sql = 'select sum(fk_competitions = "{active}") as num_entries, ' \
              'sum(inventory = "1") as inventory, ' \
              'sum(location_0 is NULL or location_0 = "") as location_0, ' \
              'sum(location_1 is NULL or location_0 = "") as location_1 ' \
              'from entries where ' \
              'fk_competitions = "{active}"'.format(active=Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        #result = {'num_entries': Decimal('136'), 'inventory': Decimal('0'), 'location_0': Decimal('136'), 'location_1': Decimal('136')}
        #remove the Decimal object to allow for JSON serialization
        for r in result:
            result[r] = int(result[r])

        return result


if __name__ == '__main__':

    print(Entrys().inventory_status())


    pass