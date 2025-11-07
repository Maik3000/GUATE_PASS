# 🏗️ Arquitectura - Slice #1: Carga Inicial de Datos

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Componentes](#componentes)
3. [Flujo de Datos](#flujo-de-datos)
4. [Decisiones Arquitectónicas](#decisiones-arquitectónicas)
5. [Modelo de Datos](#modelo-de-datos)
6. [Seguridad](#seguridad)
7. [Escalabilidad](#escalabilidad)
8. [Monitoreo y Observabilidad](#monitoreo-y-observabilidad)

---

## Descripción General

El Slice #1 implementa el componente fundamental del sistema GUATEPASS: la **carga inicial de usuarios** desde un archivo CSV hacia la base de datos DynamoDB. Este componente es el punto de partida que permite tener una base de usuarios para los siguientes slices del sistema.

### Objetivos del Slice

✅ Cargar datos iniciales de usuarios desde CSV  
✅ Validar y normalizar datos  
✅ Persistir en DynamoDB con modelo de datos apropiado  
✅ Manejar errores de forma resiliente  
✅ Proporcionar observabilidad completa  
✅ Infrastructure as Code (SAM)

---

## Componentes

### 1. Amazon S3 Bucket - `GuatepassDataBucket`

**Propósito:** Almacenamiento de archivos CSV con datos iniciales de usuarios.

**Características:**
- **Nombre:** `guatepass-data-{env}-{account-id}`
- **Encriptación:** AES-256 (server-side)
- **Versionamiento:** Habilitado (permite auditoría y recuperación)
- **Acceso público:** Bloqueado completamente
- **Lifecycle:** Versiones antiguas se eliminan después de 30 días

**Justificación:**
- S3 es el servicio nativo de AWS para almacenamiento de objetos
- Integración directa con Lambda mediante triggers
- Altamente durable (99.999999999% durability)
- Costo muy bajo para archivos pequeños
- Serverless, no requiere administración

### 2. AWS Lambda - `ImportUsersFunction`

**Propósito:** Procesar el archivo CSV y cargar usuarios a DynamoDB.

**Características:**
- **Runtime:** Python 3.11
- **Memoria:** 256 MB
- **Timeout:** 30 segundos
- **Trigger:** S3 ObjectCreated (filtro: `clientes*.csv`)
- **Concurrencia:** Sin límite específico (usa cuenta default)

**Proceso:**
1. Recibe evento de S3 cuando se sube un archivo
2. Descarga el archivo CSV del bucket
3. Parsea y valida cada línea del CSV
4. Normaliza datos (mayúsculas, tipos, validaciones)
5. Escribe en DynamoDB usando batch write (25 items por batch)
6. Reporta estadísticas de éxito/errores

**Manejo de Errores:**
- Si una fila del CSV es inválida, se registra un WARNING y continúa
- Si falla un batch completo, se registra ERROR pero no detiene el proceso
- La función retorna estadísticas: `{total, success, errors}`

**Justificación:**
- Lambda es el servicio serverless estándar para procesamiento event-driven
- Escalamiento automático basado en eventos
- Solo pagas por el tiempo de ejecución
- Integración nativa con S3 y DynamoDB
- 30 segundos es suficiente para procesar CSV de miles de usuarios

### 3. Amazon DynamoDB - `GuatepassUsers`

**Propósito:** Base de datos NoSQL serverless para almacenar información de usuarios.

**Esquema:**

```
Tabla: GuatepassUsers
├── Partition Key: placa (String)
├── Global Secondary Index: TagIndex
│   └── Partition Key: tag_id (String)
├── Billing Mode: PAY_PER_REQUEST
└── Point-in-Time Recovery: Enabled
```

**Atributos:**

| Atributo | Tipo | Requerido | Descripción |
|----------|------|-----------|-------------|
| `placa` | String | ✅ | Identificador único del vehículo (PK) |
| `nombre` | String | ✅ | Nombre del propietario |
| `email` | String | ❌ | Correo electrónico |
| `telefono` | String | ❌ | Número de teléfono |
| `tipo_usuario` | String | ✅ | `registrado` \| `no_registrado` |
| `tiene_tag` | Boolean | ✅ | Indica si posee dispositivo Tag |
| `tag_id` | String | ❌ | ID del Tag (null si no tiene) |
| `saldo_disponible` | Number | ✅ | Saldo en quetzales (Decimal) |
| `estado` | String | ✅ | `activo` \| `inactivo` \| `suspendido` |

**Índices:**

1. **Primary Key:** `placa`
   - Permite consultas rápidas por placa del vehículo
   - Caso de uso: Validar si un vehículo está registrado al pasar por peaje

2. **GSI TagIndex:** `tag_id`
   - Permite consultas rápidas por Tag ID
   - Caso de uso: Cuando el sistema detecta un Tag, buscar el usuario asociado
   - Proyección: ALL (incluye todos los atributos)

**Justificación:**
- DynamoDB es la base de datos serverless recomendada para cargas event-driven
- PAY_PER_REQUEST elimina la necesidad de provisionar capacidad
- Latencias de lectura/escritura de un solo dígito (milisegundos)
- Escalamiento automático hasta millones de requests por segundo
- Point-in-Time Recovery protege contra eliminaciones accidentales
- GSI permite consultas eficientes tanto por placa como por tag_id

### 4. Amazon CloudWatch

**Propósito:** Observabilidad, logging, métricas y alarmas.

**Componentes:**

1. **Log Group:** `/aws/lambda/guatepass-import-users-{env}`
   - Retención: 7 días
   - Logs estructurados con niveles: INFO, WARNING, ERROR

2. **Dashboard:** `GUATEPASS-Slice1-{env}`
   - Invocaciones de Lambda
   - Errores de Lambda
   - Duración promedio
   - Capacidad consumida en DynamoDB
   - Log insights query para errores recientes

3. **Alarm:** `guatepass-import-users-errors-{env}`
   - Métrica: Lambda Errors
   - Threshold: ≥1 error en 5 minutos
   - Acción: (Preparado para SNS topic en slices futuros)

**Justificación:**
- CloudWatch es el servicio nativo de observabilidad en AWS
- Integración automática con Lambda y DynamoDB
- Dashboards personalizables para monitoreo en tiempo real
- Alarmas proactivas para detectar problemas
- Log Insights permite queries SQL-like sobre logs

---

## Flujo de Datos

### Diagrama de Secuencia

```
Usuario/Admin          S3 Bucket              Lambda                 DynamoDB
    |                     |                      |                       |
    |-- Upload CSV ------>|                      |                       |
    |                     |                      |                       |
    |                     |-- S3:ObjectCreated ->|                       |
    |                     |                      |                       |
    |                     |                      |-- GetObject --------->|
    |                     |<----- CSV content ---|                       |
    |                     |                      |                       |
    |                     |                      |-- Parse & Validate   |
    |                     |                      |                       |
    |                     |                      |-- BatchWriteItem ---->|
    |                     |                      |<----- Success --------|
    |                     |                      |                       |
    |                     |                      |-- BatchWriteItem ---->|
    |                     |                      |<----- Success --------|
    |                     |                      |                       |
    |                     |                      |-- Return stats        |
    |                     |                      |                       |
    |<--- View Logs --------------------------------- CloudWatch -------|
```

### Paso a Paso Detallado

1. **Trigger Inicial**
   - Admin/Usuario sube `clientes.csv` a S3
   - Comando: `aws s3 cp data/clientes.csv s3://{bucket}/clientes.csv`

2. **Evento S3**
   - S3 genera evento `ObjectCreated:Put`
   - Evento incluye: bucket name, object key, size, timestamp
   - Filtro: Solo archivos con prefijo `clientes` y sufijo `.csv`

3. **Invocación Lambda**
   - EventSourceMapping invoca `ImportUsersFunction`
   - Lambda recibe evento con metadata del objeto S3

4. **Download CSV**
   ```python
   s3_client.get_object(Bucket=bucket, Key=key)
   ```
   - Lambda descarga el archivo completo en memoria
   - Decodifica UTF-8

5. **Parse CSV**
   ```python
   csv.DictReader(StringIO(csv_content))
   ```
   - Parsea línea por línea
   - Valida campos requeridos
   - Normaliza datos (mayúsculas, tipos)

6. **Validación y Transformación**
   - `placa`: Requerido, uppercase
   - `tiene_tag`: String → Boolean
   - `saldo_disponible`: String → Decimal
   - `tipo_usuario`: Inferir si está vacío
   - Limpia valores None (DynamoDB no los acepta)

7. **Batch Write a DynamoDB**
   ```python
   with table.batch_writer() as batch:
       for user in users:
           batch.put_item(Item=user)
   ```
   - Batches de máximo 25 items
   - Manejo de errores por item

8. **Logging y Estadísticas**
   - Log estructurado con prefijos [INFO], [WARNING], [ERROR]
   - Retorna: `{total, success, errors}`

9. **Monitoreo**
   - CloudWatch captura todos los logs
   - Métricas se actualizan automáticamente
   - Dashboard refleja la ejecución

---

## Decisiones Arquitectónicas

### 1. ¿Por qué S3 + Lambda Trigger?

**Alternativas consideradas:**
- ❌ API Gateway + Lambda: Requiere subir CSV vía HTTP (limitaciones de tamaño)
- ❌ EventBridge Scheduler + Lambda: No hay eventos periódicos, es carga inicial
- ❌ Step Functions: Sobrecarga para un proceso simple

**Decisión:** S3 + Lambda Trigger  
**Justificación:**
- Patrón estándar de AWS para procesamiento de archivos
- Desacoplamiento: S3 actúa como buffer
- Simplicidad: Trigger automático, sin código adicional
- Escalabilidad: Maneja archivos de cualquier tamaño
- Auditoría: Versionamiento de S3 mantiene histórico

### 2. ¿Por qué DynamoDB PAY_PER_REQUEST?

**Alternativas consideradas:**
- ❌ DynamoDB Provisioned: Requiere estimar capacidad, desperdicio si carga es variable
- ❌ Aurora Serverless: Más costoso, capacidades relacionales no necesarias
- ❌ RDS: No serverless, requiere administración

**Decisión:** DynamoDB PAY_PER_REQUEST  
**Justificación:**
- Costo: Solo pagas por requests reales
- Escalamiento: Automático, sin configuración
- Latencia: <10ms lecturas/escrituras
- Serverless: Cero administración
- Integración: SDKs nativos con Lambda

### 3. ¿Por qué Python 3.11?

**Alternativas consideradas:**
- ❌ Node.js: Menos legible para procesamiento de datos
- ❌ Java: Cold start más largo, overhead innecesario
- ❌ Go: Compilación adicional, menos familiaridad

**Decisión:** Python 3.11  
**Justificación:**
- Librería estándar `csv` robusta
- `boto3` es el SDK oficial de AWS
- Sintaxis clara y mantenible
- Runtime optimizado (mejor que 3.9)
- Cold start aceptable (~500ms)

### 4. ¿Por qué batch_writer de boto3?

**Alternativas consideradas:**
- ❌ `put_item` individual: 25x más lento, más costoso
- ❌ `batch_write_item` manual: Más código, propenso a errores

**Decisión:** `batch_writer()` context manager  
**Justificación:**
- Automatiza batching (25 items)
- Manejo de throttling automático (exponential backoff)
- Código más limpio
- Menos errores

### 5. ¿Por qué GSI en tag_id?

**Decisión:** Global Secondary Index en `tag_id`  
**Justificación:**
- Caso de uso futuro: Al detectar Tag en peaje, buscar usuario
- Query eficiente: O(1) vs Scan O(n)
- Costo: Mínimo, PAY_PER_REQUEST escala automáticamente
- Flexibilidad: Permite búsquedas por placa Y por tag

---

## Modelo de Datos

### Esquema Lógico

```json
{
  "placa": "P-123ABC",              // PK, String, Uppercase
  "nombre": "Juan Pérez",           // String
  "email": "juan@email.com",        // String | null
  "telefono": "50212345678",        // String | null
  "tipo_usuario": "registrado",     // "registrado" | "no_registrado"
  "tiene_tag": false,               // Boolean
  "tag_id": null,                   // String | null
  "saldo_disponible": 100.00,       // Decimal (DynamoDB Number)
  "estado": "activo"                // "activo" | "inactivo" | "suspendido"
}
```

### Patrones de Acceso (Slice #1)

| Caso de Uso | Operación | Clave |
|-------------|-----------|-------|
| Verificar si usuario existe | `GetItem` | `placa` |
| Buscar usuario por Tag | `Query` GSI | `tag_id` |
| Cargar todos los usuarios | `Scan` | - |

### Patrones de Acceso (Futuros Slices)

| Caso de Uso | Operación | Clave |
|-------------|-----------|-------|
| Paso por peaje sin Tag | `GetItem` | `placa` |
| Paso por peaje con Tag | `Query` GSI | `tag_id` |
| Actualizar saldo | `UpdateItem` | `placa` |
| Asociar nuevo Tag | `UpdateItem` | `placa` |
| Historial de usuario | Query en tabla `GuatepassTransactions` | `placa` (PK) |

---

## Seguridad

### 1. IAM - Principle of Least Privilege

**Lambda Execution Role:**
```yaml
Policies:
  - S3ReadPolicy:
      BucketName: !Ref GuatepassDataBucket
  - DynamoDBCrudPolicy:
      TableName: !Ref GuatepassUsersTable
```

**Permisos específicos:**
- ✅ `s3:GetObject` en bucket específico
- ✅ `dynamodb:PutItem`, `BatchWriteItem` en tabla específica
- ❌ NO tiene acceso a otros buckets o tablas

### 2. S3 - Seguridad de Bucket

- ✅ Block Public Access: TODO habilitado
- ✅ Encriptación: AES-256 en reposo
- ✅ Versionamiento: Habilitado (auditoría)
- ✅ Bucket Policy: Solo Lambda puede leer
- ❌ NO hay acceso público bajo ninguna circunstancia

### 3. DynamoDB - Seguridad de Datos

- ✅ Encriptación en reposo: Default AWS-managed keys
- ✅ Encriptación en tránsito: HTTPS/TLS
- ✅ Point-in-Time Recovery: Habilitado
- ✅ IAM policies: Acceso granular por tabla

### 4. CloudWatch - Logs Seguros

- ✅ Logs no contienen información sensible (PII protegida)
- ✅ Retención limitada: 7 días
- ✅ Acceso controlado por IAM

---

## Escalabilidad

### Dimensiones de Escalamiento

#### 1. Tamaño del Archivo CSV

| Tamaño | Usuarios | Tiempo Estimado | Consideraciones |
|--------|----------|-----------------|-----------------|
| 1 KB | 10 | <1 segundo | Caso actual |
| 100 KB | 1,000 | ~5 segundos | Sin cambios necesarios |
| 10 MB | 100,000 | ~20 segundos | Sin cambios necesarios |
| 100 MB | 1,000,000 | ~30 segundos | Límite de timeout Lambda |
| >100 MB | >1,000,000 | N/A | Requiere arquitectura alternativa |

**Soluciones para archivos muy grandes:**
- Dividir CSV en múltiples archivos
- Usar AWS Batch o Step Functions con chunking
- Stream processing con Kinesis Data Firehose

#### 2. Throughput de DynamoDB

**PAY_PER_REQUEST Limits:**
- Burst: 40,000 WCU/s (Write Capacity Units)
- Steady: Ilimitado con throttling automático

**Batch write con 25 items:**
- 1 batch = 25 WCU
- 1,000 batches/s = 25,000 items/s
- **Capacidad teórica: 25,000 usuarios por segundo**

Para el caso de uso (cargas iniciales esporádicas), PAY_PER_REQUEST es más que suficiente.

#### 3. Concurrencia de Lambda

**Cuenta AWS default:**
- Concurrencia: 1,000 ejecuciones simultáneas
- Burst: 500-3,000 dependiendo de la región

**Este slice:**
- Esperamos 1 ejecución a la vez (carga inicial)
- No hay problemas de concurrencia

**Slices futuros (webhook de peajes):**
- Podrían requerir reserved concurrency
- CloudWatch alarmas monitorearan throttling

### Testing de Escalabilidad

```bash
# Generar CSV grande para pruebas
python scripts/generate_large_csv.py --users 10000 > data/clientes_10k.csv

# Subir y medir
time aws s3 cp data/clientes_10k.csv s3://$BUCKET/clientes_10k.csv

# Monitorear duración
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail
```

---

## Monitoreo y Observabilidad

### 1. Métricas Clave (KPIs)

| Métrica | Objetivo | Alerta Si |
|---------|----------|-----------|
| **Lambda Invocations** | 1 por cada CSV subido | = 0 cuando se espera CSV |
| **Lambda Errors** | 0 | > 0 |
| **Lambda Duration** | <5s para 1000 users | >25s (timeout proche) |
| **DynamoDB Write Throttles** | 0 | > 0 |
| **CSV Parse Errors** | <1% de filas | >5% |

### 2. Logs Estructurados

**Formato:**
```
[LEVEL] Mensaje descriptivo: {contexto JSON si aplica}
```

**Ejemplos:**
```
[INFO] Iniciando importación de usuarios - Environment: dev
[INFO] Procesando archivo: s3://bucket/clientes.csv
[INFO] Total de usuarios en CSV: 10
[WARNING] Error parseando fila 5: Placa vacía. Fila: {...}
[SUCCESS] Importación completada: {'total': 10, 'success': 9, 'errors': 1}
[ERROR] Error durante la importación: S3 AccessDenied
```

### 3. CloudWatch Insights Queries

**Query 1: Estadísticas de importaciones**
```
SOURCE '/aws/lambda/guatepass-import-users-dev'
| filter @message like /SUCCESS/
| parse @message /success: (?<success>\d+)/
| parse @message /errors: (?<errors>\d+)/
| stats sum(success) as total_success, sum(errors) as total_errors by bin(5m)
```

**Query 2: Errores por tipo**
```
SOURCE '/aws/lambda/guatepass-import-users-dev'
| filter @message like /ERROR/
| stats count() by @message
```

### 4. Dashboard Widgets

**Widget 1: Lambda Health**
- Invocations (Sum)
- Errors (Sum)
- Duration (Average, p99)

**Widget 2: DynamoDB Performance**
- ConsumedWriteCapacityUnits
- UserErrors (throttling)

**Widget 3: Recent Errors**
- Log Insights query
- Auto-refresh cada 1 minuto

---

## Próximos Pasos

Una vez completado y probado el Slice #1, los siguientes componentes a implementar son:

### Slice #2: API de Consulta de Usuarios
- `GET /users/{placa}` - Obtener información de usuario
- `GET /users/{placa}/tag` - Consultar Tag asociado
- API Gateway + Lambda

### Slice #3: Webhook de Peajes
- `POST /webhook/toll` - Recibir evento de paso por peaje
- EventBridge para enrutamiento de eventos
- Lambda ResolveUserProfile

### Slice #4: Procesamiento de Transacciones
- Step Functions State Machine
- Lambdas: GetTollPrice, ApplyBusinessRules, ProcessPayment, GenerateInvoice

### Slice #5: Gestión de Tags
- `POST /users/{placa}/tag` - Asociar Tag
- `PUT /users/{placa}/tag` - Actualizar Tag
- `DELETE /users/{placa}/tag` - Desasociar Tag

### Slice #6: Notificaciones
- SNS Topic
- Lambda NotifyUser
- Simulación de emails/SMS

---

## Referencias

- [AWS SAM Specification](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Lambda + S3 Tutorial](https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example.html)
- [Serverless Patterns: S3 to DynamoDB](https://serverlessland.com/patterns/s3-lambda-dynamodb)

---

**Documento creado:** Noviembre 2025  
**Versión:** 1.0  
**Slice:** #1 - Carga Inicial de Datos

