import json
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.environ.get('BITRIGHT_CONFIG', os.path.join(PROJECT_DIR, 'config.json'))) as source:
    CONFIG = json.load(source)
DATA_DIR = os.path.join(PROJECT_DIR, CONFIG['data_dir'])
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
TMP_FOLDER = os.path.join(DATA_DIR, 'tmp')
CHAIN_FILE = os.path.join(DATA_DIR, 'blockchain', 'chain.json')
