# Media Module

- Name: media
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend, worker

## Purpose

Provides the provider-neutral media capability contract defined by the DevForge Phase-3 roadmap and module catalog. This foundation slice covers only the remaining media-specific catalog gaps after the existing storage foundation: image processing and video upload.

File upload, private/signed access, and storage-provider adaptation remain owned by `packages/storage/`. Media messages, realtime voice/video, product-specific transformations, moderation, and UI behavior are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`media-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `media-contract.json` — versioned media capability metadata.
- `validate_media_contract.py` — fail-closed repository validator.

Consumers may implement image-processing and video-upload behavior behind their own reviewed runtime boundaries. Provider-specific services must not become authoritative in this reusable contract.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice. Consuming applications remain responsible for authorization and tenant boundaries before accepting or transforming media.

## Security Considerations

- Product-specific identifiers, customer media, provider credentials, bucket/container IDs, and transformation secrets must not be committed to this package.
- Media handling must not bypass storage authorization, tenant isolation, malware/content-safety controls, or size/type limits in consuming applications.
- No `tusd`, `imgproxy`, `LiveKit`, or other external media runtime dependency is approved by this foundation contract.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_media_contract.py` proves:
- the committed contract is valid;
- the domain is `media`;
- baseline capabilities are exactly `image_processing` then `video_upload`;
- missing, extra, reordered, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability set/order, or schema version is a public-contract change and requires compatibility review for storage integration, adapters, generators, and generated products.

The module remains EXPERIMENTAL until reviewed runtime integrations and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
