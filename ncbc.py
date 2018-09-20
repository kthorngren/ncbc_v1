import re
import json
import sys
import datetime
from csv import reader, QUOTE_NONE, QUOTE_ALL
from time import sleep


import qrcode
from qrcode.image.pure import PymagingImage

import requests
from fpdf import FPDF, HTMLMixin

from Styles import Style
from Email import Email

from Import import Import
from Volunteers import Volunteers

from Competitions import DATABASE

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
logger = logging.getLogger(os.path.basename(__file__).split('.')[0] if __name__ == '__main__' else __name__.split('.')[1])
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

db = Database(local_host['host'], local_host['user'], local_host['password'], 'ncbc_data')


class BottleLabelFPDF(FPDF, HTMLMixin):

    def header(self):
        """
        Header on each page
        """

        # Effective page width, or just epw
        epw = self.w - 2 * self.l_margin




        # insert my logo
        #self.image("logo.png", x=10, y=8, w=23)
        # position logo on the right
        #self.cell(w=80)

        # set the font for the header, B=Bold
        self.set_font("Arial", style="B", size=15)
        # page title
        self.cell(epw, 10, "NC Brewers Cup 2018 Entry Labels", border=1, ln=0, align="C")
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

    def intro(self, first_name, homebrew=False):

        # Effective page width, or just epw
        epw = self.w - 2 * self.l_margin

        self.set_font("Arial", size=12)

        hello = 'Hello {},'.format(first_name)
        text = ['Welcome to the NC Brewers Cup!  Your entry labels are contained in this document.  ',
               'Please cut them out and attach them to each entry as described below.  Please make sure to ',
               'place them on the correct entries.  The beers will be judged based on the entry label attached. ',

                ]
        if homebrew:
            text2 = ['Last year we had over 700 entries, thats over 1400 entries to handle.  ',
                     'Placing the labels on the entries correctly will help us during ',
                   'inventory, staging and judging the entries.  The labels need to be ',
                   'oriented so they are readable.  Please use only rubberbands to attach ',
                    'to the entries.  Placing the labels in ziplock sandwich bags is ',
                    'highly recommended.  Use the picture to the right as an example.'
                    ]
        else:

            text2 = ['Last year we had over 700 entries, thats over 1400 entries to handle.  ',
                     'Placing the labels on the entries correctly will help us during ',
                   'inventory, staging and judging the entries.  The labels need to be ',
                   'oriented so they are readable.  Please use rubberbands or clear packing ',
                    'tape to attach to the entries.  Placing the labels in ziplock sandwich ',
                    'bags is highly recommended.  Use the picture to the right as an example.'
                    ]

        self.ln(5)
        self.cell(0, 10, hello, align="L")
        self.ln(10)

        for line in text:
            self.cell(0, 10, line, align="L")
            self.ln(5)

        self.ln(5)
        for line in text2:
            self.cell(0, 10, line, align="L")
            self.ln(5)

        self.image("files/example.jpg", x=155, y=53, w=45)

    def table(self, data, homebrew=False):
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

        # Here we add more padding by passing 2*th as height
        for label in data:

            # Document title centered, 'B'old, 14 pt
            self.ln(2 * th)



            if first_label:  #move down the page a bit more for first label
                self.ln(4 * th)
                image_y += 92


            self.set_font('Times', 'B', 14.0)
            self.cell(epw, 0.0, 'Entry Labels for {}'.format(label[0]), align='C')
            self.ln(4 * th)

            self.cell(col_width, 2 * th, 'NC Brewer\'s Cup 2018', border='LT', align='C')
            self.cell(5, 2 * th, ' ', border='LR')
            self.cell(col_width, 2 * th, 'NC Brewer\'s Cup 2018', border='RT', align='C')
            self.ln(2 * th)

            self.cell(col_width, 2 * th, 'Homebrew Competition' if homebrew else 'Commercial Competition', border='LB', align='C')
            self.cell(5, 2 * th, ' ', border='LR')
            self.cell(col_width, 2 * th, 'Homebrew Competition' if homebrew else 'Commercial Competition', border='RB', align='C')
            self.ln(2 * th)

            self.set_font('Times', '', 12.0)
            self.cell(col_width, 2 * th, 'Attach to entry w/ Rubberband only' if homebrew else '', border='LB', align='C')
            self.cell(5, 2 * th, ' ', border='LR')
            self.cell(col_width, 2 * th, 'Attach to entry w/ Rubberband only' if homebrew else '', border='RB', align='C')
            self.ln(2 * th)

            self.set_font('Times', 'B', 12.0)

            first_row = True

            line_ht = 3
            align = 'C'

            for row in label:
                # Enter data in columns
                self.cell(col_width, line_ht * th, '  {}'.format(str(row)), border='L', align=align)
                self.cell(5, line_ht * th, ' ', border='LR')
                self.cell(col_width, line_ht * th, '  {}'.format(str(row)), border='R', align=align)

                self.ln(line_ht * th)

                if first_row:
                    self.set_font('Times', '', 12.0)
                    first_row = False
                    line_ht = 2
                    align = 'L'
                    entry_id = row.split(' ')[-1].lstrip('0')


            self.cell(col_width, 8 * th, '', border='BL')
            self.cell(5, 8 * th, ' ', border='LR')
            self.cell(col_width, 8 * th, '', border='BR')


            slide_side = 20
            self.image("files/qr_{}.png".format(entry_id), x=((col_width - col_width / 2)) - slide_side, y=image_y, w=23)
            self.image("files/qr_{}.png".format(entry_id), x=(col_width + (col_width - col_width / 2)) - slide_side + 5, y=image_y, w=23)

            self.image("files/NCBClogo.jpg", x=((col_width - col_width / 2)) + slide_side, y=image_y - 2, w=20)
            self.image("files/NCBClogo.jpg", x=(col_width + (col_width - col_width / 2)) + slide_side + 5, y=image_y - 2, w=20)


            if first_label:
                first_label = False
                #self.add_page()
            else:
                label_count += 1


            if label_count % 2 == 0 and (label_count + 1) < len(data):
                #print(label_count, len(data))
                self.add_page()
                image_y = 120

                self.ln(2 * th)
            else:
                image_y = 244

                self.ln(8 * th)



class InvoiceFPDF(FPDF, HTMLMixin):

    def header(self):
        """
        Header on each page
        """

        # Effective page width, or just epw
        epw = self.w - 2 * self.l_margin

        # insert my logo
        #self.image("logo.png", x=10, y=8, w=23)
        # position logo on the right
        #self.cell(w=80)

        # set the font for the header, B=Bold
        self.set_font("Arial", style="B", size=15)
        # page title
        self.image("files/ncbg-logo.png", x=12, y=12, w=31)
        self.image("files/NCBClogo.jpg", x=epw-5, y=9, w=14)
        self.cell(epw, 16, "        Invoice for Donation to the NC Brewers Cup 2018", border=1, ln=0, align="C")
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

    def intro(self, brewer):

        ncbg = ['NC Brewers Guild', 'PO Box 27921', 'Raleigh, NC 27611']

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

        self.cell(col_width, 2 * th, 'From:', border='LTB', align='L')
        self.cell(5, 2 * th, ' ', border='LR')
        self.cell(col_width, 2 * th, 'To:', border='RTB', align='L')
        self.ln(2 * th)


        index = 0
        line_ht = 1
        align = 'L'

        #add blank line
        self.cell(col_width, line_ht * th, ' ', border='L', align=align)
        self.cell(5, line_ht * th, ' ', border='LR')
        self.cell(col_width, line_ht * th, ' ', border='R', align=align)
        self.ln(line_ht * th)

        for b in brewer:
            self.cell(col_width, line_ht * th, '  {}'.format(b), border='L', align=align)
            self.cell(5, line_ht * th, ' ', border='LR')
            self.cell(col_width, line_ht * th, '  {}'.format(ncbg[index]), border='R', align=align)

            index += 1
            self.ln(line_ht * th)

        self.cell(col_width, line_ht * th, '', border='BL')
        self.cell(5, line_ht * th, ' ', border='LR')
        self.cell(col_width, line_ht * th, '', border='BR')

        self.line(10, 75, epw + 15, 75)
        self.ln(20)

    def table(self, data):
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


        col_widths = [20,20,60,60,30]

        self.cell(col_widths[0], 2 * th, 'Qty', border='LRTB', align='C')
        self.cell(col_widths[1], 2 * th, 'Entry_id', border='RTB', align='C')
        self.cell(col_widths[2], 2 * th, 'Category', border='RTB', align='C')
        self.cell(col_widths[3], 2 * th, 'Beer Name', border='RTB', align='C')
        self.cell(col_widths[4], 2 * th, 'Price', border='RTB', align='C')
        self.ln(2 * th)

        self.set_font('Times', '', 10.0)

        printed_lines = 0

        # Here we add more padding by passing 2*th as height
        for entry in data:
            self.cell(col_widths[0], 2 * th, entry[0], border='LRTB', align='L')
            self.cell(col_widths[1], 2 * th, entry[1], border='RTB', align='L')
            self.cell(col_widths[2], 2 * th, entry[2][:35], border='RTB', align='L')
            self.cell(col_widths[3], 2 * th, entry[3], border='RTB', align='L')
            self.cell(col_widths[4], 2 * th, entry[4], border='RTB', align='L')
            self.ln(2 * th)

            printed_lines += 1

            if printed_lines % 25 == 0:
                for i in range(0,4):
                    self.cell(col_widths[0], 2 * th, '', border='', align='L')
                    self.cell(col_widths[1], 2 * th, '', border='', align='L')
                    self.cell(col_widths[2], 2 * th, '', border='', align='L')
                    self.cell(col_widths[3], 2 * th, '', border='', align='L')
                    self.cell(col_widths[4], 2 * th, '', border='', align='L')
                    self.ln(2 * th)

        total_lines = 25 - len(data)

        for i in range(0, total_lines):
            self.cell(col_widths[0], 2 * th, ' ', border='LRB', align='L')
            self.cell(col_widths[1], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[2], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[3], 2 * th, ' ', border='RTB', align='L')
            self.cell(col_widths[4], 2 * th, ' ', border='RTB', align='L')
            self.ln(2 * th)

        self.set_font('Times', 'B', 10.0)
        self.cell(col_widths[0], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[1], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[2], 2 * th, ' ', border='', align='L')
        self.cell(col_widths[3], 2 * th, 'Total:', border='LRTB', align='R')
        self.cell(col_widths[4], 2 * th, '$0.00', border='RTB', align='L')


class Ncbc:

    def __init__(self, pkid=0):

        logger.info('Initializing download of report for pkid: {}'.format(pkid))

        self.pkid = pkid
        self.auth = None
        self.name = ''
        self.url = ''
        self.entries = []
        self.header = []
        self.person_fields = {}
        self.entry_fields = {}

        if self.pkid:
            self.get_current_competition()


    def get_current_competition(self):
        """
        get the active commercial or homebrew competition

        Get the information to collect the report; URL, authentication, etc
        :return:
        """

        if self.pkid:
            sql = 'select * from reports where pkid = "{}"'.format(self.pkid)

            uid = gen_uid()
            result = db.db_command(sql=sql, uid=uid).one(uid)

            if 'payload' in result:


                self.auth = '{' + result['payload'][1:-1].format(d=result) + '}'
                self.auth = json.loads(self.auth)

                self.url = result['url']
                self.name = result['name']
            else:
                logger.error('Unable to retrieve report info for pkid: {}'.format(self.pkid))

        else:
            logger.error('Unable to get report login info for pkid: {}'.format(self.pkid))


    def get_csv(self):
        """
        Download the CSV file
        Place CSV in self.entries
        Place header in self.header = self.entires.pop(0)
        :return:
        """

        if self.url:
            self.entries = []

            with requests.Session() as s:
                logger.info('Attempting to authenticate using UID {}'.format(self.auth['Username']))
                p = s.post('https://www.memberleap.com/members/gateway.php?org_id=NCCB', data=self.auth)
                if p.status_code == 200:
                    logger.info('Attempting to generate {} report using URL: {}'.format(self.name, self.url))
                    r = s.get(self.url)

                    if r.status_code == 200:
                        data = r.text

                        match = re.search(r'number of records:(\d+)<', data)

                        if match:
                            try:
                                record_count = int(match.group(1))
                                if record_count:
                                    record_count -= 1
                                recourd_count = str(record_count)
                            except:
                                record_count = match.group(1)
                            logger.info('Number of records in CSV: {}'.format(record_count))
                            match = re.search(r'/docs/(.*\.csv)"', data)

                            if match:
                                csv_file = match.group(1)
                                logger.info('Found CSV File: {}'.format(csv_file))
                                csv_url = 'https://www.memberleap.com/members/secure/evr/docs/{}'.format(csv_file)
                                logger.info('attempting to download {} CSV from URL: {}'.format(self.name, csv_url))
                                r = s.get(csv_url)

                                entries = r.content.replace(b'\x00', b'').decode('ascii','ignore').splitlines()
                                logger.info('Retrieved {} CSV file with {} lines including heading'.format(self.name, len(entries)))
                                self.header = entries.pop(0).replace('"', '').split(',')
                                #print(self.header)
                                #self.header = [x.decode('utf-8') for x in self.header]

                                for e in reader(entries):
                                    self.entries.append(e)


                            else:
                                logger.error('Unable to find CSV Filename in response')
                        else:
                            logger.error('Unable to find "number of records" in response')
                    else:
                        logger.error('Error code: {}, getting URL: {}'.format(r.status_code, self.url))
                else:
                    logger.error('Error code: {}, attempting authentication: {}'.format(p.status_code, self.url))
        else:
            logger.error('Unable to get CSV info due to blank URL')


    def get_csv_2(self):
        """
        Download the CSV file
        Place CSV in self.entries
        Place header in self.header = self.entires.pop(0)
        :return:
        """

        if self.url:
            self.entries = []

            with requests.Session() as s:
                logger.info('Attempting to authenticate using UID {}'.format(self.auth['Username']))
                p = s.post('https://www.memberleap.com/members/gateway.php?org_id=NCCB', data=self.auth)
                if p.status_code == 200:
                    logger.info('Attempting to generate {} report using URL: {}'.format(self.name, self.url))
                    r = s.get(self.url)

                    if r.status_code == 200:
                        data = r.text

                        match = re.search(r'number of records:(\d+)<', data)

                        if match:
                            try:
                                record_count = int(match.group(1))
                                if record_count:
                                    record_count -= 1
                                recourd_count = str(record_count)
                            except:
                                record_count = match.group(1)
                            logger.info('Number of records in CSV: {}'.format(record_count))
                            match = re.search(r'/docs/(.*\.csv)"', data)

                            if match:
                                csv_file = match.group(1)
                                logger.info('Found CSV File: {}'.format(csv_file))
                                csv_url = 'https://www.memberleap.com/members/secure/evr/docs/{}'.format(csv_file)
                                logger.info('attempting to download {} CSV from URL: {}'.format(self.name, csv_url))
                                r = s.get(csv_url)

                                entries = r.content.replace(b'\x00', b'').decode('ascii','ignore').splitlines()
                                logger.info('Retrieved {} CSV file with {} lines including heading'.format(self.name, len(entries)))

                                header = True
                                #self.header = entries.pop(0).replace('"', '').split(',')
                                #print(self.header)
                                #self.header = [x.decode('utf-8') for x in self.header]

                                for e in reader(entries, escapechar='\\', doublequote=False):
                                    if header:
                                        self.header = [x.strip('\"') for x in e]
                                        #print(self.header)
                                        header = False
                                    else:
                                        self.entries.append([x.strip('\"').strip() for x in e])
                                        #print([x.strip('\"').strip() for x in e])


                            else:
                                logger.error('Unable to find CSV Filename in response')
                        else:
                            logger.error('Unable to find "number of records" in response')
                    else:
                        logger.error('Error code: {}, getting URL: {}'.format(r.status_code, self.url))
                else:
                    logger.error('Error code: {}, attempting authentication: {}'.format(p.status_code, self.url))
        else:
            logger.error('Unable to get CSV info due to blank URL')


    def get_gen_id(self, data):
        """
        Return the gen_id which is the unique field in the raw_data, entries tables

        Currently it is self.pkid + '-' + attendee_id
        :param data: Data to append to silf.pkid
        :return: gen_id
        """

        return '{}-{}'.format(self.pkid, data)

    def get_attendee_id(self, data):
        """
        Return attendee_id from gen_id
        :param data: gen_id
        :return: attendee_id portion of gen_id
        """
        return data.split('-')[-1]

    def get_field(self, row, field):
        """
        Get the value contained in the entry (list) record at the index of the field
        :param entry: entry list
        :param field: field to get from entry list
        :return: field value or "" if field not found
        """
        try:
            index = self.header.index(field)
            return row[index]
        except:
            return ''

    def get_raw_data_pkid(self, field, data):

        sql = 'select pkid from raw_data where {field} = "{data}"'.format(field=field, data=data)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result

    def insert_raw_data(self, gen_id, attendee_id, fk_people, fk_entries, data):

        #convert row list to string
        data = json.dumps(data)

        #replace and \" with just " before excaping the quotes
        data = escape_sql(data.replace(r'\"', '"'))
        sql = 'insert into raw_data (gen_id, attendee_id, fk_people, fk_entries, fk_competitions, json_data) values ' \
              '("{}", "{}", "{}", "{}", "{}", "{}")'.format(gen_id,
                                               attendee_id,
                                               fk_people,
                                                fk_entries,
                                                self.pkid,
                                               data)
        db.db_command(sql=sql)

        sql = 'select pkid from raw_data where gen_id = "{}"'.format(gen_id)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        fk_raw_data = result.get('pkid', 0)

        return fk_raw_data

    def find_person(self, first_name, last_name, email):

        sql = 'select pkid from people where first_name = "{}" and last_name = "{}" and email = "{}"'.format(first_name,
                                                                                                          last_name,
                                                                                                          email
                                                                                                          )
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('pkid', 0)


    def find_brewer(self, email):

        sql = 'select pkid from people where email = "{}"'.format(email)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('pkid', 0)


    def get_person_fields(self):

        db = ['salutation', 'last_name', 'first_name', 'organization', 'title',
              'address', 'address 2', 'city', 'state', 'zip', 'home phone', 'email', 'create_date']
        self.person_fields = {}

        for d in db:

            try:
                index = self.header.index(d)
                self.person_fields[d] = index
            except:
                logger.error('Unable to find person field "{}" in header'.format(d))
                self.person_fields = {}
                return


    def get_person_pkid(self, email):

        sql = 'select pkid from people where email = "{}"'.format(email)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result['email']


    def get_attendee_id_list(self, pkid):

        sql = 'select attendee_id_list from people where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        try:
            id_list = json.loads(result.get('attendee_id_list', '[]'))
        except:
            logger.error('Unavble to get attendee_is_list for pkid {}'.format(pkid))
            id_list = []

        return id_list


    def update_attendee_id_list(self, pkid, id_list):

        id_list = escape_sql(json.dumps(id_list))

        sql = 'update people set attendee_id_list = "{}" where pkid = "{}"'.format(id_list, pkid)
        db.db_command(sql=sql)


    def get_entry_fields(self):

        db_fields = ['Name of Beer', 'BJCP Category Selection', 'BJCP Subcategory', 'Entry Notes', 'create_date']
        self.entry_fields = {}

        for d in db_fields:

            try:
                index = self.header.index(d)
                self.entry_fields[d] = index
            except:
                logger.error('Unable to find brewer field "{}" in header'.format(d))
                self.entry_fields = {}
                return


    def insert_person(self, entry, attendee_id):
        db_fields = ['salutation', 'last_name', 'first_name', 'organization', 'title',
              'address', 'address_2', 'city', 'state', 'zip', 'phone', 'email', 'created',
                     'updated', 'attendee_id_list', 'send_labels', 'fk_competitions']

        logger.info('Attenpting to insert person: {} {}, {}'.format(self.get_field(entry, 'first_name'),
                                             self.get_field(entry, 'last_name'),
                                             self.get_field(entry, 'email')))
        values = [entry[v].strip() for k, v in self.person_fields.items()]

        attendee_id_list = escape_sql(json.dumps([attendee_id]))

        sql = 'insert ignore into people ({}) values ("{}", NOW(), "{}", "0", {})'.format(','.join(db_fields),
                                                                                      '","'.join(values),
                                                                                      attendee_id_list,
                                                                                      self.pkid
                                                                                      )
        db.db_command(sql=sql)

        fk_people = self.find_person(self.get_field(entry, 'first_name'),
                                    self.get_field(entry, 'last_name'),
                                    self.get_field(entry, 'email')
                                    )
        return fk_people


    def parse_category(self, category, sub_category):

        cat = category.split('.')[0]
        sub_cat = sub_category[0].upper() if sub_category else 'A'

        return cat, sub_cat



    def generate_entry_id(self):

        sql = 'update entry_generator set entry_number=entry_number+1, updated=NOW()'
        db.db_command(sql=sql)

        sql = 'select entry_number from entry_generator'
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result['entry_number']

    def insert_entry(self, entry, fk_people):
        db_fields = ['name', 'category', 'sub_category', 'description', 'created', 'updated', 'label_sent',
                    'confirmation_sent', 'fk_people', 'fk_competitions', 'entry_id', 'error']
        error = ''

        temp = entry.copy()
        cat, sub_cat = self.parse_category(self.get_field(entry, 'BJCP Category Selection'), self.get_field(entry, 'BJCP Subcategory'))

        #not a valid cat sub category combo
        if not Style('BJCP2015').get_style_name(cat, sub_cat):
            error = 'Invalid category or sub category: {} {}'.format(cat, sub_cat)

        temp[self.entry_fields['BJCP Category Selection']] = cat
        temp[self.entry_fields['BJCP Subcategory']] = sub_cat


        """
        self.get_field(entry, 'Entry Notes') = American IPA, specifically "west-coast style" brewed with pale malt and dry hopped with Mosaic and Citra
        json.dumps(self.get_field(entry, 'Entry Notes')) = "American IPA, specifically \"west-coast style\" brewed with pale malt and dry hopped with Mosaic and Citra"
        escape_sql(json.dumps(self.get_field(entry, 'Entry Notes')).strip('\"') = American IPA, specifically \\"west-coast style\\" brewed with pale malt and dry hopped with Mosaic and Citra
        """
        #Removed escape_sql as it adds an extra \ in front of the "
        #desc = escape_sql(json.dumps(self.get_field(entry, 'Entry Notes')).strip('\"'))
        desc = json.dumps(self.get_field(entry, 'Entry Notes')).strip('\"')

        #print(desc)

        temp[self.entry_fields['Entry Notes']] = desc

        values = [temp[v].strip() for k, v in self.entry_fields.items()]

        entry_id = self.generate_entry_id()

        logger.info('Inserting entry id {}: {}{}'.format(entry_id, cat, sub_cat))

        sql = 'insert into entries ({}) values ("{}", NOW(), "0", "0", "{}", "{}", "{}", "{}")'.format(','.join(db_fields), '","'.join(values), fk_people, self.pkid, entry_id, error)
        db.db_command(sql=sql)


        #todo: get next entry id
        #todo: get brewer pkid
        #todo: insert entry
        #todo: set created and updated dates and fk_brewers, fk_competitions and entry id

        sql = 'select pkid from entries where entry_id = "{}"'.format(entry_id)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        fk_entries = result.get('pkid', 0)

        return fk_entries

    def update_entry_with_fk_raw_data(self, fk_entries, fk_raw_data):

        sql = 'update entries set fk_raw_data="{}" where pkid="{}"'.format(fk_raw_data, fk_entries)
        db.db_command(sql=sql)


    def set_send_labels(self, fk_people):

        sql = 'update people set send_labels="1" where pkid="{}"'.format(fk_people)
        db.db_command(sql=sql)


    def reset_send_labels(self, brewer):

        sql = 'update people set send_labels="0" where email="{}"'.format(brewer)
        db.db_command(sql=sql)

    def send_labels(self, brewer):

        sql = 'select send_labels from people where email = "{}"'.format(brewer)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        if result.get('send_labels', 0) == 1:
            return True

        return False

    def process_new_entries(self):

        self.get_person_fields()
        self.get_entry_fields()

        count = 0

        logger.info('Processing new entries')
        for row in self.entries:

            attendee_id = self.get_field(row, 'attendee_id')
            gen_id = self.get_gen_id(attendee_id)

            result =  self.get_raw_data_pkid(field='gen_id', data=gen_id)

            if not result:  # Record not find, insert it
                count += 1
                #self.get_person()
                logger.info('Inserting raw_data for attendee_id: {}'.format(attendee_id))

                #removed finding brewer with firstname and last name
                fk_people = self.find_person(self.get_field(row, 'first_name'),
                                             self.get_field(row, 'last_name'),
                                             self.get_field(row, 'email')
                                             )

                #just find the brewer using email
                fk_people = self.find_brewer(self.get_field(row, 'email'))

                if fk_people == 0:
                    fk_people = self.insert_person(row, attendee_id)

                self.set_send_labels(fk_people)

                attendee_id_list = self.get_attendee_id_list(fk_people)

                if attendee_id not in attendee_id_list:
                    logger.info('Appending attendee_id_list with {}'.format(attendee_id))
                    self.update_attendee_id_list(fk_people, attendee_id_list + [attendee_id])

                fk_entries = self.insert_entry(row, fk_people)

                fk_raw_data = self.insert_raw_data(gen_id, attendee_id, fk_people, fk_entries, row)

                self.update_entry_with_fk_raw_data(fk_entries, fk_raw_data)



        if count == 0:
            logger.info('No new entries to insert into DB')
        else:
            logger.info('Processed {} new entries'.format(count))





            #if created date > last entry created data then insert entry
            #otherwise get entry from DB and logger.info to the screen - match name, cat, sub-cat and description
            #otherwise indicate error with entry


    def validate_entries(self):

        errors = False
        sql = 'select pkid, attendee_id, fk_people, fk_entries from raw_data where fk_competitions = "{}" and (fk_people=0 or fk_entries=0)'.format(self.pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        if result:
            logger.error('The following errors are found in raw_data:')
            for r in result:
                logger.error('  pkid: {d[pkid]}, attendee_id: {d[attendee_id]}, fk_people: {d[fk_people]}, ' \
                             'fk_entries: {d[fk_entries]}'.format(d=r))
            errors = True
        else:
            logger.info('No errors found in raw_data')

        sql = 'select pkid, entry_id, fk_people, fk_raw_data from entries where fk_competitions = "{}" and (fk_people=0 or fk_raw_data=0)'.format(self.pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        if result:
            logger.error('The following errors are found in entries:')
            for r in result:
                logger.error('  pkid: {d[pkid]}, entry_id: {d[entry_id]}, fk_people: {d[fk_people]}, ' \
                             'fk_raw_data: {d[fk_raw_data]}'.format(d=r))
                errors = True
        else:
            logger.info('No errors found in entries')

        return errors


    def get_unconfirmed_entries(self):

        sql = 'select entries.pkid, entry_id, category, sub_category, name, description, error, p.email, p.first_name, ' \
              'p.last_name, p.phone, p.organization, p.address, p.city, p.state, p.zip ' \
              'from entries ' \
              'inner join people as p on p.pkid = entries.fk_people ' \
              'where entries.fk_competitions = "{}" and confirmation_sent = "0"'.format(self.pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result

    def group_entries_by_brewer(self, entries):

        brewers = {}

        for entry in entries:

            if entry['email'] not in brewers:
                brewers[entry['email']] = []

            brewers[entry['email']].append(entry)

        return brewers


    def sort_entries_by_category(self, entries):

        return sorted(entries, key=lambda k: '{:02d}{}'.format(int(k['category']), k['sub_category']))

    def get_entries_with_errors(self, entries):

        errors = []
        for entry in entries:
            if entry['error']:
                errors.append({'entry_id': entry['entry_id'], 'error': entry['error']})


        return errors


    def get_brewers(self, pkids):

        if type(pkids) != type([]):
            pkids = [pkids]

        pkids = [str(x) for x in pkids]

        sql = 'select * from people where fk_entries in ({})'.format(','.join(pkids))

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        print(result)




    def generate_qr_code(self, data):

        img = qrcode.make(data)

        sys.stdout.flush()
        sys.stdout = open('files/qr_{}.png'.format(data), 'w')
        # Use sys.stdout.buffer if available (Python 3), avoiding
        # UnicodeDecodeErrors.
        stdout_buffer = getattr(sys.stdout, 'buffer', None)
        if not stdout_buffer:
            if sys.platform == 'win32':  # pragma: no cover
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            stdout_buffer = sys.stdout

        img.save(stdout_buffer)


    def get_bottle_info(self, entries, ncbc, homebrew=False):

        entries = ncbc.sort_entries_by_category(entries)

        data = []

        for entry in entries:

            #print(entry)

            self.generate_qr_code(entry['entry_id'])

            entry['name'] = entry['name'][:36]

            label = [
                    'Entry Number: {:05d}'.format(int(entry['entry_id'])),
                    'Category: {d[category]}{d[sub_category]} - {name}'.format(d=entry, name=Style().get_style_name(entry['category'], entry['sub_category'], 'BJCP2015')),
                    'Brewer Name: {d[first_name]} {d[last_name]}'.format(d=entry),
                    'Brewer Email: {d[email]}'.format(d=entry),
                    'Brewer Phone: {d[phone]}'.format(d=entry),
                    'Beer Name: {d[name]}'.format(d=entry),
                    '{org}: {d[organization]}'.format(org='Homebrew Club' if homebrew else 'Brewery', d=entry),
            ]
            data.append(label)

        return data


    def generate_bottle_label_pdf(self, data, filename, first_name):

        pdf = BottleLabelFPDF()
        # First page
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.intro(first_name)
        pdf.table(data, 'homebrew' in self.name.lower())
        #pdf.write_html(html)
        pdf.output('files/{}_entry_labels.pdf'.format(filename), 'F')


    def parse_brewer(self, entry):

        return [entry['organization'], entry['address'], '{d[city]}, {d[state]} {d[zip]}'.format(d=entry)]

    def generate_invoice(self, entries, ncbc, filename):

        entries = ncbc.sort_entries_by_category(entries)

        data = []

        brewer = self.parse_brewer(entries[0])


        for entry in entries:

            data.append(['',
                         '{:05d}'.format(int(entry['entry_id'])),
                         'Category: {d[category]}{d[sub_category]} - {name}'.format(d=entry,
                                                                                    name=Style().get_style_name(
                                                                                        entry['category'],
                                                                                        entry['sub_category'],
                                                                                        'BJCP2015')),
                         '{d[name]}'.format(d=entry),
                         '$0.00'
                         ])

        pdf = InvoiceFPDF()

        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.intro(brewer)
        pdf.table(data)

        pdf.output('files/{}'.format(filename), 'F')



    def process_volunteer(self):

        attendee_list = []

        sql_fields = ["salutation", "last_name", "first_name", "organization", "title", "address", "address 2",
                      "city", "state", "zip", "country", "fax", "home phone", "work phone", "email",
                      "create_date", "package", "attendee_id", "notes", "Judging Certifications?",
                      "Would you consider being a Steward if needed?",
                      "If needed, would you be willing and able to serve as a Judge?",
                      "If yes, do you have any judging certifications?"
                      ]

        mapping = {
            'address 2': 'address_2',
            'home phone': 'home_phone',
            'work phone': 'work_phone',
            'Judging Certifications?': 'certifications',
            'Would you consider being a Steward if needed?': 'consider_steward',
            'If needed, would you be willing and able to serve as a Judge?': 'consider_judge',
            'If yes, do you have any judging certifications?': 'steward_certs'
        }

        rev_mapping = {}
        for m in mapping:

            rev_mapping[mapping[m]] = m

        fields = [mapping.get(x, x) for x in sql_fields]

        for row in self.entries:
            attendee_id = self.get_field(row, 'attendee_id')

            attendee_list.append(attendee_id)

            logger.info('Processing attendee_id: {}, {} {}'.format(attendee_id, self.get_field(row, 'first_name'),
                                                                 self.get_field(row, 'last_name')))

            sql = 'select {},judge from volunteers where attendee_id = "{}"'.format(','.join(fields), attendee_id)

            uid = gen_uid()
            result = db.db_command(sql=sql, uid=uid).one(uid)

            if result:
                changed = False

                for field in fields:

                    downloaded_value = self.get_field(row, rev_mapping.get(field, field)).strip()

                    saved_value = result[field]

                    if downloaded_value != saved_value:
                        changed = True
                        break



                if changed:
                    logger.info('Updating attendee_id: {}, {} {}'.format(attendee_id, self.get_field(row, 'first_name'), self.get_field(row, 'last_name')))

                    update = []

                    judge = '2'

                    for field in fields:

                        value = self.get_field(row, rev_mapping.get(field, field)).strip()

                        if field == 'consider_steward' and value:
                            judge = '1'
                        elif field == 'consider_judge' and value:
                            judge = '0'

                        update.append('{} = "{}"'.format(field, value))

                    update.append('judge = "{}"'.format(judge))

                    sql = 'update volunteers set {}, changed = "1", updated = NOW() where attendee_id = "{}"'.format(','.join(update), attendee_id)
                    db.db_command(sql=sql)

            else:

                values = []

                judge = '2'

                for field in fields:

                    value = self.get_field(row, rev_mapping.get(field, field)).strip()

                    if field == 'consider_steward' and value:
                        judge = '1'
                    elif field == 'consider_judge' and value:
                        judge = '0'

                    values.append(value)

                values.append(judge)

                sql = 'insert ignore into volunteers ({},judge,new,changed,updated) values ("{}","1","0",NOW())'.format(','.join(fields), '","'.join(values))
                db.db_command(sql=sql)

                sql = 'select pkid, first_name, last_name from volunteers where attendee_id = "{}"'.format(attendee_id)

                uid = gen_uid()
                result = db.db_command(sql=sql, uid=uid).one(uid)

                if result:
                    logger.info('Successfully inserted attendee_id: {}, {d[pkid]}: {d[first_name]} {d[last_name]}'.format(attendee_id, d=result))
                else:
                    logger.error(
                        'Unable to insert attendee_id: {}, {} {}'.format(
                            attendee_id, self.get_field(row, 'first_name'), self.get_field(row, 'last_name')))

                #insert new row
                #set new field


        sql = 'update volunteers set deleted = "1", changed = "1", updated = NOW() where attendee_id not in ("{}")'.format('","'.join(attendee_list))
        result = db.db_command(sql=sql)

        row_count = result.row_count()

        if row_count:
            logger.info('The following {} rows were marked as deleted'.format(row_count))

            sql = 'select attendee_id, first_name, last_name, package from volunteers where deleted = "1" and changed = "1"'

            uid = gen_uid()
            result = db.db_command(sql=sql, uid=uid).all(uid)

            for r in result:
                logger.error('Attendee ID: {d[attendee_id]}, '
                             '{d[first_name]} {d[last_name]}, Session: {d[package]}'.format(d=r))


        sql = 'select pkid, attendee_id, first_name, last_name from volunteers where judge > "1"'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        for r in result:
            logger.error('Volunteer with unknown judge status: pkid: {d[pkid]}, Attendee ID: {d[attendee_id]}, '
                         '{d[first_name]} {d[last_name]}'.format(d=r))


def get_schedule_counts():

    schedule = {
        'Thursday, September 27, 9:00am 1:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0},
        'Thursday, September 27, 1:00am 5:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0},
        'Friday, Sept. 28th, 9:00am-1:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0},
        'Friday, Sept. 28th, 1:00am-5:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0},
        'Saturday, September 29, 8:30am - 12:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0},
        'Saturday, September 29, 12:30pm - 5:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0},
        'Sunday, September 30, 8:30am - 12:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0},
        'Sunday, September 29, 12:30pm - 5:00pm': {'Judge': 0, 'Steward': 0, 'Unknown': 0}
    }

    sql = 'SELECT count(*), package, judge from volunteers where fk_competitions = "1" group by package, judge'

    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)

    for r in result:

        judge = r['judge']
        session_name = r['package']

        session_type = 'Judge' if judge == 1 else 'Steward' if judge == 0 else 'Unknown'

        schedule[session_name][session_type] += int(r['count(*)'])

    return schedule


def email_status(pkid=1, test=False):

    e = Email('files/kevin.json')
    sql = 'select count(distinct fk_people) from entries where fk_competitions = "{}"'.format(pkid)

    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).one(uid)

    num_brewers = result.get('count(distinct fk_people)', 'Not found')


    sql = 'select count(*) from entries where fk_competitions = "{}"'.format(pkid)

    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).one(uid)


    schedule = (get_schedule_counts())

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

    for r in schedule:

        num_judges += schedule[r]['Judge']
        table += '<tr>' \
            '<td>{}</td>' \
            '<td>{}</td>' \
            '<td>{}</td>' \
            '</tr>'.format(r, schedule[r]['Judge'], schedule[r]['Steward'])

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

    num_entries = result.get('count(*)', 'Not found')
    beers_per_judge = round(num_entries / (num_judges / 2))

    msg = 'Good Morning,<br/>' \
          '<br/>' \
          'Wow, 28 beers from one brewery.  Erik, are you entering?.' \
          '<h3>Entry Info:</h3>' \
          'Number of entries: {}<br/>' \
          'Number of brewers: {}<br/>' \
          '{} days left for registration.' \
          '<br/>' \
          '{}' \
          '<br/>' \
          'Average beers per judge: {}' \
          '<br/>' \
          '<br/>' \
          'Kevin'.format(num_entries,  num_brewers, (datetime.date(2018, 9, 23) - datetime.date.today()).days, table, beers_per_judge)

    #print(msg)

    message = e.create_html_message('NC Brewers Cup <kevin.thorngren@gmail.com>',
                                    'kevin.thorngren@gmail.com' if test else
                                               ['operations@ncbeer.org', 'jasmine@ncbeer.org',
                                                'erik@mysterybrewing.com', 'hopson@mindspring.com',
                                                'kevin.thorngren@gmail.com'],
                                               'NCBC Commercial Competition Status',
                                               msg,
                                               )

    if DATABASE != 'competitions':
        logger.info('Skipping email due to using test DB')
        result = False
    else:
        result = e.send_message(message)


def process_new_entries(pkid=1):

    n = Ncbc(pkid=1)
    n.get_csv_2()
    n.process_new_entries()
    validation_errors = n.validate_entries()
    result = n.get_unconfirmed_entries()

    brewers = n.group_entries_by_brewer(result)

    for brewer in brewers:
        #print(brewer)

        entries = brewers[brewer]

        errors = n.get_entries_with_errors(entries)

        if errors:
            logger.error('Check entries for brewer {}: {} {}: {}'.format(brewer,
                                                                         entries[0]['first_name'],
                                                                         entries[0]['last_name'],
                                                                         '  \n'.join(
                                                                             ['{} - {}'.format(x['entry_id'], x['error'])
                                                                              for x in errors])))
            continue

        if n.send_labels(brewer):

            logger.info('sending to bottle labels to: '.format(brewer))

            msg = 'Hi {},\n'.format(entries[0]['first_name'])
            msg += '\n'
            msg += 'The NC Brewers Guild and I would like to thank you for your entries.  Attached you will find your '
            msg += 'entry labels and zero dollar invoice.  '
            msg += 'The Entry ID is on the label.  Please verify the information on the labels.  ' \
                   'Each entry will be judged against the Category and Subcategory on the label.  ' \
                   'Please fill in the quantities and include the invoice with your entries '
            msg += 'when they are dropped of at Pro Refrigeration.  Please let Lisa (operations@ncbeer.org) and I know '
            msg += 'if you have any questions or issues.\n'
            msg += '\n'
            msg += 'Drop off info:\n'
            msg += 'September 27th & 28th, 2018 (Thursday + Friday)\n'
            msg += '9am - 5pm\n'
            msg += 'Pro Refrigeration, Inc.\n'
            msg += '319 Farmington Road\n'
            msg += 'Mocksville, NC 27028\n'
            msg += '\n'
            msg += 'Thanks,\nLisa and Kevin\n\n'
            msg += 'Lisa Parker\n'
            msg += 'NC Brewers Cup Superintendent\n'
            msg += 'NCCBG Operations Manager\n'
            msg += 'e. operations@ncbeer.org\n'
            msg += 'c. 919.951.8588\n\n'

            msg += 'Kevin Thorngren\n'
            msg += 'NC Brewers Cup Manager\n'
            msg += 'e. kevin.thorngren@gmail.com\n'
            msg += 'c. 919.418.2350\n'

            data = n.get_bottle_info(entries, n)
            n.generate_bottle_label_pdf(data, brewer, entries[0]['first_name'])
            data = n.generate_invoice(entries, n, '{}_invoice.pdf'.format(brewer))

            e = Email('files/kevin.json')

            message = e.create_message_with_attachment('NC Brewers Cup <kevin.thorngren@gmail.com>',
                                                       brewer,
                                                       'NC Brewers Cup Entry Labels',
                                                       msg,
                                                       'files/',
                                                       ['{}_entry_labels.pdf'.format(brewer),
                                                        '{}_invoice.pdf'.format(brewer)]
                                                       )

            if validation_errors:
                result = False
            elif DATABASE != 'competitions':
                logger.info('Skipping email due to using test DB')
                result = False
            else:
                result = False
                try:
                    choice = int(input('Do you wish to email the brewers? '))
                except ValueError as e:
                    choice = 'n'

                if choice.lower() == 'y':
                    result = e.send_message(message)
                else:
                    logger.info('Skipping emailing brewers - please run script again to email')
                    result = False

            if result:
                n.reset_send_labels(brewer)
            else:
                logger.error('Failed to send email to {}'.format(brewer))





def process_new_volunteers(pkid=1):

    n = Ncbc(pkid=pkid)
    n.get_csv_2()
    n.process_volunteer()







def import_bjcp():

    #todo:  use strip() to strip any white space from email

    headings = ['firstname', 'lastname', 'address', 'city', 'state', 'zip', 'country', 'phone',
                'nickname', 'email', 'bjcp_id', 'level', 'region', 'mead']
    with open('files/Active Judges.csv') as csv_file:
        csv_reader = reader(csv_file, delimiter=',')
        lines = 0
        for row in csv_reader:
            sql = 'insert ignore into bjcp_judges ({}) values ("{}")'.format(','.join(headings), '","'.join(row))
            db.db_command(sql=sql)
            print(", ".join(row))
            lines += 1
        print('Number of lines: {}'.format(lines))



def email_bjcp(email, subject, message):
    e = Email('files/kevin.json')

    message = e.create_message('NC Brewers Cup <kevin.thorngren@gmail.com>',
                                               email,
                                               subject,
                                               message,
                                               )
    result = e.send_message(message)


    if result:
        pass
        logger.info('Sent email to {}'.format(email))

        sql = 'update bjcp_judges set first_call = "1" where email = "{}"'.format(email)
        db.db_command(sql=sql)

        return True

    else:
        logger.error('Failed to send email to {}'.format(email))
        return False


def first_bjcp_email():

    subject = 'First Call: NC Brewers Cup Commercial Competition'
    message = 'Hi {firstname},\n' \
              '\n' \
              'This email is being sent to BJCP judges in the south eastern area.  The NC Brewers Cup started in 2012 ' \
              'running both a Commercial Competition and a Homebrew Competition for the NC State Fair. \n ' \
              '\n' \
              'This email is sent with short notice ' \
              'due to last minute logistic changes for both the Commercial and Homebrew Competitions.  ' \
              'This year the Commercial Competition will be held at Pro Refrigeration in Mocksville, NC.  ' \
              'The Homebrew Competition logistics are still in the works.  I\'ll send out another email with the ' \
              'final Homebrew Comp info.\n' \
              '\n' \
              'The Commercial Competition is a BJCP registered competition.  We are looking for judges and stewards ' \
              'for Saturday and Sunday September 29-30.  We will be receiving entries and performing inventory ' \
              'Thursday and Friday Sept 27-28 and can use help those days.\n' \
              '\n' \
              'More details and the registration link can be found here:\n' \
              'http://ncbeer.org/news_manager.php?page=16367\n' \
              '\n' \
              'Please forward this email to anyone or club who you feel might be interested in volunteering.\n' \
              '\n' \
              'Please let me know if you have any questions.\n' \
              '\n' \
              'Thanks,\n' \
              'Kevin\n'

    sql = 'select firstname, lastname, nickname, email from bjcp_judges where state in ("NC", "SC", "GA", "AL", "TN", "KY", "WV", "VA", "FL") and first_call = "0"'

    uid = gen_uid()
    result = db.db_command(sql=sql, uid=uid).all(uid)


    number = len(result)
    #print(number)
    count = 0

    for r in result:
        count += 1

        logger.info('Sending {} of {} to {}, {} {}'.format(count, number, r['email'], r['firstname'], r['lastname']))

        email = r['email']

        result = email_bjcp(email.strip(), subject, message.format(firstname=r['nickname'] if r['nickname'] else r['firstname']))

        if not result:
            break


        sleep(5)


def menu():

    while True:

        print(30 * '-')
        print("   M A I N - M E N U")
        print(30 * '-')
        print("1. Process New Entries")
        print("2. Process New Volunteers")
        print("3. Email Status")
        print("4. Import BJCP")
        print("0. Quit")
        print(30 * '-')

        ###########################
        ## Robust error handling ##
        ## only accept int       ##
        ###########################
        ## Wait for valid input in while...not ###
        is_valid = 0

        while not is_valid:
            try:
                choice = int(input('Enter your choice [1-3] : '))
                is_valid = 1  ## set it to 1 to validate input and to terminate the while..not loop
            except ValueError as e:
                print("'%s' is not a valid integer." % e.args[0].split(": ")[1])

        ### Take action as per selected menu-option ###
        if choice == 1:
            process_new_entries(pkid=1)
        elif choice == 2:
            process_new_volunteers(pkid=3)
        elif choice == 3:
            email_status(pkid=1)
        elif choice == 4:
            import_bjcp()
        elif choice == 0:
            break
        else:
            print("Invalid number. Try again...")


def process_import_volunteers(pkid=3):
    process_new_volunteers(pkid=pkid)
    Import().import_ncbc_volunteers()
    Volunteers().email_new()
    Volunteers().email_changed()


def fix_descriptions(pkid=1):


    n = Ncbc(pkid=pkid)
    n.get_csv_2()

    print(n.header)
    for f in n.entries:

        raw_data = [re.sub(r'[\t\r\n\f]', r'', x) for x in f]

        new_json = json.dumps(raw_data)


        attendee_id = n.get_field(f, 'attendee_id')
        desc = n.get_field(raw_data, 'Entry Notes')

        if attendee_id == '350854':
            print('350854:  ', desc)

        """
        if not desc:
            print(f)
            print(new_json)
            print(n.get_field(f, 'Entry Notes'))
            print(desc)
        """


        sql = 'select pkid from raw_data where attendee_id = "{}"'.format(attendee_id)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        pkid = result.get('pkid', 0)

        if pkid:
            sql = 'select * from entries where fk_raw_data = "{}"'.format(pkid)

            uid = gen_uid()
            result = db.db_command(sql=sql, uid=uid).one(uid)

            #print(result['name'])

            if n.get_field(f, 'Name of Beer').strip().replace('\\', '') == result['name'] or True:


                sql = 'update raw_data set json_data = "{}" where attendee_id = "{}"'.format(new_json, attendee_id)
                #print(sql)
                #db.db_command(sql=sql)
                #print('update raw_data Row count: {}'.format(db.row_count()))


                sql = 'update entries set description = "{}" where fk_raw_data = "{}"'.format(desc, pkid)
                #print(sql)
                db.db_command(sql=sql)
                print('update entries Row count: {}'.format(db.row_count()))

            else:
                print('beers dont match: "{}", "{}"'.format(n.get_field(f, 'Name of Beer'), result['name']))
            #print()
        else:
            print('Not found in DB')

if __name__ == '__main__':

    process_new_entries(pkid=1)

    #process_import_volunteers(pkid=3)

    #email_status(pkid=1, test=True)
    #email_status(pkid=1)



    #fix_descriptions()

    #menu()

    #first_bjcp_email()


    pass
