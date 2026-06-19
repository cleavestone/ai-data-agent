#!/bin/bash
# Creates the read-only role used by the AI agent.
# Runs after 01_schema.sql via docker-entrypoint-initdb.d.
# Has access to POSTGRES_READONLY_USER / POSTGRES_READONLY_PASSWORD
# because they are passed as container environment variables.
set -e

echo "Creating readonly role: ${POSTGRES_READONLY_USER}"

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOF
    CREATE ROLE "${POSTGRES_READONLY_USER}" WITH LOGIN PASSWORD '${POSTGRES_READONLY_PASSWORD}';
    GRANT CONNECT ON DATABASE "${POSTGRES_DB}" TO "${POSTGRES_READONLY_USER}";
    GRANT USAGE ON SCHEMA public TO "${POSTGRES_READONLY_USER}";
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO "${POSTGRES_READONLY_USER}";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "${POSTGRES_READONLY_USER}";
EOF

echo "Readonly role '${POSTGRES_READONLY_USER}' created successfully."
