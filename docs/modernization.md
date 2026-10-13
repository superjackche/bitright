# Modernization scope

Base: `liuyanqi/bitright` commit `b8d0b694fad1316c7599d7f8e44e3fb4f7195b4b`. Preserve original contributor names and application workflow.

The modernization is an extension to a separately reproduced Python 2 teaching experiment. It is not a claim that the original project was written by the student.

## Runtime and compatibility

Python 3.12 and uv replace the Python 2 virtualenv installer. `pyproject.toml` declares direct dependencies, `.python-version` selects the runtime family, and `uv.lock` provides exact versions. Flask 3 keeps the existing route and template structure.

image-match 1.1.2 requires scikit-image `<0.13` in its package metadata and passes the removed `as_grey` parameter when reading paths. The uv override is explicit. The adapter decodes supported images using Pillow and passes an RGB array to the same ImageSignature implementation. No threshold tuning or alternative image similarity model is introduced.

pyacoustid's modern default may choose audioread, changing audio decoding slightly and producing EOFError for some malformed inputs. `audio_force_fpcalc` defaults to true, deliberately using the same system fpcalc path as the original reproduction. This is an explicit configuration choice, not an implicit fallback.

## Ledger improvements

Canonical JSON serialization includes the full transaction in the block hash. The stored hash is compared with the recomputed value, links and sequence numbers are checked, and actual media bytes are hashed again. The ledger is stored as JSON through a temporary file followed by replacement, rather than unpickling a local object graph.

Persistence remains a small single-node file-based design. There is no automatic migration of old pickle files, distributed consensus or signature authentication. Hash checks cannot establish the truth of authorship or prevent rewriting and rehashing the whole local chain.

## Evidence

`tests/test_bitright.py` exercises field/content tampering, JSON persistence and the full-rehash limitation. The original Block class is preserved in `tests/fixtures/legacy_block.py` solely for the comparison experiment. `scripts/compare_versions.py` records the old/new hashes and media scores. `scripts/verify_experiment.py` checks the original UI's HTTP workflow against a live service.
