from pathlib import Path

from .database.MySql import MySql

project_root = Path(__file__).parent.parent

DATABASE = ''
# https://gist.github.com/igniteflow/1760854
try:
    # use the develop database if we are using develop
    import os
    from git import Repo

    repo = Repo(project_root)
    branch = repo.active_branch
    branch = branch.name
    if branch == 'master':
        DATABASE = 'competitions'
    else:
        DATABASE = 'comp_test'
except ImportError:
    pass

with open(f'{project_root}/.db_config') as f:

    pairs = (line.strip().split('=', 1) for line in f)
    CONN = {pair[0]:pair[1] for pair in pairs if len(pair) == 2}
