import os
from competition import get_logger, set_log_level
logger = get_logger(os.path.basename(__file__).split('.')[0])

#set_log_level(logger, 'info')

from utils import MySql
from utils import DATABASE, CONN

db = MySql(**CONN, db=DATABASE)

class People:

    def __init__(self):

        pass

    def _get_fields(self, fields):
        """Returns a str of comma separated fields.

        Args:
            fields (list): List of fields to retrieve.

        Returns:
            str: Comma separated fields in a str.
        """
        default_fields = ['pkid', 'firstname', 'lastname', 'nickname', 'email', 'alias']

        return ",".join(fields) if fields else ",".join(default_fields)

    def get_all_people(self, pkid=None, name=None, firstname=None, lastname=None,
                   nickname=None, email=None, alias=None, fields=None, filter=None):
        """Fetches people from the DB.

        Builds SQL query, based on parameters, to fetch one or more people.  The filters are `and` based.

        Args:
            pkid (int): PKID of individual person to fetch.
            name: (str): Uses like wild card for firstname, lastname or nickname matches.
            firstname (str): Find where firstname =.
            lastname (str): Find where lastname =.
            nickname (str): Find where nickname =.
            email (str): Find where email =.
            alias (int): alias is PKID pointer for alias record to point to main record in table.
            fields (list): List of fields to retrieve for each person.
            filters (str | list): Custom filters to use in where clause.

        Returns:
            (dict | list of dicts):  Returns dict if one person (pkid) else list of dicts.
        """
        fields = self._get_fields(fields)
        sql = f'select {fields} from people'

        if pkid:
            sql += f' where pkid="{pkid}"'
        elif alias:
            sql += f' where pkid="{alias}"'
        elif email:
            sql += f' where email="{email}"'
        elif name:
            sql += f' where firstname like "%{name}%" or lastname like "%{name}%" or nickname like "%{name}%"'
        elif firstname or lastname or nickname:
            name_list = []
            if firstname:
                name_list.append(f' firstname = "{firstname}"')
            if lastname:
                name_list.append(f' lastname = "{lastname}"')
            if nickname:
                name_list.append(f' nickname = "{nickname}"')
            sql += f' where {" and ".join(name_list)} '

        if filter:
            if isinstance(filter, str):
                filter = [filter]

            if hasattr(filter, '__iter__'):
                filter = ' and '.join(filter)

            if 'where' in sql:
                sql += f' and {filter}'
            else:
                sql += f' where {filter}'

        logger.debug(sql)
        result = db.run_sql(sql=sql, get='one' if pkid else 'all')

        return result

    def get_person(self, pkid=None, firstname=None, lastname=None, nickname=None, email=None, alias=None, fields=None):
        """Returns person's main record plus alias info combined.


        """
        result = self.get_all_people(pkid=pkid, firstname=firstname, lastname=lastname,
                                 nickname=nickname, email=email, alias=alias, fields=fields)

        # Return the result is list of one element or dict (pkid search)
        if len(result) == 1 and isinstance(result, list):
            return result[0]
        elif isinstance(result, dict):
            return result

        people = {}
        alias = []

        # Get a list of (main.pkid, alias.pkid) pairs.
        for person in result:
            people[person['pkid']] = person
            if person['alias']:
                alias.append((person['pkid'], person['alias']))

        # If more than one alias, won't be able to determine specifc person.
        if len(alias) > 1:
            logger.error(f'Error too many aliases: {alias}')
            for r in result:
                logger.debug(r)
            return None


        if alias:
            alias = alias[0]  # Get the single alias list element

            alias_record = people[alias[1]]
            main_record = people[alias[0]]

            # Alias info is preferred over main record info.
            for k, v in alias_record.items():
                if v:
                    main_record[k] = v

            return main_record

        # Get list of all PKID's returned for debugging purposes.
        x = [x['pkid'] for x in result]
        logger.error(f'Too many records to determine person: pkids: {x}')

        for r in result:
            logger.debug(r)


        return None


    def get_aliases(self, pkid=None, firstname=None, lastname=None, nickname=None, email=None, alias=None, fields=None):
        """Get records that are aliases.

        Args:
            pkid (int): PKID of individual person to fetch.
            name: (str): Uses like wild card for firstname, lastname or nickname matches.
            firstname (str): Find where firstname =.
            lastname (str): Find where lastname =.
            nickname (str): Find where nickname =.
            email (str): Find where email =.
            alias (int): alias is PKID pointer for alias record to point to main record in table.
            fields (list): List of fields to retrieve for each person.

        Returns:
            (dict | list of dicts):  Returns dict if one person (pkid) else list of dicts.
        """
        result = self.get_all_people(pkid=pkid, firstname=firstname, lastname=lastname,
                                 nickname=nickname, email=email, alias=alias, fields=fields,
                                 filter='alias>0'
                                 )

        return result


    def get_non_aliases(self, pkid=None, firstname=None, lastname=None, nickname=None, email=None, alias=None, fields=None):
        """Returns records that are not aliases.

        Args:
            pkid (int): PKID of individual person to fetch.
            name: (str): Uses like wild card for firstname, lastname or nickname matches.
            firstname (str): Find where firstname =.
            lastname (str): Find where lastname =.
            nickname (str): Find where nickname =.
            email (str): Find where email =.
            alias (int): alias is PKID pointer for alias record to point to main record in table.
            fields (list): List of fields to retrieve for each person.

        Returns:
            (dict | list of dicts):  Returns dict if one person (pkid) else list of dicts.

        """
        result = self.get_all_people(pkid=pkid, firstname=firstname, lastname=lastname,
                                 nickname=nickname, email=email, alias=alias, fields=fields,
                                 filter='alias=0'
                                 )

        return result


    def get_people(self, pkid=None, firstname=None, lastname=None, nickname=None, email=None, alias=None, fields=None):
        """Returns one or more poeple combined with alias information.

        Args:
            pkid (int): PKID of individual person to fetch.
            name: (str): Uses like wild card for firstname, lastname or nickname matches.
            firstname (str): Find where firstname =.
            lastname (str): Find where lastname =.
            nickname (str): Find where nickname =.
            email (str): Find where email =.
            alias (int): alias is PKID pointer for alias record to point to main record in table.
            fields (list): List of fields to retrieve for each person.

        Returns:
            (dict | list of dicts):  Returns dict if one person (pkid) else list of dicts.
        """
        aliases = self.get_aliases()

        alias_map = {}

        count = 0
        for a in aliases:
            alias_map[a['alias']] = count
            count += 1



        result = self.get_non_aliases(pkid=pkid, firstname=firstname, lastname=lastname,
                                 nickname=nickname, email=email, alias=alias, fields=fields)

        for r in result:
            if r['pkid'] in alias_map:
                r['email'] = aliases[alias_map[r['pkid']]]['email']
                r['alias'] = aliases[alias_map[r['pkid']]]['alias']

        return result


p = People()
"""
result = p.get_all_people(firstname='chris', lastname='creech')
for r in result:
    print(r)

result = p.get_person(firstname='chris', lastname='creech')
print(result)
"""

email = []
result = p.get_people()
for r in result:
    print(r)
    email.append(r['email'])

print(','.join(email))

