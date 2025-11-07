#!/bin/bash

# Script de despliegue para GUATEPASS Slice #1
# Automatiza el proceso de build y deploy de SAM

set -e  # Exit on error

echo "🚀 GUATEPASS - Desplegando Slice #1: Carga Inicial de Datos"
echo "=================================================="

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "infrastructure/template.yaml" ]; then
    echo -e "${RED}❌ Error: No se encuentra infrastructure/template.yaml${NC}"
    echo "   Asegúrate de ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Paso 1: Validar template
echo ""
echo -e "${YELLOW}📝 Paso 1: Validando template de SAM...${NC}"
sam validate -t infrastructure/template.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Template válido${NC}"
else
    echo -e "${RED}❌ Template inválido. Corrige los errores antes de continuar.${NC}"
    exit 1
fi

# Paso 2: Build
echo ""
echo -e "${YELLOW}🔨 Paso 2: Compilando aplicación...${NC}"
sam build -t infrastructure/template.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build exitoso${NC}"
else
    echo -e "${RED}❌ Error en build${NC}"
    exit 1
fi

# Paso 3: Deploy
echo ""
echo -e "${YELLOW}🚀 Paso 3: Desplegando en AWS...${NC}"

# Verificar si es la primera vez (guided mode)
if [ ! -f "samconfig.toml" ]; then
    echo "   Primera vez - modo guiado"
    sam deploy --guided
else
    echo "   Usando configuración existente de samconfig.toml"
    sam deploy
fi

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Despliegue exitoso!${NC}"
else
    echo -e "${RED}❌ Error en despliegue${NC}"
    exit 1
fi

# Paso 4: Obtener outputs
echo ""
echo -e "${YELLOW}📊 Paso 4: Obteniendo información del stack...${NC}"
STACK_NAME=$(grep "stack_name" samconfig.toml | cut -d'"' -f2)

echo ""
echo "Stack: $STACK_NAME"
echo "Outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Guardar outputs en archivo
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
    --output text)

TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`UsersTableName`].OutputValue' \
    --output text)

echo ""
echo "export GUATEPASS_BUCKET=$BUCKET_NAME" > .env.local
echo "export GUATEPASS_TABLE=$TABLE_NAME" >> .env.local
echo -e "${GREEN}✅ Variables de entorno guardadas en .env.local${NC}"

# Paso 5: Instrucciones siguientes
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 ¡Despliegue completado exitosamente!${NC}"
echo ""
echo "Próximos pasos:"
echo "  1. Cargar datos iniciales:"
echo "     ${YELLOW}aws s3 cp data/clientes.csv s3://$BUCKET_NAME/clientes.csv${NC}"
echo ""
echo "  2. Ver logs:"
echo "     ${YELLOW}sam logs -n ImportUsersFunction --stack-name $STACK_NAME --tail${NC}"
echo ""
echo "  3. Ver dashboard:"
echo "     Abre la URL del output 'DashboardURL'"
echo ""
echo "  4. Verificar datos en DynamoDB:"
echo "     ${YELLOW}aws dynamodb scan --table-name $TABLE_NAME --max-items 5${NC}"
echo ""

