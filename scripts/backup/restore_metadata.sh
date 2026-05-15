#!/bin/bash
# Restore script for QueryBridge PostgreSQL metadata
docker exec querybridge_db pg_restore -U admin -d querybridge -1 /backups/metadata_backup.dump
