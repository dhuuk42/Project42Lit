#!/bin/bash
TIMESTAMP=$(date +%F_%T)
docker exec -t project42lit-db-1 pg_dump -U tracker weightdb > ./backups/backup_$TIMESTAMP.sql
