# QoverwRap

PoC for a **payload-level** QR data string: a leading plaintext **Layer A**, a fixed **delimiter**, a **base64 trailer** (versioned binary header + **Layer B** + **Layer C** signature bytes), plus a **safe-fallback resolver** driven by output policy.

The importable Python package lives under `qoverwrap/`.

## Core idea

```
[Layer A — UTF-8 plaintext]
\n---QWR---\n
base64( [1B version][2B b_len BE][2B c_len BE][Layer B][Layer C signature] )
```

- **Simple mode**: if both B and C are empty, the delimiter and trailer are omitted (A only).
- **Signing**: Ed25519 over the canonical message from the spec (`QWR1`||version||len(A)||A||len(B)||B).
- **Resolver**: `public`, `authenticated` (parsed metadata, **not** cryptographic authentication), and `verified` (signature check), with downgrade to A-only on failures.

## What this is not

- Not QR **module / ECC codeword** steganography.
- Not cryptographic **access control** on the payload; it is an **application output policy** for what to reveal.
- Not a generic “QR + signature” snippet; it is the specific combination of wire format, canonical signing, strict v1 decoding, and resolver behaviour.

## Layout

| Path | Role |
|------|------|
| [src/qoverwrap/](src/qoverwrap/) | Core library |
| [demo/](demo/) | FastAPI + React demo |
| [tests/](tests/) | Unit, integration, demo API tests |
| [docs/patent/spec-draft.md](docs/patent/spec-draft.md) | Patent specification draft |
| [docs/research/prior-art-survey.md](docs/research/prior-art-survey.md) | Prior-art survey |

## Quick start (dev)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" -r demo/backend/requirements.txt
export QWR_ENABLE_DEMO_SIGNING=1
PYTHONPATH=src .venv/bin/pytest -q
```

See [demo/README.md](demo/README.md) to run the web demo.

## License / Notice

Copyright © 2026 Sangrae Kim (김상래). All rights reserved.

This repository is published **for research, demonstration, and patent-pending disclosure purposes only**. **No license is granted** to use, copy, modify, distribute, sublicense, or commercialize the code, documentation, figures, or related materials except with prior written permission from the copyright holder.

Patent application pending.

See the [`LICENSE`](LICENSE) file at the repository root for the full notice. Public availability on GitHub is for *viewing and research* only and does not imply an open-source license.
