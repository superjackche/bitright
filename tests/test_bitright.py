import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import blockchain


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(blockchain, 'UPLOAD_FOLDER', str(tmp_path))
    monkeypatch.setattr(blockchain, 'CHAIN_FILE', str(tmp_path / 'chain.json'))
    payload = b'Original demonstration media'
    media = hashlib.sha256(payload).hexdigest()
    (tmp_path / media).write_bytes(payload)
    transaction = dict(title='Original', filename='work.txt', author='Demo',
                       public_key='DEMO', genre='Text', media=media)
    chain = blockchain.Blockchain()
    block = blockchain.Block(1, transaction, 0)
    chain.add_block(block)
    return chain, block, tmp_path


@pytest.mark.parametrize('field', ['title', 'filename', 'author', 'public_key', 'genre', 'media'])
def test_detects_changed_transaction(ledger, field):
    chain, block, _ = ledger
    block.transaction[field] += '-changed'
    assert not chain.check_integrity()


@pytest.mark.parametrize('field', ['index', 'timestamp', 'previous_hash', 'hash'])
def test_detects_changed_block(ledger, field):
    chain, block, _ = ledger
    setattr(block, field, str(getattr(block, field)) + '-changed')
    assert not chain.check_integrity()


def test_file_content_tampering(ledger):
    chain, block, directory = ledger
    (directory / block.transaction['media']).write_bytes(b'Changed content')
    assert not chain.check_integrity()


def test_json_round_trip(ledger):
    chain, _, directory = ledger
    rows = json.loads((directory / 'chain.json').read_text())
    restored = blockchain.Blockchain()
    restored.chain = [blockchain.Block.from_dict(row) for row in rows]
    assert restored.check_integrity()
    assert [b.__dict__ for b in restored.chain] == [b.__dict__ for b in chain.chain]


def test_empty_pending_does_not_duplicate_block(ledger):
    chain, _, _ = ledger
    assert chain.mine() is None
    assert len(chain.chain) == 1


def test_full_rehash_limit_is_explicit(ledger):
    chain, block, directory = ledger
    payload = b'Second independent work'
    media = hashlib.sha256(payload).hexdigest()
    (directory / media).write_bytes(payload)
    transaction = block.transaction.copy()
    transaction.update(title='Second', media=media)
    successor = blockchain.Block(2, transaction, block.hash)
    chain.add_block(successor)
    block.transaction['title'] = 'Rewritten and rehashed'
    block.hash = block.compute_hash()
    successor.previous_hash = block.hash
    successor.hash = successor.compute_hash()
    assert chain.check_integrity()  # No trusted external anchor in this single-node demo.


def test_legacy_title_is_not_covered(ledger):
    _, modern, _ = ledger
    path = Path(__file__).parent / 'fixtures' / 'legacy_block.py'
    spec = importlib.util.spec_from_file_location('legacy_block', path)
    legacy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_module)
    old = legacy_module.Block(1, modern.transaction.copy(), 0)
    before = old.compute_hash()
    old.transaction['title'] = 'Changed'
    assert old.compute_hash() == before
