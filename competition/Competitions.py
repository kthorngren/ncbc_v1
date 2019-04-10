

from utils import MySql
from utils import DATABASE, CONN

db = MySql(**CONN, db=DATABASE)

class Competitions:

    def __init__(self):

        self.pkid = 0

    def get_active_competition(self):
        """Returns active competition pkid"""
        sql = 'select pkid from competitions where active = "1"'
        result = db.run_sql(sql=sql, get='one')

        self.pkid = result.get('pkid', 0)
        return self.pkid

c = Competitions()
print(c.get_active_competition())
