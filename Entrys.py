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
        """
        Get inventory status
        :return: {'num_entries': 136, 'inventory': 0, 'location_0': 136, 'location_1': 136}
        """

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


    def add_inventory(self, entry_id, location_0='', location_1=''):
        """
        Update entry by marking it as inventoried and adding location info

        returns 0 if entry not found, entry id if updated and negative entry id if found but nothing updated
        :param entry_id: entry id
        :param location_0: location of entry 1
        :param location_1: location of entry 2
        :return:
        """
        sql = 'select pkid from entries ' \
              'where entry_id = "{}" and fk_competitions = "{}"'.format(entry_id, Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        if not result:
            logger.error('Entry ID {}  not found in database'.format(entry_id))
            return 0

        sql = 'update entries set inventory = "1", location_0 = "{}", location_1 = "{}" ' \
              'where pkid = "{}"'.format(location_0, location_1, result['pkid'])

        db.db_command(sql=sql)

        if db.row_count() == 0:
            logger.info('No changes made for Entry ID {}'.format(entry_id))
            return -result['pkid']

        if db.sql_error:
            logger.error('Error updating Entry ID {}, error: {}'.format(entry_id, db.sql_error))
            return 0

        return result['pkid']


    def remove_inventory(self, entry_id):
        """
        Update entry by marking it as not in inventory

        returns 0 if entry not found, entry id if updated and negative entry id if found but nothing updated
        :param entry_id: entry id
        :return:
        """

        sql = 'select pkid from entries ' \
              'where entry_id = "{}" and fk_competitions = "{}"'.format(entry_id, Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        if not result:
            logger.error('Entry ID {}  not found in database'.format(entry_id))
            return 0

        sql = 'update entries set inventory = "0", location_0 = "", location_1 = "" ' \
              'where pkid = "{}"'.format(result['pkid'])

        db.db_command(sql=sql)

        if db.row_count() == 0:
            logger.info('No changes made for Entry ID {}'.format(entry_id))
            return -result['pkid']

        if db.sql_error:
            logger.error('Error updating Entry ID {}, error: {}'.format(entry_id, db.sql_error))
            return 0

        return result['pkid']

    def get_inventory(self, all=False, inventory=False, wo_location=False):

        where = 'fk_competitions ="{}"'.format(Competitions().get_active_competition())

        if not all:
            where += ' and inventory = "{}"'.format('1' if inventory else '0')

        if wo_location:
            where += ' and ((location_0 is NULL or location_0 = "") or ' \
                     '(location_1 is NULL or location_1 = ""))'

        sql = 'select * from entries where {}'.format(where)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


    def get_brewer_categories(self, fk_brewers):

        sql = 'SELECT distinct category FROM entries where fk_brewers = "{}" order by CAST(category AS UNSIGNED)'.format(fk_brewers)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        category_list = []

        for r in result:
            category_list.append(r['category'])

        return category_list

def test_add_inventory():
    print(Entrys().inventory_status())
    print(Entrys().add_inventory(2))
    print(Entrys().inventory_status())

    print(Entrys().add_inventory(2))
    print(Entrys().inventory_status())

    print(Entrys().add_inventory(3, 'Cooler1', 'Box5'))
    print(Entrys().inventory_status())

    print(Entrys().add_inventory(1))
    print(Entrys().inventory_status())

def test_remove_inventory():
    print(Entrys().remove_inventory(2))
    print(Entrys().inventory_status())

    print(Entrys().remove_inventory(2))
    print(Entrys().inventory_status())

    print(Entrys().remove_inventory(3))
    print(Entrys().inventory_status())


def test_inventory_report(**kwargs):

    result = Entrys().get_inventory(**kwargs)

    for r in result:
        print('Entry ID:{d[entry_id]}, Inv: {d[inventory]}, Loc0: "{d[location_0]}", '
              'Loc1: "{d[location_1]}"'.format(d=r))

    print('Number of returned inventory items: {}'.format(len(result)))


def test_get_inv():

    print('Inventory')
    test_inventory_report(inventory=True)

    print('\nInventory without locations')
    test_inventory_report(inventory=True, wo_location=True)


    #print('\nAll')
    #test_inventory_report(all=True)



if __name__ == '__main__':

    #test_add_inventory()
    #test_get_inv()

    #test_remove_inventory()
    #test_get_inv()



    pass