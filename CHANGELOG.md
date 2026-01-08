# Changelog

All notable changes to this project will be documented in this file.

## [0.1.2] - 2026-01-08

### Fixed
- `add_relations_by_cvr`: Fixed incorrect return type annotation and parsing logic found during audit. The API returns a list of response objects, not strings.
- `delete_relation`: Fixed incorrect check for `success` field. Now correctly checks the boolean `result` field.

### Changed
- Comprehensive audit of all client methods against API schemas to ensure correctness.
- **Major Model Refactor**:
    - Complete implementation of all API response models, including detailed support for **Charges**, **Time Series**, and **Metering Point Details**.
    - Split `MeteringPoint` into `MeteringPoint` (Customer) and `MeteringPointThirdParty` (ThirdParty) for correct schema validation.
    - Introduced shared base models (`BaseApiModel`, `BaseCharge`) for better maintainability.
    - Added missing fields across multiple models (e.g., `timeStamp` in `AuthorizationDto`, `settlement_method` in `MeteringPoint`).
    - Renamed `Authorization` to `AuthorizationDto` to match API naming.

- Significantly improved docstrings for all client methods and models, following Google Style.

## [0.1.1] - 2026-01-07

### Changed
- Relaxed `pydantic` dependency to `>=2.10.0,<3.0.0` to support more environments.

## [0.1.0] - 2026-01-07

### Added
- Initial release of `aioeloverblik`.
- `EloverblikClient` for accessing customer data (metering points, charges, time series).
- `EloverblikThirdPartyClient` for accessing data via authorization scope.
- `TypeAdapter` based strictly typed responses using Pydantic models.
- Robust token handling with JWT expiry inspection and optimistic 401 retries.
- Comprehensive test suite with mocked responses.
- Async support via `httpx`.
