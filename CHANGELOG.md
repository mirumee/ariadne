# CHANGELOG

All notable unreleased changes to this project will be documented in this file.

For released versions, see the [Releases](https://github.com/mirumee/ariadne/releases) page.

## Unreleased

### ⚠️ Breaking Changes
- **Remove deprecated `EnumType.bind_to_default_values`**
- **Remove deprecated apollo tracing, opentracing, and extend_federated_schema**
- **Make base handler class names consistent**
- **Make convert_names_case handle digit boundaries in lowercase names**

### 🐛 Bug Fixes
- Add subresource integrity (SRI) to GraphiQL explorer scripts
- Add missing permission
- Return correct success value when errors occurs
- Fix GraphQL.get_request_data return type

### 📚 Documentation
- Get rid of deprecated. Fix llms.txt paths
- Fixing styles, typos. Cleanups
- Update typing in api references
- Add more examples
- Fix description for string-based enums

### 🛠️ Build System
- Update classifiers and versioning policy
- Add git-cliff for automated changelog and release notes


