#!/bin/bash
echo "Installing QueryBridge Enterprise..."
docker-compose -f docker-compose.yml up -d
echo "QueryBridge Installed."
