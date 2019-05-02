import os
from competition import get_logger, set_log_level
logger = get_logger(os.path.basename(__file__).split('.')[0])

#set_log_level(logger, 'info')

from utils import MySql
from utils import DATABASE, CONN

db = MySql(**CONN, db=DATABASE)

class Competitions:

    def __init__(self):

        logger.info('Competitions init')
        self.pkid = 0

    def get_active_competition(self):
        """Returns active competition pkid"""
        sql = 'select pkid from competitions where active = "1"'
        logger.info(sql)
        result = db.run_sql(sql=sql, get='one')

        self.pkid = result.get('pkid', 0)
        return self.pkid

    def get_name(self, pkid):
        sql = 'select name from competitions where pkid = "{}"'.format(pkid)
        result = db.run_sql(sql=sql, get='one')

        return result.get('name', '')

    def get_style_guidelines(self):

        sql = 'select style_guidelines from competitions where active = "1"'
        result = db.run_sql(sql=sql, get='one')

        return result.get('style_guidelines', '')


    def get_categories(self):

        sql = 'select fk_categories_list from competitions where active = "1"'
        result = db.run_sql(sql=sql, get='one')

        return result.get('fk_categories_list', '')

    def get_comp_status(self):

        status = {'entries': {}, 'sessions': []}

        sql = 'select count(*) as brewers from brewers where fk_competitions = "{}"'.format(self.get_active_competition())
        result = db.run_sql(sql=sql, get='one')

        status['entries']['brewers'] = result.get('brewers', 0)


        sql = 'select sum(fk_competitions = "{pkid}") as entries, sum(inventory = "1") as checked_in, ' \
              'sum(judged = "1") as judged ' \
              'from entries where fk_competitions = "{pkid}"'.format(pkid=self.get_active_competition())
        result = db.run_sql(sql=sql, get='one')

        status['entries']['entries'] = int(result.get('entries', 0))
        status['entries']['checked_in'] = int(result.get('checked_in', 0))
        status['entries']['judged'] = int(result.get('judged', 0))
        status['entries']['remaining'] = int(result.get('checked_in', 0)) - int(result.get('judged', 0))


        sql = 'select * from sessions where judging = "1" or setup = "1" and ' \
              'fk_competitions = "{}" '.format(self.get_active_competition())
        sessions = db.run_sql(sql=sql, get='all')

        sql = 'select fk_sessions_list, is_judge from volunteers where fk_competitions = "{}"'.format(self.get_active_competition())
        result = db.run_sql(sql=sql, get='all')

        sessions_list = {0: [], 1 : [], 2: []}  # 0=steward, 1=judge, 2=unknown
        for r in result:
            sessions_list[r['is_judge']] += [int(x) for x in r['fk_sessions_list'].split(',')]

        for r in sorted(sessions, key = lambda k:k['session_number']):

            session_type = []
            if r['setup'] == 1:
                session_type.append('Setup')
            if r['judging'] == 1:
                session_type.append('Judging')


            status['sessions'].append({
                'name': r['name'],
                'type': '/'.join(session_type),
                'stewards': sessions_list[0].count(r['pkid']),
                'judges': sessions_list[1].count(r['pkid']),
                'other': sessions_list[2].count(r['pkid']),
            })


        return status

if __name__ == '__main__':

    pass
