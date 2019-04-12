
import pytest

import utils.database.MySql
from competition.Competitions import Competitions
from competition.Competitions import db

def test_db_class():
    """Test db object is created as MySql class"""
    assert isinstance(db, utils.database.MySql.MySql)

def test_Competitions():
    """Test Competitions object is created and self.pkid == 0"""
    c = Competitions()
    assert isinstance(c, Competitions)
    assert c.pkid == 0

def test_get_active_competition():
    """Verify active competition is retrieved as int and self.pkid is set to the retrieved pkid"""
    c = Competitions()
    pkid = c.get_active_competition()

    assert isinstance(pkid, int)
    assert pkid > 0
    assert c.pkid == pkid


def test_get_name():
    """Verify active competition is retrieved as int and self.pkid is set to the retrieved pkid"""
    c = Competitions()
    pkid = c.get_active_competition()

    result = c.get_name(pkid)

    assert isinstance(result, str)
    assert len(result) > 0


def test_get_style_guidelines():
    """Verify active competition is retrieved as int and self.pkid is set to the retrieved pkid"""
    c = Competitions()
    pkid = c.get_active_competition()

    result = c.get_style_guidelines()

    assert isinstance(result, str)
    assert len(result) > 0


def test_get_categories():
    """Verify active competition is retrieved as int and self.pkid is set to the retrieved pkid"""
    c = Competitions()
    pkid = c.get_active_competition()

    result = c.get_categories()

    assert isinstance(result, str)
    assert len(result) > 0

def test_get_comp_status():
    """Verify active competition is retrieved as int and self.pkid is set to the retrieved pkid"""
    c = Competitions()
    pkid = c.get_active_competition()

    result = c.get_comp_status()

    assert isinstance(result, dict)
    assert len(result) > 0

    entries = result.get('entries', None)

    assert isinstance(entries, dict)
    assert len(entries) == 5
    assert isinstance(entries['brewers'], int)
    assert isinstance(entries['entries'], int)
    assert isinstance(entries['checked_in'], int)
    assert isinstance(entries['judged'], int)
    assert isinstance(entries['remaining'], int)
    assert entries['remaining'] == entries['checked_in'] - entries['judged']


    sessions = result.get('sessions', None)

    assert isinstance(sessions, list)
    session0 = sessions[0]

    assert len(session0) == 5
    assert isinstance(session0['name'], str)
    assert isinstance(session0['type'], str)
    assert isinstance(session0['stewards'], int)
    assert isinstance(session0['judges'], int)
    assert isinstance(session0['other'], int)

