import logging
import sys

from evernote2md.flow import evernote_to_obsidian_flow, db_to_pickle_flow

logging.getLogger('evernote_backup').setLevel(logging.INFO)

ci_dir = sys.argv[1] if len(sys.argv) > 1 else 'small'
run_db_to_pickle = sys.argv[2]  == 'db_to_pickle' if len(sys.argv) > 2 else 'skip'

if run_db_to_pickle:
    db_to_pickle_flow(context_dir='data/' + ci_dir)
evernote_to_obsidian_flow(context_dir='data/' + ci_dir)