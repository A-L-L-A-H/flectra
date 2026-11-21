# MoonWitness Sidra — Backup & Disaster Recovery Runbook

## Stack Topology
- Database Container: `flectra-db` (`pgvector/pgvector:pg15`, volume `flectra_flectra-db-data`)
- App Container: `flectra-app` (volume `flectra_flectra-data`, bind `./addons:/opt/flectra/addons:ro`)

## Backup Procedure (Target RTO < 20 min)
```bash
docker exec flectra-db pg_dump -U flectra -Fc -d dev > sidra_dev_$(date +%Y%m%d_%H%M).dump
```

## Restore Procedure (Clean Stack)
```bash
docker compose up -d db
docker exec -i flectra-db pg_restore -U flectra -d dev --clean --if-exists < sidra_dev_YYYYMMDD_HHMM.dump
docker compose up -d flectra
```

## Verification After Restore
1. Confirm `pgvector` extension active: `SELECT extversion FROM pg_extension WHERE extname='vector';`
2. Confirm passage count matches pre-backup snapshot: `SELECT count(*) FROM moonwitness_sidra_passage;`
3. Run P1-006 validator: `env['moonwitness.sidra.validator.service'].validate_all()` -> 0 ERROR findings.
