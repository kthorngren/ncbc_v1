

DATABASE = ''
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


from Styles import Style
from Email import Email

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

logger.info('Starting competition using database: {}'.format(DATABASE))
db = Database(local_host['host'], local_host['user'], local_host['password'], DATABASE)



class Competitions:

    def __init__(self):

        self.pkid = 0

    def get_active_competition(self):

        sql = 'select pkid from competitions where active = "1"'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        self.pkid = result.get('pkid', 0)

        return self.pkid

    def get_style_guidelines(self):

        sql = 'select style_guidelines from competitions where active = "1"'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('style_guidelines', '')

    def name(self, pkid):
        sql = 'select name from competitions where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('name', '')


if __name__ == '__main__':

    c = Competitions()

    name = c.get_active_competition()


    print(name)

    pass
