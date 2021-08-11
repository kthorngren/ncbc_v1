from datetime import datetime

from Competitions import DATABASE
from Competitions import Competitions
from Sessions import Sessions
from Email import Email
from Tools import Tools


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

    def get_ncbc_email_list(self):

        sql = 'select distinct email from people'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        email_list = [x['email'].lower() for x in result]
        email_list = list(set(email_list))
        print(len(email_list))

        sql = 'select distinct email from ncbc_email_list'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        email_list += [x['email'].lower() for x in result if x['email'].lower() not in email_list]
        print(len(email_list))


        return email_list

    def get_volunteers(self, new=False, changed=False, active=True):

        where = []
        if new:
            where.append('new = "1"')

        elif changed:
            where.append('changed = "1"')

        if active:
            where.append('active = "1"')

        where = ' and '.join(where)

        if where:
            where = '{} and '.format(where)

        sql = 'select * from volunteers where {} fk_competitions = "{}"'.format(where, Competitions().get_active_competition())
        #print(sql)
        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result


    def add_record(self, record):

        success = True
        inserted = False

        sql = 'select pkid, fk_sessions_list from volunteers where firstname = "{d[firstname]}" and ' \
              'lastname = "{d[lastname]}" and email = "{d[email]}" and ' \
              'fk_competitions = "{d[fk_competitions]}"'.format(d=record)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        pkid = 0
        fk_sessions_list = []

        if result:

            pkid = result['pkid']
            fk_sessions_list = result['fk_sessions_list'].split(',')

        #appned new sessions to original sessions
        #fk_sessions is the session PKID from NCBC import if attendee_id
        fk_sessions_list.append(str(record['fk_sessions']))

        #use set to remove duplicates the return a sorted list
        fk_sessions_list = sorted(list(set(fk_sessions_list)))

        del record['fk_sessions']

        record['fk_sessions_list'] = ','.join(fk_sessions_list)

        if pkid:

            record['new'] = 0
            record['changed'] = 1
            update = ['{} = "{}"'.format(k, v) for k, v in record.items()]

            sql = 'update volunteers set {}, updated = NOW() where pkid = "{}"'.format(','.join(update), pkid)

            db.db_command(sql=sql)

            if (db.row_count() > 0):
                logger.info('Updated volunteer {d[firstname]} {d[lastname]} with pkid {pkid}'.format(d=record, pkid=pkid))
                inserted = False
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
                inserted = True
            else:
                logger.error(
                    'Unable to insert volunteer {d[firstname]} {d[lastname]}'.format(d=record))
                success = False

        return success, inserted


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

    def get_judging_location(self, pkid):

        sql = 'select fk_sessions_list from volunteers where pkid = "{}"'.format(pkid)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        #print(result)
        
        fk_sessions = result['fk_sessions_list'].split(',')

        sql = 'select fk_judge_locations from sessions where pkid in ("{}")'.format('","'.join(fk_sessions))

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        fk_locations = [str(x['fk_judge_locations']) for x in result]
        fk_locations = set(fk_locations)

        sql = 'select * from judge_locations where pkid in ("{}")'.format('","'.join(fk_locations))

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)
        
        return result

    def email_confirmation_to_all(self):

        logger.info('Starting process to email all active volunteers')
        result = Volunteers().get_volunteers(active=True)

        errors = []
        email_counter = 0

        if len(result) == 0:
            logger.info('No volunteers to email')
            errors.append('No volunteers to email')
            return {'count': email_counter, 'error': errors}

        e = Email('files/kevin.json')

        for r in result:    

            #if r["email"] != 'kevin.thorngren@gmail.com':
            #    continue

            firstname = r['firstname'].title()
            logger.info(f'Processing {r["firstname"]} {r["lastname"]} - {r["email"]}')

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

            vol_types.append('Judge' if r['judge'] == 1 else 'Steward' if r['judge'] == 0 else 'Staff')

            table += '</tbody>' \
                     '</table>'

            table = '<h3>Volunteer Type: {}</h3>'.format(', '.join(vol_types)) + table

            locations = Volunteers().get_judging_location(pkid=r['pkid'])

            html = f'<h3>Your Competition Location{"s" if len(locations) > 1 else ""}</h3>'
            br = ''
            for l in locations:
                html += (f'{br}{l["name"]}<br>'
                        f'{l["address"]}<br>'
                        f'{l["city"]} {l["state"]} {l["zip"]}<br>'
                )
                br = '<br>'

            msg = 'Hi {firstname},<br/>' \
                  '<br/>' \
                  'Just a quick email with your session information for this weekend.  Please arrive around 8:30 to get checked in.  We plan to start judging at 9:00AM.<br/>' \
                  '<br/>' \
                  'We have 632 entries from 94 brewers this year to judge between the Triangle and Asheville sites.<br/>' \
                  '<br/>' \
                  '{table}' \
                  '<br/>' \
                  '{html}' \
                  '<br/>' \
                  'Please let me know if you have any questions.<br/>' \
                  '<br/>' \
                  'Thanks,<br/>' \
                  'Kevin<br/>'.format(firstname=firstname, table=table, html=html)

            message = e.create_html_message(sender='NC Brewers Cup <kevin.thorngren@gmail.com>',
                                                to=r['email'],
                                                #to='kevin.thorngren@gmail.com',
                                                subject='NC Brewers Cup Final Confirmation',
                                                message_text=msg,
                                                )
            """
            if DATABASE != 'competitions':
                logger.info('Skipping email due to using test DB')
                result = False
            else:
            """
            result = e.send_message(message, rcpt=[r['email']])
            #result = False  # remove this for prod
            #result = e.send_message(message, rcpt=['kevin.thorngren@gmail.com'])


            if result:
                email_counter += 1
            else:
                logger.error('Welcome email not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))
                errors.append('Welcome email not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))

        return {'count': email_counter, 'error': errors}



    def email_new(self):

        logger.info('Starting process to email new volunteers')
        result = Volunteers().get_volunteers(new=True)

        errors = []
        email_counter = 0

        if len(result) == 0:
            logger.info('No new volunteers to email')
            errors.append('No new volunteers to email')
            return {'count': email_counter, 'error': errors}

        e = Email('files/kevin.json')

        for r in result:    

            #if r["email"] != 'kevin.thorngren@gmail.com':
            #    continue

            firstname = r['firstname'].title()
            logger.info(f'Processing {r["firstname"]} {r["lastname"]} - {r["email"]}')
            if r['welcome_email'] == 1:
                logger.error('Volunteer {d[firstname]} {d[lastname]} PKID: {d[pkid]} marked as new but the '
                             'welcome email has been sent - not sending email'.format(d=r))
                errors.append('Volunteer {d[firstname]} {d[lastname]} PKID: {d[pkid]} marked as new but the '
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

            vol_types.append('Judge' if r['judge'] == 1 else 'Steward' if r['judge'] == 0 else 'Staff')

            table += '</tbody>' \
                     '</table>'

            table = '<h3>Volunteer Type: {}</h3>'.format(', '.join(vol_types)) + table

            locations = Volunteers().get_judging_location(pkid=r['pkid'])

            html = f'<h3>Your Competition Location{"s" if len(locations) > 1 else ""}</h3>'
            br = ''
            for l in locations:
                html += (f'{br}{l["name"]}<br>'
                        f'{l["address"]}<br>'
                        f'{l["city"]} {l["state"]} {l["zip"]}<br>'
                )
                br = '<br>'

            msg = 'Hi {firstname},<br/>' \
                  '<br/>' \
                  'Welcome to the NC Brewers Cup Commercial Competition for 2021.  The NC Brewers Guild and I would like to ' \
                  'thank you for volunteering your time.  Below you will find your current schedule.  Please review ' \
                  'it closely to make sure the schedule is correct and your volunteer type (judge/steward) is correct.<br/>' \
                  '<br/>' \
                  'Once we get closer to the competition I will send a last confirmation email with more logistic ' \
                  'information.  <br/>' \
                  '<br/>' \
                  '{table}' \
                  '<br/>' \
                  '{html}' \
                  '<br/>' \
                  'Please let me know if you have any questions.<br/>' \
                  '<br/>' \
                  'Thanks,<br/>' \
                  'Kevin<br/>'.format(firstname=firstname, table=table, html=html)

            message = e.create_html_message(sender='NC Brewers Cup <kevin.thorngren@gmail.com>',
                                                to=r['email'],
                                                #to='kevin.thorngren@gmail.com',
                                                subject='NC Brewers Cup Welcome',
                                                message_text=msg,
                                                )
            """
            if DATABASE != 'competitions':
                logger.info('Skipping email due to using test DB')
                result = False
            else:
            """
            result = e.send_message(message, rcpt=[r['email']])
            #result = False  # remove this for prod
            #result = e.send_message(message, rcpt=['kevin.thorngren@gmail.com'])


            if result:
                sql = 'update volunteers set welcome_email = "1", new = "0", changed = "0" where pkid = "{}"'.format(r['pkid'])
                db.db_command(sql=sql)
                email_counter += 1
            else:
                logger.error('Welcome email not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))
                errors.append('Welcome email not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))

        return {'count': email_counter, 'error': errors}


    def email_changed(self):

        errors = []
        email_counter = 0

        result = Volunteers().get_volunteers(changed=True)

        if len(result) == 0:
            logger.info('No changed volunteers to email')
            errors.append('No changed volunteers to email')
            return {'count': email_counter, 'error': errors}

        e = Email('files/kevin.json')

        #result = [] # remove for prod
        for r in result:
            if r['new'] == 1 and r['welcome_email'] == 0:
                logger.error('Skipping New entry for {d[firstname]} {d[lastname]}, PKID: {d[pkid]} because the Welcome Email '
                             'has not been sent'.format(d=r))
                errors.append('Skipping New entry for {d[firstname]} {d[lastname]}, PKID: {d[pkid]} because the Welcome Email '
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

            vol_types.append('Judge' if r['judge'] == 1 else 'Steward' if r['judge'] == 0 else 'Staff')

            table += '</tbody>' \
                     '</table>'

            table = '<h3>Volunteer Type: {}</h3>'.format(', '.join(vol_types)) + table

            locations = Volunteers().get_judging_location(pkid=r['pkid'])

            html = f'<h3>Your Competition Location{"s" if len(locations) > 1 else ""}</h3>'
            br = ''
            for l in locations:
                html += (f'{br}{l["name"]}<br>'
                        f'{l["address"]}<br>'
                        f'{l["city"]} {l["state"]} {l["zip"]}<br>'
                )
                br = '<br>'
                
            msg = 'Hi {firstname},<br/>' \
                  '<br/>' \
                  'Here is your updated registration information.  Please let me know if ' \
                  'there are any changes to make.<br/>' \
                  '<br/>' \
                  '{table}<br/>' \
                  '{html}' \
                  '<br/>' \
                  'Please let me know if you have any questions.<br/>' \
                  '<br/>' \
                  'Thanks,<br/>' \
                  'Kevin<br/>'.format(firstname=firstname, table=table, html=html)

            message = e.create_html_message(sender='NC Brewers Cup <kevin.thorngren@gmail.com>',
                                                to=r['email'],
                                                #to='kevin.thorngren@gmail.com',
                                                subject='NC Brewers Cup Schedule Change Confirmation',
                                                message_text=msg,
                                                )
            """
            if DATABASE != 'competitions':
                logger.info('Skipping email due to using test DB')
                result = False
            else:
            """
            result = e.send_message(message, rcpt=[r['email']])
            #result = False  # remove this for prod
            #result = e.send_message(message, rcpt=['kevin.thorngren@gmail.com'])



            if result:
                sql = 'update volunteers set new = "0", changed = "0" where pkid = "{}"'.format(r['pkid'])
                db.db_command(sql=sql)
                email_counter += 1
            else:
                logger.error('Session change email not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))
                errors.append('Session change not sent to {d[firstname]} {d[lastname]}, pkid: {d[pkid]}'.format(d=r))

        return {'count': email_counter, 'error': errors}


    def find_volunteer_entries(self):

        judging_sessions = [str(x['pkid']) for x in Sessions().get_sessions(judging=True)]

        

        #print(judging_sessions)

        sql = 'select b.pkid, b.firstname, b.lastname, b.email, b.organization, v.pkid as vol_pkid, ' \
              'v.firstname as vol_firstname, v.lastname as vol_lastname, v.email as vol_email, ' \
              'v.organization as vol_organization, v.fk_brewers as fk_brewers, v.fk_sessions_list ' \
              'from brewers as b join volunteers as v on v.lastname like CONCAT( "%", b.lastname, "%") ' \
              'or (SUBSTRING_INDEX(v.email,"@",-1) like CONCAT( "%",SUBSTRING_INDEX(b.email,"@",-1), "%") ' \
              '  and SUBSTRING_INDEX(v.email,"@",-1) <> "gmail.com")' \
              'or v.organization like CONCAT( "%",b.organization,"%") ' \
              'or (v.organization != "" and b.organization like CONCAT( "%",v.organization,"%") )' \
              'or v.fk_brewers = b.pkid'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)
        #print(sql)

        for r in result:
            fk_sessions_list = r['fk_sessions_list'].split(',')
            #print('fk_sessions_list', fk_sessions_list)

            for fk in fk_sessions_list:

                #print(fk)

                if fk in judging_sessions:
                    location = Sessions().get_judge_location_by_session(fk)

                    if location:
                        r['location'] = location['city']
                    else:
                        r['location'] = 'Unknown'

        return result



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


def test_get_locations(pkid):

    result = Volunteers().get_judging_location(pkid=pkid)

    print(result)


def test_find_person():

    vol = Volunteers().get_volunteers()

    for v in vol:
        fk_people = v['fk_people']
        firstname = v['firstname']
        lastname = v['lastname']
        email = v['email']
        phone = v['phone']
        logger.info('')
        logger.info(f"{firstname} {lastname} ({email}) has fk_people {fk_people}")
        people = Tools().find('people', ['firstname', 'lastname', 'nickname', 'alias', 'email'], name=lastname, email=email)

        if fk_people == 0 and len(people) == 0:
            logger.info(f'  Adding person {firstname} {lastname}')

            sql = f'insert into people (firstname, lastname, email, phone, updated) values ("{firstname}","{lastname}","{email}","{phone}",NOW())'
            db.db_command(sql=sql)

            if (db.row_count() > 0):
                logger.info(f'  Inserted person {firstname} {lastname}')
                # Get inserted person for next step - to obtain the pkid.
                people = Tools().find('people', ['firstname', 'lastname', 'nickname', 'alias', 'email'], email=email)
            else:
                logger.error(f'  *** Unable to insert person {firstname} {lastname} ***')

        num_people_options = len(people)
        if fk_people == 0 and num_people_options == 0:
            logger.error('  *** Unable to find match in people for volunteer ***')
            continue

        if fk_people == 0:
            exact_match = False
            # If one people in list then check to see if its an exact match .
            # if exact update the volunteer's fk_people id.
            if num_people_options == 1:
                person = people[0]

                if (person['firstname'] == v['firstname'] or person['nickname'] == v['firstname'])  \
                        and person['lastname'] == v['lastname'] and person['email'] == v['email']:
                    exact_match = True
                    logger.info(f'  Matched firstname, lastname and email, updating fk_people to {person["pkid"]}')
                    sql = f'update volunteers set fk_people = {person["pkid"]}, updated = NOW() where pkid = "{v["pkid"]}"'
                    db.db_command(sql=sql)

                    if (db.row_count() > 0):
                        logger.info(f'  Updated volunteer {firstname} {lastname} with pkid {v["pkid"]}')
                    else:
                        logger.error(f'  *** Unable to update volunteer {firstname} {lastname} with pkid {v["pkid"]} ***')

            if not exact_match:

                pkid_list = []
                for p in people:
                    #print(f'  {p}')
                    pkid_list.append(int(p['pkid']))

                pkid_choice = ''
                try:
                    pkid_choice = input('Please choose person using pkid or type "new" for new person: ')
                    
                except Exception as e:
                    pkid_choice = ''

                if pkid_choice == '':
                    logger.info('  No selection made')
                    continue

                try:
                    pkid_choice = int(pkid_choice)
                except:
                    pass

                if isinstance(pkid_choice, str):

                    if pkid_choice.lower() == 'new':
                        logger.info(f'  Adding person {firstname} {lastname}')

                        sql = f'insert into people (firstname, lastname, email, phone, updated) values ("{firstname}","{lastname}","{email}","{phone}",NOW())'
                        db.db_command(sql=sql)

                        if (db.row_count() > 0):
                            logger.info(f'  Inserted person {firstname} {lastname}')
                            # Get inserted person for next step - to obtain the pkid.
                            people = Tools().find('people', ['firstname', 'lastname', 'nickname', 'alias', 'email'], email=email)
                            person = people[0]
                            sql = f'update volunteers set fk_people = {person["pkid"]}, updated = NOW() where pkid = "{v["pkid"]}"'
                            db.db_command(sql=sql)

                            if (db.row_count() > 0):
                                logger.info(f'  Updated volunteer {firstname} {lastname} with fk_people {person["pkid"]}')
                            else:
                                logger.error(f'  *** Unable to update volunteer {firstname} {lastname} with pkid {v["pkid"]} ***')

                        else:
                            logger.error(f'  *** Unable to insert person {firstname} {lastname} ***')

                else:
                    
                    
                    if pkid_choice not in pkid_list:
                        logger.error(f'  Invalid select made: {pkid_choice}')
                        continue

                    person = people[pkid_list.index(pkid_choice)]
                    logger.info(f'  Selected {person["pkid"]} for {firstname}, {lastname} and {email}, updating fk_people to {person["pkid"]}')


                    sql = f'update volunteers set fk_people = {person["pkid"]}, updated = NOW() where pkid = "{v["pkid"]}"'
                    db.db_command(sql=sql)

                    if (db.row_count() > 0):
                        logger.info(f'  Updated volunteer {firstname} {lastname} with pkid {v["pkid"]}')
                    else:
                        logger.error(f'  *** Unable to update volunteer {firstname} {lastname} with pkid {v["pkid"]} ***')

                    person_email = person['email']

                    set_email = ''
                    if person_email != email:

                        choice = ''
                        try:
                            choice = input('Email addresses don\'t match, do you want to update (y/n) ')
                        except Exception as e:
                            choice = 'n'

                        if choice == 'y':
                            set_email = f'email = "{email}"'
                        else:
                            set_email = ''

                    if set_email:
                        sql = f'update people set {set_email}, updated = NOW() where pkid = "{person["pkid"]}"'
                        db.db_command(sql=sql)
                        print(sql)
                        if (db.row_count() > 0):
                            logger.info(f'  Updated person email for {firstname} {lastname} with new email {email}')
                        else:
                            logger.error(f'  *** Unable to update person email for {firstname} {lastname} with pkid {person["pkid"]} ***')

                    
                    

                    

if __name__ == '__main__':


    #print(Volunteers().get_ncbc_email_list())
    #test_get_sessions()

    #test_remove_dup_sessions()

    #email_new()

    #email_changed()

    test_get_locations(pkid=10)

    #test_find_person()

    #Volunteers().email_confirmation_to_all()
    pass
