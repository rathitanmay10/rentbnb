# This directory is mounted into the PostgreSQL container as /docker-entrypoint-initdb.d/
# Any .sql or .sh files here are executed automatically on the FIRST boot of the container
# (i.e., when the postgres_data volume is empty/new).
#
# To seed data from your local database, run:
#   ./scripts/export_db.sh
#
# That will create dump.sql in this directory.
# Then run: docker compose up --build
