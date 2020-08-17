import json
from textwrap import wrap, dedent, fill
import csv
import re
from collections import defaultdict

from Tools import Tools
from Competitions import DATABASE
from Competitions import Competitions
from Entrys import Entrys
from Styles import Style
from Brewers import Brewers


from pdflabels import PDFLabel
from pif import get_public_ip

from fpdf import FPDF, HTMLMixin


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

    def table_assignments(self):

        sql = f'select * from tables where fk_competitions = "{Competitions().get_active_competition()}"'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        tables = {}

        for r in result:
            head_judge = json.loads(r['head_judge'])
            second_judge = json.loads(r['second_judge'])
            hj_certs = f'(BJCP {head_judge["bjcp_rank"]})' if head_judge["bjcp_rank"] else ''
            sj_certs = f'(BJCP {second_judge["bjcp_rank"]})' if second_judge["bjcp_rank"] else ''

            tables[r['name']] = {
                    'head_judge': f'{head_judge["firstname"]} {head_judge["lastname"]}',
                    'hj_certs': hj_certs,
                    'sj_certs': sj_certs,
                    'second_judge': f'{second_judge["firstname"]} {second_judge["lastname"]}'
                }
            

        for t in tables:
            print(f'{t},Head Judge:,{tables[t]["head_judge"]},{tables[t]["hj_certs"]},Second Judge:,{tables[t]["second_judge"]},{tables[t]["sj_certs"]}')



    def print_round_bottle_labels(self, number=4):

        PADDING = 5
        l = PDFLabel('075-circle', font = 'Courier', font_size=13)
        l.add_page()

        labels = Entrys().get_inventory(all=True)
        #print(labels)
        for i in sorted(labels, key=lambda r: r['entry_id']):

            for x in range(0, number):
                entry_id = int(i['entry_id'])
                category = f"F {Style('NCBC2020').get_judging_category('{}{}'.format(i['category'], i['sub_category']))}"
                l.add_label(' {:03d}\n{}\n'.format(entry_id, category))

        l.output('public/reports/bottle_labels.pdf')


    def print_round_cup_labels(self):

        paging = False

        # Use 9 and 12 becuase we can't get all the way to the margins
        LABELS_PER_LINE = 9
        LINES_PER_PAGE = 12 if paging else 1
        PADDING = 5

        sql = 'SELECT * FROM flights where fk_competitions = "5"'
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        fk_judge_locations = {}
        for r in result:
            flight = r['number']
            location = r['fk_judge_locations']
            fk_judge_locations[flight] = location

        print(fk_judge_locations)
        labels = Entrys().get_inventory(inventory=True)

        for label in labels:
            label['flight'] = Style('NCBC2020').get_judging_category(f'{label["category"]}{label["sub_category"]}')
 

        # Todo add support for locations

        locations = {
            1: 'Triangle',
            3: 'Asheville'
        }
        for location in [3]:  # todo: Get the session locations from DB
            l = PDFLabel('050-circle', font = 'Courier', font_size=13)
            l.add_page()
            label_count = 0
            category = ''
            prev_cat = ''
            entry_id_count = 0
            for i in sorted(labels, key=lambda r: int(r['flight'])):
                #print(i)
                if fk_judge_locations[int(i['flight'])] == location:
                    #print(i['flight'], i['entry_id'])
                    
                    if category != i['flight']:
                        category = i['flight']
                        #print('cat change', category)
                        if prev_cat: 
                            print(f'Flt: {prev_cat} Num: {entry_id_count}')
                        entry_id_count = 0
                        while label_count % (LABELS_PER_LINE * LINES_PER_PAGE) != 0:
                            l.add_label(' ')
                            label_count += 1
                            #print('space', label_count)
                        l.add_label("===Flt===")
                        l.add_label("==={:03d}===".format(int(i['flight'])))
                        label_count += 2
                        #print(f"print cat{i['flight']}", label_count)
                        while label_count % LABELS_PER_LINE != 0:
                            l.add_label(' ')
                            label_count += 1
                            #print('add space', label_count)
                    else:
                        prev_cat = i['flight']

                    entry_id = int(i['entry_id'])
                    entry_id_count += 1
                    l.add_label('  {:03d}'.format(entry_id))
                    l.add_label('  {:03d}'.format(entry_id))
                    label_count += 2
                    #print('print entry id', i['entry_id'], label_count)
            l.output(f'public/reports/{locations[location]} cup_labels.pdf')

    def master_flight_list(self):

        sql = 'SELECT * FROM flights where fk_competitions = "5"'
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        fk_judge_locations = {}
        for r in result:
            flight = r['number']
            location = r['fk_judge_locations']
            fk_judge_locations[flight] = location

        #print(fk_judge_locations)
        labels = Entrys().get_inventory(inventory=True)

        for label in labels:
            label['flight'] = Style('NCBC2020').get_judging_category(f'{label["category"]}{label["sub_category"]}')
 

        # Todo add support for locations

        locations = {
            1: 'Triangle',
            3: 'Asheville'
        }
        for location in [1, 3]:
            category = ''
            prev_cat = ''
            entry_id_count = 0
            new_cat = True
            for i in sorted(labels, key=lambda r: int(r['flight'])):
                #print(i)

                if fk_judge_locations[int(i['flight'])] == location:
                    if new_cat:
                        print(f"\n{i['flight']} {Style('NCBC2020').get_category_name(i['flight'])}")
                        new_cat = False
                        prev_cat = i['flight']

                    #print(i['flight'], i['entry_id'])
                    
                    if category != i['flight']:
                        category = i['flight']
                        new_cat = True
                        #print('cat change', category)
                        #if prev_cat: 
                        #    print(f'\nFlight: {prev_cat}, Number: {entry_id_count}')
                        entry_id_count = 0
                    else:
                        prev_cat = i['flight']
                    brewer = Brewers().get_brewer(i['fk_brewers'])
                    style_name = Style('NCBC2020').get_style_name(str(i['category']), str(i['sub_category']))
                    print(f",{i['entry_id']},{str(i['category'])}{str(i['sub_category'])} {style_name},{brewer['organization']},{i['comments']},")

                    """
                    {'pkid': 511, 'entry_id': 611, 'category': '32', 'sub_category': 'A', 
                    'fk_competitions': 5, 'description': 'Base style is an oatmeal/tropical stout, smoke is from peat smoked malt.', 
                    'name': 'Temporal Justice', 'fk_brewers': 72, 'original_description': None, 
                    'inventory': 1, 'judged': 0, 'place': 0, 'bos': 0, 'bos_place': 0, 
                    'updated': datetime.datetime(2020, 8, 7, 16, 4, 5), 'location_0': '', 'location_1': '', 
                    'one_bottle': 0, 'comments': '', 'ncbc_validation': 0, 'flight': '29'}
                    """

                    #print('print entry id', i['entry_id'], label_count)
            



    def print_round_bos_cup_labels(self):

        LABELS_PER_LINE = 11
        PADDING = 5

        sql = 'select entry_id, category, sub_category from entries where place = "1" order by LPAD(entries.category, 2, "0"), sub_category'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        for r in result:
            r['flight'] = Style('NCBC2020').get_judging_category(f'{r["category"]}{r["sub_category"]}')

        #print(result)



        l = PDFLabel('050-circle', font = 'Courier', font_size=13)
        l.add_page()
        label_count = 0
        category = ''
        for r in sorted(result, key=lambda x: x['flight']):
            #if r['entry_id'] == 214:
            l.add_label("===Cat===")
            l.add_label("==={:03d}===".format(int(r['flight'])))

            for x in range(0, 7):
                l.add_label(' ')

            for x in range(0, 9):
                #l.add_label('  {:03d}{}{}'.format(r['entry_id'],int(r['category']), r['sub_category']))
                l.add_label('  {:03d}'.format(r['entry_id']))

        l.output('public/flights/bos/bos_cup_labels.pdf')

    def flight_avery_cup_labels(self, entries, flight, filename):

        LABELS_PER_LINE = 9
        LINES_PER_PAGE = 12
        PADDING = 5
        l = PDFLabel('Avery-5160', font = 'Courier', font_size=13)
        l.add_page()
        labels = Entrys().get_inventory(inventory=False)
        label_count = 0
        category = ''
        print(entries)

        count = 0

        if entries:
            l.add_label("===Flt===")
            l.add_label("==={:03d}===".format(int(flight)))
            label_count += 2

            while label_count % LABELS_PER_LINE != 0:
                l.add_label(' ')
                label_count += 1
            # print('add space', label_count)

            for i in sorted(entries, key=lambda r: int(r['category'])):
                print(i)
                #if category != i['category']:
                category = i['category']
                #print('cat change')
                #print(f"print cat{i['category']}", label_count)


                entry_id = int(i['entry_id'])
                l.add_label('  {:03d}'.format(entry_id))
                l.add_label('  {:03d}'.format(entry_id))
                #l.add_label('  {:03d}'.format(entry_id))
                #l.add_label('  {:03d}'.format(entry_id))
                label_count += 2

                #if count % 2 == 0:
                #    l.add_label(' ')
                #    label_count += 1

                count += 1
                #print('print entry id', i['entry_id'], label_count)
            l.output(f'public/flights/{filename}.pdf')



    def flight_round_cup_labels(self, entries, flight, filename):

        LABELS_PER_LINE = 9
        LINES_PER_PAGE = 12
        PADDING = 5
        l = PDFLabel('050-circle', font = 'Courier', font_size=13)
        l.add_page()
        labels = Entrys().get_inventory(inventory=False)
        label_count = 0
        category = ''
        print(entries)

        count = 0

        if entries:
            l.add_label("===Flt===")
            l.add_label("==={:03d}===".format(int(flight)))
            label_count += 2

            while label_count % LABELS_PER_LINE != 0:
                l.add_label(' ')
                label_count += 1
            # print('add space', label_count)

            for i in sorted(entries, key=lambda r: int(r['category'])):
                print(i)
                #if category != i['category']:
                category = i['category']
                #print('cat change')
                #print(f"print cat{i['category']}", label_count)


                entry_id = int(i['entry_id'])
                l.add_label('  {:03d}'.format(entry_id))
                l.add_label('  {:03d}'.format(entry_id))
                #l.add_label('  {:03d}'.format(entry_id))
                #l.add_label('  {:03d}'.format(entry_id))
                label_count += 2

                #if count % 2 == 0:
                #    l.add_label(' ')
                #    label_count += 1

                count += 1
                #print('print entry id', i['entry_id'], label_count)
            l.output(f'public/flights/{filename}.pdf')


    def flight_pull_sheets(self, my_flights, descriptions=True):

        unasigned_counter = 1

        for category in my_flights:

            flights = {}
            table_list = []
            filenames = {}

            #print('category', category)

            sql = 'select * from flights where number = "{}" and ' \
                  'fk_competitions = "{}"'.format(category, Competitions().get_active_competition())

            uid = gen_uid()
            result = db.db_command(sql=sql, uid=uid).all(uid)


            flight_cat = []
            flight_sub_cat = []

            # Flight categories

            list_of_categories = []
            location = ''

            # todo: fetch this from DB
            judge_locations = {
                0: 'Unassigned',
                1: 'Triangle',
                2: 'Charlotte',
                3: 'Asheville'
            }
            if result:
                location = judge_locations.get(result[0]['fk_judge_locations'], '')
                location = f' - {location}' if location else ''

                for r in result:
                    #print('flight:', r)
                    # todo: make more generic
                    #list_of_categories.append(f'{r["category_id"]}{r["sub_category_id"]}')
                    list_of_categories.append(f'{r["sub_category_id"]}')

            try:
                tables_list = json.loads(result[0]['tables'])
            except:
                tables_list = []

            # Tables
            #print('tables_list', tables_list)

            if tables_list:

                sql = 'select * from tables where name in ("{}") and fk_competitions = "{}"'.format('","'.join(tables_list), Competitions().get_active_competition())

                uid = gen_uid()
                tables = db.db_command(sql=sql, uid=uid).all(uid)
            
            else:
                # todo: fi - specicif to ncbc 2020 to pre build flight sheets and build mini BOS if needed
                if result[0]['number'] in (27, 13):
                    tables = [None, None]
                else:
                    tables = [None]


            # Assigned judges
            #for t in tables:
            #    print(t)

            cup_labels = {}

            for table in tables:

                if table:
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
                        # the `|` are used for line splitting in FlightSheet, need four lines for intro area.
                        'head_judge': '{} {}|{}| | '.format(head_judge['firstname'], head_judge['lastname'], ', '.join(hj_certs)),
                        'second_judge': '{} {}|{}| | '.format(second_judge['firstname'], second_judge['lastname'], ', '.join(sj_certs)),
                        'category': category,
                        'table': table['name'],
                        'category_name': '{} {}'.format(category, Style('NCBC2020').get_category_name(category)),
                        'beers': []
                    }

                else:
                    flights[f'Unassigned {unasigned_counter}'] = {
                        # the `|` are used for line splitting in FlightSheet, need four lines for intro area.
                        'head_judge': '',
                        'second_judge': '',
                        'category': category,
                        'table': '',
                        'category_name': '{} {}'.format(category, Style('NCBC2020').get_category_name(category)),
                        'beers': []
                    }

                    unasigned_counter += 1
                #print(flights[table['name']] )
            category_list = []

            #print('list_of_categories', list_of_categories)
            sql = 'select * from entries ' \
                  '' \
                  'where CONCAT(category, sub_category) in ("{}")  and fk_competitions = "{}" and inventory = "1" ' \
                  'order by category, sub_category, entry_id'.format('","'.join(list_of_categories), Competitions().get_active_competition())
            uid = gen_uid()
            cat  = db.db_command(sql=sql, uid=uid).all(uid)

            dup_cat = cat.copy()

            categories = {}


            entry = {}
            for c in cat:
                #print(c)
                if Style('NCBC2020').is_specialty(str(c['category']), str(c['sub_category']) ):
                    c['is_specialty'] = 1 if descriptions else 0
                else:
                    c['is_specialty'] = 0

                c['style_name'] = Style('NCBC2020').get_style_name(str(c['category']), str(c['sub_category']))

                if not descriptions:
                    #if c['entry_id'] == 581:
                    #    print(c)
                    c['notes'] = c['comments']  # Get inventory comments for cellar
                else:
                    c['notes'] = ''

                if c['category'] not in categories:
                    categories[c['category']] = []
                categories[c['category']].append(c)
            #print('doing cat')
            while len(cat) > 0 and flights:
                #print('cat', flights)
                for f in flights:
                    if cat:
                        #print(cat)
                        flights[f]['beers'].append(cat.pop(0))

            #for f in flights:
            #    print(flights[f])
            #    for b in flights[f]['beers']:
            #        print(b)
            miniBos_count = 1
            for f in flights:

                flight = flights[f]

                judge_info = {
                    'head_judge': flight['head_judge'],
                    'second_judge': flight['second_judge']
                }

                if len(flights) > 1:
                    mini = f' (mBOS {miniBos_count} of {len(flights)})'
                else:
                    mini = ''

                miniBos_count += 1

                pdf = FlightSheet()

                pdf.flight = f'{f}: Flight: {category} {Style("NCBC2020").get_category_name(category)}: # of Entries: {len(flight["beers"])}{mini}'

                #print(pdf.flight)

                pdf.alias_nb_pages()
                pdf.add_page()

                pdf.intro(judge_info)
                pdf.table(flight['beers'])

                sheet_type = f'Cellar - {f}' if not descriptions else f

                filename = 'public/flights/{}.pdf'.format(f'Flight {category} - {sheet_type}{location} ')


                pdf.output(filename, 'F')

                filenames[f] = filename

            #self.flight_round_cup_labels(dup_cat, category, f'Flight Number {category} Cup Labels')

        # todo: plan is to return filenames to web page for links
        #return filenames


    def flight_mini_bos_pull_sheets(self, my_flights, descriptions=True):

        unasigned_counter = 1

        for category in my_flights:

            flights = {}
            table_list = []
            filenames = {}

            #print('category', category)

            sql = 'select * from flights where number = "{}" and ' \
                  'fk_competitions = "{}"'.format(category, Competitions().get_active_competition())

            uid = gen_uid()
            result = db.db_command(sql=sql, uid=uid).all(uid)


            flight_cat = []
            flight_sub_cat = []

            # Flight categories

            list_of_categories = []
            location = ''

            # todo: fetch this from DB
            judge_locations = {
                0: 'Unassigned',
                1: 'Triangle',
                2: 'Charlotte',
                3: 'Asheville'
            }
            if result:
                location = judge_locations.get(result[0]['fk_judge_locations'], '')
                location = f' - {location}' if location else ''

                for r in result:
                    #print('flight:', r)
                    # todo: make more generic
                    #list_of_categories.append(f'{r["category_id"]}{r["sub_category_id"]}')
                    list_of_categories.append(f'{r["sub_category_id"]}')

            try:
                tables_list = json.loads(result[0]['tables'])
            except:
                tables_list = []

            # Tables
            #print('tables_list', tables_list)
            """
            if tables_list:

                sql = 'select * from tables where name in ("{}") and fk_competitions = "{}"'.format('","'.join(tables_list), Competitions().get_active_competition())

                uid = gen_uid()
                tables = db.db_command(sql=sql, uid=uid).all(uid)
            
            else:
                # todo: fi - specicif to ncbc 2020 to pre build flight sheets and build mini BOS if needed
                if result[0]['number'] in (27, 13):
                    tables = [None, None]
                else:
                    tables = [None]
            """
            tables = [None]

            # Assigned judges
            #for t in tables:
            #    print(t)

            cup_labels = {}

            for table in tables:

                if table:
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
                        # the `|` are used for line splitting in FlightSheet, need four lines for intro area.
                        'head_judge': '{} {}|{}| | '.format(head_judge['firstname'], head_judge['lastname'], ', '.join(hj_certs)),
                        'second_judge': '{} {}|{}| | '.format(second_judge['firstname'], second_judge['lastname'], ', '.join(sj_certs)),
                        'category': category,
                        'table': table['name'],
                        'category_name': '{} {}'.format(category, Style('NCBC2020').get_category_name(category)),
                        'beers': []
                    }

                else:
                    flights[f'Unassigned {unasigned_counter}'] = {
                        # the `|` are used for line splitting in FlightSheet, need four lines for intro area.
                        'head_judge': '',
                        'second_judge': '',
                        'category': category,
                        'table': '',
                        'category_name': '{} {}'.format(category, Style('NCBC2020').get_category_name(category)),
                        'beers': []
                    }

                    unasigned_counter += 1
                #print(flights[table['name']] )
            category_list = []

            #print('list_of_categories', list_of_categories)
            sql = 'select * from entries ' \
                  '' \
                  'where CONCAT(category, sub_category) in ("{}")  and fk_competitions = "{}" and mini_bos = "1" and inventory = "1" ' \
                  'order by category, sub_category, entry_id'.format('","'.join(list_of_categories), Competitions().get_active_competition())
            uid = gen_uid()
            cat  = db.db_command(sql=sql, uid=uid).all(uid)

            dup_cat = cat.copy()

            categories = {}


            entry = {}
            for c in cat:
                #print(c)
                if Style('NCBC2020').is_specialty(str(c['category']), str(c['sub_category']) ):
                    c['is_specialty'] = 1 if descriptions else 0
                else:
                    c['is_specialty'] = 0

                c['style_name'] = Style('NCBC2020').get_style_name(str(c['category']), str(c['sub_category']))

                if not descriptions:
                    #if c['entry_id'] == 581:
                    #    print(c)
                    c['notes'] = c['comments']  # Get inventory comments for cellar
                else:
                    c['notes'] = ''

                if c['category'] not in categories:
                    categories[c['category']] = []
                categories[c['category']].append(c)
            #print('doing cat')
            while len(cat) > 0 and flights:
                #print('cat', flights)
                for f in flights:
                    if cat:
                        #print(cat)
                        flights[f]['beers'].append(cat.pop(0))

            #for f in flights:
            #    print(flights[f])
            #    for b in flights[f]['beers']:
            #        print(b)
            miniBos_count = 1
            for f in flights:

                flight = flights[f]

                judge_info = {
                    'head_judge': flight['head_judge'],
                    'second_judge': flight['second_judge']
                }

                if len(flights) > 1:
                    mini = f' (mBOS {miniBos_count} of {len(flights)})'
                else:
                    mini = ''

                miniBos_count += 1

                pdf = FlightSheet()

                pdf.flight = f'{f}: Flight: {category} {Style("NCBC2020").get_category_name(category)}: # of Entries: {len(flight["beers"])}{mini}'

                #print(pdf.flight)

                pdf.alias_nb_pages()
                pdf.add_page()

                pdf.intro(judge_info)
                pdf.table(flight['beers'])

                sheet_type = f'Cellar - {f}' if not descriptions else f

                filename = 'public/flights/{}.pdf'.format(f'MB-Flight {category} - {sheet_type}{location} ')


                pdf.output(filename, 'F')

                filenames[f] = filename

            #self.flight_round_cup_labels(dup_cat, category, f'Flight Number {category} Cup Labels')

        # todo: plan is to return filenames to web page for links
        #return filenames



    def bos_flight_pull_sheets(self, descriptions=True):




        category_list = []
        flights = {}


        sql = 'select * from entries ' \
              'where fk_competitions = "{}" and place = "1" ' \
              'order by LPAD(entries.category, 2, "0"), sub_category'.format(Competitions().get_active_competition())
        uid = gen_uid()
        cat  = db.db_command(sql=sql, uid=uid).all(uid)

        dup_cat = cat.copy()

        categories = {}


        entry = {}
        for c in cat:
            if Style('NCBC2020').is_specialty(str(c['category']), str(c['sub_category']) ):
                c['is_specialty'] = 1 if descriptions else 0
            else:
                c['is_specialty'] = 0

            c['style_name'] = Style('NCBC2020').get_style_name(str(c['category']), str(c['sub_category']))
            flight_number = Style('NCBC2020').get_judging_category(f'{c["category"]}{c["sub_category"]}')
            flight_name = Style('NCBC2020').get_category_name(flight_number)
            c['medal'] = f'{flight_number} {flight_name}'

            if not descriptions:
                #if c['entry_id'] == 581:
                #    print(c)
                c['notes'] = c['comments']  # Get inventory comments for cellar
            else:
                c['notes'] = ''

            #print(c)

            if c['category'] not in categories:
                categories[c['category']] = []
            categories[c['category']].append(c)
            #print(c)

            #print(f'{c["entry_id"]},{c["category"]}{c["sub_category"]},{c["style_name"].replace(",",";")}')

            #if int(c['is_specialty']) == 1 or c['category'] == '35':
            #    print(' , ,{}'.format(c['description'].replace('\n', '').replace(',',  ';')))

        #for c in categories:
        #    print(c)

        tables = [None]

        # Assigned judges
        #for t in tables:
        #    print(t)

        cup_labels = {}

        for table in tables:

            if table:
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
                    # the `|` are used for line splitting in FlightSheet, need four lines for intro area.
                    'head_judge': '{} {}|{}| | '.format(head_judge['firstname'], head_judge['lastname'], ', '.join(hj_certs)),
                    'second_judge': '{} {}|{}| | '.format(second_judge['firstname'], second_judge['lastname'], ', '.join(sj_certs)),
                    'category': 'NC Brewers CUP BOS 2020',
                    'table': table['name'],
                    'category_name': '',
                    'beers': []
                }

            else:
                flights['BOS'] = {
                    # the `|` are used for line splitting in FlightSheet, need four lines for intro area.
                    'head_judge': '',
                    'second_judge': '',
                    'category': 'NC Brewers CUP BOS 2020',
                    'table': '',
                    'category_name': '',
                    'beers': []
                }



        cat = sorted(cat, key = lambda x: x['medal'])

        while len(cat) > 0:
            #print('cat', flights)
            if cat:
                #print(cat)
                flights['BOS']['beers'].append(cat.pop(0))

        #for f in flights:
        #    print(flights[f])
        #    for b in flights[f]['beers']:
        #        print(b)

        for f in flights:
            #print(f)

            flight = flights[f]

            judge_info = {
                'head_judge': flight['head_judge'],
                'second_judge': flight['second_judge']
            }

        pdf = FlightSheet()

        sheet_type = 'Judge' if descriptions else 'Cellar'

        pdf.flight = f'{sheet_type} Flight Sheet - NC Brewers Cup BOS 2020'

        #print(pdf.flight)

        pdf.alias_nb_pages()
        pdf.add_page()



        pdf.bos_intro(judge_info)
        pdf.bos_table(flight['beers'])

        if descriptions:
            filename = 'public/flights/bos/BOS Judge Flight Sheets.pdf'
        else:
            filename = 'public/flights/bos/BOS Cellar Flight Sheets.pdf'

        pdf.output(filename, 'F')



        # todo: plan is to return filenames to web page for links
        #return filenames



    def bos_grid_sheets(self):




        category_list = []
        flights = []


        sql = 'select * from entries ' \
              'where fk_competitions = "{}" and place = "1" ' \
              'order by LPAD(entries.category, 2, "0"), sub_category'.format(Competitions().get_active_competition())
        uid = gen_uid()
        cat  = db.db_command(sql=sql, uid=uid).all(uid)

        dup_cat = cat.copy()

        categories = {}


        entry = {}
        for c in cat:
            if Style('NCBC2020').is_specialty(str(c['category']), str(c['sub_category']) ):
                c['is_specialty'] = 1
            else:
                c['is_specialty'] = 0

            c['style_name'] = Style('NCBC2020').get_style_name(str(c['category']), str(c['sub_category']))
            flight_number = Style('NCBC2020').get_judging_category(f'{c["category"]}{c["sub_category"]}')
            flight_name = Style('NCBC2020').get_category_name(flight_number)
            c['medal'] = f'{flight_number} {flight_name}'


            if c['category'] not in categories:
                categories[c['category']] = []
            categories[c['category']].append(c)


        cat = sorted(cat, key = lambda x: x['medal'])

        """
        for c in cat:

            print(c['entry_id'], c['medal'], f'{c["category"]}{c["sub_category"]} {c["style_name"]}')
        """
        
        pdf = FlightSheet()

        pdf.flight = f'NC Brewers Cup BOS 2020'

        #print(pdf.flight)

        pdf.alias_nb_pages()
        pdf.add_page(orientation='Landscape')


        
        pdf.bos_grid(cat)

        filename = 'public/flights/bos/BOS Grid Sheets.pdf'


        pdf.output(filename, 'F')

        





    def flight_round_cup_labels_new(self, entries, flight, filename):

        LABELS_PER_LINE = 9
        LINES_PER_PAGE = 12
        PADDING = 5
        l = PDFLabel('050-circle', font = 'Courier', font_size=13)
        l.add_page()
        labels = Entrys().get_inventory(inventory=False)
        label_count = 0
        category = ''
        print(entries)

        count = 0

        if entries:
            l.add_label("===Flt===")
            l.add_label("==={:03d}===".format(int(flight)))
            label_count += 2

            for e in entries:
                while label_count % LABELS_PER_LINE != 0:
                    l.add_label(' ')
                    label_count += 1
                # print('add space', label_count)
                print('e', e)
                l.add_label("===tbl===")
                l.add_label("==={:03d}===".format(int(e.split(' ')[-1])))
                label_count += 2

                while label_count % LABELS_PER_LINE != 0:
                    l.add_label(' ')
                    label_count += 1

                for i in sorted(entries[e], key=lambda r: int(r['category'])):
                    print(i)
                    #if category != i['category']:
                    category = i['category']
                    #print('cat change')
                    #print(f"print cat{i['category']}", label_count)


                    entry_id = int(i['entry_id'])
                    l.add_label('  {:03d}'.format(entry_id))
                    l.add_label('  {:03d}'.format(entry_id))
                    l.add_label('  {:03d}'.format(entry_id))
                    l.add_label('  {:03d}'.format(entry_id))
                    label_count += 4

                    if count % 2 == 0:
                        l.add_label(' ')
                        label_count += 1

                    count += 1
                    #print('print entry id', i['entry_id'], label_count)
                l.output(f'public/flights/{filename}.pdf')




    def print_checkin(self, session):

        sql = 'select name from sessions where pkid = "{}"'.format(session)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        session_name = result['name']

        checkin = [[session_name, ''], ['','*Please initial you name or add it to the list if not listed'], ['', '']]


        sql = 'select firstname, lastname, fk_sessions_list from volunteers where fk_competitions = "{}" order by lastname'.format(Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        #print(result)
        for r in result:

            sessions = r['fk_sessions_list'].split(',')

            if str(session) in sessions:
                checkin.append(['', f'{r["lastname"]}, {r["firstname"]}'])

        #print(checkin)
        with open(f'public/flights/{session_name} check in sheet.csv', 'w') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerows(checkin)
        writeFile.close()


class FlightSheet(FPDF, HTMLMixin):


    def header(self):
        """
        Header on each page
        """

        #print('header', self.flight)
        # Effective page width, or just epw
        epw = self.w - 2 * self.l_margin

        # insert my logo
        #self.image("logo.png", x=10, y=8, w=23)
        # position logo on the right
        #self.cell(w=80)

        # set the font for the header, B=Bold
        #self.set_font("Arial", style="B", size=15)
        self.set_font("Arial", style="B", size=12)
        # page title
        #self.image("files/ncbg-logo.png", x=12, y=12, w=31)
        #self.image("files/NCBClogo.jpg", x=epw-5, y=9, w=14)
        #self.cell(epw, 16, "        Invoice for Donation to the NC Brewers Cup 2019", border=1, ln=0, align="C")
        self.cell(epw, 16, self.flight, border=1, ln=0, align="C")
        # insert a line break of 20 pixels
        self.set_font("Arial", style="B", size=15)

        self.ln(5)

    def footer(self):
        """
        Footer on each page
        """
        # position footer at 15mm from the bottom
        self.set_y(-15)

        # set the font, I=italic
        self.set_font("Arial", style="I", size=8)

        # display the page number and center it
        pageNum = "Page %s/{nb}" % self.page_no()
        self.cell(0, 10, pageNum, align="C")

    def intro(self, judges):

        #ncbg = ['NC Brewers Guild', 'PO Box 27921', 'Raleigh, NC 27611']

        # Effective page width, or just epw
        epw = self.w - 2.5 * self.l_margin

        # Set column width to 1/4 of effective page width to distribute content
        # evenly across table and page
        col_width = epw / 2

        # Since we do not need to draw lines anymore, there is no need to separate
        # headers from data matrix.

        # Text height is the same as current font size
        th = self.font_size

        self.ln(3 * th)

        self.set_font("Arial", size=12)

        self.cell(col_width, 2 * th, 'Head Judge:', border='LTB', align='L')
        self.cell(5, 2 * th, ' ', border='LR')
        self.cell(col_width, 2 * th, 'Judge:', border='RTB', align='L')
        self.ln(2 * th)


        index = 0
        line_ht = 1
        align = 'L'

        #add blank line
        self.cell(col_width, line_ht * th, ' ', border='L', align=align)
        self.cell(5, line_ht * th, ' ', border='LR')
        self.cell(col_width, line_ht * th, ' ', border='R', align=align)
        self.ln(line_ht * th)

        hj = judges['head_judge'].split('|')
        sj = judges['second_judge'].split('|')

        if len(hj) != 4:
            hj=['','','']
        if len(sj) != 4:
            sj=['','','']

        for j in range(0, 3):
            self.cell(col_width, line_ht * th, '  {}'.format(hj[j]), border='L', align=align)
            self.cell(5, line_ht * th, ' ', border='LR')
            self.cell(col_width, line_ht * th, '  {}'.format(sj[j]), border='R', align=align)

            index += 1
            self.ln(line_ht * th)

        self.cell(col_width, line_ht * th, '', border='BL')
        self.cell(5, line_ht * th, ' ', border='LR')
        self.cell(col_width, line_ht * th, '', border='BR')

        self.line(10, 75, epw + 15, 75)
        self.ln(20)

    def bos_intro(self, judges):

        #ncbg = ['NC Brewers Guild', 'PO Box 27921', 'Raleigh, NC 27611']

        # Effective page width, or just epw
        epw = self.w - 2.5 * self.l_margin

        # Set column width to 1/4 of effective page width to distribute content
        # evenly across table and page
        col_width = epw / 2

        # Since we do not need to draw lines anymore, there is no need to separate
        # headers from data matrix.

        # Text height is the same as current font size
        th = self.font_size

        self.ln(3 * th)

        self.set_font("Arial", size=12)

        self.cell(col_width, 2 * th, '', border='LTB', align='L')
        self.cell(5, 2 * th, ' ', border='LR')
        self.cell(col_width, 2 * th, '', border='RTB', align='L')
        self.ln(2 * th)


        index = 0
        line_ht = 1
        align = 'L'

        #add blank line
        self.cell(col_width, line_ht * th, ' ', border='L', align=align)
        self.cell(5, line_ht * th, ' ', border='LR')
        self.cell(col_width, line_ht * th, ' ', border='R', align=align)
        self.ln(line_ht * th)

        hj = judges['head_judge'].split('|')
        sj = judges['second_judge'].split('|')

        if len(hj) != 4:
            hj=['','','']
        if len(sj) != 4:
            sj=['','','']

        for j in range(0, 3):
            self.cell(col_width, line_ht * th, '  {}'.format(hj[j]), border='L', align=align)
            self.cell(5, line_ht * th, ' ', border='LR')
            self.cell(col_width, line_ht * th, '  {}'.format(sj[j]), border='R', align=align)

            index += 1
            self.ln(line_ht * th)

        self.cell(col_width, line_ht * th, '', border='BL')
        self.cell(5, line_ht * th, ' ', border='LR')
        self.cell(col_width, line_ht * th, '', border='BR')

        self.line(10, 75, epw + 15, 75)
        self.ln(20)


    def table(self, beers):

        LINES_PER_PAGE = 25
        # Remember to always put one of these at least once.
        self.set_font('Times', '', 10.0)

        # Effective page width, or just epw
        epw = self.w - 2 * self.l_margin

        # Set column width to 1/4 of effective page width to distribute content
        # evenly across table and page
        col_width = epw / 2

        # Since we do not need to draw lines anymore, there is no need to separate
        # headers from data matrix.



        # Text height is the same as current font size
        th = self.font_size


        # Line break equivalent to 4 lines
        #self.ln(4 * th)


        first_label = True
        label_count = 0

        image_y = 100

        self.set_font('Times', 'B', 14.0)


        #col_widths = [20,20,60,60,30]
        col_widths = [5, 15,20,20,40,90]

        self.cell(col_widths[0], 2 * th, '#', border='LRTB', align='C')
        self.cell(col_widths[1], 2 * th, 'Judged', border='RTB', align='C')
        self.cell(col_widths[2], 2 * th, 'Entry ID', border='RTB', align='C')
        self.cell(col_widths[3], 2 * th, 'Category', border='RTB', align='C')
        self.cell(col_widths[4], 2 * th, 'Style', border='RTB', align='C')
        self.cell(col_widths[5], 2 * th, 'Notes', border='RTB', align='C')
        self.ln(2 * th)

        self.set_font('Times', '', 10.0)

        printed_lines = 0
        count = 0
        first_page = True

        # Here we add more padding by passing 2*th as height
        for beer in beers:
            # Get list of description lines.
            if beer['is_specialty'] == 1 or beer['category'] == '35':
                # https://pymotw.com/2/textwrap/
                desc = dedent(beer['description']).strip().replace(u"\u2019", "")

                if len(desc) == 0:
                    desc = '** No description provide by brewer  **'
                desc = fill(desc, width=110)

                desc = desc.split('\n')
            else:
                desc = []
            count += 1
            # Todo: check to see if descriotion plus category will fit on the page
            # if not print blank rows and start on new page

            #print('num lines to print', len(desc) + 1, printed_lines)
            #print('is there room', (LINES_PER_PAGE - (printed_lines % LINES_PER_PAGE)) > (len(desc) + 1))

            # If descript too long to fit on current page go to next
            if not (LINES_PER_PAGE - (printed_lines % LINES_PER_PAGE)) > (len(desc) + 1):

                # Add blank lines to end of page
                while printed_lines % LINES_PER_PAGE != 0:
                    #print('while')
                    self.cell(col_widths[0], 2 * th, '', border='', align='L')
                    self.cell(col_widths[1], 2 * th, '', border='', align='L')
                    self.cell(col_widths[2], 2 * th, '', border='', align='L')
                    self.cell(col_widths[3], 2 * th, '', border='', align='L')
                    self.cell(col_widths[4], 2 * th, '', border='', align='L')
                    self.cell(col_widths[5], 2 * th, '', border='', align='L')
                    self.ln(2 * th)
                    printed_lines += 1

                #if first_page and LINES_PER_PAGE == printed_lines:
                #    first_page = False
                #    LINES_PER_PAGE = LINES_PER_PAGE + 5
                #    print('incrementing lines per page', LINES_PER_PAGE)

                # Skip 4 lines at the top.  If not first page then skip 8 more lines to include bottom of previous page
                for i in range(0,4 if first_page else 12):
                    first_page = False
                    self.cell(col_widths[0], 2 * th, '', border='', align='L')
                    self.cell(col_widths[1], 2 * th, '', border='', align='L')
                    self.cell(col_widths[2], 2 * th, '', border='', align='L')
                    self.cell(col_widths[3], 2 * th, '', border='', align='L')
                    self.cell(col_widths[4], 2 * th, '', border='', align='L')
                    self.cell(col_widths[5], 2 * th, '', border='', align='L')
                    self.ln(2 * th)

            self.cell(col_widths[0], 2 * th, str(count) , border='LRTB', align='L')
            self.cell(col_widths[1], 2 * th, '', border='LRTB', align='L')
            self.cell(col_widths[2], 2 * th, str(beer['entry_id']), border='RTB', align='L')
            self.cell(col_widths[3], 2 * th, f"{beer['category']}{beer['sub_category']}", border='RTB', align='L')
            self.cell(col_widths[4], 2 * th, beer['style_name'], border='RTB', align='L')
            self.cell(col_widths[5], 2 * th, beer['notes'], border='RTB', align='L')
            self.ln(2 * th)

            printed_lines += 1

            """
            Looks like this can be removed
            if printed_lines % LINES_PER_PAGE == 0:
                for i in range(0,4):
                    self.cell(col_widths[0], 2 * th, '', border='', align='L')
                    self.cell(col_widths[1], 2 * th, '', border='', align='L')
                    self.cell(col_widths[2], 2 * th, '', border='', align='L')
                    self.cell(col_widths[3], 2 * th, '', border='', align='L')
                    self.cell(col_widths[4], 2 * th, '', border='', align='L')
                    self.cell(col_widths[5], 2 * th, '', border='', align='L')
                    self.ln(2 * th)
            """

            # Print each description line
            desc_line = 1
            for d in desc:
                self.cell(col_widths[0], 2 * th, '', border='LRTB', align='L')
                self.cell(col_widths[1], 2 * th, '', border='LRTB', align='L')

                # Set the cell border ro remove grid lines
                if desc_line == 1 and desc_line == len(desc):
                    border = 'RTB'
                elif desc_line == 1:
                    border = 'RT'
                elif desc_line == len(desc):
                    border = 'RB'
                else:
                    border = 'R'
                self.cell(190 - (col_widths[0] + col_widths[1]), 2 * th, d, border=border, align='L')
                self.ln(2 * th)
                printed_lines += 1
                desc_line += 1

                """
                Looks like this can be removed
                if printed_lines % LINES_PER_PAGE == 0:
                    for i in range(0,4):
                        self.cell(col_widths[0], 2 * th, '', border='', align='L')
                        self.cell(col_widths[1], 2 * th, '', border='', align='L')
                        self.cell(col_widths[2], 2 * th, '', border='', align='L')
                        self.cell(col_widths[3], 2 * th, '', border='', align='L')
                        self.cell(col_widths[4], 2 * th, '', border='', align='L')
                        self.cell(col_widths[5], 2 * th, '', border='', align='L')
                        self.ln(2 * th)
                """


        """
        Can remove - tries to pad page with blank lines

        # Todo: calc total lines differently to fill the last page with blank lines
        # todo: fix this first- table 4 has a bug where a blank pag eis generated.
        #total_lines = 25 - len(beers)

        print('printer lines', printed_lines)
        if printed_lines < LINES_PER_PAGE:
            total_lines = LINES_PER_PAGE - (printed_lines % LINES_PER_PAGE)
        elif printed_lines == LINES_PER_PAGE:
            total_lines = 0
        else:
            total_lines = (printed_lines % LINES_PER_PAGE)

        print('total_lines', total_lines)
        for i in range(0, total_lines):
            self.cell(col_widths[0], 2 * th, ' ', border='LRB', align='L')
            self.cell(col_widths[1], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[2], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[3], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[4], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[5], 2 * th, ' ', border='RTB', align='L')
            self.ln(2 * th)
        """

        """
        Total lines - can remove
        self.set_font('Times', 'B', 10.0)
        self.cell(col_widths[0], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[1], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[2], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[3], 2 * th, 'Total:', border='LRTB', align='R')
        self.cell(col_widths[4], 2 * th, '$0.00', border='RTB', align='L')
        """

    def bos_table(self, beers):

        LINES_PER_PAGE = 25
        # Remember to always put one of these at least once.
        self.set_font('Times', '', 10.0)

        # Effective page width, or just epw
        epw = self.w - 2 * self.l_margin

        # Set column width to 1/4 of effective page width to distribute content
        # evenly across table and page
        col_width = epw / 2

        # Since we do not need to draw lines anymore, there is no need to separate
        # headers from data matrix.



        # Text height is the same as current font size
        th = self.font_size


        # Line break equivalent to 4 lines
        #self.ln(4 * th)


        first_label = True
        label_count = 0

        image_y = 100

        self.set_font('Times', 'B', 14.0)


        #col_widths = [20,20,60,60,30]
        col_widths = [5, 15,20,50,50,50]

        self.cell(col_widths[0], 2 * th, '#', border='LRTB', align='C')
        self.cell(col_widths[1], 2 * th, 'Judged', border='RTB', align='C')
        self.cell(col_widths[2], 2 * th, 'Entry ID', border='RTB', align='C')
        self.cell(col_widths[3], 2 * th, 'Medal Category', border='RTB', align='C')
        self.cell(col_widths[4], 2 * th, 'BJCP Style', border='RTB', align='C')
        self.cell(col_widths[5], 2 * th, 'Notes', border='RTB', align='C')
        self.ln(2 * th)

        self.set_font('Times', '', 10.0)

        printed_lines = 0
        count = 0
        first_page = True

        # Here we add more padding by passing 2*th as height
        for beer in beers:
            # Get list of description lines.
            if beer['is_specialty'] == 1:
                # https://pymotw.com/2/textwrap/
                desc = dedent(beer['description']).strip().replace(u"\u2019", "")

                if len(desc) == 0:
                    desc = '** No description provide by brewer  **'
                desc = fill(desc, width=110)

                desc = desc.split('\n')
            else:
                desc = []
            count += 1
            # Todo: check to see if descriotion plus category will fit on the page
            # if not print blank rows and start on new page

            #print('num lines to print', len(desc) + 1, printed_lines)
            #print('is there room', (LINES_PER_PAGE - (printed_lines % LINES_PER_PAGE)) > (len(desc) + 1))

            # If descript too long to fit on current page go to next
            if not (LINES_PER_PAGE - (printed_lines % LINES_PER_PAGE)) > (len(desc) + 1):

                # Add blank lines to end of page
                while printed_lines % LINES_PER_PAGE != 0:
                    #print('while')
                    self.cell(col_widths[0], 2 * th, '', border='', align='L')
                    self.cell(col_widths[1], 2 * th, '', border='', align='L')
                    self.cell(col_widths[2], 2 * th, '', border='', align='L')
                    self.cell(col_widths[3], 2 * th, '', border='', align='L')
                    self.cell(col_widths[4], 2 * th, '', border='', align='L')
                    self.cell(col_widths[5], 2 * th, '', border='', align='L')
                    self.ln(2 * th)
                    printed_lines += 1

                #if first_page and LINES_PER_PAGE == printed_lines:
                #    first_page = False
                #    LINES_PER_PAGE = LINES_PER_PAGE + 5
                #    print('incrementing lines per page', LINES_PER_PAGE)

                # Skip 4 lines at the top.  If not first page then skip 8 more lines to include bottom of previous page
                for i in range(0,4 if first_page else 12):
                    first_page = False
                    self.cell(col_widths[0], 2 * th, '', border='', align='L')
                    self.cell(col_widths[1], 2 * th, '', border='', align='L')
                    self.cell(col_widths[2], 2 * th, '', border='', align='L')
                    self.cell(col_widths[3], 2 * th, '', border='', align='L')
                    self.cell(col_widths[4], 2 * th, '', border='', align='L')
                    self.cell(col_widths[5], 2 * th, '', border='', align='L')
                    self.ln(2 * th)

            self.cell(col_widths[0], 2 * th, str(count) , border='LRTB', align='L')
            self.cell(col_widths[1], 2 * th, '', border='LRTB', align='L')
            self.cell(col_widths[2], 2 * th, str(beer['entry_id']), border='RTB', align='L')
            self.cell(col_widths[3], 2 * th, beer['medal'], border='RTB', align='L')
            self.cell(col_widths[4], 2 * th, f"{beer['category']}{beer['sub_category']} {beer['style_name']}", border='RTB', align='L')
            self.cell(col_widths[5], 2 * th, beer['notes'], border='RTB', align='L')
            self.ln(2 * th)

            printed_lines += 1

            """
            Looks like this can be removed
            if printed_lines % LINES_PER_PAGE == 0:
                for i in range(0,4):
                    self.cell(col_widths[0], 2 * th, '', border='', align='L')
                    self.cell(col_widths[1], 2 * th, '', border='', align='L')
                    self.cell(col_widths[2], 2 * th, '', border='', align='L')
                    self.cell(col_widths[3], 2 * th, '', border='', align='L')
                    self.cell(col_widths[4], 2 * th, '', border='', align='L')
                    self.cell(col_widths[5], 2 * th, '', border='', align='L')
                    self.ln(2 * th)
            """

            # Print each description line
            desc_line = 1
            for d in desc:
                self.cell(col_widths[0], 2 * th, '', border='LRTB', align='L')
                self.cell(col_widths[1], 2 * th, '', border='LRTB', align='L')

                # Set the cell border ro remove grid lines
                if desc_line == 1 and desc_line == len(desc):
                    border = 'RTB'
                elif desc_line == 1:
                    border = 'RT'
                elif desc_line == len(desc):
                    border = 'RB'
                else:
                    border = 'R'
                self.cell(190 - (col_widths[0] + col_widths[1]), 2 * th, d, border=border, align='L')
                self.ln(2 * th)
                printed_lines += 1
                desc_line += 1

                """
                Looks like this can be removed
                if printed_lines % LINES_PER_PAGE == 0:
                    for i in range(0,4):
                        self.cell(col_widths[0], 2 * th, '', border='', align='L')
                        self.cell(col_widths[1], 2 * th, '', border='', align='L')
                        self.cell(col_widths[2], 2 * th, '', border='', align='L')
                        self.cell(col_widths[3], 2 * th, '', border='', align='L')
                        self.cell(col_widths[4], 2 * th, '', border='', align='L')
                        self.cell(col_widths[5], 2 * th, '', border='', align='L')
                        self.ln(2 * th)
                """


        """
        Can remove - tries to pad page with blank lines

        # Todo: calc total lines differently to fill the last page with blank lines
        # todo: fix this first- table 4 has a bug where a blank pag eis generated.
        #total_lines = 25 - len(beers)

        print('printer lines', printed_lines)
        if printed_lines < LINES_PER_PAGE:
            total_lines = LINES_PER_PAGE - (printed_lines % LINES_PER_PAGE)
        elif printed_lines == LINES_PER_PAGE:
            total_lines = 0
        else:
            total_lines = (printed_lines % LINES_PER_PAGE)

        print('total_lines', total_lines)
        for i in range(0, total_lines):
            self.cell(col_widths[0], 2 * th, ' ', border='LRB', align='L')
            self.cell(col_widths[1], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[2], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[3], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[4], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[5], 2 * th, ' ', border='RTB', align='L')
            self.ln(2 * th)
        """

        """
        Total lines - can remove
        self.set_font('Times', 'B', 10.0)
        self.cell(col_widths[0], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[1], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[2], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[3], 2 * th, 'Total:', border='LRTB', align='R')
        self.cell(col_widths[4], 2 * th, '$0.00', border='RTB', align='L')
        """

    def build_grids(self, l1, l2, l3, col_width, col_height, th):
        self.set_font('Times', 'B', 10.0)
        for i in l1:
            self.cell(col_width, col_height, str(i), border='LRT')
        self.ln(2 * th)
        for z in range (0, 3):
            for i in l1:
                self.cell(col_width, col_height, '', border='LR')
            self.ln(2 * th)
        self.set_font('Times', 'B', 12.0)
        for i in l1:
            self.cell(col_width, col_height, f'Entry ID: {i}', border='LR', align='C')
        self.ln(2 * th)
        for i in l2:
            self.cell(col_width, col_height, f'Medal Category: {i}', border='LR', align='C')
        self.ln(2 * th)
        for i in l3:
            self.cell(col_width, col_height, f'BJCP Style: {i}', border='LR', align='C')
        self.ln(2 * th)
        for z in range (0, 3):
            for i in l1:
                self.cell(col_width, col_height, '', border='LR')
            self.ln(2 * th)
        for i in l1:
            self.cell(col_width, col_height, '', border='LRB')
        self.ln(2 * th)


    def bos_grid(self, beers):

        LINES_PER_PAGE = 25
        # Remember to always put one of these at least once.
        self.set_font('Times', '', 10.0)

        # Effective page width, or just epw
        epw = self.w - 2 * self.l_margin

        # Set column width to 1/4 of effective page width to distribute content
        # evenly across table and page
        col_width = epw / 2

        # Since we do not need to draw lines anymore, there is no need to separate
        # headers from data matrix.



        # Text height is the same as current font size
        th = self.font_size


        # Line break equivalent to 4 lines
        #self.ln(4 * th)


        first_label = True
        label_count = 0

        image_y = 100

        self.set_font('Times', 'B', 14.0)

        """
        #col_widths = [20,20,60,60,30]
        col_widths = [5, 15,20,50,50,50]

        self.cell(col_widths[0], 2 * th, '#', border='LRTB', align='C')
        self.cell(col_widths[1], 2 * th, 'Judged', border='RTB', align='C')
        self.cell(col_widths[2], 2 * th, 'Entry ID', border='RTB', align='C')
        self.cell(col_widths[3], 2 * th, 'Medal Category', border='RTB', align='C')
        self.cell(col_widths[4], 2 * th, 'BJCP Style', border='RTB', align='C')
        self.cell(col_widths[5], 2 * th, 'Notes', border='RTB', align='C')
        self.ln(2 * th)
        """

        self.set_font('Times', '', 10.0)

        count = 0
        first_page = True
        col_width =  epw / 3  # 3 columns per line
        col_height = th * 2
        cell_height = th * 22  # Todo: how to calc col height

        
        cell_lines = defaultdict(list)

        # Build cell data structure
        for beer in beers:

            cell_lines[count].append(beer['entry_id'])
            count += 1
            cell_lines[count].append(beer['medal'])
            count += 1
            cell_lines[count].append(f"{beer['category']}{beer['sub_category']} {beer['style_name']}")
            
            count += 1

            if count % 3 == 0:
                count -= 3

        #for line in sorted(cell_lines):
        #    print(line, cell_lines[line])

        count = 0
        row_count = -1
        l1 = []
        l2 = []
        l3 = []
        self.ln(4 * th)

        while cell_lines[0]:

            if count > 0 and count % 3 == 0:
                if row_count > 2 and row_count % 2 == 0:
                    #print('new page')
                    self.add_page(orientation='Landscape')
                    self.ln(4 * th)
                """
                print(l1)
                print(l2)
                print(l3)
                """

                self.build_grids(l1, l2, l3, col_width, col_height, th)
                l1 = []
                l2 = []
                l3 = []

            
            if cell_lines[0]:
                l1.append(cell_lines[0].pop(0))
                l2.append(cell_lines[1].pop(0))
                l3.append(cell_lines[2].pop(0))

                row_count += 1



            count += 1

        if l1:
            #print('new page')
            self.add_page(orientation='Landscape')
            self.ln(4 * th)
            self.build_grids(l1, l2, l3, col_width, col_height, th)
           

            







            """
            entry_string = f"Entry ID: {beer['entry_id']}\nMedal Category: {beer['medal']}\nBJCP Category: {beer['category']}{beer['sub_category']} {beer['style_name']}"
            if count > 0 and count % 3 == 0:
                if count % 6 == 0:   
                    print('next page')
                    self.add_page(orientation='Landscape')
                    #self.ln(6 * col_height)
                    self.ln(4 * th)
                else:
                    print('next line', printed_lines)
                    self.ln(col_height)
            self.cell(col_width, col_height, self.multi_cell(10,th,entry_string), border='LRTB')
            count += 1
            """





def generate_flight_sheets():

    sql = 'select number from flights where fk_judge_locations = "3" and fk_competitions = "5"'
    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)

    flights = list(set([int(x['number']) for x in result]))


    Reports().flight_pull_sheets(flights)
    Reports().flight_pull_sheets(flights, descriptions=False)

def generate_mini_bos_flight_sheets(flight):

    sql = f'select number from flights where fk_judge_locations = "3" and number="{flight}" and fk_competitions = "5"'
    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)

    flights = list(set([int(x['number']) for x in result]))


    Reports().flight_mini_bos_pull_sheets(flights)
    Reports().flight_mini_bos_pull_sheets(flights, descriptions=False)


def bos_round_cup_labels():

    Reports().print_round_bos_cup_labels()

def bos_placemats():

    Reports().bos_grid_sheets()

def bos_flight_sheets(descriptions=True):

    Reports().bos_flight_pull_sheets(descriptions=False)
    Reports().bos_flight_pull_sheets()





if __name__ == '__main__':

    #Reports().print_round_bottle_labels(6)
    #Reports().print_round_cup_labels()
    #Reports().print_round_bos_cup_labels()
    #Reports().bos_grid_sheets()

    #generate_flight_sheets()
    #Reports().master_flight_list()

    #flight = 1
    #generate_mini_bos_flight_sheets(flight)


    #Reports().table_assignments()

    #session = 100
    #Reports().print_checkin(session)


    #flights = [17, 13, 29, 11]
    #flights = [19,2,26,3]
    #flights = [26]
    # Sat Pm extra
    #flights = [4, 1]
    #flights = [12]
    #flights = [7]
    #flights = [20]
    #flights = [6]
    #flights = [10]
    #flights = [8]
    #flights = [5]

    #flights = [15, 16, 22, 25, 28, 31]
    #flights = [14, 18, 21, 24, 30, 27]
    #flights = [18, 21, 16, 31, 22]

    #result = Reports().flight_pull_sheets(flights)
    #print(result)

    #Reports().bos_flight_pull_sheets()
    #Reports().bos_flight_pull_sheets(descriptions=False)
    """
    for r in result:
        #print(r)

        flight = result[r]
        print(flight['head_judge'])
        print(flight['second_judge'])

        for beer in flight['beers']:
            #print('  ', beer)

            print(f'{beer["entry_id"]} {beer["category"]}{beer["sub_category"]} - {beer["style_name"]}')

            if beer['is_specialty'] == 1:
                print(f'  {beer["description"]}')
    """
    pass