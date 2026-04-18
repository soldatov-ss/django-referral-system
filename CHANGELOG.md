# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-18

### Added
- Async support via decorator in `referrals/repositories/decorators.py`
- Python 3.12 and 3.13 support
- `Makefile` with common dev commands (`test`, `testall`, `qa`, `coverage`, `build`, `publish`, `tag`, `clean`)

### Changed
- Migrated build tooling from `setup.cfg`/`setup.py` to `pyproject.toml` with full `[project]` table and `uv` support
- Use `django.utils.timezone.now()` instead of `datetime.today()` for timezone-aware datetime handling
- Simplified `append_query_params` — `parse_qs` always returns lists, removed redundant branch
- `ReferralService.get_promoter_by_user_id` now checks `user is None` before attribute access instead of catching `User.DoesNotExist`

### Fixed
- Extended test coverage across referral, promoter, and commission flows (81 tests total)

## [0.1.3] - 2025-03-03

### Added
- Authorization support

## [0.1.1] - 2025-01-01

### Added
- Initial public release with referral program management, promoter tracking, commission handling, and Wise payout integration
