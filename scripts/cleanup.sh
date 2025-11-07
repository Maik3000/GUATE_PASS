#!/bin/bash

# Script para limpiar todos los recursos creados

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "🧹 GUATEPASS - Limpieza de Recursos"
echo "====================================="
echo ""
echo -e "${RED}⚠️  ADVERTENCIA: Esta acción eliminará TODOS los recursos del stack${NC}"
echo ""
read -p "¿Estás seguro? (escribe 'SI' para confirmar): " CONFIRM

if [ "$CONFIRM" != "SI" ]; then
    echo "Operación cancelada"
    exit 0
fi

STACK_NAME="guatepass-slice1"

# Obtener nombre del bucket
echo ""
echo -e "${YELLOW}Obteniendo información del stack...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
    --output text 2>/dev/null)

# Vaciar bucket S3 (CloudFormation no puede eliminar buckets con contenido)
if [ ! -z "$BUCKET_NAME" ]; then
    echo -e "${YELLOW}Vaciando bucket S3: $BUCKET_NAME${NC}"
    aws s3 rm s3://$BUCKET_NAME --recursive
    echo -e "${GREEN}✅ Bucket vaciado${NC}"
fi

# Eliminar stack
echo ""
echo -e "${YELLOW}Eliminando stack de CloudFormation...${NC}"
sam delete --stack-name $STACK_NAME --no-prompts

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Stack eliminado exitosamente${NC}"
    
    # Limpiar archivos locales
    rm -f .env.local
    echo -e "${GREEN}✅ Archivos locales limpiados${NC}"
else
    echo -e "${RED}❌ Error eliminando stack${NC}"
    exit 1
fi

echo ""
echo "🎉 Limpieza completada"

