#!/bin/bash

# Script para subir CSV a S3 y disparar la importación

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "📤 GUATEPASS - Carga de CSV"
echo "============================="

# Verificar que existe el archivo CSV
if [ ! -f "data/clientes.csv" ]; then
    echo -e "${RED}❌ Error: No se encuentra data/clientes.csv${NC}"
    exit 1
fi

# Obtener nombre del bucket
if [ -f ".env.local" ]; then
    source .env.local
    BUCKET_NAME=$GUATEPASS_BUCKET
else
    STACK_NAME="guatepass-slice1"
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
        --output text)
fi

if [ -z "$BUCKET_NAME" ]; then
    echo -e "${RED}❌ Error: No se pudo obtener el nombre del bucket${NC}"
    echo "   Asegúrate de que el stack está desplegado"
    exit 1
fi

echo -e "${YELLOW}📦 Bucket destino: $BUCKET_NAME${NC}"
echo -e "${YELLOW}📄 Archivo: data/clientes.csv${NC}"
echo ""

# Subir archivo
echo "Subiendo archivo..."
aws s3 cp data/clientes.csv s3://$BUCKET_NAME/clientes.csv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Archivo subido exitosamente${NC}"
    echo ""
    echo "La Lambda ImportUsersFunction se ejecutará automáticamente"
    echo ""
    echo "Para ver los logs en tiempo real:"
    echo "  ${YELLOW}sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail${NC}"
else
    echo -e "${RED}❌ Error subiendo archivo${NC}"
    exit 1
fi

