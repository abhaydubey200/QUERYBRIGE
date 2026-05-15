#!/bin/bash
# Backup script for QueryBridge PostgreSQL metadata
docker exec querybridge_db pg_dump -U admin -d querybridge -F c -f /backups/metadata_backup.dump
