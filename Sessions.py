import json

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

    def get_judge_location(self, fk_judge_locations):

        sql = f'select * from judge_locations where pkid = "{fk_judge_locations}"'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result

    def get_session_volunteers(self, session_number, judges=False, stewards=False, all=False):

        where = ''

        if stewards and not judges:
            where = 'and judge = "0"'
        elif judges and not stewards:
            where = 'and judge = "1"'

        if not all:
            where += ' and active = "1" '

        sql = 'select volunteers.firstname, volunteers.lastname, volunteers.fk_sessions_list, volunteers.fk_brewers, ' \
              'p.bjcp_id, p.bjcp_rank, p.cicerone, ' \
                'p.ncbc_points, p.dont_pair, p.speed, p.other_cert, p.pkid, p.likes, p.dislikes ' \
                'from volunteers '\
                'left join people as p on p.pkid = fk_people ' \
                'where find_in_set("{session_number}", cast(fk_sessions_list as char)) > 0 ' \
                'and deleted = "0" and fk_competitions = "{pkid}" {where}'.format(session_number=session_number,
                                                                pkid=Competitions().get_active_competition(),
                                                                where=where
                                                                )
        print(sql)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


    def save_session_pairs(self, session_pairs):

        result = False

        fk_sessions = session_pairs.get('fk_sessions', 0)

        if fk_sessions:

            data = {}

            data['judges'] = escape_sql(json.dumps(session_pairs.get('judges', '')))
            data['head_judge'] = escape_sql(json.dumps(session_pairs.get('hj_judges', '')))
            data['second_judge'] = escape_sql(json.dumps(session_pairs.get('sj_judges', '')))

            print('session pairs', data)

            sql = 'insert ignore into judge_pairing (fk_sessions, judges, head_judge, second_judge) values ' \
            ' ("{}", "", "", "") '.format(fk_sessions)
            db.db_command(sql=sql)

            result = False if db.sql_error else True

            if result:
                sql = 'update judge_pairing set judges = "{d[judges]}", head_judge = "{d[head_judge]}", ' \
                      'second_judge = "{d[second_judge]}" where fk_sessions = "{fk_sessions}"'.format(d=data,
                                                                                                       fk_sessions=fk_sessions
                                                                                                       )
                db.db_command(sql=sql)


            result = False if db.sql_error else True

        return result

    def get_daily_pkids(self, session_number):

        sql = 'select pkid from sessions where day = ' \
              '(select day from sessions ' \
              'where pkid = "{}" and fk_competitions = "{}")'.format(session_number, Competitions().get_active_competition())
        print(sql)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        session_list = []

        for r in result:
            session_list.append(r['pkid'])

        return session_list


def get_session_mapping():

    ncbc_db = Database(local_host['host'], local_host['user'], local_host['password'], 'ncbc-data-2020')

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

    result = Sessions().get_session_volunteers(98, judges=True)
    for r in result:
        print(r)

    pass
