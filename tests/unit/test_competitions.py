from unittest.mock import patch
import pytest

from competition.Competitions import Competitions

ACTIVE_COMP = {
    'pkid_5': dict(return_value={'pkid': 5}, result=5),
    'pkid_0': dict(return_value={'pkid': 0}, result=0),
    'no_pkid_result': dict(return_value={'zip': 5}, result=0),
}

@pytest.mark.parametrize('params', ACTIVE_COMP)
@patch('competition.Competitions.MySql')
def test_get_active_competition(MySql, params):
    """Test get_active_competition method"""
    c = Competitions()

    # Mock data
    sql = 'select pkid from competitions where active = "1"'
    c._db.run_sql.return_value = ACTIVE_COMP[params]['return_value']

    pkid = c.get_active_competition()

    MySql.assert_called_once()
    assert pkid == ACTIVE_COMP[params]['result']
    assert c.pkid == pkid
    c._db.run_sql.assert_called_once()
    c._db.run_sql.assert_called_with(sql=sql, get='one')


NAMES = {
    'myName': dict(pkid=1, return_value={'name': 'My Name'}, result='My Name'),
    'no_name_result': dict(pkid=1, return_value={'zip': 'My Name'}, result='')
}

@pytest.mark.parametrize('params', NAMES)
@patch('competition.Competitions.MySql')
def test_get_name(MySql, params):
    """Test get_name method."""
    c = Competitions()

    # Mock data
    pkid = NAMES[params]['pkid']
    sql = 'select name from competitions where pkid = "{}"'.format(pkid)
    c._db.run_sql.return_value = NAMES[params]['return_value']

    name = c.get_name(pkid)

    MySql.assert_called_once()
    assert name == NAMES[params]['result']
    c._db.run_sql.assert_called_once()
    c._db.run_sql.assert_called_with(sql=sql, get='one')

GUIDLELINES = {
    'myGuideline': dict(return_value={'style_guidelines': 'My Style'}, result='My Style'),
    'no_name_result': dict(return_value={'zip': 'My Name'}, result='')
}

@pytest.mark.parametrize('params', GUIDLELINES)
@patch('competition.Competitions.MySql')
def test_get_style_guidelines(MySql, params):
    """Test get_name method."""
    c = Competitions()

    # Mock data
    sql = 'select style_guidelines from competitions where active = "1"'
    c._db.run_sql.return_value = GUIDLELINES[params]['return_value']

    style_guidelines = c.get_style_guidelines()

    MySql.assert_called_once()
    assert style_guidelines == GUIDLELINES[params]['result']
    c._db.run_sql.assert_called_once()
    c._db.run_sql.assert_called_with(sql=sql, get='one')


CATEGORIES = {
    'myCategory': dict(return_value={'fk_categories_list': 'My Caterogies'}, result='My Caterogies'),
    'no_name_result': dict(return_value={'zip': 'My Name'}, result='')
}

@pytest.mark.parametrize('params', CATEGORIES)
@patch('competition.Competitions.MySql')
def test_get_catergories(MySql, params):
    """Test get_name method."""
    c = Competitions()

    # Mock data
    sql = 'select fk_categories_list from competitions where active = "1"'
    c._db.run_sql.return_value = CATEGORIES[params]['return_value']

    category = c.get_categories()

    MySql.assert_called_once()
    assert category == CATEGORIES[params]['result']
    c._db.run_sql.assert_called_once()
    c._db.run_sql.assert_called_with(sql=sql, get='one')


COMP_STATUS = {
    'test': dict(
        side_effect=[
            dict(pkid=1),
            dict(brewers=5),
            dict(entries=10, checked_in=7, judged=2),
            [],
            []
        ]
    )
}

@pytest.mark.parametrize('params', COMP_STATUS)
@patch('competition.Competitions.MySql')
def test_get_catergories(MySql, params):

    c = Competitions()

    c._db.run_sql.side_effect = COMP_STATUS[params]['side_effect']

    status = c.get_comp_status()

    print(status)