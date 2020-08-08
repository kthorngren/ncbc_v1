

DATABASE = ''
#https://gist.github.com/igniteflow/1760854
try:
    # use the develop database if we are using develop
    import os
    from git import Repo
    repo = Repo(os.getcwd())
    branch = repo.active_branch
    branch = branch.name
    if branch == 'master':
        DATABASE = 'ncbc-2020'
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


    def get_categories(self):

        sql = 'select fk_categories_list from competitions where active = "1"'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('fk_categories_list', '')


    def name(self, pkid):
        sql = 'select name from competitions where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('name', '')

    def get_session_volunteers(self, session_number, judges=False, stewards=False, other=False, all=False):
        """Copied from Sessions.py as Session cant be imported"""
        where = ''

        if stewards and not judges:
            where = 'and judge = "0"'
        elif judges and not stewards:
            where = 'and judge = "1"'
        elif other and not judges and not stewards:
            where = 'and judge > "1"'

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

    def get_comp_status(self):

        status = {'entries': {}, 'sessions': []}

        sql = 'select count(*) as brewers from brewers where fk_competitions = "{}"'.format(self.get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        status['entries']['brewers'] = result.get('brewers', 0)

        sql = 'select sum(fk_competitions = "{pkid}") as entries, sum(inventory = "1") as checked_in, ' \
              'sum(judged = "1") as judged ' \
              'from entries where fk_competitions = "{pkid}"'.format(pkid=self.get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)
        logger.info(result)

        entries = result.get('entries', 0)
        entries = 0 if entries is None else int(entries)
        checked_in = result.get('checked_in', 0)
        checked_in = 0 if checked_in is None else int(checked_in)
        judged = result.get('judged', 0)
        judged = 0 if judged is None else int(judged)


        status['entries']['entries'] = entries
        status['entries']['checked_in'] = checked_in
        status['entries']['judged'] = judged
        status['entries']['remaining'] = checked_in - judged


        sql = 'select * from sessions where (judging = "1" or setup = "1") and ' \
              'fk_competitions = "{}" '.format(self.get_active_competition())

        uid = gen_uid()
        sessions = db.db_command(sql=sql, uid=uid).all(uid)

        sql = 'select fk_sessions_list, judge from volunteers where active="1" and fk_competitions = "{}"'.format(self.get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)
        #print('reslt', result)
        sessions_list = {0: [], 1 : [], 2: []}
        for r in result:
            #print(r)
            #print(r['fk_sessions_list'].split(','))
            sessions_list[r['judge']] += [int(x) for x in r['fk_sessions_list'].split(',')]

        #print('sessions_list', sessions_list)

        num_judges = 0

        for r in sorted(sessions, key = lambda k:k['session_number']):

            session_type = []
            if r['setup'] == 1:
                session_type.append('Setup')
            if r['judging'] == 1:
                session_type.append('Judging')

            #print(r['pkid'], sessions_list[1].count(r['pkid']))
            #print(sessions_list[1])


            session_judges = self.get_session_volunteers(r['pkid'], judges=True)
            session_stewards = self.get_session_volunteers(r['pkid'], stewards=True)
            session_other = self.get_session_volunteers(r['pkid'], other=True)

            status['sessions'].append({
                'name': r['name'],
                'type': '/'.join(session_type),
                'stewards': len(session_stewards), #sessions_list[0].count(r['pkid']),
                'judges': len(session_judges), #sessions_list[1].count(r['pkid']),
                'other': len(session_other), #sessions_list[2].count(r['pkid']),
                'session_judges': session_judges,
                'session_stewards': session_stewards,
                'session_other': session_other
            })

        judge_sessions = sessions_list[1]

        set_sessions = set(judge_sessions)

        for s in set_sessions:
            judge_count = judge_sessions.count(s)
            print('*** ', judge_count)
            if judge_count % 2 == 1:
                judge_count -= 1
            num_judges += judge_count


        status['entries']['average'] = round(entries / (num_judges / 2))
        print(status['entries']['average'] )

        #for s in status['sessions']:
        #    print(s)


        return status


    def validate_ncbc_data(self, entries_report_pkid=0, volunteers_report_pkid=1):

        if entries_report_pkid:

            sql = 'update entries set ncbc_validation = "0" where fk_competitions = "{}"'.format(self.get_active_competition())
            db.db_command(sql=sql)

            from ncbc import Ncbc

            n = Ncbc(pkid=entries_report_pkid)
            n.get_csv_2()

            print(n.header)


if __name__ == '__main__':

    c = Competitions()

    #name = c.get_active_competition()

    result = c.get_comp_status()

    #print(result)

    #Competitions().validate_ncbc_data(entries_report_pkid=1)

    pass
