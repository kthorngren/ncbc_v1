import json

from Tools import Tools
from Competitions import DATABASE
from Competitions import Competitions
from Entrys import Entrys
from Styles import Style


from pdflabels import PDFLabel
from pif import get_public_ip

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


class Reports:

    def __init__(self):

        pass


    def print_round_bottle_labels(self):

        PADDING = 5
        l = PDFLabel('075-circle', font = 'Courier', font_size=13)
        l.add_page()
        labels = Entrys().get_inventory(all=True)
        for i in sorted(labels, key=lambda r: r['entry_id']):
            entry_id = int(i['entry_id'])
            category = '{}{}'.format(i['category'], i['sub_category'])
            l.add_label('  {:05d}\n {}\n'.format(entry_id, category))
        l.output('files/reports/bottle_labels.pdf')


    def print_round_cup_labels(self):

        LABELS_PER_LINE = 9
        PADDING = 5
        l = PDFLabel('050-circle', font = 'Courier', font_size=13)
        l.add_page()
        labels = Entrys().get_inventory(inventory=True)
        label_count = 0
        category = ''
        for i in sorted(labels, key=lambda r: r['category']):
            print(i['category'])
            if category != i['category']:
                category = i['category']
                print('cat change')
                while label_count % LABELS_PER_LINE != 0:
                    print('space')
                    l.add_label(' ')
                    label_count += 1
                l.add_label('C: {}'.format(i['category']))
                print('print cat')
                label_count += 1
                while label_count % LABELS_PER_LINE != 0:
                    print('add space')
                    l.add_label(' ')
                    label_count += 1


            entry_id = int(i['entry_id'])
            print('print entry id')
            l.add_label('  {:03d}'.format(entry_id))
            l.add_label('  {:03d}'.format(entry_id))
            label_count += 2
        l.output('files/reports/cup_labels.pdf')



    def flight_pull_sheets(self, category):

        flights = {}
        table_list = []

        #print('category', category)

        sql = 'select * from flights where category_id = "{}" and ' \
              'fk_competitions = "{}"'.format(category, Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        try:
            tables_list = json.loads(result[0]['tables'])
        except:
            tables_list = []

        #print(tables_list)



        sql = 'select * from tables where name in ("{}")'.format('","'.join(tables_list))


        uid = gen_uid()
        tables = db.db_command(sql=sql, uid=uid).all(uid)


        for table in tables:

            table_list.append(table)

            try:
                head_judge = json.loads(table['head_judge'])
            except:
                head_judge = {}
            hj_certs = []

            if head_judge['bjcp_rank']:
                hj_certs.append('BJCP {}'.format(head_judge['bjcp_rank']))
            if head_judge['cicerone']:
                hj_certs.append('Cicerone {}'.format(head_judge['cicerone']))
            if head_judge['other_cert'] and head_judge['other_cert'] != 'Apprentice':
                hj_certs.append(head_judge['other_cert'])


            try:
                second_judge = json.loads(table['second_judge'])
            except:
                second_judge = {}
            sj_certs = []

            if second_judge['bjcp_rank']:
                sj_certs.append('BJCP {}'.format(second_judge['bjcp_rank']))
            if second_judge['cicerone']:
                sj_certs.append('Cicerone {}'.format(second_judge['cicerone']))
            if second_judge['other_cert'] and second_judge['other_cert'] != 'Apprentice':
                sj_certs.append(second_judge['other_cert'])

            flights[table['name']] = {
                'head_judge': '{} {}\n{}'.format(head_judge['firstname'], head_judge['lastname'], ', '.join(hj_certs)),
                'second_judge': '{} {}\n{}'.format(second_judge['firstname'], second_judge['lastname'], ', '.join(sj_certs)),
                'category': category,
                'table': table['name'],
                'category_name': Style('BJCP2015').get_category_name(category),
                'beers': []
            }

        category_list = []



        sql = 'select * from entries ' \
              '' \
              'where category = "{}" and fk_competitions = "{}" ' \
              'order by category, sub_category, entry_id'.format(category, Competitions().get_active_competition())
        uid = gen_uid()
        cat  = db.db_command(sql=sql, uid=uid).all(uid)

        categories = {}


        entry = {}
        for c in cat:
            print(c)
            if Style('BJCP2015').is_specialty(str(c['category']), str(c['sub_category']) ):
                c['is_specialty'] = 1
            else:
                c['is_specialty'] = 0

            c['style_name'] = Style('BJCP2015').get_style_name(str(c['category']), str(c['sub_category']))



            if c['category'] not in categories:
                categories[c['category']] = []
            categories[c['category']].append(c)

        while len(cat) > 0:
            for f in flights:
                if cat:
                    flights[f]['beers'].append(cat.pop(0))

        #for f in flights:
        #    print(flights[f])
        #    for b in flights[f]['beers']:
        #        print(b)

        return flights



if __name__ == '__main__':

    #Reports().print_round_bottle_labels()
    #Reports().print_round_cup_labels()
    Reports().flight_pull_sheets(89)

