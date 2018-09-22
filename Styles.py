import json

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
logger = logging.getLogger(os.path.basename(__file__).split('.')[0] if __name__ == '__main__' else __name__.split('.')[-1])
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

db = Database(local_host['host'], local_host['user'], local_host['password'], 'styles')


class Style:

    def __init__(self, version=''):

        self.version = version   #default version to use


    def get_style_name(self, style_group, style_num, version=None):
        """
        Return sub category style name
        :param style_group: Category
        :param style_num: Sub Category
        :param version: BJCP or BA
        :return: Style Name or '' if not found
        """

        if version is None:
            version = self.version

        try:
            style_group = '{:02d}'.format(int(style_group))
        except:
            pass

        sql = 'select style_name from baseline_styles where style_num="{}" and style_group="{}" and version="{}"'.format(style_num.upper(), style_group, version.upper())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return result.get('style_name', '')




    def get_versions(self, JSON=False):
        """
        Return list of style guideline versions in the DB
        :param JSON: Return as JSON formatted string
        :return: list of versions found in DB
        """

        sql = 'select distinct version from baseline_styles'

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        if JSON:
            return json.dumps([r['version'] for r in result] if result else result)
        else:
            return [r['version'] for r in result] if result else result



    def is_specialty(self, style_group, style_num, version=None):
        """
        Return sub category style name
        :param style_group: Category
        :param style_num: Sub Category
        :param version: BJCP or BA
        :return: Style Name or '' if not found
        """

        if version is None:
            version = self.version

        try:
            style_group = '{:02d}'.format(int(style_group))
        except:
            pass

        sql = 'select req_spec from baseline_styles where style_num="{}" and style_group="{}" and version="{}"'.format(style_num.upper(), style_group, version.upper())

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).one(uid)

        return True if result.get('req_spec', 0) else False


    def get_styles_for_group(self, style_group, version=None, style_type=None, req_spec=None):
        """
        Get styles based on category groups
        :param style_group: category
        :param version: style guidelines
        :param style_type: 1,2,3 or beer,cider,mead
        :param req_spec: require specialty ingredients, True or False or None
        :return:
        """

        sql = 'select style_group, style_num, style_name  from baseline_styles where {style_group} {style_type} ' \
              '{req_spec} version = "{version}" order by style_group, style_num'

        if version is None:
            version = self.version

        if req_spec is None:
            req_spec = ''

        else:
            if req_spec:
                req_spec = 'req_spec = "1" and '
            else:
                req_spec = 'req_spec = "0" and '


        if style_type is None:
            style_type = ''
        else:
            #todo: dynamically figure out the style types and mapping

            mapping = {'beer': '1',
                       'cider': '2',
                       'mead': '3'
                       }

            if type(style_type) != type([]):
                style_type = [style_type]

            #get style type numbers from mapping if
            style_type = [mapping.get(s.lower(), '') if type(s) == type(' ') else str(s) for s in style_type]

            style_type = 'style_type in ("{}") and '.format('","'.join(style_type))


        if str(style_group) in ('-1', 'all', 'ALL'):
            style_group = ''

        else:
            if type(style_group) != type([]):
                style_group = [style_group]

            # prefix 0 if element is single digit
            style_group = ['{:02d}'.format(int(s)) if str(s).isdigit() else str(s) for s in style_group]

            style_group = 'style_group in ("{}") and '.format('","'.join(style_group))


        sql = sql.format(style_group=style_group, style_type=style_type, req_spec=req_spec, version=version)
        #print(sql)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result

    def get_styles(self, version=''):

        if version:

            where = ' where version = "{}" '
        else:
            where = ''

        sql = 'select style_num, style_name, category, style_group, version, pkid from baseline_styles {}'.format(where)

        uid = gen_uid()
        result = db.db_command(sql=sql, uid=uid).all(uid)

        return result



if __name__ == '__main__':

    print(Style().get_versions())

    print(Style('BJCP2015').get_style_name('1', 'c'))

    result = Style('BJCP2015').get_styles_for_group(-1, style_type=['beer', 1], req_spec=True)

    for r in result:
        print(r)


