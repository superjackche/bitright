![BitRights](./static/logo.png)

# BitRights with Python 3 and uv

A small modernization of [liuyanqi/bitright](https://github.com/liuyanqi/bitright), originally created by Yanqi Liu, Brandon Tan and George Spahn. The original Flask pages, transaction/block classes, sample media and similarity thresholds are retained. The upstream README is preserved in [docs/README.upstream.md](docs/README.upstream.md).

This is a single-node teaching demonstration of digital-work registration and similarity lookup. It does not implement consensus, proof of work, verified authorship or externally anchored evidence.

## Run

Tested on Ubuntu 24.04 x86_64 with Python 3.12. CPU only; no GPU is used. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) first, then run:

```bash
git clone https://github.com/superjackche/bitright.git
cd bitright
sudo apt-get update
sudo apt-get install build-essential python3.12-dev libchromaprint-tools ffmpeg
uv sync --locked
uv run --locked network.py
```

Open `http://127.0.0.1:8001`. The Python headers are needed to build `py-tlsh`; Chromaprint provides both the native library and the `fpcalc` audio command. `bash install.sh` and `bash run.sh` wrap the two uv commands above.

Browse File → choose Audio/Image/Text → Publish to register a work, or Lookup to find a similar registered work. View Blockchain lists records; Check Integrity checks the stored ledger and media bytes. The public-key field is descriptive metadata only: entering text there does not verify an identity or a signature.

`uv.lock` locks dependencies; use `uv sync --locked` rather than the old pip requirements. `requirements.txt` is retained only as a historical upstream file. See [modernization notes](docs/modernization.md) for the narrowly scoped compatibility changes.

## Configuration

Edit `config.json`, or set `BITRIGHT_CONFIG` to the path of a separate JSON file containing all five settings:

| Setting | Default | Purpose |
| --- | --- | --- |
| `host` | `127.0.0.1` | Listen on the local machine. |
| `port` | `8001` | Web service port. |
| `debug` | `false` | Flask debug mode. |
| `data_dir` | `outputs/runtime` | Ledger, uploaded files and temporary files; relative paths resolve from the repository root. |
| `audio_force_fpcalc` | `true` | Use the original experiment's audio decoding path. |

The Flask development server runs one request at a time. This is a local teaching application, not a deployment with authentication or concurrent writers. The original pages also load CSS and JavaScript from public CDNs, so the browser needs internet access.

## Changes

- Python 3.12, Flask 3, current numerical/media dependencies, and uv project management.
- An explicit override of image-match's obsolete scikit-image constraint. Pillow loads the image; the original Goldberg signature and distance are still used.
- Maintained pyacoustid bindings, with `fpcalc` explicitly selected to match the original experiment's decoding path.
- Hashes cover the full block and transaction. Integrity checks cover block links and media bytes.
- Human-readable JSON persistence replaces pickle. Old pickle ledgers are not imported automatically; keep the original experiment in its own data directory.
- Actual media failures return errors, instead of being presented as matches. Small fixes to legacy JavaScript, timestamps and download links preserve the original UI.

No new top-level license has been invented: upstream has no repository-level license declaration. Existing notices and third-party attribution are preserved.

## Verify

```bash
uv run --locked pytest
uv run --locked python scripts/compare_versions.py
```

The comparison script writes `outputs/modern-comparison.json`: original versus modern hashes for three changed fields, plus nine media similarity scores. It does not run the entire Python 2 application.

For the HTTP experiment, start the application with an empty ledger and run this command in a second terminal:

```bash
uv run --locked python scripts/verify_experiment.py
```

This writes six demonstration records and saves `outputs/experiment-results.json`. It aborts if the ledger is not empty. For another run, copy `config.json` to a local file, choose a new `data_dir` (and a different `port` if another service is running), and set the same `BITRIGHT_CONFIG` in both terminals. Existing records do not need to be deleted.

Validated on Ubuntu 24.04 / Python 3.12:

- 15 unit tests passed: transaction/block tampering, media bytes, JSON round trip, empty pending transactions and the full-rehash limitation.
- 34 HTTP checks passed: publish, duplicate/similar rejection, lookup, malformed media errors, integrity and downloads; six records remained after restart with integrity intact.
- All nine sample scores matched the separately reproduced Python 2 baseline using `fpcalc`. Original thresholds remain Text distance `< 100`, Image distance `< 0.4`, Audio similarity `> 0.9`.

The tests use private temporary fixtures. They also demonstrate the limitation that a person who can rewrite the entire local ledger and recompute its hashes is not detected without an independent trusted anchor. Matching scores are not plagiarism probabilities.

## Files

`network.py` remains the web entry point, `blockchain.py` the ledger implementation, and `acoustic/`, `image_compare/`, `text_compare/` the comparison adapters. The original vendored acoustic modules remain as upstream history; runtime imports use the maintained `pyacoustid` package. Generated results and runtime data under `outputs/` are ignored by Git. If using a custom config or data directory elsewhere, keep those local files out of commits.
