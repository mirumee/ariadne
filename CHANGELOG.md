# CHANGELOG

All notable unreleased changes to this project will be documented in this file.

For released versions, see the [Releases](https://github.com/mirumee/ariadne/releases) page.

## Unreleased

### ⚠️ Breaking Changes
- **Remove deprecated `EnumType.bind_to_default_values`**
- **Remove deprecated apollo tracing, opentracing, and extend_federated_schema**

### 🐛 Bug Fixes
- Add subresource integrity (SRI) to GraphiQL explorer scripts
- Add missing permission
- Return correct success value when errors occurs
- Fix GraphQL.get_request_data return type

### 📚 Documentation
- Get rid of deprecated.
- Fixing styles, typos. Cleanups
- Update typing in api references
- Fix description for string-based enums

### 🛠️ Build System
- Update classifiers and versioning policy
- Add git-cliff for automated changelog and release notes
