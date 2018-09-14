from datetime import datetime

from Competitions import DATABASE
from Competitions import Competitions
from Sessions import Sessions
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

db = Database(local_host['host'], local_host['user'], local_host['password'], DATABASE)


class Volunteers:

    def __init__(self):

        pass

    def get_volunteers(self, new=False, changed=False):

        where = []
        if new:
            where.append('new = "1"')

        if changed:
            where.append('changed = "1"')

        where = ' or '.join(where)

        if where:
            where = '{} and '.format(where)

        sql = 'select * from volunteers where {} fk_competitions = "{}"'.format(where, Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


    def add_record(self, record):

        success = True

        sql = 'select pkid, fk_sessions_list from volunteers where email = "{d[email]}" and ' \
              'fk_competitions = "{d[fk_competitions]}"'.format(d=record)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        pkid = 0
        fk_sessions_list = []

        if result:

            pkid = result['pkid']
            fk_sessions_list = result['fk_sessions_list'].split(',')

        fk_sessions_list.append(str(record['fk_sessions']))

        del record['fk_sessions']

        record['fk_sessions_list'] = ','.join(fk_sessions_list)

        if pkid:

            update = ['{} = "{}"'.format(k, v) for k, v in record.items()]

            sql = 'update volunteers set {}, updated = NOW() where pkid = "{}"'.format(','.join(update), pkid)

            db.db_command(sql=sql)

            if (db.row_count() > 0):
                logger.info('Updated volunteer {d[firstname]} {d[lastname]} with pkid {pkid}'.format(d=record, pkid=pkid))
            else:
                logger.error('Unable to update volunteer {d[firstname]} {d[lastname]} with pkid {pkid}'.format(d=record, pkid=pkid))
                success = False

        else:

            fields = []
            values = []

            for k, v in record.items():
                fields.append(str(k))
                values.append(str(v))

            sql = 'insert into volunteers ({}, updated) values ("{}", NOW())'.format(','.join(fields), '","'.join(values))
            db.db_command(sql=sql)

            if (db.row_count() > 0):
                logger.info('Insert volunteer {d[firstname]} {d[lastname]}'.format(d=record))
            else:
                logger.error(
                    'Unable to insert volunteer {d[firstname]} {d[lastname]}'.format(d=record))
                success = False

        return success


    def remove_duplicate_sessions(self):

        logger.info('Checking for duplicate sessions for all volunteers')

        sql = 'select pkid, firstname, lastname, fk_sessions_list ' \
              'from volunteers where fk_competitions = "{}"'.format(Competitions().get_active_competition())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        for r in result:
            sessions = r['fk_sessions_list'].split(',')

            sessions_check = list(set(sessions))

            #do nothing if the lnegths are the same - no duplicates
            if len(sessions) == len(sessions_check):
                continue

            logger.info('Removing duplicate sessions for {d[firstname]} {d[lastname]}'.format(d=r))

            sql = 'update volunteers set fk_sessions_list = "{}" ' \
                  'where pkid = "{}"'.format(','.join(sorted(sessions_check)), r['pkid'])

            db.db_command(sql=sql)



    def get_sessions(self, pkid):

        sql = 'select firstname, lastname, email, fk_sessions_list from volunteers where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        if result:

            Sessions().get_fk_sessions(result['fk_sessions_list'].split(','))


    def email_new(self):
        result = Volunteers().get_volunteers(new=True)
        if len(result) == 0:
            logger.info('No new volunteers to email')
            return

        e = Email('files/kevin.json')

        for r in result:

            firstname = r['firstname'].title()

            if r['welcome_email'] == 1:
                logger.error('Volunteer {d[firstname]} {d[lastname]} PKID: {d[pkid]} marked as new but the '
                             'welcome email has been sent - not sending email'.format(d=r))
                continue
            sessions = Sessions().get_fk_sessions(r['fk_sessions_list'])

            vol_types = []
            comments = ''


            table = '<table border="1" style="border-collapse:collapse" cellpadding="2" >' \
                     '<thead>' \
                     '<tr>' \
                     '<th>Session</th>' \
                     '<th>Start</th>' \
                     '<th>End</th>' \
                     '<th>Comments</th>' \
                     '</tr>' \
                     '</thead>' \
                     '<tbody>'

            for session in sessions:

                if session['setup'] == 1:
                    if 'Setup' not in vol_types:
                        vol_types.append('Setup')
                    comments = ''
                elif 'AM' in session['name']:
                    comments = 'Light breakfast'
                elif 'PM' in session['name']:
                    comments = 'Lunch'

                session['session_start'] = session['session_start'].strftime('%m-%d-%Y %H:%M:%S')
                session['session_end'] = session['session_end'].strftime('%m-%d-%Y %H:%M:%S')

                table += '<tr>' \
                    '<td>{d[name]}</td>' \
                    '<td>{d[session_start]}</td>' \
                    '<td>{d[session_end]}</td>' \
                    '<td>{comments}</td>' \
                    '</tr>'.format(d=session, comments=comments)

            vol_types.append('Judge' if r['judge'] == 1 else 'Steward')

            table += '</tbody>' \
                     '</table>'

            table = '<h3>Volunteer Type: {}</h3>'.format(', '.join(vol_types)) + table

            msg = 'Hi {firstname},<br/>' \
                  '<br/>' \
                  'Welcome to the NC Brewers Cup Commercial Competition for 2018.  The NC Brewers Guild and I would like to ' \
                  'thank you for volunteering your time.  Below you will find your current schedule.  Please review ' \
                  'it closely to make sure the schedule is correct and your volunteer type (judge/steward) is correct.  ' \
                  'We used a new volunteer registration system and it is not the most intuitive system to use.  ' \
                  'If it is inaccurate or you need to make other changes please let me know.<br/>' \
                  '<br/>' \
                  'Once we get closer to the competition I will send a last confirmation email with more logistic ' \
                  'information.  <br/>' \
                  '<br/>' \
                  '{table}<br/>' \
                  '<br/>' \
                  'Please let me know if you have any questions.<br/>' \
                  '<br/>' \
                  'Thanks,<br/>' \
                  'Kevin<br/>'.format(firstname=firstname, table=table)

            message = e.create_html_message('NC Brewers Cup <kevin.thorngren@gmail.com>',
                                            r['email'],
                                                       'NC Brewers Cup Welcome',
                                                       msg,
                                                       )
            if DATABASE != 'competitions':
                logger.info('Skipping email due to using test DB')
                result = False
            else:
                result = e.send_message(message)


            if result:
                sql = 'update volunteers set welcome_email = "1", new = "0", changed = "0" where pkid = "{}"'.format(r['pkid'])
                db.db_command(sql=sql)
            else:
                logger.error('Welcome email not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))


    def email_changed(self):

        result = Volunteers().get_volunteers(new=True, changed=True)

        if len(result) == 0:
            logger.info('No changed volunteers to email')
            return

        e = Email('files/kevin.json')

        for r in result:
            if r['new'] == 1 and r['welcome_email'] == 0:
                logger.error('Skipping New entry for {d[firstname]} {d[lastname]}, PKID: {d[pkid]} because the Welcome Email '
                             'has not been sent'.format(d=r))
                continue

            firstname = r['firstname'].title()

            sessions = Sessions().get_fk_sessions(r['fk_sessions_list'])

            vol_types = []
            comments = ''


            table = '<table border="1" style="border-collapse:collapse" cellpadding="2" >' \
                     '<thead>' \
                     '<tr>' \
                     '<th>Session</th>' \
                     '<th>Start</th>' \
                     '<th>End</th>' \
                     '<th>Comments</th>' \
                     '</tr>' \
                     '</thead>' \
                     '<tbody>'

            for session in sessions:

                if session['setup'] == 1:
                    if 'Setup' not in vol_types:
                        vol_types.append('Setup')
                    comments = ''
                elif 'AM' in session['name']:
                    comments = 'Light breakfast'
                elif 'PM' in session['name']:
                    comments = 'Lunch'

                session['session_start'] = session['session_start'].strftime('%m-%d-%Y %H:%M:%S')
                session['session_end'] = session['session_end'].strftime('%m-%d-%Y %H:%M:%S')

                table += '<tr>' \
                    '<td>{d[name]}</td>' \
                    '<td>{d[session_start]}</td>' \
                    '<td>{d[session_end]}</td>' \
                    '<td>{comments}</td>' \
                    '</tr>'.format(d=session, comments=comments)

            vol_types.append('Judge' if r['judge'] == 1 else 'Steward')

            table += '</tbody>' \
                     '</table>'

            table = '<h3>Volunteer Type: {}</h3>'.format(', '.join(vol_types)) + table

            msg = 'Hi {firstname},<br/>' \
                  '<br/>' \
                  'Here is your updated registration information.  Please let me know if ' \
                  'there are any changes to make.<br/>' \
                  '<br/>' \
                  '{table}<br/>' \
                  '<br/>' \
                  'Please let me know if you have any questions.<br/>' \
                  '<br/>' \
                  'Thanks,<br/>' \
                  'Kevin<br/>'.format(firstname=firstname, table=table)

            message = e.create_html_message('NC Brewers Cup <kevin.thorngren@gmail.com>',
                                            r['email'],
                                                       'NC Brewers Cup Schedule Change Confirmation',
                                                       msg,
                                                       )
            if DATABASE != 'competitions':
                logger.info('Skipping email due to using test DB')
                result = False
            else:
                result = e.send_message(message)


            if result:
                sql = 'update volunteers set new = "0", changed = "0" where pkid = "{}"'.format(r['pkid'])
                db.db_command(sql=sql)
            else:
                logger.error('Welcome email not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))





def test_get_sessions():

    result = Volunteers().get_volunteers()

    count = 0

    for r in result:
        print(r['firstname'], r['lastname'])
        sessions = Sessions().get_fk_sessions(r['fk_sessions_list'])

        for s in sessions:
            count += 1
            print(s)

    print('Total Volunteers: {}'.format(len(result)))
    print('Total session registratin count: {}'.format(count))


def test_remove_dup_sessions():

    Volunteers().remove_duplicate_sessions()


if __name__ == '__main__':

    #test_get_sessions()

    test_remove_dup_sessions()

    #email_new()

    #email_changed()
    pass
