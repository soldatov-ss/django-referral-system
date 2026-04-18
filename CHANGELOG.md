# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-04-18

### Fixed
- Replace hardcoded `auth.User` with `settings.AUTH_USER_MODEL` in `Promoter` and `Referral` models so the package works with custom user models
- Use `get_user_model()` instead of importing `auth.User` directly in views and services
- Use `getattr` fallback for `user.email` in `Promoter.__str__` and `ReferralSerializer` to avoid `AttributeError` on user models without an email field
- Raise `ImproperlyConfigured` with a clear message when `BASE_REFERRAL_LINK` is not set, instead of silently producing broken referral links

## [0.3.0] - 2026-04-18

### Changed
- Dropped Python 3.8 support and updated packaging, tooling, and documentation for Python 3.9 through 3.13
- Adjusted Django, Django REST framework, NumPy, and pandas dependency resolution so Python 3.13 installs versions with official 3.13 support
- CI now tests Python 3.9 through 3.13, with coverage uploaded from Python 3.12 only
- Updated local tooling defaults and automation for the new support matrix

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
- Pinned build and runtime dependencies to Python 3.8-compatible ranges for the final Python 3.8-supported release
- CI now tests Python 3.8 through 3.13, with coverage uploaded from Python 3.12 only

### Fixed
- Extended test coverage across referral, promoter, and commission flows (81 tests total)
- Replaced 3.9+ generic type-hint syntax in runtime-facing annotations to avoid Python 3.8 introspection issues

### Deprecated
- Python 3.8 support ends after `0.2.0`; the next release will require Python 3.9+

## [0.1.3] - 2025-03-03

### Added
- Authorization support

## [0.1.1] - 2025-01-01

### Added
- Initial public release with referral program management, promoter tracking, commission handling, and Wise payout integration
