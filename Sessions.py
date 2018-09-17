from Tools import Tools
from Competitions import DATABASE
from Competitions import Competitions


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


class Sessions:

    def __init__(self):

        pass

    def get_sessions(self, setup=False, judging=False, bos=False):
        """
        Get sessions based on session types

        :param setup: Get setup sessions
        :param judging: Get judging sessions
        :param bos: Get BOS sessions
        :return: list of sessions
        """
        where = []

        if setup:
            where.append('setup = "1"')
        if judging:
            where.append('judging = "1"')
        if bos:
            where.append('bos = "1"')


        where = ' or '.join(where)

        sql = 'select * from sessions where {} and ' \
              'fk_competitions = "{}"'.format(where, Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result

    def get_session_by_number(self, session_number):

        sql = 'select * from sessions where session_number = "{}" and ' \
              'fk_competitions = "{}"'.format(session_number, Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result

    def get_fk_sessions(self, fk_sessions_list):

        if type(fk_sessions_list) != type([]):
            fk_sessions_list = fk_sessions_list.split(',')

        sql = 'select * from sessions where pkid in ("{}") order by session_number'.format('","'.join(fk_sessions_list))

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result

    def get_session_volunteers(self, session_number, judges=False, stewards=False):

        where = ''

        if stewards and not judges:
            where = 'and judge = "0"'
        elif judges and not stewards:
            where = 'and judge = "1"'

        sql = 'select volunteers.firstname, volunteers.lastname, p.bjcp_id, p.bjcp_rank, p.cicerone, ' \
                'p.ncbc_points, p.dont_pair, p.speed, p.other_cert, p.pkid ' \
                'from volunteers '\
                'inner join people as p on p.pkid = fk_people ' \
                'where find_in_set("{session_number}", cast(fk_sessions_list as char)) > 0 ' \
                'and fk_competitions = "{pkid}" {where}'.format(session_number=session_number,
                                                                pkid=Competitions().get_active_competition(),
                                                                where=where
                                                                )

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


def get_session_mapping():

    ncbc_db = Database(local_host['host'], local_host['user'], local_host['password'], 'ncbc_data')

    sql = 'select * from session_mapping where fk_competitions = "{}"'.format(Competitions().get_active_competition())

    uid = gen_uid()
    result = ncbc_db.db_command(sql=sql, uid=uid).all(uid)

    return result

if __name__ == '__main__':

    #result = Sessions().get_sessions(judging=True)

    #result = get_session_mapping()

    #for r in result:
    #    session = Sessions().get_session_by_number(r['session_number'])

    #    print(session)


    pass
