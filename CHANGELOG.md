# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-01-07

### Added
- Initial release of `aioeloverblik`.
- `EloverblikClient` for accessing customer data (metering points, charges, time series).
- `EloverblikThirdPartyClient` for accessing data via authorization scope.
- `TypeAdapter` based strictly typed responses using Pydantic models.
- Robust token handling with JWT expiry inspection and optimistic 401 retries.
- Comprehensive test suite with mocked responses.
- Async support via `httpx`.
