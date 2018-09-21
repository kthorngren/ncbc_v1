from Tools import Tools
from Sessions import Sessions
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


class Flights:

    def __init__(self):

        pass


    def auto_assign_judges(self, session_number):

        BJCP_MULTIPLIER = 2  #because BJCP judges are just better ;-)

        result = self.get_judges_for_session(session_number)
        ranks = Tools().get_cert_rank()

        #calculate ranking for all judges in session
        for r in result:

            r['rank'] = 0

            if r['bjcp_rank']:
                r['rank'] += ranks['BJCP'][r['bjcp_rank']] * BJCP_MULTIPLIER

            if r['cicerone']:
                r['rank'] += ranks['Cicerone'][r['cicerone']]

            if r['other_cert']:
                r['rank'] += ranks['Other'][r['other_cert']]

            r['rank'] += r['ncbc_points']

        #get reverse ordered list of judges by the ranking
        judges = [x for x in sorted(result, key=lambda k: k['rank'], reverse=True)]

        # split the judges in half
        half = len(judges) // 2
        head_judges = judges[:half]
        judges = judges[half:]

        pairing = []

        while head_judges:

            #get head judge pkid and don't pair list
            hj = head_judges.pop()
            hj_pkid = str(hj['pkid'])
            hj_dont_pair = hj['dont_pair'].split(',')

            #postion of match in judges list
            position = 0

            for judge in judges:
                #get judges don't pair list
                j_dont_pair = judge['dont_pair'].split(',') if judge['dont_pair'] else ''

                #if head judge pkid not in judge do not pair with and
                #judge pkid not in head judge do not pair with then pair the judges
                if hj_pkid not in j_dont_pair and str(judge['pkid']) not in hj_dont_pair:
                    pairing.append([hj, judge])
                    break

                #otherwise go to the next position in the judges list
                position += 1

            #if position count is = len of judges list then didn't match head judge, add to the list without judging mate
            if position >= len(judges):
                pairing.append([hj, {}])

            #if matched then remove the judge from the list
            else:
                judges.pop(position)


        return {'pairing': pairing, 'judges': judges}


    def get_judges_for_session(self, session_number):

        result = Sessions().get_session_volunteers(session_number, judges=True)

        session_list = Sessions().get_daily_pkids(session_number)

        for r in result:

            count = 0
            judge_sessions = r['fk_sessions_list'].split(',')

            for s in session_list:

                count += judge_sessions.count(str(s))

            r['total_day'] = count
            r['total_sessions'] = len(judge_sessions)

        return result


    def get_session_pairing(self, session_number):

        sql = 'select * from judge_pairing where fk_sessions = "{}" ' \
              ''.format(session_number)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


if __name__ == '__main__':


    result = Flights().auto_assign_judges(89)

    for p in result['pairing']:
        print(p)

    print('remaining', result['judges'])



    pass