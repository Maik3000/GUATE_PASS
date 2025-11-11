# 🏗️ GUATEPASS - Diagrama de Arquitectura Técnica

## Componentes AWS Serverless Implementados

Este documento detalla todos los componentes AWS serverless utilizados en el sistema GUATEPASS y sus interacciones.

---

## 📊 Arquitectura General del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GUATEPASS - Sistema Completo                         │
│                         Arquitectura 100% Serverless                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: INGRESO DE DATOS                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                                           │
│  │   Usuario    │                                                           │
│  │  Administrador│                                                          │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         │ Upload CSV                                                        │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │           AWS S3 Bucket                                 │              │
│  │           guatepass-data-{environment}                  │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  Trigger: S3:ObjectCreated:*                   │    │              │
│  │  │  Filter: prefix="clientes", suffix=".csv"      │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └─────────────────────┬───────────────────────────────────┘              │
│                        │                                                    │
│                        │ Event                                              │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │     AWS Lambda: ImportUsersFunction                     │              │
│  │     Runtime: Python 3.11 | Memory: 256MB                │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  1. Download CSV from S3                       │    │              │
│  │  │  2. Parse CSV (validates format)               │    │              │
│  │  │  3. Validate user data                         │    │              │
│  │  │  4. Batch write to DynamoDB (25 items/batch)   │    │              │
│  │  │  5. Log results to CloudWatch                  │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └─────────────────────┬───────────────────────────────────┘              │
│                        │                                                    │
│                        │ BatchWriteItem                                     │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │        DynamoDB: GuatepassUsers                         │              │
│  │        BillingMode: PAY_PER_REQUEST                     │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  PK: placa (String)                            │    │              │
│  │  │  Attributes:                                   │    │              │
│  │  │    - nombre, email, telefono                   │    │              │
│  │  │    - tipo_usuario (registrado/no_registrado)   │    │              │
│  │  │    - tiene_tag, tag_id, tag_status             │    │              │
│  │  │    - saldo_disponible, estado                  │    │              │
│  │  │  GSI: TagIndex (tag_id as PK)                  │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └─────────────────────────────────────────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 2: API REST (API Gateway + Lambda)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │        AWS API Gateway REST                             │              │
│  │        Name: guatepass-api                              │              │
│  │        Stage: dev                                       │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  CORS Enabled: *                               │    │              │
│  │  │  Authorization: None (public endpoints)        │    │              │
│  │  │  Throttling: 10,000 req/sec burst              │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └───┬─────────────┬────────────┬──────────────┬──────────┘              │
│      │             │            │              │                          │
│      │ GET         │ GET/POST/  │ GET          │ POST                     │
│      │ /users      │ PUT/DELETE │ /history     │ /webhook                 │
│      ▼             ▼            ▼              ▼                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐                   │
│  │Lambda   │  │Lambda   │  │Lambda   │  │Lambda    │                   │
│  │GetUser  │  │Tag CRUD │  │History  │  │IngestToll│                   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────┬────┘                   │
│       │            │            │              │                          │
│       └────────────┴────────────┴──────────────┘                          │
│                          │                                                 │
│                          ▼                                                 │
│          ┌───────────────────────────────────┐                           │
│          │    DynamoDB Tables (4 tablas)     │                           │
│          │  • GuatepassUsers                 │                           │
│          │  • GuatepassTolls                 │                           │
│          │  • GuatepassTransactions          │                           │
│          │  • GuatepassInvoices              │                           │
│          └───────────────────────────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 3: PROCESAMIENTO DE EVENTOS (EventBridge + Step Functions)             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  POST /webhook/toll                                                         │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │  Lambda: IngestTollFunction                             │              │
│  │  • Recibe evento de paso por peaje                      │              │
│  │  • Valida formato del payload                           │              │
│  │  • Publica evento a EventBridge                         │              │
│  └─────────────────────┬───────────────────────────────────┘              │
│                        │                                                    │
│                        │ PutEvents                                          │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │        AWS EventBridge Bus                              │              │
│  │        Name: guatepass-event-bus                        │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  Event Pattern:                                │    │              │
│  │  │  {                                             │    │              │
│  │  │    "source": ["guatepass.toll"],              │    │              │
│  │  │    "detail-type": ["Toll Event"]              │    │              │
│  │  │  }                                             │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └─────────────────────┬───────────────────────────────────┘              │
│                        │                                                    │
│                        │ Trigger Rule                                       │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │        AWS Step Functions                               │              │
│  │        Name: guatepass-process-toll                     │              │
│  │        Type: STANDARD                                   │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │                                                 │    │              │
│  │  │  ┌──────────────────────────────────────┐     │    │              │
│  │  │  │ 1. ResolveUserProfile                │     │    │              │
│  │  │  │    • Query DynamoDB por placa        │     │    │              │
│  │  │  │    • Determinar modalidad            │     │    │              │
│  │  │  │    • Output: user_profile            │     │    │              │
│  │  │  └──────────────┬───────────────────────┘     │    │              │
│  │  │                 ▼                              │    │              │
│  │  │  ┌──────────────────────────────────────┐     │    │              │
│  │  │  │ 2. CalculateTollFare                 │     │    │              │
│  │  │  │    • Query toll price from Tolls     │     │    │              │
│  │  │  │    • Apply multiplier (1.0 o 1.5)    │     │    │              │
│  │  │  │    • Output: fare_calculation        │     │    │              │
│  │  │  └──────────────┬───────────────────────┘     │    │              │
│  │  │                 ▼                              │    │              │
│  │  │  ┌──────────────────────────────────────┐     │    │              │
│  │  │  │ 3. RecordTransaction                 │     │    │              │
│  │  │  │    • Create transaction record       │     │    │              │
│  │  │  │    • Write to Transactions table     │     │    │              │
│  │  │  │    • Output: transaction_id          │     │    │              │
│  │  │  └──────────────┬───────────────────────┘     │    │              │
│  │  │                 ▼                              │    │              │
│  │  │  ┌──────────────────────────────────────┐     │    │              │
│  │  │  │ 4. UpdateBalance (Modalidad 2 only) │     │    │              │
│  │  │  │    • Deduct from saldo_disponible    │     │    │              │
│  │  │  │    • Update Users table              │     │    │              │
│  │  │  └──────────────┬───────────────────────┘     │    │              │
│  │  │                 ▼                              │    │              │
│  │  │  ┌──────────────────────────────────────┐     │    │              │
│  │  │  │ 5. GenerateInvoice                   │     │    │              │
│  │  │  │    • Create invoice record           │     │    │              │
│  │  │  │    • Add multa if Modalidad 1 (50%)  │     │    │              │
│  │  │  │    • Write to Invoices table         │     │    │              │
│  │  │  │    • Output: invoice                 │     │    │              │
│  │  │  └──────────────┬───────────────────────┘     │    │              │
│  │  │                 ▼                              │    │              │
│  │  │  ┌──────────────────────────────────────┐     │    │              │
│  │  │  │ 6. NotifyUser                        │     │    │              │
│  │  │  │    • Generate email template         │     │    │              │
│  │  │  │    • Log simulated email             │     │    │              │
│  │  │  │    • Modalidad 1: Invitación         │     │    │              │
│  │  │  │    • Modalidad 2: Notificación       │     │    │              │
│  │  │  └──────────────┬───────────────────────┘     │    │              │
│  │  │                 ▼                              │    │              │
│  │  │        [Processing Success]                    │    │              │
│  │  │                                                 │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  │                                                          │              │
│  │  Error Handling:                                        │              │
│  │    • Catch all errors                                   │              │
│  │    • Log to CloudWatch                                  │              │
│  │    • Return error details                               │              │
│  └─────────────────────────────────────────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 4: MONITOREO Y OBSERVABILIDAD (CloudWatch)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │          AWS CloudWatch Dashboard                        │              │
│  │          Name: GUATEPASS-Complete-dev                    │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  11 Widgets:                                   │    │              │
│  │  │  • Lambda Invocations (total)                  │    │              │
│  │  │  • Lambda Errors & Throttles                   │    │              │
│  │  │  • Lambda Duration (avg, p99)                  │    │              │
│  │  │  • Lambda Concurrency                          │    │              │
│  │  │  • API Gateway Requests                        │    │              │
│  │  │  • API Gateway Latency                         │    │              │
│  │  │  • API Gateway 4XX/5XX Errors                  │    │              │
│  │  │  • DynamoDB Read Capacity (4 tables)           │    │              │
│  │  │  • DynamoDB Write Capacity (4 tables)          │    │              │
│  │  │  • DynamoDB Throttling Errors (4 tables)       │    │              │
│  │  │  • Logs - Recent Errors (unified query)        │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └─────────────────────────────────────────────────────────┘              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │          AWS CloudWatch Logs                            │              │
│  │          17 Log Groups (Retention: 7 days)              │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  /aws/lambda/guatepass-import-users-dev        │    │              │
│  │  │  /aws/lambda/guatepass-get-user-by-placa-dev   │    │              │
│  │  │  /aws/lambda/guatepass-get-tag-by-placa-dev    │    │              │
│  │  │  /aws/lambda/guatepass-create-tag-dev          │    │              │
│  │  │  /aws/lambda/guatepass-update-tag-dev          │    │              │
│  │  │  /aws/lambda/guatepass-delete-tag-dev          │    │              │
│  │  │  /aws/lambda/guatepass-get-tag-by-id-dev       │    │              │
│  │  │  /aws/lambda/guatepass-ingest-toll-dev         │    │              │
│  │  │  /aws/lambda/guatepass-resolve-user-dev        │    │              │
│  │  │  /aws/lambda/guatepass-calculate-fare-dev      │    │              │
│  │  │  /aws/lambda/guatepass-record-transaction-dev  │    │              │
│  │  │  /aws/lambda/guatepass-update-balance-dev      │    │              │
│  │  │  /aws/lambda/guatepass-generate-invoice-dev    │    │              │
│  │  │  /aws/lambda/guatepass-notify-user-dev         │    │              │
│  │  │  /aws/lambda/guatepass-get-payments-by-plate-dev│   │              │
│  │  │  /aws/lambda/guatepass-get-invoices-by-plate-dev│   │              │
│  │  │  /aws/stepfunctions/guatepass-process-toll-dev │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └─────────────────────────────────────────────────────────┘              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │          AWS CloudWatch Alarms                          │              │
│  │  ┌────────────────────────────────────────────────┐    │              │
│  │  │  ImportUsersErrorAlarm                         │    │              │
│  │  │    • Metric: Lambda Errors                     │    │              │
│  │  │    • Threshold: >= 1 error in 5 minutes        │    │              │
│  │  │    • Action: Log alarm state                   │    │              │
│  │  └────────────────────────────────────────────────┘    │              │
│  └─────────────────────────────────────────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Componentes Detallados

### 1. AWS Lambda (17 Funciones)

| Función | Runtime | Memoria | Timeout | Trigger | Propósito |
|---------|---------|---------|---------|---------|-----------|
| ImportUsersFunction | Python 3.11 | 256MB | 30s | S3 | Importar usuarios desde CSV |
| GetUserByPlacaFunction | Python 3.11 | 256MB | 30s | API Gateway | Consultar usuario por placa |
| GetTagByPlacaFunction | Python 3.11 | 256MB | 30s | API Gateway | Consultar tag por placa |
| CreateTagFunction | Python 3.11 | 256MB | 30s | API Gateway | Crear tag RFID |
| UpdateTagFunction | Python 3.11 | 256MB | 30s | API Gateway | Actualizar tag RFID |
| DeleteTagFunction | Python 3.11 | 256MB | 30s | API Gateway | Eliminar tag RFID |
| GetTagFunction | Python 3.11 | 256MB | 30s | API Gateway | Buscar usuario por Tag ID |
| IngestTollFunction | Python 3.11 | 256MB | 30s | API Gateway | Recibir evento de peaje |
| ResolveUserProfileFunction | Python 3.11 | 256MB | 30s | Step Functions | Resolver perfil de usuario |
| CalculateTollFareFunction | Python 3.11 | 256MB | 30s | Step Functions | Calcular tarifa |
| RecordTransactionFunction | Python 3.11 | 256MB | 30s | Step Functions | Registrar transacción |
| UpdateBalanceFunction | Python 3.11 | 256MB | 30s | Step Functions | Actualizar saldo |
| GenerateInvoiceFunction | Python 3.11 | 256MB | 30s | Step Functions | Generar factura |
| NotifyUserFunction | Python 3.11 | 256MB | 30s | Step Functions | Enviar notificación |
| GetPaymentsByPlateFunction | Python 3.11 | 256MB | 30s | API Gateway | Historial de pagos |
| GetInvoicesByPlateFunction | Python 3.11 | 256MB | 30s | API Gateway | Historial de facturas |

**Características Comunes:**
- Active Tracing habilitado (AWS X-Ray)
- Variables de entorno configuradas
- IAM Roles con permisos mínimos necesarios
- CloudWatch Logs con retención de 7 días

### 2. AWS DynamoDB (4 Tablas)

#### Tabla 1: GuatepassUsers
```
BillingMode: PAY_PER_REQUEST
PartitionKey: placa (String)

Attributes:
- placa: String (PK)
- nombre: String
- email: String
- telefono: String
- tipo_usuario: String (registrado/no_registrado)
- tiene_tag: Boolean
- tag_id: String
- tag_status: String
- tag_created_at: String (ISO 8601)
- tag_updated_at: String (ISO 8601)
- saldo_disponible: Number
- estado: String

Global Secondary Indexes:
- TagIndex
  - PartitionKey: tag_id
  - Projection: ALL
  - Purpose: Búsqueda rápida por Tag ID

Features:
- Point-in-time recovery enabled
- DynamoDB Streams enabled
- Encryption at rest (AES-256)
```

#### Tabla 2: GuatepassTolls
```
BillingMode: PAY_PER_REQUEST
PartitionKey: toll_id (String)

Attributes:
- toll_id: String (PK)
- toll_name: String
- location: String
- base_price: Number
- created_at: String (ISO 8601)
- updated_at: String (ISO 8601)

Features:
- Point-in-time recovery enabled
```

#### Tabla 3: GuatepassTransactions
```
BillingMode: PAY_PER_REQUEST
PartitionKey: transaction_id (String)

Attributes:
- transaction_id: String (PK)
- placa: String
- toll_id: String
- toll_name: String
- modalidad: Number (1 or 2)
- base_fare: Number
- multiplier: Number
- amount_charged: Number
- timestamp: String (ISO 8601)
- created_at: String (ISO 8601)
- status: String

Global Secondary Indexes:
- PlacaTimestampIndex
  - PartitionKey: placa
  - SortKey: timestamp
  - Projection: ALL
  - Purpose: Historial de transacciones por placa

Features:
- DynamoDB Streams enabled
- Point-in-time recovery enabled
```

#### Tabla 4: GuatepassInvoices
```
BillingMode: PAY_PER_REQUEST
PartitionKey: invoice_id (String)

Attributes:
- invoice_id: String (PK)
- placa: String
- transaction_id: String
- toll_name: String
- modalidad: Number (1 or 2)
- monto_base: Number
- multa: Number (50% for Modalidad 1)
- total: Number
- estado: String (pendiente/pagada)
- concepto: String
- created_at: String (ISO 8601)
- contribuyente: Map (nombre, email, nit, direccion)

Global Secondary Indexes:
- PlacaCreatedIndex
  - PartitionKey: placa
  - SortKey: created_at
  - Projection: ALL
  - Purpose: Historial de facturas por placa

Features:
- Point-in-time recovery enabled
```

### 3. AWS API Gateway REST

```
Type: REST API
Name: guatepass-api
Stage: dev
Deployment: Automatic via SAM

Endpoints (12 total):
1. GET    /users/{placa}              → GetUserByPlacaFunction
2. GET    /users/{placa}/tag          → GetTagByPlacaFunction
3. POST   /users/{placa}/tag          → CreateTagFunction
4. PUT    /users/{placa}/tag          → UpdateTagFunction
5. DELETE /users/{placa}/tag          → DeleteTagFunction
6. GET    /tags/{tag_id}              → GetTagFunction
7. GET    /history/payments/{placa}   → GetPaymentsByPlateFunction
8. GET    /history/invoices/{placa}   → GetInvoicesByPlateFunction
9. POST   /webhook/toll               → IngestTollFunction

Features:
- CORS enabled (AllowOrigin: *)
- Default throttling: 10,000 req/sec burst
- Integration: Lambda Proxy
- Authorization: None (public API)
- CloudWatch Logs enabled
```

### 4. AWS Step Functions

```
Name: guatepass-process-toll
Type: STANDARD
Definition: process_toll.asl.json

States (6):
1. ResolveUserProfile (Task → Lambda)
2. CalculateTollFare (Task → Lambda)
3. RecordTransaction (Task → Lambda)
4. UpdateBalance (Task → Lambda) [Conditional]
5. GenerateInvoice (Task → Lambda)
6. NotifyUser (Task → Lambda)
7. ProcessingSuccess (Succeed)
8. ProcessingFailed (Fail)

Features:
- CloudWatch Logs enabled (ALL level)
- Execution data logging enabled
- X-Ray tracing enabled
- Error handling with Catch blocks
- Retry policies configured
```

### 5. AWS EventBridge

```
Name: guatepass-event-bus
Type: Custom Event Bus

Rules:
- ProcessTollEventRule
  - Event Pattern:
    {
      "source": ["guatepass.toll"],
      "detail-type": ["Toll Event"]
    }
  - Target: Step Functions State Machine
  - Transform: Event → Step Functions input

Features:
- Archive disabled (logs in CloudWatch)
- Dead Letter Queue: None (handled by Step Functions)
```

### 6. AWS S3

```
Bucket Name: guatepass-data-{environment}-{account-id}

Features:
- Server-side encryption (AES-256)
- Versioning enabled
- Public access blocked
- Lifecycle policy: Delete old versions after 30 days
- Event notification to Lambda (ImportUsersFunction)

Trigger Configuration:
- Event: s3:ObjectCreated:*
- Prefix: "clientes"
- Suffix: ".csv"
```

### 7. AWS CloudWatch

#### Dashboard
```
Name: GUATEPASS-Complete-{environment}
Widgets: 11 widgets
- 4 Lambda widgets (invocations, errors, duration, concurrency)
- 3 API Gateway widgets (requests, latency, errors)
- 3 DynamoDB widgets (read/write capacity, throttling)
- 1 Logs widget (unified error query)

Refresh: Every 5 minutes (300 seconds)
```

#### Log Groups
```
Total: 17 log groups
Retention: 7 days
Encryption: AES-256 (default)
```

#### Alarms
```
ImportUsersErrorAlarm:
- Metric: AWS/Lambda Errors
- Threshold: >= 1
- Period: 5 minutes
- Statistic: Sum
- Action: None (logging only)
```

---

## 🔧 Políticas de IAM y Seguridad

### Lambda Execution Roles

Cada Lambda tiene un rol de ejecución con permisos mínimos:

```yaml
Permissions:
  - CloudWatch Logs (write)
  - DynamoDB (read/write según función)
  - S3 (read only para ImportUsers)
  - EventBridge (PutEvents para IngestToll)
  - X-Ray (tracing)
```

### API Gateway

```yaml
Authorization: None (public API)
CORS: Enabled
Resource Policy: None (open access)
```

### DynamoDB

```yaml
Encryption: AWS managed key
Backup: Point-in-time recovery
Streams: Enabled for change tracking
```

---

## 📊 Métricas de Performance

### Latencias Esperadas

| Componente | Latencia Típica | Latencia P99 |
|-----------|-----------------|--------------|
| Lambda (Cold Start) | 1000-1500ms | 2000ms |
| Lambda (Warm) | 50-150ms | 300ms |
| API Gateway | 20-50ms | 100ms |
| DynamoDB Query | 5-20ms | 50ms |
| Step Functions | 2-5 segundos | 10 segundos |

### Escalabilidad

- **Lambda**: 1,000 ejecuciones concurrentes (default limit)
- **API Gateway**: 10,000 req/sec burst, 5,000 steady-state
- **DynamoDB**: Ilimitado (PAY_PER_REQUEST)
- **EventBridge**: 2,400 eventos/segundo (default)
- **Step Functions**: 1,300 transiciones de estado/segundo

---

## 🌐 Regiones y Disponibilidad

```
Primary Region: us-east-1 (N. Virginia)
Availability: Multi-AZ (automático en servicios serverless)
Disaster Recovery: Point-in-time recovery habilitado en DynamoDB
```

---

**Última actualización:** Noviembre 11, 2025  
**Versión del Sistema:** 1.0.0  
**Estado:** Producción

