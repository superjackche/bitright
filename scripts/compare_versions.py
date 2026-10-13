"""Compare the original hash function and modern media results on fixed fixtures."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from blockchain import Block
from acoustic.acoustid_check import calc_accuracy as audio_similarity
from image_compare.image_check import calc_accuracy as image_distance
from text_compare.test_text import check_text_similarity

spec = importlib.util.spec_from_file_location('legacy_block', ROOT / 'tests/fixtures/legacy_block.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
tx = dict(title='Original', filename='work.txt', author='Demo', public_key='Demo key',
          genre='Text', media=hashlib.sha256(b'Original work').hexdigest())
results = {'tampering': [], 'scores': []}
for field in ('title', 'media', 'public_key'):
    row = {'field': field}
    for name, cls in [('original', legacy.Block), ('modern', Block)]:
        block = cls(1, tx.copy(), 0)
        block.timestamp = 1791864000.0
        before = block.compute_hash()
        block.transaction[field] += '-modified'
        after = block.compute_hash()
        row[name] = {'before': before, 'after': after, 'changed': before != after}
    results['tampering'].append(row)
for genre, func, base, variants in [
    ('Text', check_text_similarity, 'doc1.txt', ['doc1_same.txt', 'doc2.txt', 'doc3.txt']),
    ('Image', image_distance, 'MonaLisa_1.jpg', ['MonaLisa_2.jpg', 'Other.jpg']),
    ('Audio', audio_similarity, 'heaven.mp3', ['heaven_small.mp3', 'heaven_first_half.mp3', 'heaven_second_half.mp3', 'undertheice.mp3'])]:
    for variant in variants:
        score = float(func(str(ROOT/'media'/base), str(ROOT/'media'/variant)))
        results['scores'].append({'genre': genre, 'a': base, 'b': variant, 'score': score})
(ROOT/'outputs').mkdir(exist_ok=True)
(ROOT/'outputs/modern-comparison.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
