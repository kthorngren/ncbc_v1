import re
import json
from _collections import defaultdict
from pprint import pprint
import shutil
import time

import requests
import yaml

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
LEVEL = logging.DEBUG
logger = logging.getLogger(os.path.basename(__file__).split('.')[0] if __name__ == '__main__' else __name__)
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

from MySql import local_host
from Database import Database


class Datatables:

    def __init__(self, db_user,db_host, db_password, db):
        logger.debug('Datatables.__init__()')
        self.db = Database(db_user,db_host, db_password, db)
        self.active_testbed = 0

    ######################
    #
    # Datatables JS and CSS includes
    #
    ######################

    def update_dt_versions(self):
        try:
            r = requests.get('https://datatables.net/feeds/versions')
            result = r.json()
        except:
            result = {}

        return result

    def get_dt_versions(self, dt='', release=True):

        #use update version to populate DB table and this funciton will use the DB to get the info
        versions = {'DataTables': {'release': {'version': '1.10.16', 'previous': '1.10.15', 'date': 1504185643, 'package': 'http://datatables.net/releases/DataTables-1.10.16.zip', 'files': {'debug': {'md5': '28e78e8c1897d5a8bcf7e18b2f2ba0b6', 'path': 'https://cdn.datatables.net/1.10.16/js/jquery.dataTables.js'}, 'min': {'md5': '114c26084cb472c6a5f8b58908472ad7', 'path': 'https://cdn.datatables.net/1.10.16/js/jquery.dataTables.min.js'}, 'css': {'md5': '3f15c4222ee5d7eb70a67727c613be8b', 'path': 'https://cdn.datatables.net/1.10.16/css/jquery.dataTables.css'}, 'cssMin': {'md5': '01660835fe229de543497371787d0c8e', 'path': 'https://cdn.datatables.net/1.10.16/css/jquery.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': True}, 'foundation': {'js': True, 'css': True}, 'jqueryui': {'js': True, 'css': True}}}, 'nightly': {'version': '1.10.17-dev', 'date': 1521105980, 'files': {'debug': {'md5': '0b59ef38d0240b8563709632aac45faa', 'path': 'https://nightly.datatables.net/js/jquery.dataTables.js'}, 'min': {'md5': '6aab6912d1539f63254bc13c87ed2fa7', 'path': 'https://nightly.datatables.net/js/jquery.dataTables.min.js'}, 'css': {'md5': '5ba5207a457f5abeba8cb851d86158e8', 'path': 'https://nightly.datatables.net/css/jquery.dataTables.css'}, 'cssMin': {'md5': '50f59d3ac7fbb87a0b283f831e1ff418', 'path': 'https://nightly.datatables.net/css/jquery.dataTables.min.css'}}}}, 'AutoFill': {'release': {'version': '2.2.2', 'previous': '2.2.1', 'date': 1505215455, 'package': 'http://datatables.net/releases/AutoFill-2.2.2.zip', 'files': {'debug': {'md5': '370c6a8f08d9b2fbb8c7a19805985f88', 'path': 'https://cdn.datatables.net/autofill/2.2.2/js/dataTables.autoFill.js'}, 'min': {'md5': '8d3cf423eb9e7371ea19e55f37fa1f2c', 'path': 'https://cdn.datatables.net/autofill/2.2.2/js/dataTables.autoFill.min.js'}, 'css': {'md5': '3caa069a89e6f8ae4d7a932fdec17966', 'path': 'https://cdn.datatables.net/autofill/2.2.2/css/autoFill.dataTables.css'}, 'cssMin': {'md5': '9fe81eb0ac694ee91d97c5d7a8b3ad43', 'path': 'https://cdn.datatables.net/autofill/2.2.2/css/autoFill.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': True}, 'foundation': {'js': True, 'css': True}, 'jqueryui': {'js': True, 'css': True}}}, 'nightly': {'version': '2.2.2', 'date': 1519318398, 'files': {'debug': {'md5': '370c6a8f08d9b2fbb8c7a19805985f88', 'path': 'https://nightly.datatables.net/autofill/js/dataTables.autoFill.js'}, 'min': {'md5': '8d3cf423eb9e7371ea19e55f37fa1f2c', 'path': 'https://nightly.datatables.net/autofill/js/dataTables.autoFill.min.js'}, 'css': {'md5': '3caa069a89e6f8ae4d7a932fdec17966', 'path': 'https://nightly.datatables.net/autofill/css/autoFill.dataTables.css'}, 'cssMin': {'md5': '9fe81eb0ac694ee91d97c5d7a8b3ad43', 'path': 'https://nightly.datatables.net/autofill/css/autoFill.dataTables.min.css'}}}}, 'Buttons': {'release': {'version': '1.5.1', 'previous': '1.5.0', 'date': 1513941878, 'package': 'http://datatables.net/releases/Buttons-1.5.1.zip', 'files': {'debug': {'md5': '05a237151234f7e8caf17d0c608b019b', 'path': 'https://cdn.datatables.net/buttons/1.5.1/js/dataTables.buttons.js'}, 'min': {'md5': 'ef66b6c574a0c5e99faebbf70f2fa1b8', 'path': 'https://cdn.datatables.net/buttons/1.5.1/js/dataTables.buttons.min.js'}, 'css': {'md5': '9576f1e9c364c157240122d44ddea3ca', 'path': 'https://cdn.datatables.net/buttons/1.5.1/css/buttons.dataTables.css'}, 'cssMin': {'md5': 'a47708ac4c445a0a520c97f1bcf301f8', 'path': 'https://cdn.datatables.net/buttons/1.5.1/css/buttons.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': True}, 'foundation': {'js': True, 'css': True}, 'jqueryui': {'js': True, 'css': True}}}, 'nightly': {'version': '1.5.1', 'date': 1520960749, 'files': {'debug': {'md5': '903879de0ebb598f3d7aa142680fe5b1', 'path': 'https://nightly.datatables.net/buttons/js/dataTables.buttons.js'}, 'min': {'md5': 'f8064a997172ab06849320f20ade3e6f', 'path': 'https://nightly.datatables.net/buttons/js/dataTables.buttons.min.js'}, 'css': {'md5': '4a38396ec2b79b579cb7b15da27ca2ea', 'path': 'https://nightly.datatables.net/buttons/css/buttons.dataTables.css'}, 'cssMin': {'md5': '789a755e2b03075b8207e83290255d63', 'path': 'https://nightly.datatables.net/buttons/css/buttons.dataTables.min.css'}}}}, 'ColReorder': {'release': {'version': '1.4.1', 'previous': '1.4.0', 'date': 1505219846, 'package': 'http://datatables.net/releases/ColReorder-1.4.1.zip', 'files': {'debug': {'md5': 'cfd77a992b8401df510480f2ea845416', 'path': 'https://cdn.datatables.net/colreorder/1.4.1/js/dataTables.colReorder.js'}, 'min': {'md5': 'd815a48497eb616a91880b05ed22dd68', 'path': 'https://cdn.datatables.net/colreorder/1.4.1/js/dataTables.colReorder.min.js'}, 'css': {'md5': '1b09250a9379dffcd3ef71a5bf6ebdb2', 'path': 'https://cdn.datatables.net/colreorder/1.4.1/css/colReorder.dataTables.css'}, 'cssMin': {'md5': 'a2e75082bb806b3a302604cfc8e22540', 'path': 'https://cdn.datatables.net/colreorder/1.4.1/css/colReorder.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': False}, 'foundation': {'js': True, 'css': False}, 'jqueryui': {'js': True, 'css': False}}}, 'nightly': {'version': '1.4.2-dev', 'date': 1519552004, 'files': {'debug': {'md5': '2b52cdba8794d7b223993bc1f41b9d12', 'path': 'https://nightly.datatables.net/colreorder/js/dataTables.colReorder.js'}, 'min': {'md5': '97eca86c7aa218dd98bba793bc26bcb1', 'path': 'https://nightly.datatables.net/colreorder/js/dataTables.colReorder.min.js'}, 'css': {'md5': '4514f3803705939d730441bdadc9a77f', 'path': 'https://nightly.datatables.net/colreorder/css/colReorder.dataTables.css'}, 'cssMin': {'md5': 'a429c1da42cf04c2885585a073f5d458', 'path': 'https://nightly.datatables.net/colreorder/css/colReorder.dataTables.min.css'}}}}, 'ColVis': {'release': {'version': '1.1.2', 'previous': '1.1.1', 'date': 1427893187, 'package': 'http://datatables.net/releases/ColVis-1.1.2.zip', 'files': {'debug': {'md5': '', 'path': ''}, 'min': {'md5': '', 'path': ''}, 'css': {'md5': '', 'path': ''}, 'cssMin': {'md5': '', 'path': ''}}, 'styling': {'bootstrap': {'js': False, 'css': False}, 'foundation': {'js': False, 'css': False}, 'jqueryui': {'js': False, 'css': False}}}, 'nightly': {'version': '1.1.2', 'date': 1427893187, 'files': {'debug': {'md5': '', 'path': ''}, 'min': {'md5': '', 'path': ''}, 'css': {'md5': '', 'path': ''}}}}, 'FixedColumns': {'release': {'version': '3.2.4', 'previous': '3.2.3', 'date': 1512646050, 'package': 'http://datatables.net/releases/FixedColumns-3.2.4.zip', 'files': {'debug': {'md5': 'ee7d8b0bc33074fbbe9c479172815b79', 'path': 'https://cdn.datatables.net/fixedcolumns/3.2.4/js/dataTables.fixedColumns.js'}, 'min': {'md5': '300fdd935b51997982dbe73abae654ac', 'path': 'https://cdn.datatables.net/fixedcolumns/3.2.4/js/dataTables.fixedColumns.min.js'}, 'css': {'md5': 'e06318d2305fbc66aa6fc8f4f2754cdf', 'path': 'https://cdn.datatables.net/fixedcolumns/3.2.4/css/fixedColumns.dataTables.css'}, 'cssMin': {'md5': '194c3762df658fd5e90b39903c937591', 'path': 'https://cdn.datatables.net/fixedcolumns/3.2.4/css/fixedColumns.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': False}, 'foundation': {'js': True, 'css': False}, 'jqueryui': {'js': True, 'css': False}}}, 'nightly': {'version': '3.2.4', 'date': 1519380801, 'files': {'debug': {'md5': 'ee7d8b0bc33074fbbe9c479172815b79', 'path': 'https://nightly.datatables.net/fixedcolumns/js/dataTables.fixedColumns.js'}, 'min': {'md5': '300fdd935b51997982dbe73abae654ac', 'path': 'https://nightly.datatables.net/fixedcolumns/js/dataTables.fixedColumns.min.js'}, 'css': {'md5': 'e06318d2305fbc66aa6fc8f4f2754cdf', 'path': 'https://nightly.datatables.net/fixedcolumns/css/fixedColumns.dataTables.css'}, 'cssMin': {'md5': '194c3762df658fd5e90b39903c937591', 'path': 'https://nightly.datatables.net/fixedcolumns/css/fixedColumns.dataTables.min.css'}}}}, 'FixedHeader': {'release': {'version': '3.1.3', 'previous': '3.1.2', 'date': 1505225389, 'package': 'http://datatables.net/releases/FixedHeader-3.1.3.zip', 'files': {'debug': {'md5': '09626dac7b9db8e20efba76e362bf0be', 'path': 'https://cdn.datatables.net/fixedheader/3.1.3/js/dataTables.fixedHeader.js'}, 'min': {'md5': '9d3ba9ac7a9a52e647c605509b5612e4', 'path': 'https://cdn.datatables.net/fixedheader/3.1.3/js/dataTables.fixedHeader.min.js'}, 'css': {'md5': 'c99020cbb8a3e0a65c034fa780588429', 'path': 'https://cdn.datatables.net/fixedheader/3.1.3/css/fixedHeader.dataTables.css'}, 'cssMin': {'md5': '446a1fe52d8ce74449ab8199e1134f6c', 'path': 'https://cdn.datatables.net/fixedheader/3.1.3/css/fixedHeader.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': False}, 'foundation': {'js': True, 'css': False}, 'jqueryui': {'js': True, 'css': False}}}, 'nightly': {'version': '3.1.4-dev', 'date': 1519836470, 'files': {'debug': {'md5': '401a2a979f106c2a15bd4cac06dfa0e9', 'path': 'https://nightly.datatables.net/fixedheader/js/dataTables.fixedHeader.js'}, 'min': {'md5': '7ca5a4f15bbbdaf7b52643496e89d148', 'path': 'https://nightly.datatables.net/fixedheader/js/dataTables.fixedHeader.min.js'}, 'css': {'md5': 'c99020cbb8a3e0a65c034fa780588429', 'path': 'https://nightly.datatables.net/fixedheader/css/fixedHeader.dataTables.css'}, 'cssMin': {'md5': '446a1fe52d8ce74449ab8199e1134f6c', 'path': 'https://nightly.datatables.net/fixedheader/css/fixedHeader.dataTables.min.css'}}}}, 'KeyTable': {'release': {'version': '2.3.2', 'previous': '2.3.1', 'date': 1505226253, 'package': 'http://datatables.net/releases/KeyTable-2.3.2.zip', 'files': {'debug': {'md5': 'aef0399fdf6705bfeb94c2a0fa22ca27', 'path': 'https://cdn.datatables.net/keytable/2.3.2/js/dataTables.keyTable.js'}, 'min': {'md5': '8058377cbfed5b94eb620c25eabac001', 'path': 'https://cdn.datatables.net/keytable/2.3.2/js/dataTables.keyTable.min.js'}, 'css': {'md5': '8fc98094e890b054ee9761b8595a71aa', 'path': 'https://cdn.datatables.net/keytable/2.3.2/css/keyTable.dataTables.css'}, 'cssMin': {'md5': 'e82963d0bfaed314c00dfe1872a45b24', 'path': 'https://cdn.datatables.net/keytable/2.3.2/css/keyTable.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': False}, 'foundation': {'js': True, 'css': False}, 'jqueryui': {'js': True, 'css': False}}}, 'nightly': {'version': '2.3.2-dev', 'date': 1519318631, 'files': {'debug': {'md5': '60571081f68224657830b4ea854d517b', 'path': 'https://nightly.datatables.net/keytable/js/dataTables.keyTable.js'}, 'min': {'md5': '168205558271b86faae135530422305c', 'path': 'https://nightly.datatables.net/keytable/js/dataTables.keyTable.min.js'}, 'css': {'md5': '8f7a8dfce44443c8b3190910b2882a58', 'path': 'https://nightly.datatables.net/keytable/css/keyTable.dataTables.css'}, 'cssMin': {'md5': 'd3ca237c29ba5bbecd44fc06ce3a18a7', 'path': 'https://nightly.datatables.net/keytable/css/keyTable.dataTables.min.css'}}}}, 'Responsive': {'release': {'version': '2.2.1', 'previous': '2.2.0', 'date': 1512744834, 'package': 'http://datatables.net/releases/Responsive-2.2.1.zip', 'files': {'debug': {'md5': '4ef956b04413700b6b7741885f0723a1', 'path': 'https://cdn.datatables.net/responsive/2.2.1/js/dataTables.responsive.js'}, 'min': {'md5': '242f735c55adeeb56eebdd06aac8eafe', 'path': 'https://cdn.datatables.net/responsive/2.2.1/js/dataTables.responsive.min.js'}, 'css': {'md5': 'c01133c8ce9aa43590a474c31ee9b118', 'path': 'https://cdn.datatables.net/responsive/2.2.1/css/responsive.dataTables.css'}, 'cssMin': {'md5': 'da7262fc183e15ecaceee9f0efaa4655', 'path': 'https://cdn.datatables.net/responsive/2.2.1/css/responsive.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': False}, 'foundation': {'js': True, 'css': False}, 'jqueryui': {'js': True, 'css': False}}}, 'nightly': {'version': '2.2.2-dev', 'date': 1520855499, 'files': {'debug': {'md5': 'fddbde76cf6822f93a5c660b13de4dfe', 'path': 'https://nightly.datatables.net/responsive/js/dataTables.responsive.js'}, 'min': {'md5': '943cb9180224d515c84a350ea134fc4c', 'path': 'https://nightly.datatables.net/responsive/js/dataTables.responsive.min.js'}, 'css': {'md5': 'c01133c8ce9aa43590a474c31ee9b118', 'path': 'https://nightly.datatables.net/responsive/css/responsive.dataTables.css'}, 'cssMin': {'md5': 'da7262fc183e15ecaceee9f0efaa4655', 'path': 'https://nightly.datatables.net/responsive/css/responsive.dataTables.min.css'}}}}, 'RowGroup': {'release': {'version': '1.0.2', 'previous': '1.0.1', 'date': 1505227247, 'package': 'http://datatables.net/releases/RowGroup-1.0.2.zip', 'files': {'debug': {'md5': '68cff71a947ce8c2796e5ca2c01f5e05', 'path': 'https://cdn.datatables.net/rowgroup/1.0.2/js/dataTables.rowGroup.js'}, 'min': {'md5': 'ecdba74c3dd05699d5246526ab515c95', 'path': 'https://cdn.datatables.net/rowgroup/1.0.2/js/dataTables.rowGroup.min.js'}, 'css': {'md5': 'e3b0c6827173cb2e84400a664c2dc7c0', 'path': 'https://cdn.datatables.net/rowgroup/1.0.2/css/rowGroup.dataTables.css'}, 'cssMin': {'md5': '3d68fbb20e9102f3e8f731d7efd66183', 'path': 'https://cdn.datatables.net/rowgroup/1.0.2/css/rowGroup.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': False, 'css': True}, 'foundation': {'js': False, 'css': True}, 'jqueryui': {'js': False, 'css': True}}}, 'nightly': {'version': '1.0.3-dev', 'date': 1519318695, 'files': {'debug': {'md5': 'f93e09994576e43312eaf69825a3d3c0', 'path': 'https://nightly.datatables.net/rowgroup/js/dataTables.rowGroup.js'}, 'min': {'md5': '00d2522cf75cd13df3496769c7ffe857', 'path': 'https://nightly.datatables.net/rowgroup/js/dataTables.rowGroup.min.js'}, 'css': {'md5': 'e3b0c6827173cb2e84400a664c2dc7c0', 'path': 'https://nightly.datatables.net/rowgroup/css/rowGroup.dataTables.css'}, 'cssMin': {'md5': '3d68fbb20e9102f3e8f731d7efd66183', 'path': 'https://nightly.datatables.net/rowgroup/css/rowGroup.dataTables.min.css'}}}}, 'RowReorder': {'release': {'version': '1.2.3', 'previous': '1.2.2', 'date': 1505227437, 'package': 'http://datatables.net/releases/RowReorder-1.2.3.zip', 'files': {'debug': {'md5': 'b9d756883455988b516149babafce494', 'path': 'https://cdn.datatables.net/rowreorder/1.2.3/js/dataTables.rowReorder.js'}, 'min': {'md5': '6e75adbc7bf320800f32a996c531b246', 'path': 'https://cdn.datatables.net/rowreorder/1.2.3/js/dataTables.rowReorder.min.js'}, 'css': {'md5': '600ddf10d204f624057816f88fbd9122', 'path': 'https://cdn.datatables.net/rowreorder/1.2.3/css/rowReorder.dataTables.css'}, 'cssMin': {'md5': '2904496643d6ad5935a8d7edafef22d2', 'path': 'https://cdn.datatables.net/rowreorder/1.2.3/css/rowReorder.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': False, 'css': True}, 'foundation': {'js': False, 'css': True}, 'jqueryui': {'js': False, 'css': True}}}, 'nightly': {'version': '1.2.3', 'date': 1519318714, 'files': {'debug': {'md5': 'b9d756883455988b516149babafce494', 'path': 'https://nightly.datatables.net/rowreorder/js/dataTables.rowReorder.js'}, 'min': {'md5': '6e75adbc7bf320800f32a996c531b246', 'path': 'https://nightly.datatables.net/rowreorder/js/dataTables.rowReorder.min.js'}, 'css': {'md5': 'd2f6f35338d7fb6373783e0f0ba781fd', 'path': 'https://nightly.datatables.net/rowreorder/css/rowReorder.dataTables.css'}, 'cssMin': {'md5': '0a7fe9d0cc536ddc4a2f51e582f8ce52', 'path': 'https://nightly.datatables.net/rowreorder/css/rowReorder.dataTables.min.css'}}}}, 'Scroller': {'release': {'version': '1.4.4', 'previous': '1.4.3', 'date': 1516986151, 'package': 'http://datatables.net/releases/Scroller-1.4.4.zip', 'files': {'debug': {'md5': '321ab175f0d2be0039059526ebf9467a', 'path': 'https://cdn.datatables.net/scroller/1.4.4/js/dataTables.scroller.js'}, 'min': {'md5': '109d1d727d859f983205837791a75523', 'path': 'https://cdn.datatables.net/scroller/1.4.4/js/dataTables.scroller.min.js'}, 'css': {'md5': 'ae78ce3352033ad30e14bd94ee94b6d1', 'path': 'https://cdn.datatables.net/scroller/1.4.4/css/scroller.dataTables.css'}, 'cssMin': {'md5': '582c940ca1a63b7b2b782f62ecce378a', 'path': 'https://cdn.datatables.net/scroller/1.4.4/css/scroller.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': True, 'css': False}, 'foundation': {'js': True, 'css': False}, 'jqueryui': {'js': True, 'css': False}}}, 'nightly': {'version': '1.4.4', 'date': 1519318736, 'files': {'debug': {'md5': '321ab175f0d2be0039059526ebf9467a', 'path': 'https://nightly.datatables.net/scroller/js/dataTables.scroller.js'}, 'min': {'md5': '109d1d727d859f983205837791a75523', 'path': 'https://nightly.datatables.net/scroller/js/dataTables.scroller.min.js'}, 'css': {'md5': 'ae78ce3352033ad30e14bd94ee94b6d1', 'path': 'https://nightly.datatables.net/scroller/css/scroller.dataTables.css'}, 'cssMin': {'md5': '582c940ca1a63b7b2b782f62ecce378a', 'path': 'https://nightly.datatables.net/scroller/css/scroller.dataTables.min.css'}}}}, 'Select': {'release': {'version': '1.2.5', 'previous': '1.2.4', 'date': 1516985187, 'package': 'http://datatables.net/releases/Select-1.2.5.zip', 'files': {'debug': {'md5': 'c8e83aa35e15f60f6ac07fc5654f3387', 'path': 'https://cdn.datatables.net/select/1.2.5/js/dataTables.select.js'}, 'min': {'md5': '99f78d237e462711abf0f6bb9165c08e', 'path': 'https://cdn.datatables.net/select/1.2.5/js/dataTables.select.min.js'}, 'css': {'md5': 'aeb13b69ab4558751f40beb762cfc834', 'path': 'https://cdn.datatables.net/select/1.2.5/css/select.dataTables.css'}, 'cssMin': {'md5': 'aebdacb509c7a9f9579a6b9aa15dec99', 'path': 'https://cdn.datatables.net/select/1.2.5/css/select.dataTables.min.css'}}, 'styling': {'bootstrap': {'js': False, 'css': True}, 'foundation': {'js': False, 'css': True}, 'jqueryui': {'js': False, 'css': True}}}, 'nightly': {'version': '1.2.5', 'date': 1521047918, 'files': {'debug': {'md5': '6dc5aee097c132cea22729d135322833', 'path': 'https://nightly.datatables.net/select/js/dataTables.select.js'}, 'min': {'md5': 'ffebb837a664e8effa53c647a68605a9', 'path': 'https://nightly.datatables.net/select/js/dataTables.select.min.js'}, 'css': {'md5': '70492b84bec08bf666b555e82921b046', 'path': 'https://nightly.datatables.net/select/css/select.dataTables.css'}, 'cssMin': {'md5': 'afe1262918994e1e8170e7a39c229463', 'path': 'https://nightly.datatables.net/select/css/select.dataTables.min.css'}}}}, 'TableTools': {'release': {'version': '2.2.4', 'previous': '2.2.3', 'date': 1521079324, 'package': 'http://datatables.net/releases/TableTools-2.2.4.zip', 'files': {'debug': {'md5': 'ca77964cf998db4f318d17e9c499b57b', 'path': 'https://cdn.datatables.net/tabletools/2.2.4/js/dataTables.tableTools.js'}, 'min': {'md5': '3786f5909b2e6b391b91e1fcb60364c3', 'path': 'https://cdn.datatables.net/tabletools/2.2.4/js/dataTables.tableTools.min.js'}, 'css': {'md5': '1e42303ba72c5d6b7abb43724e976e37', 'path': 'https://cdn.datatables.net/tabletools/2.2.4/css/dataTables.tableTools.min.css'}}, 'styling': {'bootstrap': {'js': False, 'css': False}, 'foundation': {'js': False, 'css': False}, 'jqueryui': {'js': False, 'css': False}}}, 'nightly': {'version': '2.2.4', 'date': 1427914060, 'files': {'debug': {'md5': '', 'path': ''}, 'min': {'md5': '', 'path': ''}, 'css': {'md5': '', 'path': ''}}}}, 'Editor': {'release': {'version': '1.7.2', 'previous': '', 'date': 1517245200, 'package': '', 'files': {'debug': {'path': 'https://editor.datatables.net/extensions/Editor/js/dataTables.editor.min.js', 'md5': ''}, 'min': {'path': 'https://editor.datatables.net/extensions/Editor/js/dataTables.editor.min.js', 'md5': ''}, 'css': {'path': 'https://editor.datatables.net/extensions/Editor/css/editor.dataTables.min.css', 'md5': ''}}, 'styling': {'bootstrap': {'js': True, 'css': True}, 'foundation': {'js': True, 'css': True}, 'jqueryui': {'js': True, 'css': True}}}, 'nightly': {'version': '1.7.2', 'previous': '', 'date': 1517245200, 'package': '', 'files': {'debug': {'path': 'https://editor.datatables.net/extensions/Editor/js/dataTables.editor.min.js', 'md5': ''}, 'min': {'path': 'https://editor.datatables.net/extensions/Editor/js/dataTables.editor.min.js', 'md5': ''}, 'css': {'path': 'https://editor.datatables.net/extensions/Editor/css/editor.dataTables.min.css', 'md5': ''}}}}, 'Plugins': {'release': {'version': '1.10.16', 'date': 1504193340}}}


        external_versions = {'Bootstrap 3': '3.3.7',
                             'Bootstrap 4': '4-4.0.0-beta',
                             'jQuery': '3.2.1',
                             'JSZip': '2.5.0',
                             'Semantic UI': '2.2.13',
                             'Column visibility': '1.5.1',
                             'Flash export': '1.5.1',
                             'HTML5 export': '1.5.1',
                             'Print view': '1.5.1',
                             }

        get_version = 'release' if release else 'nightly'

        result = versions.get(dt, {}).get(get_version, {}).get('version', '')

        if result == '':
            result = external_versions.get(dt, '')


        return result

    def get_dt_libraries(self):

        #Initially assign list but store in DB and periodically update versions, etc
        lib = ['Bootstrap 3', 'jQuery', 'JSZip',
               'DataTables', 'AutoFill', 'Buttons', 'ColReorder', 'ColVis', 'FixedColumns', 'FixedHeader',
               'KeyTable', 'Responsive', 'RowGroup', 'RowReorder', 'Scroller', 'Select',
               'TableTools', 'Editor', 'Plugins']

        return lib

    def get_dt_short_names(self, dt=''):

        abbr = {'Bootstrap 3': 'bs',
                'Bootstrap 4': 'bs',
                'jQuery': 'jq',
                'JSZip': 'jszip',
                'DataTables': 'dt',
                'AutoFill': 'af',
                'Buttons': 'b',
                'Column visibility': 'b-colvis',
                'Flash export': 'b-flash',
                'HTML5 export': 'b-html5',
                'Print view': 'b-print',
                'ColReorder': 'cr',
                'FixedColumns': 'fc',
                'FixedHeader': 'fh',
                'KeyTable': 'kt',
                'Responsive': 'r',
                'RowGroup': 'rg',
                'RowReorder': 'rr',
                'Scroller': 'sc',
                'Select': 'sl'
                }
        return abbr.get(dt, '')

    def get_styling_short_names(self, dt=''):

        abbr = {'Bootstrap 3': 'bs',
                'Bootstrap 4': 'bs4',
                'jQuery UI': 'ju',
                'Foundation': 'zf',
                'DataTables': 'dt',
                'Semantic UI': 'se',
                }
        return abbr.get(dt, '')

    ######################
    #
    # External JS and CSS libraries
    #
    ######################

    def get_external_includes(self, includes, styling):
        #print(includes)
        if 'Editor' in includes:
            includes.remove('Editor')
            includes = ['Editor'] + includes

        styling = styling.split(' ')[0].lower()
        css_includes = ''
        script_includes = ''
        external = {'PDFMake': {'js': ['https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.32/pdfmake.min.js',
                                       'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.32/vfs_fonts.js'
                                       ]
                                },
                    'Editor': {'js': 'static/js/dataTables.editor.min.js',
                               'css': 'static/css/editor.{styling}.min.css',
                               'styling': 'static/js/editor.{styling}.min.js'},
                    'Select2': {'js': ['static/js/editor.select2.js',
                                       'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/js/select2.min.js'],
                                'css': 'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/css/select2.min.css'
                                },
                    'Bootstrap Toggle': {'js': 'https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js',
                                         'css': 'https://gitcdn.github.io/bootstrap-toggle/2.2.2/css/bootstrap-toggle.min.css'},
                    'Highlight': {'js': 'static/js/jquery.highlight.js'},
                    'Page Visibility': {'js': 'static/js/pageVisibility.js'},
                    'Natural': {'js': 'static/js/natural.js'},
                    'Throttle Debounce': {'js': 'static/js/jquery.ba-throttle-debounce.min.js'},
                    'Quill': {'js': ['https://cdn.quilljs.com/1.2.2/quill.min.js',
                                       'static/js/editor.quill_text.js'],
                                'css': ['https://cdn.quilljs.com/1.2.2/quill.snow.css',
                                        'static/css/editor.quill.css']
                                },
                    'Font Awesome': {'css': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'
                                },
                    'status_display': {'css': 'static/css/status_display.css'
                                },
                    'jscolor': {'js': 'static/js/jscolor.js'
                                },
                    }

        for i in includes:
            if i == 'Editor':
                s = external[i]['css'].format(styling=styling)
                css_includes += '    <!-- DataTables Editor -->\n'
                css_includes += '    <link rel="stylesheet" type="text/css" href="{}">\n'.format(s)

                script_includes += '    <!-- DataTables Editor -->\n'
                script_includes += '    <script type="text/javascript" src="{}"></script>\n'.format(external[i]['js'])
                if styling != 'DataTables':
                    s = external[i]['styling'].format(styling=styling)
                    script_includes += '    <script type="text/javascript" src="{}"></script>\n'.format(s)
            else:
                js = external.get(i, {}).get('js', [])
                css = external.get(i, {}).get('css', [])

                if type(js) == type(' '):
                    js = [js]
                if type(css) == type(' '):
                    css = [css]

                if js:
                    script_includes += '    <!-- {} -->\n'.format(i)
                    for c in js:
                        script_includes += '    <script type="text/javascript" src="{}"></script>\n'.format(c)

                if css:
                    css_includes += '    <!-- {} -->\n'.format(i)
                    for c in css:
                        #print(c)
                        css_includes += '    <link rel="stylesheet" type="text/css" href="{}">\n'.format(c)

        return (css_includes, script_includes)

    def get_plugins(self, plugin):

        mapping = {'fieldType.toggle': 'field_type_toggle_plugin.js'}

        return mapping.get(plugin, '')




    ######################
    #
    # DT functions that can be subclassed
    #
    ######################




    def parse_DT_post(self, post, upload_many=None):
        """
        post is from the DataTables Editor and
        :param post:
        :return:
        """
        logger.debug('parse_DT_post post: {}'.format(post))

        if not upload_many:
            upload_many = {}

        upm_keys = upload_many.keys()

        records = {}
        for record in post:
            logger.debug('parse_DT_post record: {}'.format(record))
            #print('parse_DT_post record: {}'.format(record))
            match = re.findall(r'\[([A-Za-z0-9_\-]+)\]', record)
            logger.debug('parse_DT_post regex match: {}'.format(match))
            if not match and record != 'action':
                if record != 'pkid':
                    logger.debug('parse_DT_post is unable to process DataTables post, found record name of "{}"'.format(record))
            elif match and len(match) < 2:
                logger.debug('parse_DT_post is unable to process DataTables post, regex match is "{}"'.format(str(match)))
            elif match:
                #print('match:', match)
                pkid = int(match.pop(0))
                if pkid not in records:
                    records[pkid] = {}
                files_table = match[0]
                if '-many-count' in files_table and files_table.split('-')[0] in upm_keys:
                    pass  #skip 'files-many-count': '2' data as this is not a multi field join record
                elif files_table in upm_keys:
                    # files update: ['1', 'files', '1', 'id'] - less pkid which was just popped
                    field = upload_many[files_table]
                    if field not in records[pkid]:
                        records[pkid][field] = []
                    #print('post[record]', post[record])
                    records[pkid][field].append({'id': str(post[record])})
                else:
                    records[pkid][match.pop()] = post[record]
                # records[match.group(1)][match.group(2)] = post[record]
            elif record != 'action':
                logger.debug('parse_DT_post is unable to process DataTables post, no match found for record {}'.format(record))
        logger.debug('parse_DT_post records result: {}'.format(records))
        return records

    def build_editor_options(self, fk_list=None, blank_option=False):
        options = defaultdict(list)
        logger.debug('options list: {}'.format(fk_list))
        if type(fk_list) == type([]):
            for l in fk_list:
                if type(l) == type(' '):
                    if l[-5:] == '_list':   #if the fkey ends in list then its a list and make a multi value
                        table = l[3:-5]     #table name is field name with 'fk_' and '_list' removed
                        multi_value = '[]'
                    else:
                        table = l[3:]       #table name is field name with 'fk_' removed
                        multi_value = ''    #Not a multi value
                    #print 'table', table
                    if table == 'types':    #deal with non-standard unique / index field names
                        index = 'type'
                    elif table == 'commands':
                        index = 'command'
                        multi_value = '[]'
                    elif table == 'hosts':
                        index = 'hostname'
                    else:
                        index = 'name'
                    sql = 'select pkid, {} from {}'.format(index, table)
                    # print sql
                    uid = gen_uid()
                    result = self.db.db_command(sql=sql, uid=uid).all(uid)
                    for r in sorted(result, key=lambda k: k[index]):  #return sorted options
                        options['main.{}{}'.format(l, multi_value)].append({'label': r[index],
                                                                            'value': r['pkid']
                                                                            })
                elif type(l) == type ({}):
                    if l['match'][-5:] == '_list':   #if the fkey ends in list then its a list and make a multi value
                        table = l['match'][3:-5]     #table name is field name with 'fk_' and '_list' removed
                        multi_value = '[]'
                    else:
                        table = l['match'][3:]       #table name is field name with 'fk_' removed
                        multi_value = ''    #Not a multi value
                    #print 'table', table
                    concat = '{}'.format(l['concat']) if 'concat' in l else ''   #build concat for the fields
                    #where_clause = 'where fk_testbeds = "{}"'.format(self.get_active_testbed()) if self.is_testbed_table(table) else ''
                    where_clause = ''
                    sql = 'select pkid, concat({fields}) ' \
                                           'as label from {table} {where}'.format(table=table,
                                                             fields='{},'.format(concat)
                                                                       .join([table + '.' + x for x in l['fields']]),
                                                             field=l['fields'][0]
                                                                      if type(l['fields']) == type([]) else '',
                                                             where=where_clause
                                                             )
                    uid = gen_uid()
                    result = self.db.db_command(sql=sql, uid=uid).all(uid)
                    for r in sorted(result, key=lambda k: k['label']):  #return sorted options
                        options['main.{}{}'.format(l['match'], multi_value)].append({'label': r['label'],
                                                                            'value': r['pkid']
                                                                            })
        #sort options by label
        for o in options:
            #todo: determine the need of having a blankoptino with value of 0
            #if blank_option:
            #    pass
                #options[o].append({'label': '',
                #                    'value': 0
                #                    })
            options[o] = sorted(options[o], key=lambda k: k['label'])
        #print(options)

        return options

    def get_unique_column(self, table):
        if table == 'types':  # deal with non-standard unique / index field names
            return 'type'
        elif table == 'commands':
            return 'command'
        elif table == 'hosts':
            return 'hostname'
        else:
            return 'name'

    def get_uploaded_files(self):

        sql = 'select * from uploads'

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)

        files = {}

        for r in result:
            files[r['id']] = r

        return {'files': files}



    def get_table_data(self, pkid='', sql='', fields='', options_list='', debug=False, get_uploads=False, upload_many=None):
        #print('get table data fields', fields)
        logger.debug('options list: {}'.format(options_list))
        if not upload_many:     #make sure to process as dictionary
            upload_many = {}
        files = []
        error_list = []

        if sql:
            if type(sql) == type(' '):
                uid = gen_uid()
                result = self.db.db_command(sql=sql, uid=uid).all(uid)
            else:
                uid = gen_uid()
                result = self.db.db_command(uid=uid, **sql).all(uid)


            #temp code to build fk_ objects
            #todo: find permanent solution to build fk_ objects
            for row in result:
                orig_row = row.copy()
                for field in orig_row:


                    temp = field.split('.')

                    if len(temp) == 2:
                        new_key = temp[0]
                        new_sub_key = temp[1]

                        if new_key not in row:
                            row[new_key] = {}

                        row[new_key][new_sub_key] = row[field]


            collect_data = result
            #if debug:
            #    return {'data': result, 'sql': self.db.sql, 'errors': self.db.error}
            #return {'data': result}
        elif fields:
            logger.debug('Processing fields: {}'.format(fields))
            where_clause = ''
            sql_join = []
            options = {}
            error_list = []
            group_by = ''
            if type(fields) != type({}) or not fields:  # basic sanity check
                return {'error': 'Fields is {}'.format('not a dictionary' if type(fields) != type({}) else 'empty')}
            elif 'main' not in fields:
                return {'error': 'Fields does not contain the object "main" for the main table'}
            elif 'table' not in fields['main'] or 'fields' not in fields['main']:
                return {
                    'error': 'Fields contains "main" object but does not contain either "table" or " fields" sub-objects'}

            if pkid:
                logger.debug('checking pkid: {}, type: {}'.format(pkid, type(pkid)))
                if type(pkid) == type(1):   #if pkid is number convert to string and put in list
                    pkid = [str(pkid)]
                elif type(pkid) == type([]):  #process list and build list of string pkids
                    # print 'pkid is a list'
                    temp = [str(item) for item in pkid if type(item) == type(1) or item.isdigit()]
                    # print temp
                    if len(temp) != len(pkid):
                        return {'error': 'PKID list contains non numeric elements "{}"'.format(str(pkid))}
                    pkid = ','.join(temp)
                elif type(pkid) == type(' '):   #pkid list is a string, process as CSV list
                    temp_pkid = pkid.split(',')
                    temp = [str(item) for item in temp_pkid if type(item) == type(int) or item.isdigit()]
                    if len(temp) != pkid.count(',') + 1:
                        return {'error': 'PKID string contains non numeric elements "{}"'.format(pkid)}
                    pkid = ','.join(temp)
                where_field = fields['main'].get('where', 'pkid')
                where_clause = ' where {table}.{field} in ({pkid}) '.format(table=fields['main']['table'],
                                                                            field=where_field,
                                                                            pkid=pkid)
                logger.debug('Using where clause: {}'.format(where_clause))

            if options_list == '':
                options_list = []
            if options_list and type(options_list) != type([]):
                return {'error': 'options_list is not a list'}

            main_table = fields['main']['table']  # store the main table name in main_table
            if self.active_testbed:
                where_clause += ' and ' if where_clause else ' where '
                where_clause += ' {}.fk_testbeds = "{}" '.format(main_table, self.active_testbed)
            fields_list = []
            if 'pkid' not in fields['main']['fields']:  # make sure to get the row's pkid
                fields['main']['fields'].append('pkid')

            for table in fields['table_order']:   #use table_order list to process tables
                #print ('table:', table)
                if type(fields[table]['fields']) == type([]):
                    for field in fields[table]['fields']:  # build SQL select fields list with prefixed table names
                        #print ('table field:', table, field)
                        fields_list.append('{}.{}'.format(main_table if table == 'main' else table,  # use real field name if 'main'
                                                          field))
                    if table != 'main':  #joined table is not multiselect so build a simple join statement
                        #print('joined table is not multiselect so build a simple join statement')
                        sql_join.append(' {join_type} {table} as {object} on ' \
                                        '{object}.pkid = {main_table}.{match}'.format(join_type=fields[table]['type'],
                                                                                table=fields[table]['table'],
                                                                                object=table,
                                                                                main_table=main_table,
                                                                                match=fields[table]['match']
                                                                                ))
                        if 'fk_{}'.format(fields[table]['table']) not in options_list:
                            options_list.append('fk_{}'.format(fields[table]['table']))  # build options object names
                elif type(fields[table]['fields']) == type({}):  #dict used to specify PKID
                    if fields[table]['select'] == 'multi':
                        #print ('multi', fields[table]['match'], fields[table]['fields'])
                        concat = ',"{}"'.format(fields[table]['concat']) if 'concat' in fields[table] else ''
                        if '{}'.format(fields[table]['match']) not in options_list:
                            if type(fields[table]['fields']['fields']) == type([]):
                                options_list.append({'fields': fields[table]['fields']['fields'],
                                                     'concat': concat,
                                                     'match': '{}'.format(fields[table]['match'])
                                                     }
                                                    )  # build options object names with multi select [] and concat label
                            else:
                                options_list.append('{}'.format(fields[table]['match']))  # build options object names with multi select []
                        if 'fields' in fields[table]['fields'] and 'pkid' in fields[table]['fields']:
                            concat = ',"{}"'.format(fields[table]['concat']) if 'concat' in fields[table] else ''
                            fields_list.append('group_concat(distinct {fields} order by {table}.{field}) '   #build label, value pairs for html select
                                               'as {table}$label'.format(table=table,
                                                                        fields='{}, '.format(concat)
                                                                           .join([table + '.' + x for x in fields[table]['fields']['fields']]),
                                                                        field=fields[table]['fields']['fields'][0]
                                                                          if type(fields[table]['fields']['fields']) == type([]) else '',
                                                                        dt_object=fields[table]['dt_object']))
                            fields_list.append('group_concat(distinct {table}.{pkid} order by {table}.{field}) '
                                               'as {table}$value'.format(table=table,
                                                                       field=fields[table]['fields']['fields'][0]
                                                                          if type(fields[table]['fields']['fields']) == type([]) else '',
                                                                       pkid=fields[table]['fields']['pkid'],
                                                                               dt_object=fields[table]['dt_object']))
                        sql_join.append(' {join_type} {table} as {object} on find_in_set(' \
                                        '{table}.{pkid}, {main_table}.{match}) > 0'.format(join_type=fields[table]['type'],
                                                                                table=fields[table]['table'],
                                                                                object=table,
                                                                                main_table=main_table,
                                                                                pkid=fields[table]['fields']['pkid'],
                                                                                match=fields[table]['match']
                                                                                ))
                        if not group_by:
                            group_by = 'group by {}.pkid'.format(main_table)
                    elif fields[table]['select'] == 'single':           #don't need to build label/value pairs if single select
                        sql_join.append(' {join_type} {table} as {object} on ' \
                                '{object}.pkid = {main_table}.fk_{table}'.format(join_type=fields[table]['type'],
                                                                          table=fields[table]['table'],
                                                                          object=table,
                                                                          main_table=main_table
                                                                          ))
            order_by = []
            for o in fields['main'].get('order', ''):
                order_by.append(' {d[column]} {d[direction]} '.format(d=o))
            order_by = 'order by ' + ','.join(order_by) if order_by else ''
            limit_results = ' limit {} '.format(fields['main']['limit']) if 'limit' in fields['main'] else ''

            sql = 'select {fields} from {table} {join} {where} {group_by} {order_by} {limit_results}'.format(fields=', '.join(fields_list),
                                                                       table=main_table,
                                                                       join=' '.join(sql_join),
                                                                       where=where_clause,
                                                                       group_by=group_by,
                                                                       order_by=order_by,
                                                                       limit_results=limit_results
                                                                       )
            logger.debug('Using generated SQL: {}'.format(sql))
            uid = gen_uid()
            result = self.db.db_command(sql=sql, uid=uid).all(uid)
            logger.debug('SQL query result: {}'.format(result))
            #print(options_list)

            #pprint (result)
            collect_data = []
            for row in result:
                #print('row: {}'.format(row))
                pkid = str(row['pkid'])
                #print 'row pkid', type(row['pkid']), row['pkid']
                temp = {'DT_RowId': pkid}
                temp['main'] = defaultdict(list)
                for table in fields['table_order']:  # loop through all the tables provided
                    #print('processing table: {}, {}'.format(table,fields[table]['fields']))
                    dt_table = 'main'
                    if table != 'main':  # if its not the main table then create the DT object for that table
                        dt_table = fields[table].get('dt_object', table)  #use table name as dt_object if not defined
                        temp[dt_table] = {}
                    for f in fields[table]['fields']:
                        if '{}.{}'.format(main_table, table) in row:
                            #print('{}.{} (complex object) in row with value'.format(table, f), row)
                            temp[dt_table][f] = row['{}.{}'.format(dt_table, f)]
                            del row['{}.{}'.format(table, f)]
                        elif f in row:
                            #print('{} (single object) in row with value: "{}"'.format(f, row[f]))
                            #print(f, upload_many)

                            upload_many_dict = {}
                            upm_key = ''
                            for u in upload_many:
                                if f in upload_many[u]:
                                    upload_many_dict = upload_many[u]
                                    upm_key = u

                            if upload_many_dict:
                                #print(upload_many_dict, row[f])
                                if upm_key not in temp:
                                    temp[upm_key] = []
                                if row[f] is None:
                                    temp[upm_key] = []
                                else:
                                    try:
                                        temp[upm_key] = json.loads(row[f])
                                        temp[upm_key] = [{'id': int(i['id'])} for i in temp[upm_key]]
                                    except:
                                        temp[upm_key] =[]

                            if type(row[f]) != type(' ') and (f[:3] == 'fk_' and f[-5:] == '_list') and row[f] is not None:
                                error_list.append('Field {} returned type: {}, value: {} when expecting string'.format(f, type(row[f]), row[f]))
                                #print('Field {} returned type: {}, value: {} when expecting string'.format(f, type(row[f]), row[f]))
                            if f[:3] == 'fk_' and f[-5:] == '_list':
                                if row[f] is None:
                                    row[f] = ''
                                temp[dt_table][f] = [int(x) for x in row[f].split(',')] if row[f] else ''
                            else:
                                temp[dt_table][f] = row[f]
                            del row[f]
                        else:
                            pass
                            #print('key "{}" not found in result dictionary {}'.format(f, table))
                            #error_list.append('key "{}" not found in result dictionary'.format(f))
                multi = {}
                for selects in row:
                    #print('dt_object', selects)
                    if selects.count('$') == 1:
                        table, label_value = selects.split('$')
                        dt_table = fields[table].get('dt_object', table)
                        if dt_table not in multi:
                            multi[dt_table] = {}
                        multi[dt_table][label_value] = [int(x) for x in row[selects].split(',')] if label_value == 'value' and row[selects] else row[selects].split(',') if row[selects] else ''
                    elif selects.count('.') == 1:
                        table, field = selects.split('.')
                        #print(table, field)
                        dt_table = fields[table].get('dt_object', table)
                        temp[dt_table][field] = row[selects]
                for m in multi:
                    temp[m] = []
                    if len(multi[m]['value']) == len(multi[m]['label']):
                        while multi[m]['value']:
                            temp[m].append({'value': multi[m]['value'].pop(0),
                                            'label': multi[m]['label'].pop(0)
                                            })
                collect_data.append(temp)
                #print ('temp dict:', temp)
            # if row:
            #    error_list.append('Items remaining from sql result after parsing: {}'.format(str(row)))
            #print 'collect_data'
            #pprint(collect_data)
            #print('get_table_data debug', debug)

        options = self.build_editor_options(options_list)
        logger.debug('Options: {}'.format(options))

        if get_uploads:
            files = self.get_uploaded_files()

        if error_list:
            if debug:
                return {'error': error_list, 'sql': self.db.sql}
            return {'error': error_list}
        else:
            if debug:
                return {'data': collect_data, 'options': options, 'files': files,
                        'sql': sql, 'errors': '{} (sql: {}'.format(self.db.error, self.db.sql) if self.db.error else ''}
            return {'data': collect_data, 'options': options}

    def validate_table_data(self, pkid, record, table_name, action, object_prefix='', upload_many=None, tags=None):
        logger.debug('Validate pkid: {}, record: {}, table name: "{}", action: "{}"'.format(pkid, record, table_name, action))

        if not upload_many:
            upload_many = {}
        upm_values = [v for k, v in upload_many.items()]
        #print('upm_values', upm_values)

        if object_prefix:
            object_prefix = object_prefix + '.'
        field_errors = []
        result_name = ''
        sql = 'select column_name, column_type, column_key, column_comment ' \
              'from information_schema.columns ' \
              'where table_name = "{}"'.format(table_name)
        logger.debug('Col Requirments query: {}'.format(sql))
        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)
        #print ('validate_table_data table_schema')
        #pprint(result)
        column_requirements = {}
        delete_fields = []
        add_fields = []
        for r in result:
            #print r
            match = re.match(r'^([a-zA-Z]*)(?:(?:\()*(.*)(?:\)))*', r['column_type'])
            #print r['column_name'], match.groups()
            #print r['column_name'], repr(r['column_comment'])
            temp = re.sub(r'[\x93|\x94]', '"', r['column_comment'])
            #print temp
            try:
                reqs = json.loads(temp)
            except Exception as e:
                #print e
                reqs = {}
            column_requirements[r['column_name']] = {'column_type': match.group(1) if match else '',
                                                     'column_length': int(match.group(2)) if match and match.group(
                                                         2) and match.group(2).isdigit() else 0,
                                                     'column_key': r['column_key'],
                                                     'column_reqs': reqs
                                                     }
        #logger.debug('Column requirements: {}'.format(column_requirements))
        #print('column_requirements')
        #pprint(column_requirements)
        many_count = []
        foreign_tables = {}
        #print ('validate record', record)
        for r in record.keys():  # see if there are any multi-select fields being updated
            match = re.match(r'^(.*)?-many-count$', r)
            if match:  # match.group(0) is "dt_parent_test-many-count" and match.group(1) is "dt_parent_test"
                #print match.group(0)   #the -many-count field
                #print match.group(1)
                ftable_name = match.group(1)
                #print record[match.group(0)]
                #print r, record[r]
                if int(record[match.group(0)]) > 0:  #don't process if 0 values in multi select field
                    if ftable_name not in record:
                        field_errors.append({'name': ftable_name,
                                             'status': 'System error: No field found for multi-select'})
                        continue
                    if ftable_name[:3] == 'fk_':
                        ftable_name = ftable_name[3:]
                        if ftable_name[-5:] == '_list':
                            ftable_name = ftable_name[:-5]
                    foreign_tables[ftable_name] = {'field': 'fk_{}'.format(table_name),
                                                   'value': pkid,
                                                   'pkid': record[match.group(1)]
                                                   }
                if int(record[match.group(0)]) == 0 and ftable_name not in record:  # add column if it doesn't exists and there are no items selected
                    record[ftable_name] = ''        #blank out the empty multi select
        #print foreign_tables   #the foriegn talbe is not currently used
        if action == 'create' and pkid == 0 and 'pkid' in record:
            # print 'deleteing pkid for new record'
            del record['pkid']
        if action == 'create' and pkid == 0 and 'DT_RowId' in record:
            # print 'deleteing pkid for new record'
            del record['DT_RowId']
        for r in record:
            logger.debug('Validating: {}: {}'.format(r, record[r]))
            # print column_requirements[r]
            # print type(column_requirements[r]['column_length'])
            if r[-11:] == '-many-count':   #don't process the returned object <field>-many-count
                delete_fields.append(r)
                continue
            if r == 'row_order':
                delete_fields.append(r)
                continue
            logger.debug('Field {} found in column_requirements: {}'.format(r, r in column_requirements))
            if r in column_requirements:
                #print('checking column reqs', column_requirements[r]['column_key'], r)
                if record[r] == '' and column_requirements[r]['column_reqs']:
                    #print('{}, {}, {}, "{}"'.format(r, column_requirements[r]['column_reqs'], action , record[r]))
                    if (action == 'create' and
                                column_requirements[r]['column_reqs'].get('insert', '').lower() != 'required') \
                                or (action == 'edit' and
                                column_requirements[r]['column_reqs'].get('update', '').lower() != 'required'):
                        #print 'not required field'
                        if r[:3] == 'fk_':
                            #print 'found fk'
                            delete_fields.append(r)
                            continue
                        elif column_requirements[r]['column_type'] == 'int':
                            #print 'found int'
                            record[r] = '0'


                if column_requirements[r]['column_type'] == 'varchar':
                    logger.debug('Column: {}, DB Type: {}, Action: {}, Content: "{}", Type: {}'.format(r,
                                                                                                       column_requirements[r]['column_type'],
                                                                                                       action ,
                                                                                                       record[r],
                                                                                                       type(record[r])))
                    #print(type(record[r]))
                    try:
                        record[r] = re.sub(r'\xa0', ' ', record[r])
                    except:
                        pass
                    try:
                        record[r] = re.sub(r"'", r"\'", record[r])
                    except:
                        pass
                    if type(record[r]) == type([]):
                        if r in upm_values:
                            record[r] = json.dumps(record[r])
                        else:
                            record[r] = ','.join(record[r])
                    elif type(record[r]) != type(' ') and type(record[r].encode()) != type(' '):   #not a string
                        record[r] = re.sub(r'\xa0', ' ', record[r])
                        record[r] = re.sub(r"'", r"\'", record[r])
                        temp = str(type(record[r].encode())).replace('<', '').replace('>', '')
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Required type varchar(string) but submitted as ' + temp})
                        continue
                    elif len(record[r]) > column_requirements[r]['column_length']:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Data length ({}) greater than DB length of {}'.format(
                                                 len(record[r]), column_requirements[r]['column_length'])})
                        continue
                elif column_requirements[r]['column_type'] == 'int':
                    try:
                        #print('int: ', repr(record[r]))
                        temp = int(record[r])
                        record[r] = temp
                    except:
                        #print('** not isdigit?', not record[r].isdigit(), r, record[r])
                        temp = str(type(record[r])).replace('<', '').replace('>', '')
                        #print(repr(temp), len(record[r]))
                        if temp == "class 'str'":
                            if len(record[r]) == 0:
                                record[r] = '^NULL^' if action.lower() == 'edit' else 'NULL'
                                #todo: simply just adding null of integer value is blank string  do we want to make sure its a fkey field?
                                #todo: and throw error if not
                                #todo: using null is for the cae of using select2 and deleting all options for no selection
                                #field_errors.append({'name': object_prefix + r,
                                #                     'status': 'Required type int but submitted as ' + temp})
                                continue

                            #if the field is a fk field and the field is found in tags then add a new tag and get the new pkid
                            if r[:3] == 'fk_' and r[3:] in tags:
                                fk_table = r[3:]
                                fk_field = tags[fk_table]
                                fk_value = record[r]
                                sql = 'insert ignore into {} ({}) values ("{}")'.format(fk_table, fk_field, fk_value)
                                self.db.db_command(sql=sql)
                                sql = 'select pkid from {} where {} = "{}"'.format(fk_table, fk_field, fk_value)
                                uid = gen_uid()
                                pkid = self.db.db_command(sql=sql, uid=uid).one(uid)
                                if pkid:
                                    record[r] = pkid['pkid']
                                else:
                                    field_errors.append({'name': object_prefix + r,
                                                         'status': 'Unable to add {} to table {}'.format(fk_value, fk_table)})
                                continue

                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Required type int but submitted as ' + temp})
                        continue
                    if len(str(record[r])) > column_requirements[r]['column_length']:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Data length ({}) greater than DB length of {}'.format(
                                                 len(record[r]), column_requirements[r]['column_length'])})
                        continue
                elif column_requirements[r]['column_type'] == 'date':
                    if len(record[r]) == 0:
                        delete_fields.append(r)
                        continue
                        # elif
                        #    temp = str(type(record[r].encode())).replace('<', '').replace('>', '')
                        #    field_errors.append({'name': object_prefix + r,
                        #                         'status': 'Required type int but submitted as ' + temp})
                        #    continue
                else:
                    print('Field not validated', r, record[r])
                if column_requirements[r]['column_key'] and action == 'create':
                    #print('checking for duplicate record ', r, record[r])
                    sql = 'select {column} from {table_name} where {column} = "{value}"'.format(column=r,
                                                                                                table_name=table_name,
                                                                                                value=record[r]
                                                                                                )
                    uid = gen_uid()
                    temp = self.db.db_command(sql=sql, uid=uid).one(uid)
                    if temp:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Duplicate data, modify to be unique.'})
                    continue
                if column_requirements[r]['column_key'] and action == 'edit':
                    #print('checking for duplicate record ', r, record[r], record['pkid'])
                    sql = 'select {column}, pkid from {table_name} where {column} = "{value}"'.format(column=r,
                                                                                                table_name=table_name,
                                                                                                value=record[r]
                                                                                                )
                    uid = gen_uid()
                    temp = self.db.db_command(sql=sql, uid=uid).one(uid)
                    #print(pkid, temp, record)
                    #print( temp['pkid'] == int(record['pkid']))
                    if temp and temp['pkid'] != pkid:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Duplicate data, modify to be unique.'})
                    continue
            else:
                if r == 'DT_RowId':
                    delete_fields.append(r)
                else:
                    return {'error': 'Unable to validate field "{}"'.format(r)}

        #print 'field errors:', field_errors
        if field_errors:
            return {'fieldErrors': field_errors}
        else:
            for r in delete_fields:
                del record[r]
            for r in add_fields:
                for field in r:
                    record[field] = r[field]
            #print 'return validated records'
            #pprint (record)
            return record

    def update_table_data(self, pkid, record, table_name):
        #print ('update_table_data', pkid, record, table_name)
        if record:                  #may be blank due to parent table field containing list of child elements, ie, app_teast_suite editor and reordering child test cases
            field_value_pairs = []
            update_error = False
            for r in record:
                if record[r] == '^NULL^':
                    field_value_pairs.append("{} = {}".format(r, record[r].replace('^', '')))
                else:
                    field_value_pairs.append("{} = '{}'".format(r, record[r]))
                #print "{} = '{}'".format(r, record[r])
            sql = 'update {table_name} set {field_pairs} where pkid = "{pkid}"'.format(table_name=table_name,
                                                                                       field_pairs=','.join(
                                                                                           field_value_pairs),
                                                                                       pkid=pkid)
            #print (sql)
            self.db.db_command(sql=sql)
            # if sql_conn.sql_execute_result == 0:
            #    update_error = True
            #print 'update error:', update_error
            if not update_error:
                return {}
            else:
                return {'error': 'update_table_data is unable to update {} with SQL query: {}'.format(table_name, sql)}
        return {}

    def create_table_data(self, data, table_name):
        """
        Save updated links to sql
        :param key_name: Name of the
        :param links: Set of links to update
        :return: Blank dict if successful else dict with key 'error' and error message
        """
        update_error = False
        #print 'create_table_data', data
        hostname = ''
        object_name = ''
        if type(data) != type(list):
            data = [data]
        for record in data:
            fields = []
            values = []
            object_name = ''
            for r in record:
                # print 'create', r, record[r]
                if r == 'name':
                    object_name = record[r]
                #todo:  find more automated way to get unique field name
                elif r in ['hostname', 'type', 'property'] and not object_name:
                    object_name = record[r]
                if r != 'pkid':
                    if record[r] != 'NULL':
                        fields.append(r)
                        values.append(str(record[r]))
            sql = "insert into {table_name} ({fields}) values ('{values}') ".format(table_name=table_name,
                                                                                    fields=','.join(fields),
                                                                                    values="','".join(values))
            #print sql
            self.db.db_command(sql=sql)
            #print sql_conn.sql_execute_result
            if self.db.error:
                update_error = True
        if not update_error:
            unique_col = self.get_unique_column(table_name)
            sql = 'select pkid from {table_name} where {unique_col} = "{object_name}"'.format(table_name=table_name,
                                                                                             object_name=object_name,
                                                                                             unique_col=unique_col)
            #print(sql)
            uid = gen_uid()
            result = self.db.db_command(sql=sql, uid=uid).one(uid)
            #print(result)
            if result:
                return result
            else:
                return {
                    'error': 'create_table_data is unable to retrieve inserted data collections with SQL query: {}'.format(
                        sql)}
        else:
            return {'error': 'create_table_data is unable to update data collections with SQL query: {}'.format(sql)}

    def verify_updated_table_data(self, pkid='', sql='', fields='', upload_many = None):
        """
        Verify updated links are properly written to SQL
        :param key_name: List of key names to verify
        :return: dict with key 'data' with updated link info and linkOrder field or key 'error' with error message
        """
        logger.debug('verify_updated_table pkid: {}, sql: {}, fields: {}'.format(pkid, sql, fields))
        #print 'checking fields', fields
        print('pkid', pkid)
        if pkid and type(pkid) == type([]) and pkid[0]:

            if sql and 'where' not in sql.lower():

                #todo: temp code to get table name from sql
                match = re.search(r'from (\w+)?\s', sql)
                if match:
                    table_name = '{}.'.format(match.group(1))
                else:
                    table_name = ''

                sql = sql + ' where {}pkid in ("{}")'.format(table_name, '","'.join([str(x) for x in pkid]))

            logger.debug('Retrieving record using SQL: {}'.format(sql))
            result = self.get_table_data(pkid=pkid, sql=sql, fields=fields, upload_many=upload_many)
            logger.debug('Retieved data to verify: {}'.format(result))
            #pprint(result)
            updated_data = []
            updated_keys = []
            if result:
                data = {}
                for data in result['data']:
                    logger.debug('Verifying data: {}'.format(data))
                    if 'main' in data:
                        if 'pkid' in data['main']:
                            #print 'pkid in main', data['main']['pkid']
                            updated_keys.append(str(data['main']['pkid']))
                        updated_data.append(data['main'])
                    else:
                        if 'pkid' in data:
                            #print 'pkid in main', data['main']['pkid']
                            updated_keys.append(str(data['pkid']))
                        updated_data.append(data)

                logger.debug('comparing pkid list {} to updated list {}'.format(sorted(pkid), sorted(updated_keys)))
                if sorted(pkid) == sorted(updated_keys):
                    logger.debug('verify updated: {}'.format(result['data']))
                    return result['data']   #changed this from data to result['data'] to return pkid list
                else:
                    return {'error': 'verify_updated_table_data retrieved data but could not find updated data.'}
            else:
                return {'error': 'verify_updated_table_data could not retrieve data.'}
        else:
            return {'error': 'verify_updated_table_data did not receive key_names parameters.'}

    def get_table_data_dependencies(self, pkid, table_name):
        logger.debug('table dependancies: {}, {}'.format(pkid, table_name))
        if table_name[:3] == 'fk_':
            table_name = table_name[3:]
        dependencies = []
        sql = 'select table_name, column_name ' \
              'from information_schema.columns ' \
              'where column_name like "%{}%"'.format('fk_' + table_name)
        #print sql
        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)
        #print result
        for r in result:
            if r['column_name'][-4:] == 'list':
                sql = 'select count(pkid) from {table} where FIND_IN_SET({pkid}, {field})'.format(table=r['table_name'], field=r['column_name'], pkid=pkid)
            else:
                sql = 'select count(pkid) from {} where {} = "{}"'.format(r['table_name'], r['column_name'], pkid)
            print(sql)
            uid = gen_uid()
            result_count = self.db.db_command(sql=sql, uid=uid).one(uid)
            if result_count and result_count['count(pkid)'] > 0:
                dependencies.append('{} with {} dependencies'.format(r['table_name'], result_count['count(pkid)']))
        return r'</br>'.join(dependencies)

    def delete_table_data(self, pkid, table_name):
        error_pkids = []
        # print table_name
        field_errors = ''
        if pkid and table_name:
            sql = 'delete from {table_name} where pkid = "{pkid}"'.format(table_name=table_name,
                                                                          pkid=pkid
                                                                          )
            # print sql
            self.db.db_command(sql=sql)
            if self.db.error:
                error_pkids.append(str(pkid))
        # print field_errors
        if error_pkids:
            return {'error': 'Error deleting records with PKIDs: {}.'.format(','.join(error_pkids))}
        elif field_errors:
            return {'error': field_errors}
        else:
            return {}

    def dt_row_reorder(self, records):
        #print 'checking for row reorder', records
        for r in records:
            #print r
            #print records[r]
            #print len(records[r])
            if 'DT_RowId' not in records[r] or len(records[r]) > 1:  #if only DT_RowId in record then it may be a row reorder
                return False
        return True

    def parse_request(self, allow_row_reorder=True, debug=False, *args, **kwargs):
        logger.debug('parse_request: {}'.format(kwargs))


        sql_param = kwargs.pop('sql', '')
        fields = kwargs.get('fields', {})

        main_table = kwargs.get('table','')
        tags = {}

        for f in fields:
            #print(f, type(fields[f]), fields[f])
            if type(fields[f]) == type({}) and fields[f].get('tags', False):
                field_name = fields[f].get('fields', '')

                if type(field_name) == type([]):
                    field_name = field_name[0]
                if field_name:
                    tags[f] = field_name
        #print('Tagged fields', tags)
        #print('parse request', fields)
        options_list = kwargs.pop('options_list', '')
        get_uploads = kwargs.get('get_uploads', False)
        upload_many = kwargs.get('uploadMany', '')
        #debug = kwargs.pop('debug', False)
        self.active_testbed = kwargs.pop('active_testbed', 0)

        if not kwargs:  # child table kwargs request is blank
            return {'data': {}}
        elif 'pkid' in kwargs and 'action' not in kwargs:
            data = self.get_table_data(pkid=kwargs['pkid'], sql=sql_param, fields=fields, options_list=options_list, debug=debug, get_uploads=get_uploads, upload_many=upload_many)
            # print 'manage_{} datatables data\n'.format(main_table), json.dumps(data, cls=DatetimeEncoder)
            return data
        elif '_' in kwargs:  # get request from DataTables
            data = self.get_table_data(sql=sql_param, fields=fields, options_list=options_list, debug=debug, get_uploads=get_uploads, upload_many=upload_many)
            # print 'manage_{} datatables data\n'.format(main_table), json.dumps(data, cls=DatetimeEncoder)
            return data

        elif 'action' in kwargs:
            #print ('manage_{} action kwargs'.format(main_table), kwargs)
            if kwargs['action'] == 'upload':
                #print(kwargs)
                upload = {'uploadField': kwargs.get('uploadField', ''),
                        'upload': kwargs.get('upload', None),
                          'request_body': kwargs.get('request_body', None)
                        }

                result = self.upload_file(upload)
                #print(result)
                if 'filename' in result:
                    sql = 'insert ignore into uploads (filename) values ("{}")'.format(result['filename'])
                    self.db.db_command(sql=sql)
                    sql = 'select pkid from uploads where filename = "{}"'.format(result['filename'])
                    uid = gen_uid()
                    pkid = self.db.db_command(sql=sql, uid=uid).one(uid)
                    #print('pkid', pkid)
                    sql = 'update uploads set id = {pkid}, timestamp = NOW(), filesize = "{d[filesize]}", system_path = "{d[system_path]}", web_path = "{d[web_path]}" ' \
                          'where pkid = "{pkid}"'.format(d=result, pkid=pkid['pkid'])
                    self.db.db_command(sql=sql)

                    sql = 'select * from uploads where filename = "{}"'.format(result['filename'])
                    uid = gen_uid()
                    uploaded = self.db.db_command(sql=sql, uid=uid).one(uid)

                    result = {
                                "files": {
                                        "files": {
                                                uploaded['id']: uploaded
                                        }
                                },
                                    "upload": {
                                        "id": uploaded['id']
                                    }
                            }

                return result
            main_table = fields.get('main', {}).get('table', main_table)
            records = self.parse_DT_post(kwargs, upload_many=upload_many)
            #print ('parse_DT_post results', records)
            row_reorder = self.dt_row_reorder(records)
            if kwargs['action'] == 'edit' and row_reorder and allow_row_reorder:
                updated_rows = {}
                updated_pkids = []
                #print('row reorder')
                for r in records:
                    #print ('processing pkid {} moving to {}'.format(r, records[r]))
                    updated_pkids.append(str(r))
                    sql = 'select row_order from {main_table} where pkid = "{pkid}"'.format(main_table=main_table,
                                                                                        pkid=records[r]['DT_RowId'])
                    #print sql
                    uid = gen_uid()
                    new_row_id = self.db.db_command(sql=sql, uid=uid).one(uid)
                    #print 'new row id', new_row_id
                    if new_row_id:
                        updated_rows[r] = new_row_id['row_order']
                for r in updated_rows:
                    sql = 'update {main_table} set row_order = "{value}" where pkid = "{pkid}"'.format(main_table=main_table,
                                                                                                      value=updated_rows[r],
                                                                                                      pkid=r)
                    #print sql
                    self.db.db_command(sql=sql)
                result = self.verify_updated_table_data(updated_pkids, sql=sql_param, fields=fields)
                #print 'got back verified data'
                #pprint(result)
                if 'error' in result:
                    return result
                return {'data': result}
            elif kwargs['action'] == 'edit' or kwargs['action'] == 'create':
                #print('edit', kwargs)
                results = []
                for pkid in records:
                    logger.debug('Processing edit or create for table:{}, pkid:{}, record: {}'.format(main_table, pkid, records[pkid]))
                    validation = self.validate_table_data(pkid, records[pkid], main_table, kwargs['action'],
                                                          object_prefix='main', upload_many=upload_many, tags=tags)
                    if 'fieldErrors' in validation or 'error' in validation:
                        logger.error('Processing edit or create validation errors: {}'.format(validation))
                        return validation
                    elif validation:
                        records[pkid] = validation
                    if kwargs['action'] == 'edit':
                        result = self.update_table_data(pkid, records[pkid], main_table)
                        logger.debug('Edit records result: {}'.format(result))
                        if 'error' in result:
                            logger.error('Edit errors: {}'.format(result))
                            return result
                        result = self.verify_updated_table_data([str(pkid)], sql=sql_param, fields=fields, upload_many=upload_many)
                        if 'error' in result:
                            logger.error('Edit validation data errors: {}'.format(result))
                            return result
                    else:
                        result = self.create_table_data(records[pkid], main_table)
                        if 'error' in result:
                            logger.error('Create errors: {}'.format(result))
                            return result
                        result = self.verify_updated_table_data([str(result['pkid'])], sql=sql_param, fields=fields, upload_many=upload_many)
                        if 'error' in result:
                            logger.error('Create valdation data errors: {}'.format(result))
                            return result

                    results.append(result[0] if type(result) == type([]) else result)
                logger.debug('Edit or create results: {}'.format(results))
                return {'data': results}  #result was returned in a list previously [result]
            elif kwargs['action'] == 'remove':
                result = {'error': 'No pkids in delete for table {}'.format(main_table)}
                for pkid in records:
                    result = self.get_table_data_dependencies(pkid, main_table)
                    if result:
                        # print 'dependencies', result
                        result = {
                            'error': 'Unable to delete record, please remove the following dependencies:</br>' + result}
                    else:
                        result = self.delete_table_data(pkid, main_table)
                        # print 'manage_{} delete result'.format(main_table), result
                return result


    def upload_file(self, kwargs):
        UPLOAD_WEB_PATH = './public/uploads/{}'
        upload = kwargs.get('upload', None)
        request_body = kwargs.get('request_body', None)
        #print('uploadField', kwargs.get('uploadField'))
        #print('upload filename', upload.filename)

        upload_file = upload.file.read()



        #print(len(upload_file))

        try:
            with open(UPLOAD_WEB_PATH.format(upload.filename), 'wb') as f:
                f.write(upload_file)
                """
                According to this thread using the below is more memory efficient fo rlarge files
                Need a way to get the file size
                https://stackoverflow.com/questions/26576349/streaming-post-a-large-file-to-cherrypy-by-python-client
                """
                #todo: investigate using shutil.copyfileobj
                #shutil.copyfileobj(request_body, f)
            #todo: see if the warning can be hidden / suppressed
            #might get warning (seems to be ok though): ResourceWarning: unclosed file <_io.BufferedRandom name=13> self.cpapp.release_serving()
        except Exception as e:
            logger.error('File upload exception for file {}: {}'.format(upload.filename, e))
            result = {'error': 'Unable to save file, error: {}'.format(e)}
        else:
            result = {'filename': upload.filename,
                      'filesize': len(upload_file),
                      'web_path': UPLOAD_WEB_PATH.format(upload.filename),
                      'system_path': UPLOAD_WEB_PATH.format(upload.filename)
                      }
        return result





class DTSpelunker(Datatables):

    def __init__(self):

        super(DTSpelunker, self).__init__()

    ######################
    #
    # Testbed web page - Datatables code
    #
    ######################

    def get_active_testbed (self):
        return self.active_testbed

    def is_testbed_table(self, table):
        sql = 'show columns from {} like "fk_testbeds"'.format(table)
        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).one(uid)
        if result and 'Field' in result:
            return True
        else:
            return False

    def get_pkids(self, post):
        pkids= []

        for record in post:
            match = re.search(r'data\[([A-Za-z0-9_\-]+)\]', record)

            if match:
                pkid = match.group(1)

                if pkid not in pkids:
                    pkids.append(pkid)

        return pkids

    def parse_DT_post(self, post, upload_many=None):
        """
        post is from the DataTables Editor and
        :param post:
        :return:
        """
        #print('parse_DT_post post:', post)

        if not upload_many:
            upload_many = {}

        upm_keys = upload_many.keys()

        records = {}
        for record in post:
            logger.debug('record: {}'.format(record))
            #print('parse_DT_post record: {}'.format(record))
            match = re.findall(r'\[([A-Za-z0-9_\-]+)\]', record)
            logger.debug('match: {}'.format(match))
            if not match and record != 'action':
                if record != 'pkid':
                    logger.debug('parse_DT_post is unable to process DataTables post, found record name of "{}"'.format(record))
            elif match and len(match) < 2:
                logger.debug('parse_DT_post is unable to process DataTables post, regex match is "{}"'.format(str(match)))
            elif match:
                #print('match:', match)
                pkid = int(match.pop(0))
                if pkid not in records:
                    records[pkid] = {}
                files_table = match[0]
                if '-many-count' in files_table and files_table.split('-')[0] in upm_keys:
                    pass  #skip 'files-many-count': '2' data as this is not a multi field join record
                elif files_table in upm_keys:
                    # files update: ['1', 'files', '1', 'id'] - less pkid which was just popped
                    field = upload_many[files_table]
                    if field not in records[pkid]:
                        records[pkid][field] = []
                    #print('post[record]', post[record])
                    records[pkid][field].append({'id': str(post[record])})
                else:
                    records[pkid][match.pop()] = post[record]
                # records[match.group(1)][match.group(2)] = post[record]
            elif record != 'action':
                logger.debug('parse_DT_post is unable to process DataTables post, no match found for record {}'.format(record))
        #print('parse_DT_post records:', records)
        return records

    def build_editor_options(self, fk_list=None, blank_option=False):
        options = defaultdict(list)
        #print fk_list
        if type(fk_list) == type([]):
            for l in fk_list:
                if l == 'cucm':
                    sql = 'select pkid, type from types where object_type = "Cucm"'  #get all CUCM types (Pub, Sub, MoH, TFTP)
                    uid = gen_uid()
                    result = self.db.db_command(sql=sql, uid=uid).all(uid)
                    for r in result:            #get CUCM devices for each type from active testbed
                        sql = 'select pkid, hostname from hosts where fk_types = "{}" and fk_testbeds = "{}"'.format(
                            r['pkid'], self.get_active_testbed())
                        uid = gen_uid()
                        nodes = self.db.db_command(sql=sql, uid=uid).all(uid)
                        for n in sorted(nodes, key=lambda k: k['hostname']):
                            if r['type'].split(' ')[-1] != 'Pub':   #save as a multi select option if not the Pub
                                multi_value = '[]'
                            else:
                                multi_value = ''
                            options['main.{}{}'.format(r['type'].split(' ')[-1], multi_value)].append(
                                {'label': n['hostname'],            #save to the options as main.type or main.type[] for multi
                                 'value': n['pkid']
                                 })
                elif l == 'ucce':
                    sql = 'select pkid, type from types where object_type = "Ucce"'    #get all UCCE types - Main server componenet not the secondary definitions
                    uid = gen_uid()
                    result = self.db.db_command(sql=sql, uid=uid).all(uid)
                    for r in result:  #get UCCE devices for each type
                        sql = 'select pkid, hostname from hosts where fk_types = "{}" and fk_testbeds = "{}" and server = "1"'.format(
                            r['pkid'], self.get_active_testbed())
                        uid = gen_uid()
                        nodes = self.db.db_command(sql=sql, uid=uid).all(uid)
                        for n in sorted(nodes, key=lambda k: k['hostname']):        #assign to side a or side b options
                            if n['hostname'][-1].lower() == 'a':
                                options['main.side_a_pkid'].append({'label': n['hostname'],
                                                                    'value': n['pkid']
                                                                    })
                            elif n['hostname'][-1].lower() == 'b':
                                options['main.side_b_pkid'].append({'label': n['hostname'],
                                                                    'value': n['pkid']
                                                                    })
                            else:                                                    #if end of name is not 'a' or 'b' then assign to both sides
                                options['main.side_a_pkid'].append({'label': n['hostname'],
                                                                    'value': n['pkid']
                                                                    })
                                options['main.side_b_pkid'].append({'label': n['hostname'],
                                                                    'value': n['pkid']
                                                                    })
                elif type(l) == type(' '):
                    if l[-5:] == '_list':   #if the fkey ends in list then its a list and make a multi value
                        table = l[3:-5]     #table name is field name with 'fk_' and '_list' removed
                        multi_value = '[]'
                    else:
                        table = l[3:]       #table name is field name with 'fk_' removed
                        multi_value = ''    #Not a multi value
                    #print 'table', table
                    if table == 'types':    #deal with non-standard unique / index field names
                        index = 'type'
                    elif table == 'commands':
                        index = 'command'
                        multi_value = '[]'
                    elif table == 'hosts':
                        index = 'hostname'
                    else:
                        index = 'name'
                    if self.is_testbed_table(table):   #if table has fk_testbeds filed then limit options to active testbed
                        sql = 'select pkid, {} from {} where fk_testbeds = "{}"'.format(index, table,
                                                                                          self.get_active_testbed())
                    else:
                        sql = 'select pkid, {} from {}'.format(index, table)
                    # print sql
                    uid = gen_uid()
                    result = self.db.db_command(sql=sql, uid=uid).all(uid)
                    for r in sorted(result, key=lambda k: k[index]):  #return sorted options
                        options['main.{}{}'.format(l, multi_value)].append({'label': r[index],
                                                                            'value': r['pkid']
                                                                            })
                elif type(l) == type ({}):
                    if l['match'][-5:] == '_list':   #if the fkey ends in list then its a list and make a multi value
                        table = l['match'][3:-5]     #table name is field name with 'fk_' and '_list' removed
                        multi_value = '[]'
                    else:
                        table = l['match'][3:]       #table name is field name with 'fk_' removed
                        multi_value = ''    #Not a multi value
                    #print 'table', table
                    concat = '{}'.format(l['concat']) if 'concat' in l else ''   #build concat for the fields
                    where_clause = 'where fk_testbeds = "{}"'.format(self.get_active_testbed()) if self.is_testbed_table(table) else ''
                    sql = 'select pkid, concat({fields}) ' \
                                           'as label from {table} {where}'.format(table=table,
                                                             fields='{},'.format(concat)
                                                                       .join([table + '.' + x for x in l['fields']]),
                                                             field=l['fields'][0]
                                                                      if type(l['fields']) == type([]) else '',
                                                             where=where_clause
                                                             )
                    uid = gen_uid()
                    result = self.db.db_command(sql=sql, uid=uid).all(uid)
                    for r in sorted(result, key=lambda k: k['label']):  #return sorted options
                        options['main.{}{}'.format(l['match'], multi_value)].append({'label': r['label'],
                                                                            'value': r['pkid']
                                                                            })
        #sort options by label
        for o in options:
            #todo: determine the need of having a blankoptino with value of 0
            #if blank_option:
            #    pass
                #options[o].append({'label': '',
                #                    'value': 0
                #                    })
            options[o] = sorted(options[o], key=lambda k: k['label'])
        #print(options)

        return options

    def get_unique_column(self, table):
        if table == 'types':  # deal with non-standard unique / index field names
            return 'type'
        elif table == 'commands':
            return 'command'
        elif table == 'hosts':
            return 'hostname'
        else:
            return 'name'

    def get_uploaded_files(self):

        sql = 'select * from uploads'

        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)

        files = {}

        for r in result:
            files[r['id']] = r

        return {'files': files}



    def get_table_data(self, pkid='', sql='', fields='', options_list='', debug=False, get_uploads=False, upload_many=None):
        #print('get table data fields', fields)
        #print('options list', options_list)
        if not upload_many:     #make sure to process as dictionary
            upload_many = {}
        files = []
        if sql:
            if type(sql) == type(' '):
                uid = gen_uid()
                result = self.db.db_command(sql=sql, uid=uid).all(uid)
            else:
                uid = gen_uid()
                result = self.db.db_command(uid=uid,**sql).all(uid)
            if debug:
                return {'data': result, 'sql': self.db.sql, 'errors': self.db.error}
            return {'data': result}
        elif fields:

            where_clause = ''
            sql_join = []
            options = {}
            error_list = []
            group_by = ''
            if type(fields) != type({}) or not fields:  # basic sanity check
                return {'error': 'Fields is {}'.format('not a dictionary' if type(fields) != type({}) else 'empty')}
            elif 'main' not in fields:
                return {'error': 'Fields does not contain the object "main" for the main table'}
            elif 'table' not in fields['main'] or 'fields' not in fields['main']:
                return {
                    'error': 'Fields contains "main" object but does not contain either "table" or " fields" sub-objects'}

            if pkid:
                #print 'checking pkid', pkid, type(pkid)
                if type(pkid) == type(1):   #if pkid is number convert to string and put in list
                    pkid = [str(pkid)]
                elif type(pkid) == type([]):  #process list and build list of string pkids
                    # print 'pkid is a list'
                    temp = [str(item) for item in pkid if type(item) == type(1) or item.isdigit()]
                    # print temp
                    if len(temp) != len(pkid):
                        return {'error': 'PKID list contains non numeric elements "{}"'.format(str(pkid))}
                    pkid = ','.join(temp)
                elif type(pkid) == type(' '):   #pkid list is a string, process as CSV list
                    temp_pkid = pkid.split(',')
                    temp = [str(item) for item in temp_pkid if type(item) == type(int) or item.isdigit()]
                    if len(temp) != pkid.count(',') + 1:
                        return {'error': 'PKID string contains non numeric elements "{}"'.format(pkid)}
                    pkid = ','.join(temp)
                where_field = fields['main'].get('where', 'pkid')
                where_clause = ' where {table}.{field} in ({pkid}) '.format(table=fields['main']['table'],
                                                                            field=where_field,
                                                                            pkid=pkid)

            if options_list == '':
                options_list = []
            if options_list and type(options_list) != type([]):
                return {'error': 'options_list is not a list'}

            main_table = fields['main']['table']  # store the main table name in main_table
            if self.active_testbed:
                where_clause += ' and ' if where_clause else ' where '
                where_clause += ' {}.fk_testbeds = "{}" '.format(main_table, self.active_testbed)
            fields_list = []
            if 'pkid' not in fields['main']['fields']:  # make sure to get the row's pkid
                fields['main']['fields'].append('pkid')

            for table in fields['table_order']:   #use table_order list to process tables
                #print ('table:', table)
                if type(fields[table]['fields']) == type([]):
                    for field in fields[table]['fields']:  # build SQL select fields list with prefixed table names
                        #print ('table field:', table, field)
                        fields_list.append('{}.{}'.format(main_table if table == 'main' else table,  # use real field name if 'main'
                                                          field))
                    if table != 'main':  #joined table is not multiselect so build a simple join statement
                        #print('joined table is not multiselect so build a simple join statement')
                        sql_join.append(' {join_type} {table} as {object} on ' \
                                        '{object}.pkid = {main_table}.{match}'.format(join_type=fields[table]['type'],
                                                                                table=fields[table]['table'],
                                                                                object=table,
                                                                                main_table=main_table,
                                                                                match=fields[table]['match']
                                                                                ))
                        if 'fk_{}'.format(fields[table]['table']) not in options_list:
                            options_list.append('fk_{}'.format(fields[table]['table']))  # build options object names
                elif type(fields[table]['fields']) == type({}):  #dict used to specify PKID
                    if fields[table]['select'] == 'multi':
                        #print ('multi', fields[table]['match'], fields[table]['fields'])
                        concat = ',"{}"'.format(fields[table]['concat']) if 'concat' in fields[table] else ''
                        if '{}'.format(fields[table]['match']) not in options_list:
                            if type(fields[table]['fields']['fields']) == type([]):
                                options_list.append({'fields': fields[table]['fields']['fields'],
                                                     'concat': concat,
                                                     'match': '{}'.format(fields[table]['match'])
                                                     }
                                                    )  # build options object names with multi select [] and concat label
                            else:
                                options_list.append('{}'.format(fields[table]['match']))  # build options object names with multi select []
                        if 'fields' in fields[table]['fields'] and 'pkid' in fields[table]['fields']:
                            concat = ',"{}"'.format(fields[table]['concat']) if 'concat' in fields[table] else ''
                            fields_list.append('group_concat(distinct {fields} order by {table}.{field}) '   #build label, value pairs for html select
                                               'as {table}$label'.format(table=table,
                                                                        fields='{}, '.format(concat)
                                                                           .join([table + '.' + x for x in fields[table]['fields']['fields']]),
                                                                        field=fields[table]['fields']['fields'][0]
                                                                          if type(fields[table]['fields']['fields']) == type([]) else '',
                                                                        dt_object=fields[table]['dt_object']))
                            fields_list.append('group_concat(distinct {table}.{pkid} order by {table}.{field}) '
                                               'as {table}$value'.format(table=table,
                                                                       field=fields[table]['fields']['fields'][0]
                                                                          if type(fields[table]['fields']['fields']) == type([]) else '',
                                                                       pkid=fields[table]['fields']['pkid'],
                                                                               dt_object=fields[table]['dt_object']))
                        sql_join.append(' {join_type} {table} as {object} on find_in_set(' \
                                        '{table}.{pkid}, {main_table}.{match}) > 0'.format(join_type=fields[table]['type'],
                                                                                table=fields[table]['table'],
                                                                                object=table,
                                                                                main_table=main_table,
                                                                                pkid=fields[table]['fields']['pkid'],
                                                                                match=fields[table]['match']
                                                                                ))
                        if not group_by:
                            group_by = 'group by {}.pkid'.format(main_table)
                    elif fields[table]['select'] == 'single':           #don't need to build label/value pairs if single select
                        sql_join.append(' {join_type} {table} as {object} on ' \
                                '{object}.pkid = {main_table}.fk_{table}'.format(join_type=fields[table]['type'],
                                                                          table=fields[table]['table'],
                                                                          object=table,
                                                                          main_table=main_table
                                                                          ))
            order_by = []
            for o in fields['main'].get('order', ''):
                order_by.append(' {d[column]} {d[direction]} '.format(d=o))
            order_by = 'order by ' + ','.join(order_by) if order_by else ''
            limit_results = ' limit {} '.format(fields['main']['limit']) if 'limit' in fields['main'] else ''

            sql = 'select {fields} from {table} {join} {where} {group_by} {order_by} {limit_results}'.format(fields=', '.join(fields_list),
                                                                       table=main_table,
                                                                       join=' '.join(sql_join),
                                                                       where=where_clause,
                                                                       group_by=group_by,
                                                                       order_by=order_by,
                                                                       limit_results=limit_results
                                                                       )
            #print (sql)
            uid = gen_uid()
            result = self.db.db_command(sql=sql, uid=uid).all(uid)
            #pprint(result)
            #print(options_list)
            options = self.build_editor_options(options_list)

            if get_uploads:
                files = self.get_uploaded_files()

            #pprint (result)
            collect_data = []
            for row in result:
                #print('row: {}'.format(row))
                pkid = str(row['pkid'])
                #print 'row pkid', type(row['pkid']), row['pkid']
                temp = {'DT_RowId': pkid}
                temp['main'] = defaultdict(list)
                for table in fields['table_order']:  # loop through all the tables provided
                    #print('processing table: {}, {}'.format(table,fields[table]['fields']))
                    dt_table = 'main'
                    if table != 'main':  # if its not the main table then create the DT object for that table
                        dt_table = fields[table].get('dt_object', table)  #use table name as dt_object if not defined
                        temp[dt_table] = {}
                    for f in fields[table]['fields']:
                        if '{}.{}'.format(main_table, table) in row:
                            #print('{}.{} (complex object) in row with value'.format(table, f), row)
                            temp[dt_table][f] = row['{}.{}'.format(dt_table, f)]
                            del row['{}.{}'.format(table, f)]
                        elif f in row:
                            #print('{} (single object) in row with value: "{}"'.format(f, row[f]))
                            #print(f, upload_many)

                            upload_many_dict = {}
                            upm_key = ''
                            for u in upload_many:
                                if f in upload_many[u]:
                                    upload_many_dict = upload_many[u]
                                    upm_key = u

                            if upload_many_dict:
                                #print(upload_many_dict, row[f])
                                if upm_key not in temp:
                                    temp[upm_key] = []
                                if row[f] is None:
                                    temp[upm_key] = []
                                else:
                                    try:
                                        temp[upm_key] = json.loads(row[f])
                                        temp[upm_key] = [{'id': int(i['id'])} for i in temp[upm_key]]
                                    except:
                                        temp[upm_key] =[]

                            if type(row[f]) != type(' ') and (f[:3] == 'fk_' and f[-5:] == '_list') and row[f] is not None:
                                error_list.append('Field {} returned type: {}, value: {} when expecting string'.format(f, type(row[f]), row[f]))
                                #print('Field {} returned type: {}, value: {} when expecting string'.format(f, type(row[f]), row[f]))
                            if f[:3] == 'fk_' and f[-5:] == '_list':
                                if row[f] is None:
                                    row[f] = ''
                                temp[dt_table][f] = [int(x) for x in row[f].split(',')] if row[f] else ''
                            else:
                                temp[dt_table][f] = row[f]
                            del row[f]
                        else:
                            pass
                            #print('key "{}" not found in result dictionary {}'.format(f, table))
                            #error_list.append('key "{}" not found in result dictionary'.format(f))
                multi = {}
                for selects in row:
                    #print('dt_object', selects)
                    if selects.count('$') == 1:
                        table, label_value = selects.split('$')
                        dt_table = fields[table].get('dt_object', table)
                        if dt_table not in multi:
                            multi[dt_table] = {}
                        multi[dt_table][label_value] = [int(x) for x in row[selects].split(',')] if label_value == 'value' and row[selects] else row[selects].split(',') if row[selects] else ''
                    elif selects.count('.') == 1:
                        table, field = selects.split('.')
                        #print(table, field)
                        dt_table = fields[table].get('dt_object', table)
                        temp[dt_table][field] = row[selects]
                for m in multi:
                    temp[m] = []
                    if len(multi[m]['value']) == len(multi[m]['label']):
                        while multi[m]['value']:
                            temp[m].append({'value': multi[m]['value'].pop(0),
                                            'label': multi[m]['label'].pop(0)
                                            })
                collect_data.append(temp)
                #print ('temp dict:', temp)
            # if row:
            #    error_list.append('Items remaining from sql result after parsing: {}'.format(str(row)))
            #print 'collect_data'
            #pprint(collect_data)
            #print('get_table_data debug', debug)
            if error_list:
                if debug:
                    return {'error': error_list, 'sql': self.db.sql}
                return {'error': error_list}
            else:
                if debug:
                    return {'data': collect_data, 'options': options, 'files': files,
                            'sql': sql, 'errors': '{} (sql: {}'.format(self.db.error, self.db.sql) if self.db.error else ''}
                return {'data': collect_data, 'options': options}

    def validate_table_data(self, pkid, record, table_name, action, object_prefix='', upload_many=None, tags=None):
        #print ('validate', pkid, record)

        if not upload_many:
            upload_many = {}
        upm_values = [v for k, v in upload_many.items()]
        #print('upm_values', upm_values)

        if object_prefix:
            object_prefix = object_prefix + '.'
        field_errors = []
        result_name = ''
        sql = 'select column_name, column_type, column_key, column_comment ' \
              'from information_schema.columns ' \
              'where table_name = "{}"'.format(table_name)
        #print (sql)
        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)
        #print ('validate_table_data table_schema')
        #pprint(result)
        column_requirements = {}
        delete_fields = []
        add_fields = []
        for r in result:
            #print r
            match = re.match(r'^([a-zA-Z]*)(?:(?:\()*(.*)(?:\)))*', r['column_type'])
            #print r['column_name'], match.groups()
            #print r['column_name'], repr(r['column_comment'])
            temp = re.sub(r'[\x93|\x94]', '"', r['column_comment'])
            #print temp
            try:
                reqs = json.loads(temp)
            except Exception as e:
                #print e
                reqs = {}
            column_requirements[r['column_name']] = {'column_type': match.group(1) if match else '',
                                                     'column_length': int(match.group(2)) if match and match.group(
                                                         2) and match.group(2).isdigit() else 0,
                                                     'column_key': r['column_key'],
                                                     'column_reqs': reqs
                                                     }
        #print('column_requirements')
        #pprint(column_requirements)
        many_count = []
        foreign_tables = {}
        #print ('validate record', record)
        for r in record.keys():  # see if there are any multi-select fields being updated
            match = re.match(r'^(.*)?-many-count$', r)
            if match:  # match.group(0) is "dt_parent_test-many-count" and match.group(1) is "dt_parent_test"
                #print match.group(0)   #the -many-count field
                #print match.group(1)
                ftable_name = match.group(1)
                #print record[match.group(0)]
                #print r, record[r]
                if int(record[match.group(0)]) > 0:  #don't process if 0 values in multi select field
                    if ftable_name not in record:
                        field_errors.append({'name': ftable_name,
                                             'status': 'System error: No field found for multi-select'})
                        continue
                    if ftable_name[:3] == 'fk_':
                        ftable_name = ftable_name[3:]
                        if ftable_name[-5:] == '_list':
                            ftable_name = ftable_name[:-5]
                    foreign_tables[ftable_name] = {'field': 'fk_{}'.format(table_name),
                                                   'value': pkid,
                                                   'pkid': record[match.group(1)]
                                                   }
                if int(record[match.group(0)]) == 0 and ftable_name not in record:  # add column if it doesn't exists and there are no items selected
                    record[ftable_name] = ''        #blank out the empty multi select
        #print foreign_tables   #the foriegn talbe is not currently used
        if action == 'create' and pkid == 0 and 'pkid' in record:
            # print 'deleteing pkid for new record'
            del record['pkid']
        if action == 'create' and pkid == 0 and 'DT_RowId' in record:
            # print 'deleteing pkid for new record'
            del record['DT_RowId']
        for r in record:
            #print('validate_table_data record', r, record[r])
            # print column_requirements[r]
            # print type(column_requirements[r]['column_length'])
            if r[-11:] == '-many-count':   #don't process the returned object <field>-many-count
                delete_fields.append(r)
                continue
            if r == 'row_order':
                delete_fields.append(r)
                continue
            if table_name in ('app_test_cases', 'test_cases') and r == 'test_case':   # special case for YAML field in app_test_cases
                #print 'testing yaml', r
                try:
                    temp = record[r].encode() if type(record[r]) == type(u' ') else record[r]
                    yaml.load(temp)
                except Exception as e:
                    #print 'yaml conversion error', str(e)
                    field_errors.append({'name': object_prefix + r,
                                         'status': 'YAML conversion error: ' + str(e)})
                    continue
            if (table_name == 'app_test_suites' and r == 'fk_app_test_cases_list') or \
                    (table_name == 'test_suites' and r == 'fk_test_cases_list'):   # get original pkid list and add new to the end of list
                sql = 'select {fk_list} from {table} where pkid = "{pkid}"'.format(fk_list=r,
                                                                                   table=table_name,
                                                                                   pkid=pkid)
                uid = gen_uid()
                pkid_list = self.db.db_command(sql=sql, uid=uid).one(uid)
                if pkid_list:
                    updated_pkid_list = []
                    pkid_list = pkid_list[r].split(',')
                    #print 'pkid_list', pkid_list
                    #print record[r]
                    new_pkid_list = list(record[r]) if type(record[r]) == type([]) else [record[r]]    #get list of pkids from the editor
                    #print 'new list', new_pkid_list
                    while pkid_list:
                        pkid_value = pkid_list.pop(0)
                        #print 'got pkid value', pkid_value
                        if pkid_value in new_pkid_list:   #if sotred pkid in new list then append to updated list and removed from new list
                            #print 'pkid {} in list {}'.format(pkid_value, str(new_pkid_list))
                            updated_pkid_list.append(pkid_value)   #if not in new list then that pkid was removed
                            new_pkid_list.remove(pkid_value)
                    #print 'updated pkid list', updated_pkid_list
                    updated_pkid_list.extend(new_pkid_list)   #extend updated list with remaining new - newly added from editor
                    #print 'extended pkid list', updated_pkid_list
                    record[r] = list(updated_pkid_list)
            if r in column_requirements:
                #print('checking column reqs', column_requirements[r]['column_key'], r)
                if record[r] == '' and column_requirements[r]['column_reqs']:
                    #print('{}, {}, {}, "{}"'.format(r, column_requirements[r]['column_reqs'], action , record[r]))
                    if (action == 'create' and
                                column_requirements[r]['column_reqs'].get('insert', '').lower() != 'required') \
                                or (action == 'edit' and
                                column_requirements[r]['column_reqs'].get('update', '').lower() != 'required'):
                        #print 'not required field'
                        if r[:3] == 'fk_':
                            #print 'found fk'
                            delete_fields.append(r)
                            continue
                        elif column_requirements[r]['column_type'] == 'int':
                            #print 'found int'
                            record[r] = '0'


                if column_requirements[r]['column_type'] == 'varchar':
                    #print('{}, {}, {}, "{}"'.format(r, column_requirements[r]['column_type'], action , record[r]))
                    #print(type(record[r]))
                    try:
                        record[r] = re.sub(r'\xa0', ' ', record[r])
                    except:
                        pass
                    try:
                        record[r] = re.sub(r"'", r"\'", record[r])
                    except:
                        pass
                    if type(record[r]) == type([]):
                        if r in upm_values:
                            record[r] = json.dumps(record[r])
                        else:
                            record[r] = ','.join(record[r])
                    elif not isinstance(record[r], str):   #not a string
                        record[r] = re.sub(r'\xa0', ' ', record[r])
                        record[r] = re.sub(r"'", r"\'", record[r])
                        temp = str(type(record[r].encode())).replace('<', '').replace('>', '')
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Required type varchar(string) but submitted as ' + temp})
                        continue
                    elif len(record[r]) > column_requirements[r]['column_length']:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Data length ({}) greater than DB length of {}'.format(
                                                 len(record[r]), column_requirements[r]['column_length'])})
                        continue
                elif column_requirements[r]['column_type'] == 'int':
                    try:
                        #print('int: ', repr(record[r]))
                        temp = int(record[r])
                        record[r] = temp
                    except:
                        #print('** not isdigit?', not record[r].isdigit(), r, record[r])
                        temp = str(type(record[r])).replace('<', '').replace('>', '')
                        #print(repr(temp), len(record[r]))
                        if temp == "class 'str'":
                            if len(record[r]) == 0:
                                record[r] = '^NULL^' if action.lower() == 'edit' else 'NULL'
                                #todo: simply just adding null of integer value is blank string  do we want to make sure its a fkey field?
                                #todo: and throw error if not
                                #todo: using null is for the cae of using select2 and deleting all options for no selection
                                #field_errors.append({'name': object_prefix + r,
                                #                     'status': 'Required type int but submitted as ' + temp})
                                continue

                            #if the field is a fk field and the field is found in tags then add a new tag and get the new pkid
                            if r[:3] == 'fk_' and r[3:] in tags:
                                fk_table = r[3:]
                                fk_field = tags[fk_table]
                                fk_value = record[r]
                                sql = 'insert ignore into {} ({}) values ("{}")'.format(fk_table, fk_field, fk_value)
                                self.db.db_command(sql=sql)
                                sql = 'select pkid from {} where {} = "{}"'.format(fk_table, fk_field, fk_value)
                                uid = gen_uid()
                                pkid = self.db.db_command(sql=sql, uid=uid).one(uid)
                                if pkid:
                                    record[r] = pkid['pkid']
                                else:
                                    field_errors.append({'name': object_prefix + r,
                                                         'status': 'Unable to add {} to table {}'.format(fk_value, fk_table)})
                                continue

                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Required type int but submitted as ' + temp})
                        continue
                    if len(str(record[r])) > column_requirements[r]['column_length']:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Data length ({}) greater than DB length of {}'.format(
                                                 len(record[r]), column_requirements[r]['column_length'])})
                        continue
                elif column_requirements[r]['column_type'] == 'date':
                    if len(record[r]) == 0:
                        delete_fields.append(r)
                        continue
                        # elif
                        #    temp = str(type(record[r].encode())).replace('<', '').replace('>', '')
                        #    field_errors.append({'name': object_prefix + r,
                        #                         'status': 'Required type int but submitted as ' + temp})
                        #    continue
                else:
                    print('Field not validated', r, record[r])
                if column_requirements[r]['column_key'] and action == 'create':
                    #print('checking for duplicate record ', r, record[r])
                    sql = 'select {column} from {table_name} where {column} = "{value}"'.format(column=r,
                                                                                                table_name=table_name,
                                                                                                value=record[r]
                                                                                                )
                    uid = gen_uid()
                    temp = self.db.db_command(sql=sql, uid=uid).one(uid)
                    if temp:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Duplicate data, modify to be unique.'})
                    continue
                if column_requirements[r]['column_key'] and action == 'edit':
                    #print('checking for duplicate record ', r, record[r], record['pkid'])
                    sql = 'select {column}, pkid from {table_name} where {column} = "{value}"'.format(column=r,
                                                                                                table_name=table_name,
                                                                                                value=record[r]
                                                                                                )
                    uid = gen_uid()
                    temp = self.db.db_command(sql=sql, uid=uid).one(uid)
                    #print(pkid, temp, record)
                    #print( temp['pkid'] == int(record['pkid']))
                    if temp and temp['pkid'] != pkid:
                        field_errors.append({'name': object_prefix + r,
                                             'status': 'Duplicate data, modify to be unique.'})
                    continue
            elif r in ['device_type']:      #bubble edits
                #print 'bubble edit', record[r]
                if r == 'device_type':
                    if record[r] == '0':
                        add_fields.append({'ios': '0', 'server': '0'})
                    elif record[r] == '1':
                        add_fields.append({'ios': '1', 'server': '0'})
                    elif record[r] == '2':
                        add_fields.append({'ios': '0', 'server': '1'})
                    delete_fields.append(r)
                continue
            else:
                if r == 'DT_RowId':
                    delete_fields.append(r)
                else:
                    return {'error': 'Unable to validate field "{}"'.format(r)}

        #print 'field errors:', field_errors
        if field_errors:
            return {'fieldErrors': field_errors}
        else:
            for r in delete_fields:
                del record[r]
            for r in add_fields:
                for field in r:
                    record[field] = r[field]
            #print 'return validated records'
            #pprint (record)
            return record

    def update_table_data(self, pkid, record, table_name):
        #print ('update_table_data', pkid, record, table_name)
        if record:                  #may be blank due to parent table field containing list of child elements, ie, app_teast_suite editor and reordering child test cases
            field_value_pairs = []
            update_error = False
            for r in record:
                if record[r] == '^NULL^':
                    field_value_pairs.append("{} = {}".format(r, record[r].replace('^', '')))
                else:
                    field_value_pairs.append("{} = '{}'".format(r, record[r]))
                #print "{} = '{}'".format(r, record[r])
            sql = 'update {table_name} set {field_pairs} where pkid = "{pkid}"'.format(table_name=table_name,
                                                                                       field_pairs=','.join(
                                                                                           field_value_pairs),
                                                                                       pkid=pkid)
            #print (sql)
            self.db.db_command(sql=sql)
            # if sql_conn.sql_execute_result == 0:
            #    update_error = True
            #print 'update error:', update_error
            if not update_error:
                return {}
            else:
                return {'error': 'update_table_data is unable to update {} with SQL query: {}'.format(table_name, sql)}
        return {}

    def create_table_data(self, data, table_name):
        """
        Save updated links to sql
        :param key_name: Name of the
        :param links: Set of links to update
        :return: Blank dict if successful else dict with key 'error' and error message
        """
        update_error = False
        #print 'create_table_data', data
        hostname = ''
        object_name = ''
        if type(data) != type(list):
            data = [data]
        for record in data:
            fields = []
            values = []
            object_name = ''
            for r in record:
                # print 'create', r, record[r]
                if r == 'name':
                    object_name = record[r]
                elif r in ['hostname', 'type'] and not object_name:
                    object_name = record[r]
                if r != 'pkid':
                    if record[r] != 'NULL':
                        fields.append(r)
                        values.append(str(record[r]))
            if self.is_testbed_table(table_name):
                fields.append('fk_testbeds')
                values.append(str(self.get_active_testbed()))
            sql = "insert into {table_name} ({fields}) values ('{values}') ".format(table_name=table_name,
                                                                                    fields=','.join(fields),
                                                                                    values="','".join(values))
            #print sql
            self.db.db_command(sql=sql)
            #print sql_conn.sql_execute_result
            if self.db.error:
                update_error = True
        if not update_error:
            unique_col = self.get_unique_column(table_name)
            sql = 'select pkid from {table_name} where {unique_col} = "{object_name}"'.format(table_name=table_name,
                                                                                             object_name=object_name,
                                                                                             unique_col=unique_col)
            print(sql)
            uid = gen_uid()
            result = self.db.db_command(sql=sql, uid=uid).one(uid)
            print(result)
            if result:
                return result
            else:
                return {
                    'error': 'create_table_data is unable to retrieve inserted data collections with SQL query: {}'.format(
                        sql)}
        else:
            return {'error': 'create_table_data is unable to update data collections with SQL query: {}'.format(sql)}

    def verify_updated_table_data(self, pkid='', fields='', upload_many = None):
        """
        Verify updated links are properly written to SQL
        :param key_name: List of key names to verify
        :return: dict with key 'data' with updated link info and linkOrder field or key 'error' with error message
        """
        #print 'verify_updated_table pkid', pkid
        #print 'checking fields', fields
        if pkid and type(pkid) == type([]) and pkid[0]:
            result = self.get_table_data(pkid=pkid, fields=fields, upload_many=upload_many)
            #print 'verify retrieved data'
            #pprint(result)
            updated_data = []
            updated_keys = []
            if result:
                data = {}
                for data in result['data']:
                    #print 'verifying data', data
                    if 'pkid' in data['main']:
                        #print 'pkid in main', data['main']['pkid']
                        updated_keys.append(str(data['main']['pkid']))
                    updated_data.append(data['main'])
                #print 'comparing pkid list {} to updated list {}'.format(sorted(pkid), sorted(updated_keys))
                if sorted(pkid) == sorted(updated_keys):
                    #print 'verify updated', result['data']
                    return result['data']   #changed this from data to result['data'] to return pkid list
                else:
                    return {'error': 'Verify_updated_hosts retrieved data but could not find updated data.'}
            else:
                return {'error': 'Verify_updated_hosts could not retrieve data.'}
        else:
            return {'error': 'Verify_updated_hosts did not receive key_names parameters.'}

    def get_table_data_dependencies(self, pkid, table_name):
        if table_name[:3] == 'fk_':
            table_name = table_name[3:]
        dependencies = []
        sql = 'select table_name, column_name ' \
              'from information_schema.columns ' \
              'where column_name like "%{}%"'.format('fk_' + table_name)
        #print sql
        uid = gen_uid()
        result = self.db.db_command(sql=sql, uid=uid).all(uid)
        #print result
        for r in result:
            if r['column_name'][-4:] == 'list':
                sql = 'select count(pkid) from {table} where FIND_IN_SET({pkid}, {field})'.format(table=r['table_name'], field=r['column_name'], pkid=pkid)
            else:
                sql = 'select count(pkid) from {} where {} = "{}"'.format(r['table_name'], r['column_name'], pkid)
            #print sql
            uid = gen_uid()
            result_count = self.db.db_command(sql=sql, uid=uid).one(uid)
            if result_count and result_count['count(pkid)'] > 0:
                dependencies.append('{} with {} dependencies'.format(r['table_name'], result_count['count(pkid)']))
        return r'</br>'.join(dependencies)

    def delete_table_data(self, pkid, table_name):
        error_pkids = []
        # print table_name
        field_errors = ''
        if pkid and table_name:
            sql = 'delete from {table_name} where pkid = "{pkid}"'.format(table_name=table_name,
                                                                          pkid=pkid
                                                                          )
            # print sql
            self.db.db_command(sql=sql)
            if self.db.error:
                error_pkids.append(str(pkid))
        # print field_errors
        if error_pkids:
            return {'error': 'Error deleting records with PKIDs: {}.'.format(','.join(error_pkids))}
        elif field_errors:
            return {'error': field_errors}
        else:
            return {}

    def dt_row_reorder(self, records):
        #print 'checking for row reorder', records
        for r in records:
            #print r
            #print records[r]
            #print len(records[r])
            if 'DT_RowId' not in records[r] or len(records[r]) > 1:  #if only DT_RowId in record then it may be a row reorder
                return False
        return True

    def parse_request(self, allow_row_reorder=True, debug=False, *args, **kwargs):
        #logger.debug('parse_request: {}'.format(kwargs))

        sql = kwargs.pop('sql', '')
        fields = kwargs.get('fields', {})
        #main_table = kwargs.get('table', '')
        tags = {}

        for f in fields:
            #print(f, type(fields[f]), fields[f])
            if type(fields[f]) == type({}) and fields[f].get('tags', False):
                field_name = fields[f].get('fields', '')

                if type(field_name) == type([]):
                    field_name = field_name[0]
                if field_name:
                    tags[f] = field_name
        #print('Tagged fields', tags)
        #print('parse request', fields)
        options_list = kwargs.pop('options_list', '')
        get_uploads = kwargs.get('get_uploads', False)
        upload_many = kwargs.get('uploadMany', '')
        #debug = kwargs.pop('debug', False)
        self.active_testbed = kwargs.pop('active_testbed', 0)

        if not kwargs:  # child table kwargs request is blank
            return {'data': {}}
        elif 'pkid' in kwargs and 'action' not in kwargs:
            data = self.get_table_data(pkid=kwargs['pkid'], sql=sql, fields=fields, options_list=options_list, debug=debug, get_uploads=get_uploads, upload_many=upload_many)
            # print 'manage_{} datatables data\n'.format(main_table), json.dumps(data, cls=DatetimeEncoder)
            return data
        elif '_' in kwargs:  # get request from DataTables
            data = self.get_table_data(sql=sql, fields=fields, options_list=options_list, debug=debug, get_uploads=get_uploads, upload_many=upload_many)
            # print 'manage_{} datatables data\n'.format(main_table), json.dumps(data, cls=DatetimeEncoder)
            return data

        elif 'action' in kwargs:
            #print ('manage_{} action kwargs'.format(main_table), kwargs)
            if kwargs['action'] == 'upload':
                #print(kwargs)
                upload = {'uploadField': kwargs.get('uploadField', ''),
                        'upload': kwargs.get('upload', None),
                          'request_body': kwargs.get('request_body', None)
                        }

                result = self.upload_file(upload)
                #print(result)
                if 'filename' in result:
                    sql = 'insert ignore into uploads (filename) values ("{}")'.format(result['filename'])
                    self.db.db_command(sql=sql)
                    sql = 'select pkid from uploads where filename = "{}"'.format(result['filename'])
                    uid = gen_uid()
                    pkid = self.db.db_command(sql=sql, uid=uid).one(uid)
                    #print('pkid', pkid)
                    sql = 'update uploads set id = {pkid}, timestamp = NOW(), filesize = "{d[filesize]}", system_path = "{d[system_path]}", web_path = "{d[web_path]}" ' \
                          'where pkid = "{pkid}"'.format(d=result, pkid=pkid['pkid'])
                    self.db.db_command(sql=sql)

                    sql = 'select * from uploads where filename = "{}"'.format(result['filename'])
                    uid = gen_uid()
                    uploaded = self.db.db_command(sql=sql, uid=uid).one(uid)

                    result = {
                                "files": {
                                        "files": {
                                                uploaded['id']: uploaded
                                        }
                                },
                                    "upload": {
                                        "id": uploaded['id']
                                    }
                            }

                return result
            main_table = fields.get('main', {}).get('table', main_table)
            records = self.parse_DT_post(kwargs, upload_many=upload_many)
            #print ('parse_DT_post results', records)
            row_reorder = self.dt_row_reorder(records)
            if kwargs['action'] == 'edit' and row_reorder and allow_row_reorder:
                updated_rows = {}
                updated_pkids = []
                #print('row reorder')
                for r in records:
                    #print ('processing pkid {} moving to {}'.format(r, records[r]))
                    updated_pkids.append(str(r))
                    sql = 'select row_order from {main_table} where pkid = "{pkid}"'.format(main_table=main_table,
                                                                                        pkid=records[r]['DT_RowId'])
                    #print sql
                    uid = gen_uid()
                    new_row_id = self.db.db_command(sql=sql, uid=uid).one(uid)
                    #print 'new row id', new_row_id
                    if new_row_id:
                        updated_rows[r] = new_row_id['row_order']
                for r in updated_rows:
                    sql = 'update {main_table} set row_order = "{value}" where pkid = "{pkid}"'.format(main_table=main_table,
                                                                                                      value=updated_rows[r],
                                                                                                      pkid=r)
                    #print sql
                    self.db.db_command(sql=sql)
                result = self.verify_updated_table_data(updated_pkids, fields=fields)
                #print 'got back verified data'
                #pprint(result)
                if 'error' in result:
                    return result
                return {'data': result}
            elif kwargs['action'] == 'edit' or kwargs['action'] == 'create':
                results = []
                for pkid in records:
                    print('manage_{} edit or create'.format(main_table), pkid, records[pkid])
                    validation = self.validate_table_data(pkid, records[pkid], main_table, kwargs['action'],
                                                          object_prefix='main', upload_many=upload_many, tags=tags)
                    if 'fieldErrors' in validation or 'error' in validation:
                        #print 'manage_{} edit or create validation errors'.format(main_table), validation
                        return validation
                    elif validation:
                        records[pkid] = validation
                    if kwargs['action'] == 'edit':
                        result = self.update_table_data(pkid, records[pkid], main_table)
                        #print('edit records result', result)
                        if 'error' in result:
                            #print 'manage_{} edit errors'.format(main_table), result
                            return result
                        result = self.verify_updated_table_data([str(pkid)], fields=fields, upload_many=upload_many)
                    else:
                        result = self.create_table_data(records[pkid], main_table)
                        if 'error' in result:
                            #print 'manage_{} create errors'.format(main_table), result
                            return result
                        result = self.verify_updated_table_data([str(result['pkid'])], fields=fields, upload_many=upload_many)
                    results.append(result[0] if type(result) == type([]) else result)
                #print ('manage_{} edit results'.format(main_table), results)
                return {'data': results}  #result was returned in a list previously [result]
            elif kwargs['action'] == 'remove':
                result = {'error': 'No pkids in delete for table {}'.format(main_table)}
                for pkid in records:
                    result = self.get_table_data_dependencies(pkid, main_table)
                    if result:
                        # print 'dependencies', result
                        result = {
                            'error': 'Unable to delete record, please remove the following dependencies:</br>' + result}
                    else:
                        result = self.delete_table_data(pkid, main_table)
                        # print 'manage_{} delete result'.format(main_table), result
                return result


    def upload_file(self, kwargs):
        UPLOAD_WEB_PATH = './public/uploads/{}'
        upload = kwargs.get('upload', None)
        request_body = kwargs.get('request_body', None)
        #print('uploadField', kwargs.get('uploadField'))
        #print('upload filename', upload.filename)

        upload_file = upload.file.read()



        #print(len(upload_file))

        try:
            with open(UPLOAD_WEB_PATH.format(upload.filename), 'wb') as f:
                f.write(upload_file)
                """
                According to this thread using the below is more memory efficient fo rlarge files
                Need a way to get the file size
                https://stackoverflow.com/questions/26576349/streaming-post-a-large-file-to-cherrypy-by-python-client
                """
                #todo: investigate using shutil.copyfileobj
                #shutil.copyfileobj(request_body, f)
            #todo: see if the warning can be hidden / suppressed
            #might get warning (seems to be ok though): ResourceWarning: unclosed file <_io.BufferedRandom name=13> self.cpapp.release_serving()
        except Exception as e:
            logger.error('File upload exception for file {}: {}'.format(upload.filename, e))
            result = {'error': 'Unable to save file, error: {}'.format(e)}
        else:
            result = {'filename': upload.filename,
                      'filesize': len(upload_file),
                      'web_path': UPLOAD_WEB_PATH.format(upload.filename),
                      'system_path': UPLOAD_WEB_PATH.format(upload.filename)
                      }
        return result



        #upload_file = upload.make_file()

        #print(upload_file.readlines())


if __name__ == '__main__':

    d = Datatables()

    print(d.update_dt_versions())

    #post = {'action': u'edit', 'data[836][main][app_configured]': u'', 'data[836][main][ssh]': u'', 'data[836][main][os_installed]': u'', 'data[836][main][fk_clusters]': u''}

    #result = d.parse_DT_post(post)

    #result = d.get_dt_libraries()

    #for r in result:
    #    print('{} = {}-{}'.format(r, d.get_dt_short_names(dt=r), d.get_dt_versions(dt=r)))



