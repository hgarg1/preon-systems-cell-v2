# Postgres Persistence Setup

The organism runtime schema replaces the old run, metric, lineage, and export tables.

## Apply Schema

```powershell
$env:PGPASSWORD = "<local postgres password>"
createdb -h 127.0.0.1 -U postgres preon_systems_cell
psql -h 127.0.0.1 -U postgres -d preon_systems_cell -f docs/postgres/schema.sql
```

The schema creates:

- auth tables: `users`, `sessions`, verification/reset tokens, `password_policy`
- runtime tables: `organisms`, `cells`, `genomes`, `signals`, `proteins`, `contracts`, `runtime_events`, `memory_records`, `structure_requests`

## App Role

```sql
CREATE ROLE preon_app LOGIN PASSWORD '<generated app password>';
GRANT CONNECT ON DATABASE preon_systems_cell TO preon_app;
\connect preon_systems_cell
GRANT USAGE, CREATE ON SCHEMA public TO preon_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO preon_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO preon_app;
```

Run the web app with:

```powershell
$env:PREON_DATABASE_URL = "postgresql://preon_app:<url-encoded app password>@127.0.0.1:5432/preon_systems_cell"
organism-web
```

## Removed Tables

The v1 reset no longer uses `runs`, `step_metrics`, simulation `events`, run-artifact exports, or Timescale hypertables.
