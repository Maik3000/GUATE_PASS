# 🚗 GUATEPASS - Sistema de Cobro Automatizado de Peajes

Sistema serverless para el cobro automatizado de peajes en la Ciudad de Guatemala, construido completamente con servicios administrados de AWS.

[![AWS](https://img.shields.io/badge/AWS-Serverless-orange)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![SAM](https://img.shields.io/badge/SAM-Template-green)](https://aws.amazon.com/serverless/sam/)

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Estado del Proyecto](#-estado-del-proyecto)
- [Arquitectura](#-arquitectura)
- [Prerrequisitos](#-prerrequisitos)
- [Instalación y Despliegue](#-instalación-y-despliegue)
- [Carga Inicial de Datos](#-carga-inicial-de-datos-csv)
- [Uso del Sistema](#-uso-del-sistema)
- [Ejemplos de Requests](#-ejemplos-de-requests)
- [Monitoreo y Logs](#-monitoreo-y-logs)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Estructura del Proyecto](#-estructura-del-proyecto)

---

## 🎯 Descripción General

**GUATEPASS** es un sistema completo de cobro automatizado de peajes que permite:

### Funcionalidades Principales

✅ **Gestión de Usuarios**
- Importación masiva desde CSV
- Consulta de información de usuarios
- Gestión de Tags 
- Tres modalidades: No registrados, Registrado en App y Con dispositivo Tag

✅ **Procesamiento de Transacciones**
- Webhook para recibir eventos de peaje
- Cálculo automático de tarifas segun modalidad
- Descuento automático de saldo (usuarios registrados)
- Generación de facturas

✅ **Sistema de Facturación**
- Facturas simuladas (no SAT)
- Modalidad 1 (No Registrado): Factura PENDIENTE + Multa 50%
- Modalidad 2 y 3 (Registrado en App y con Tag): Factura PAGADA automática
- Historial completo de facturas por vehículo

✅ **Notificaciones**
- Emails simulados con logs
- Invitación para registrarse (Modalidad 1)
- Notificación de cobro (Modalidad 2)
- Alertas de saldo bajo

✅ **API REST Completa**
- 9 endpoints para gestión completa
- Consulta de usuarios, tags, pagos y facturas
- CRUD completo de Tags

✅ **Monitoreo Completo**
- Dashboard de CloudWatch con 11 widgets
- Logs centralizados de 17 funciones Lambda
- Métricas de Lambda, API Gateway y DynamoDB

### Tecnologías Utilizadas

- **Compute:** AWS Lambda (Python 3.11)
- **API:** API Gateway REST
- **Storage:** DynamoDB (4 tablas), S3
- **Orchestration:** Step Functions
- **Events:** EventBridge
- **Monitoring:** CloudWatch (Dashboards, Logs, Alarms)
- **IaC:** AWS SAM (CloudFormation)

---

## 🎯 Resumen del Proyecto

| Componente | Descripción |
|-----------|-------------|
| **Fase #1** | Carga inicial de datos desde CSV |
| **Fase #2** | API de consulta de usuarios y tags |
| **Fase #3** | Webhook de peajes y EventBridge |
| **Fase #4** | Step Functions para procesamiento |
| **Fase #5** | Gestión completa de Tags RFID |
| **Fase #6** | Notificaciones y facturación |
| **Fase #7** | Endpoints de historial de pagos/facturas |
| **Fase #8** | Monitoreo completo con CloudWatch |

**Total de Funciones Lambda:** 17  
**Total de Endpoints API:** 9  
**Total de Tablas DynamoDB:** 4  
**Total de Widgets Dashboard:** 11  

---

## 🏗️ Arquitectura

### Arquitectura General del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      GUATEPASS SYSTEM                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  S3 Bucket   │────▶│   Lambda     │────▶│  DynamoDB    │
│  CSV Upload  │     │  ImportUsers │     │   Users      │
└──────────────┘     └──────────────┘     └──────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     API Gateway REST                          │
├──────────────────────────────────────────────────────────────┤
│  GET  /users/{placa}              - Consultar usuario        │
│  GET  /users/{placa}/tag          - Consultar tag            │
│  POST /users/{placa}/tag          - Crear tag                │
│  PUT  /users/{placa}/tag          - Actualizar tag           │
│  DELETE /users/{placa}/tag        - Eliminar tag             │
│  GET  /tags/{tag_id}              - Buscar por Tag ID        │
│  GET  /history/payments/{placa}   - Historial pagos         │
│  GET  /history/invoices/{placa}   - Historial facturas      │
│  POST /webhook/toll               - Recibir evento peaje     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      EventBridge Bus                          │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Step Functions (Orquestación)                │
├──────────────────────────────────────────────────────────────┤
│  1. ResolveUser    → Identificar usuario y modalidad         │
│  2. CalculateFare  → Calcular tarifa con multiplicador       │
│  3. RecordTransaction → Guardar en historial                 │
│  4. UpdateBalance  → Actualizar saldo (Modalidad 2)          │
│  5. GenerateInvoice → Crear factura (con/sin multa)          │
│  6. NotifyUser     → Enviar notificación (simulada)          │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────┐
│                    DynamoDB Tables                          │
├────────────────────────────────────────────────────────────┤
│  • GuatepassUsers         (PK: placa, GSI: tag_id)         │
│  • GuatepassTolls         (PK: toll_id)                    │
│  • GuatepassTransactions  (PK: transaction_id, GSI: placa) │
│  • GuatepassInvoices      (PK: invoice_id, GSI: placa)     │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              CloudWatch (Monitoreo y Logs)                  │
├────────────────────────────────────────────────────────────┤
│  • Dashboard con 11 widgets                                 │
│  • 17 Log Groups (7 días retención)                         │
│  • Métricas: Lambda, API Gateway, DynamoDB                  │
│  • Alarmas de errores configuradas                          │
└────────────────────────────────────────────────────────────┘
```

---

## 📦 Prerrequisitos

### Software Necesario

#### 1. AWS CLI (versión 2.x)
```bash
# Verificar instalación
aws --version
# Salida esperada: aws-cli/2.x.x o superior
```

**Instalación:**
- Windows: https://aws.amazon.com/cli/
- Mac: `brew install awscli`
- Linux: `pip install awscli`

#### 2. AWS SAM CLI
```bash
# Verificar instalación
sam --version
# Salida esperada: SAM CLI, version 1.100.0 o superior
```

**Instalación:**
- https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

#### 3. Python 3.11
```bash
# Verificar instalación
python --version
# Salida esperada: Python 3.11.x
```

#### 4. Git
```bash
git --version
```

### Configuración de AWS

#### 1. Configurar Credenciales

```bash
aws configure
```

**Información requerida:**
```
AWS Access Key ID: [tu-access-key]
AWS Secret Access Key: [tu-secret-key]
Default region name: us-east-1
Default output format: json
```

#### 2. Verificar Credenciales

```bash
aws sts get-caller-identity
```

**Salida esperada:**
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/tu-usuario"
}
```

### Permisos IAM Necesarios

El usuario/rol de AWS debe tener permisos para:

- ✅ **CloudFormation**: Crear/actualizar stacks
- ✅ **S3**: Crear buckets, subir objetos
- ✅ **Lambda**: Crear funciones, configurar triggers
- ✅ **DynamoDB**: Crear tablas, leer/escribir items
- ✅ **API Gateway**: Crear APIs y recursos
- ✅ **Step Functions**: Crear state machines
- ✅ **EventBridge**: Crear buses y reglas
- ✅ **IAM**: Crear roles y políticas
- ✅ **CloudWatch**: Crear dashboards, alarmas, log groups

**Política recomendada:** `PowerUserAccess` o permisos específicos personalizados.

---

## 🚀 Instalación y Despliegue

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/GUATE_PASS.git
cd GUATE_PASS
```

### Paso 2: Validar el Template

```bash
sam validate -t infrastructure/template.yaml
```

**Salida esperada:**
```
infrastructure/template.yaml is a valid SAM Template
```

### Paso 3: Build de la Aplicación

```bash
sam build -t infrastructure/template.yaml
```

**Salida esperada:**
```
Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
```

**Tiempo aproximado:** 1-2 minutos

### Paso 4: Desplegar en AWS

#### Opción A: Despliegue Guiado (Primera vez)

```bash
sam deploy --guided
```

**Responde las preguntas:**
```
Stack Name: guatepass-dev
AWS Region: us-east-1
Parameter Environment: dev
Confirm changes before deploy: y
Allow SAM CLI IAM role creation: Y
Disable rollback: N
Save arguments to configuration file: Y
SAM configuration file: samconfig.toml
SAM configuration environment: default
```

#### Opción B: Despliegue Directo (Siguientes veces)

```bash
sam deploy
```

**Tiempo aproximado:** 3-5 minutos

### Paso 5: Verificar el Despliegue

```bash
aws cloudformation describe-stacks \
  --stack-name guatepass-dev \
  --query 'Stacks[0].StackStatus'
```

**Salida esperada:**
```
"CREATE_COMPLETE" o "UPDATE_COMPLETE"
```

### Paso 6: Obtener Outputs del Stack

```bash
aws cloudformation describe-stacks \
  --stack-name guatepass-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

**Outputs importantes:**
- `ApiUrl`: URL base de la API REST
- `DataBucketName`: Nombre del bucket S3
- `DashboardURL`: URL del dashboard de CloudWatch
- Varios endpoints documentados

---

## 📤 Carga Inicial de Datos (CSV)

### Formato del Archivo CSV

El archivo debe tener el siguiente formato:

```csv
placa,nombre,email,telefono,tipo_usuario,tiene_tag,tag_id,saldo_disponible
P-123ABC,Juan Pérez,juan@email.com,50212345678,registrado,false,,100.00
P-456DEF,María López,maria@email.com,50298765432,registrado,true,TAG-001,250.00
P-888NOREGISTRADO,Usuario Desconocido,,,no_registrado,false,,0.00
```

**Campos:**
- `placa`: Placa del vehículo (formato: P-XXXXXX)
- `nombre`: Nombre del propietario
- `email`: Correo electrónico (opcional)
- `telefono`: Teléfono con código de país
- `tipo_usuario`: "registrado" o "no_registrado"
- `tiene_tag`: true/false
- `tag_id`: ID del tag RFID (si tiene_tag=true)
- `saldo_disponible`: Saldo en quetzales

### Subir el Archivo CSV

#### 1. Obtener el nombre del bucket

```bash
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name guatepass-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text)

echo "Bucket: $BUCKET_NAME"
```

#### 2. Subir el archivo

```bash
aws s3 cp data/clientes.csv s3://$BUCKET_NAME/clientes.csv
```

**Salida esperada:**
```
upload: data/clientes.csv to s3://guatepass-data-dev-123456789012/clientes.csv
```

#### 3. Verificar la importación

```bash
# Ver logs en tiempo real
sam logs -n ImportUsersFunction --stack-name guatepass-dev --tail

# Buscar mensaje de éxito
# [SUCCESS] Importación completada: {'total': 10, 'success': 10, 'errors': 0}
```

#### 4. Verificar datos en DynamoDB

```bash
# Contar usuarios importados
aws dynamodb scan \
  --table-name GuatepassUsers-dev \
  --select "COUNT"
```

### Generar CSV de Prueba

Puedes usar el script generador:

```bash
python scripts/generate_test_csv.py --users 100
```

Esto creará `data/clientes_test.csv` con 100 usuarios de prueba.

---

## 💻 Uso del Sistema

### Obtener la URL del API

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name guatepass-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "API URL: $API_URL"
```

### Endpoints Disponibles

#### 1. Consulta de Usuarios

**GET /users/{placa}** - Consultar información de usuario

```bash
curl "$API_URL/users/P-123ABC"
```

**Respuesta (200):**
```json
{
  "user": {
    "placa": "P-123ABC",
    "nombre": "Juan Pérez",
    "email": "juan@email.com",
    "tipo_usuario": "registrado",
    "saldo_disponible": 100.00,
    "tiene_tag": false,
    "estado": "activo"
  },
  "message": "Usuario P-123ABC encontrado exitosamente"
}
```

**GET /users/{placa}/tag** - Consultar tag asociado

```bash
curl "$API_URL/users/P-456DEF/tag"
```

#### 2. Gestión de Tags

**POST /users/{placa}/tag** - Crear/asociar tag

```bash
curl -X POST "$API_URL/users/P-123ABC/tag" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": "TAG-12345",
    "tag_status": "active"
  }'
```

**PUT /users/{placa}/tag** - Actualizar tag

```bash
curl -X PUT "$API_URL/users/P-123ABC/tag" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_status": "inactive"
  }'
```

**DELETE /users/{placa}/tag** - Eliminar tag

```bash
curl -X DELETE "$API_URL/users/P-123ABC/tag"
```

**GET /tags/{tag_id}** - Buscar usuario por Tag ID

```bash
curl "$API_URL/tags/TAG-12345"
```

#### 3. Historial

**GET /history/payments/{placa}** - Historial de pagos/transacciones

```bash
# Consulta básica
curl "$API_URL/history/payments/P-123ABC"

# Con límite de resultados
curl "$API_URL/history/payments/P-123ABC?limit=10"

# Con filtro de fechas
curl "$API_URL/history/payments/P-123ABC?from_date=2025-11-01T00:00:00&to_date=2025-11-30T23:59:59"
```

**Respuesta:**
```json
{
  "placa": "P-123ABC",
  "total_transactions": 5,
  "total_amount": 75.00,
  "transactions": [
    {
      "transaction_id": "TX-20251109103015-P123ABC",
      "toll_name": "Carretera Norte",
      "amount_charged": 15.00,
      "timestamp": "2025-11-09T10:30:15Z",
      "status": "completed"
    }
  ]
}
```

**GET /history/invoices/{placa}** - Historial de facturas

```bash
# Consulta básica
curl "$API_URL/history/invoices/P-123ABC"

# Solo facturas pendientes
curl "$API_URL/history/invoices/P-123ABC?status=pendiente"

# Solo facturas pagadas
curl "$API_URL/history/invoices/P-123ABC?status=pagada"
```

**Respuesta:**
```json
{
  "placa": "P-123ABC",
  "summary": {
    "total_invoices": 8,
    "pending_invoices": 2,
    "paid_invoices": 6,
    "total_amount": 150.00,
    "total_pending": 45.00,
    "total_paid": 105.00
  },
  "invoices": [
    {
      "invoice_id": "FAC-20251109103015",
      "estado": "pagada",
      "total": 15.00,
      "modalidad": 2,
      "concepto": "Paso por peaje - Carretera Norte"
    }
  ]
}
```

#### 4. Webhook de Peajes

**POST /webhook/toll** - Recibir evento de paso por peaje

```bash
curl -X POST "$API_URL/webhook/toll" \
  -H "Content-Type: application/json" \
  -d '{
    "placa": "P-123ABC",
    "toll_id": "PEAJE001",
    "timestamp": "2025-11-09T10:30:00Z"
  }'
```

**Respuesta (202):**
```json
{
  "message": "Evento de peaje recibido y procesando",
  "event_id": "evt-uuid-here",
  "placa": "P-123ABC"
}
```

---

## 📝 Ejemplos de Requests

### Usando Postman

1. **Importar Collection:**
   - Crear nueva collection "GUATEPASS"
   - Agregar variable `{{API_URL}}` con tu URL base

2. **Requests de ejemplo:**

```
GET {{API_URL}}/users/P-123ABC
GET {{API_URL}}/users/P-123ABC/tag
PUT {{API_URL}}/users/P-123ABC/tag
DELETE {{API_URL}}/users/P-123ABC/tag
POST {{API_URL}}/users/P-123ABC/tag
  Body: {"tag_id": "TAG-12345", "tag_status": "active"}
GET {{API_URL}}/history/payments/P-123ABC
GET {{API_URL}}/history/invoices/P-123ABC
POST {{API_URL}}/webhook/toll
  Body: {"placa": "P-123ABC", "toll_id": "PEAJE001", "timestamp": "2025-11-11T15:00:00Z"}
```

---

## 📊 Monitoreo y Logs

### Dashboard de CloudWatch

#### Acceder al Dashboard

**Opción 1: Desde AWS Console**
1. Ir a **CloudWatch** en AWS Console
2. Seleccionar **Dashboards** en el menú lateral
3. Buscar: `GUATEPASS-Complete-dev`

#### Widgets del Dashboard

El dashboard incluye **11 widgets** organizados:

1. **Lambda - Invocaciones Totales**
2. **Lambda - Errores y Throttles**
3. **Lambda - Duración (Promedio y P99)**
4. **Lambda - Concurrencia**
5. **API Gateway - Total Requests**
6. **API Gateway - Latencia**
7. **API Gateway - Errores 4XX/5XX**
8. **DynamoDB - Read Capacity** (4 tablas)
9. **DynamoDB - Write Capacity** (4 tablas)
10. **DynamoDB - Throttling Errors** (4 tablas)
11. **Logs - Errores Recientes** (Todas las funciones)

### Ver Logs en Tiempo Real

#### Logs de funciones específicas

```bash
# Lambda: Importación de usuarios
aws logs tail /aws/lambda/guatepass-import-users-dev --follow

# Lambda: Webhook de peajes
aws logs tail /aws/lambda/guatepass-ingest-toll-dev --follow

# Lambda: Historial de pagos
aws logs tail /aws/lambda/guatepass-get-payments-by-plate-dev --follow

# Lambda: Historial de facturas
aws logs tail /aws/lambda/guatepass-get-invoices-by-plate-dev --follow

# Lambda: Notificaciones
aws logs tail /aws/lambda/guatepass-notify-user-dev --follow

# Step Functions
aws logs tail /aws/stepfunctions/guatepass-process-toll-dev --follow
```

#### Filtrar solo errores

```bash
aws logs tail /aws/lambda/guatepass-ingest-toll-dev \
  --filter-pattern "ERROR"
```

### CloudWatch Logs Insights

#### Query de errores en todas las funciones

```sql
fields @timestamp, @message, @logStream
| filter @message like /ERROR/ or @message like /Error/
| sort @timestamp desc
| limit 50
```

#### Query de transacciones procesadas

```sql
fields @timestamp, @message
| filter @message like /transaction_id/
| sort @timestamp desc
| limit 20
```

### Métricas Principales

#### Lambda Invocations

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

#### API Gateway Requests

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=guatepass-api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

#### DynamoDB Operations

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=GuatepassUsers-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Log Groups Configurados

El sistema tiene **17 Log Groups** con retención de 7 días:

1. `/aws/lambda/guatepass-import-users-dev`
2. `/aws/lambda/guatepass-get-user-by-placa-dev`
3. `/aws/lambda/guatepass-get-tag-by-placa-dev`
4. `/aws/lambda/guatepass-create-tag-dev`
5. `/aws/lambda/guatepass-update-tag-dev`
6. `/aws/lambda/guatepass-delete-tag-dev`
7. `/aws/lambda/guatepass-get-tag-by-id-dev`
8. `/aws/lambda/guatepass-ingest-toll-dev`
9. `/aws/lambda/guatepass-resolve-user-dev`
10. `/aws/lambda/guatepass-calculate-fare-dev`
11. `/aws/lambda/guatepass-record-transaction-dev`
12. `/aws/lambda/guatepass-update-balance-dev`
13. `/aws/lambda/guatepass-generate-invoice-dev`
14. `/aws/lambda/guatepass-notify-user-dev`
15. `/aws/lambda/guatepass-get-payments-by-plate-dev`
16. `/aws/lambda/guatepass-get-invoices-by-plate-dev`
17. `/aws/stepfunctions/guatepass-process-toll-dev`

---

## 🧪 Testing

### Scripts Automatizados

El proyecto incluye scripts de testing completos:

```bash
# Test de API de consulta
.\scripts\test-api.ps1

# Test de webhook de peajes
.\scripts\test-webhook.ps1

# Test de Step Functions
.\scripts\test-stepfunction.ps1

# Test de gestión de tags
.\scripts\test-tags.ps1

# Test de historial
.\scripts\test-history.ps1

# Test de notificaciones
.\scripts\test-slice6-notifications.ps1
```

### Testing Manual

#### Test Completo del Flujo

```bash
# 1. Consultar usuario
curl "$API_URL/users/P-111JKL"

# 2. Simular paso por peaje
curl -X POST "$API_URL/webhook/toll" \
  -H "Content-Type: application/json" \
  -d '{"placa": "P-111JKL", "toll_id": "PEAJE001", "timestamp": "2025-11-11T15:00:00Z"}'

# 3. Esperar 10 segundos (procesamiento)
sleep 10

# 4. Ver historial de pagos actualizado
curl "$API_URL/history/payments/P-111JKL"

# 5. Ver facturas generadas
curl "$API_URL/history/invoices/P-111JKL"

# 6. Ver logs de notificaciones
aws logs tail /aws/lambda/guatepass-notify-user-dev --since 5m
```

---


## 📅 Información del Proyecto

- **Universidad:** Francisco Marroquín (UFM)
- **Curso:** Cloud Computing
- **Fecha de Entrega:** 17 de noviembre de 2025

---

## 📖 Referencias

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html)
- [Step Functions](https://docs.aws.amazon.com/step-functions/)
- [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html)

---

