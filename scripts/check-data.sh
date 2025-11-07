#!/bin/bash

# Script para verificar los datos importados en DynamoDB

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 GUATEPASS - Verificación de Datos"
echo "====================================="

# Obtener nombre de la tabla
if [ -f ".env.local" ]; then
    source .env.local
    TABLE_NAME=$GUATEPASS_TABLE
else
    STACK_NAME="guatepass-slice1"
    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`UsersTableName`].OutputValue' \
        --output text)
fi

if [ -z "$TABLE_NAME" ]; then
    echo -e "${RED}❌ Error: No se pudo obtener el nombre de la tabla${NC}"
    exit 1
fi

echo -e "${YELLOW}📊 Tabla: $TABLE_NAME${NC}"
echo ""

# Contar items
echo "Contando usuarios..."
COUNT=$(aws dynamodb scan \
    --table-name $TABLE_NAME \
    --select "COUNT" \
    --query 'Count' \
    --output text)

echo -e "${GREEN}✅ Total de usuarios: $COUNT${NC}"
echo ""

# Mostrar primeros 5 usuarios
echo "Primeros 5 usuarios:"
echo "--------------------"
aws dynamodb scan \
    --table-name $TABLE_NAME \
    --max-items 5 \
    --output table

echo ""
echo "Para ver un usuario específico:"
echo "  ${YELLOW}aws dynamodb get-item --table-name $TABLE_NAME --key '{\"placa\": {\"S\": \"P-123ABC\"}}'${NC}"

