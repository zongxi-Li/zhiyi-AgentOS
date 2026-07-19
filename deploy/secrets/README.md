# Secret initialization

The release package never contains Secret values. Create an external directory owned by the deployment administrator with these UTF-8 files, each ending in one LF:

- `db_admin_password` (at least 16 characters)
- `db_password` (at least 16 characters)
- `redis_password` (at least 16 characters)
- `jwt_secret` (at least 64 characters)
- `ai_internal_token` (at least 64 characters)

Use `scripts/init-secrets.sh <external-directory>` for a new installation. Do not rerun it for an existing deployment because rotating these values requires a coordinated procedure.
