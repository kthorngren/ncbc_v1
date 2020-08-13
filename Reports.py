import json
from textwrap import wrap, dedent, fill
import csv
import re

from Tools import Tools
from Competitions import DATABASE
from Competitions import Competitions
from Entrys import Entrys
from Styles import Style


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

        LABELS_PER_LINE = 9
        LINES_PER_PAGE = 12
        PADDING = 5
        l = PDFLabel('050-circle', font = 'Courier', font_size=13)
        l.add_page()
        labels = Entrys().get_inventory(inventory=False)
        label_count = 0
        category = ''
        for i in sorted(labels, key=lambda r: int(r['category'])):
            print(i['category'])
            if category != i['category']:
                category = i['category']
                print('cat change')
                while label_count % (LABELS_PER_LINE * LINES_PER_PAGE) != 0:
                    l.add_label(' ')
                    label_count += 1
                    print('space', label_count)
                l.add_label("===Cat===")
                l.add_label("==={:03d}===".format(int(i['category'])))
                label_count += 2
                print(f"print cat{i['category']}", label_count)
                while label_count % LABELS_PER_LINE != 0:
                    l.add_label(' ')
                    label_count += 1
                    print('add space', label_count)


            entry_id = int(i['entry_id'])
            l.add_label('  {:03d}'.format(entry_id))
            l.add_label('  {:03d}'.format(entry_id))
            label_count += 2
            print('print entry id', i['entry_id'], label_count)
        l.output('public/reports/cup_labels.pdf')


    def print_round_bos_cup_labels(self):

        LABELS_PER_LINE = 11
        PADDING = 5

        sql = 'select entry_id, category, sub_category from entries where place = "1" order by LPAD(entries.category, 2, "0"), sub_category'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        print(result)



        l = PDFLabel('050-circle', font = 'Courier', font_size=13)
        l.add_page()
        label_count = 0
        category = ''
        for r in result:
            #if r['entry_id'] == 214:
            l.add_label("===Cat===")
            l.add_label("==={:03d}===".format(int(r['category'])))

            for x in range(0, 7):
                l.add_label(' ')

            for x in range(0, 9):
                #l.add_label('  {:03d}{}{}'.format(r['entry_id'],int(r['category']), r['sub_category']))
                l.add_label('  {:03d}'.format(r['entry_id']))

        l.output('public/reports/bos_cup_labels.pdf')

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


    def flight_pull_sheets(self, my_flights):


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
            for r in result:
                print(r)
                list_of_categories.append(f'{r["category_id"]}{r["sub_category_id"]}')



            try:
                tables_list = json.loads(result[0]['tables'])
            except:
                tables_list = []

            # Tables
            print(tables_list)



            sql = 'select * from tables where name in ("{}") and fk_competitions = "{}"'.format('","'.join(tables_list), Competitions().get_active_competition())


            uid = gen_uid()
            tables = db.db_command(sql=sql, uid=uid).all(uid)

            # Assigned judges
            #for t in tables:
            #    print(t)

            cup_labels = {}

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
                    # the `|` are used for line splitting in FlightSheet, need four lines for intro area.
                    'head_judge': '{} {}|{}| | '.format(head_judge['firstname'], head_judge['lastname'], ', '.join(hj_certs)),
                    'second_judge': '{} {}|{}| | '.format(second_judge['firstname'], second_judge['lastname'], ', '.join(sj_certs)),
                    'category': category,
                    'table': table['name'],
                    'category_name': '{} {}'.format(category, Style('BJCP2015').get_category_name(category)),
                    'beers': []
                }

            category_list = []


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
                if Style('BJCP2015').is_specialty(str(c['category']), str(c['sub_category']) ):
                    c['is_specialty'] = 1
                else:
                    c['is_specialty'] = 0

                c['style_name'] = Style('BJCP2015').get_style_name(str(c['category']), str(c['sub_category']))



                if c['category'] not in categories:
                    categories[c['category']] = []
                categories[c['category']].append(c)
            print('doing cat')
            while len(cat) > 0 and flights:
                #print('cat', flights)
                for f in flights:
                    if cat:
                        print(cat)
                        flights[f]['beers'].append(cat.pop(0))

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

                pdf.flight = f'{f}: Flight Number: {category}: # of Entries: {len(flight["beers"])}'

                #print(pdf.flight)

                pdf.alias_nb_pages()
                pdf.add_page()

                pdf.intro(judge_info)
                pdf.table(flight['beers'])

                filename = 'public/flights/{}.pdf'.format(f'Flight: {category} {f} ')


                pdf.output(filename, 'F')

                filenames[f] = filename

            self.flight_round_cup_labels(dup_cat, category, f'Flight Number {category} Cup Labels')

        # todo: plan is to return filenames to web page for links
        #return filenames


    def bos_flight_pull_sheets(self):




        category_list = []


        sql = 'select * from entries ' \
              'where fk_competitions = "{}" and place = "1" ' \
              'order by LPAD(entries.category, 2, "0"), sub_category'.format(Competitions().get_active_competition())
        uid = gen_uid()
        cat  = db.db_command(sql=sql, uid=uid).all(uid)

        dup_cat = cat.copy()

        categories = {}


        entry = {}
        for c in cat:
            if Style('BJCP2015').is_specialty(str(c['category']), str(c['sub_category']) ):
                c['is_specialty'] = 1
            else:
                c['is_specialty'] = 0

            c['style_name'] = Style('BJCP2015').get_style_name(str(c['category']), str(c['sub_category']))



            if c['category'] not in categories:
                categories[c['category']] = []
            categories[c['category']].append(c)
            #print(c)

            print(f'{c["entry_id"]},{c["category"]}{c["sub_category"]},{c["style_name"].replace(",",";")}')

            if int(c['is_specialty']) == 1 or c['category'] == '35':
                print(' , ,{}'.format(c['description'].replace('\n', '').replace(',',  ';')))

        #for c in categories:
        #    print(c)

        return


        while len(cat) > 0:
            #print('cat', flights)
            if cat:
                print(cat)
                flights[f]['beers'].append(cat.pop(0))

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

        pdf.flight = f'NC Brewers Cup BOS 2019'

        #print(pdf.flight)

        pdf.alias_nb_pages()
        pdf.add_page()



        #pdf.intro(judge_info)
        pdf.table(flight['beers'])

        filename = 'public/flights/BOS Flights.pdf'


        pdf.output(filename, 'F')



        # todo: plan is to return filenames to web page for links
        #return filenames





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
        self.set_font("Arial", style="B", size=15)
        # page title
        #self.image("files/ncbg-logo.png", x=12, y=12, w=31)
        #self.image("files/NCBClogo.jpg", x=epw-5, y=9, w=14)
        #self.cell(epw, 16, "        Invoice for Donation to the NC Brewers Cup 2019", border=1, ln=0, align="C")
        self.cell(epw, 16, self.flight, border=1, ln=0, align="C")
        # insert a line break of 20 pixels

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
        hj=['','','']
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
            self.cell(col_widths[5], 2 * th, '', border='RTB', align='L')
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



if __name__ == '__main__':

    #Reports().print_round_bottle_labels(6)
    Reports().print_round_cup_labels()
    #Reports().print_round_bos_cup_labels()


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