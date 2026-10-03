# Generated Documentation Manifest Contract

Every DevForge product output includes `.devforge-generation.json`. This file is the deterministic Phase-5 documentation/provenance manifest for the generated scaffold.

The current contract records:

- schema and generator version;
- selected blueprint;
- product identity metadata;
- exact ordered reusable module set;
- dependency specifications;
- optional selected Phase-4 product pack with its committed capabilities;
- dependency mode;
- verified vendored-package destinations and SHA-256 digests when standalone bundle mode is used.

The record intentionally contains no generation timestamp, random identifier, credentials, production secrets, or deployment authorization. Unknown top-level or nested contract keys fail closed in the repository validator.

Validate a generated record with:

```bash
node generator/validate-generation-record.mjs /path/to/generated/.devforge-generation.json
```

The validator is stdlib-only and checks the current generator `0.4.0` contract, current blueprint/module boundaries, current committed pack contracts, and vendored dependency provenance rules. It validates metadata only; it does not execute generated application code, deploy anything, or publish artifacts.
