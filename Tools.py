from csv import reader, QUOTE_NONE, QUOTE_ALL

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


class Tools:

    def __init__(self):

        self.pkid = 0


    def parse_fields(self, data):

        if data and type(data[0]) == type([]):
            data= data[0]
        else:
            data = list(data)

        data.append('pkid')

        return data



    def find(self, table, *args, **kwargs):
        """
        Generic sql query using "%<string>%" for each where clause.  AND or OR search can be defind with the
        default being OR.  The fields returned can be defined.  The default is `pkid`

        :param args: Field list to return
        :param kwargs: Where clause definition, can contain search type of AND or OR
        :return: List of results
        """

        fields = self.parse_fields(args)


        search_type = kwargs.pop('search_type', 'or')  #default to or search

        name = kwargs.pop('name', '')  #see if name option exists

        if name:    #if so then search first, last and nick names

            kwargs['lastname'] = name
            kwargs['firstname'] = name
            kwargs['nickname'] = name

        where = ['{} like "%{}%"'.format(k, v) for k, v in kwargs.items()]

        sql = 'select {} from {} {}{}'.format(','.join(fields), table, 'where ' if where else '', ' {} '.format(search_type).join(where))

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


    def find_name_or_email(self, *args, **kwargs):

        fields = self.parse_fields(*args)

        name = kwargs.pop('name', '')

        name_search = 'and'

        if name:

            kwargs['lastname'] = name
            kwargs['firstname'] = name
            kwargs['nickname'] = name

            name_search = 'or'

        #where =

    def get_cert_rank(self):

        sql = 'select * from cert_rank'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        ranks = {}

        for r in result:

            key = r['organization']

            if key not in ranks:
                ranks[key] = {}

            ranks[key][r['name']] = r['rank']

        return ranks

    def import_bjcp(self):

        #todo:  use strip() to strip any white space from email

        headings = ['firstname', 'lastname', 'address', 'city', 'state', 'zip', 'country', 'phone',
                    'nickname', 'email', 'bjcp_id', 'level', 'region', 'mead', 'cider']

        print(len(headings))
        with open('files/Active Judges.csv') as csv_file:
            csv_reader = reader(csv_file, delimiter=',')
            lines = 0
            for row in csv_reader:
                if lines == 0:
                    print(row)
                sql = 'insert ignore into bjcp_judges ({}) values ("{}")'.format(','.join(headings), '","'.join([x.strip() for x in row]))
                #print(sql)
                db.db_command(sql=sql)
                #print(", ".join(row))
                lines += 1
            print('Number of lines: {}'.format(lines))

if __name__ == '__main__':

    Tools().import_bjcp()
    