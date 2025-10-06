#!/bin/bash
# scripts/setup-influxdb.sh
# Setup script for InfluxDB 3

set -e

INFLUX_HOST="http://localhost:8181"
DATABASE_NAME="bloodwork"
TOKEN_FILE="./scripts/admin-token.txt"

echo "🚀 Setting up InfluxDB 3..."

# Create scripts directory if it doesn't exist
mkdir -p ./scripts

# Wait for InfluxDB to be ready
#echo "⏳ Waiting for InfluxDB to be ready..."
#timeout 60 bash -c 'until curl -f http://localhost:8181/health > /dev/null 2>&1; do sleep 2; done'

# Check if token already exists
if [ -f "$TOKEN_FILE" ]; then
    echo "📄 Admin token already exists at $TOKEN_FILE"
    ADMIN_TOKEN=$(cat "$TOKEN_FILE")
else
    echo "🔑 Creating admin token..."
    ADMIN_TOKEN=$(docker exec influxdb3-core influxdb3 create token --admin)

    if [ $? -eq 0 ] && [ -n "$ADMIN_TOKEN" ]; then
        echo "$ADMIN_TOKEN" > "$TOKEN_FILE"
        echo "✅ Admin token saved to $TOKEN_FILE"
    else
        echo "❌ Failed to create admin token"
        exit 1
    fi
fi

# Create database
echo "🗄️  Creating database '$DATABASE_NAME'..."
docker exec influxdb3-core influxdb3 create database "$DATABASE_NAME" \
    --host http://localhost:8181 \
    --token "$ADMIN_TOKEN" || echo "Database might already exist"

# Test connection
echo "🧪 Testing connection..."
docker exec influxdb3-core influxdb3 show databases \
    --host http://localhost:8181 \
    --token "$ADMIN_TOKEN"

echo ""
echo "✅ InfluxDB 3 setup completed!"
echo ""
echo "📋 Connection details:"
echo "   Host: $INFLUX_HOST"
echo "   Database: $DATABASE_NAME"
echo "   Token: (saved in $TOKEN_FILE)"
echo ""
echo "💡 Update your .env file with these values"