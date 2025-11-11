# 🔄 GUATEPASS - Flujo de Datos Detallado

## Flujos de Datos entre Componentes AWS

Este documento detalla los flujos de datos completos del sistema GUATEPASS, mostrando cómo la información viaja entre los diferentes componentes serverless de AWS.

---

## 📥 Flujo 1: Carga Inicial de Datos (CSV → DynamoDB)

### Descripción
Importación masiva de usuarios desde archivo CSV a la base de datos DynamoDB.

### Flujo Paso a Paso

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO 1: IMPORTACIÓN DE USUARIOS DESDE CSV                      │
└─────────────────────────────────────────────────────────────────┘

PASO 1: Upload Manual
┌──────────────┐
│ Administrador│
│   Sistema    │
└──────┬───────┘
       │ aws s3 cp data/clientes.csv s3://bucket/
       │
       │ Data Format:
       │ placa,nombre,email,telefono,tipo_usuario,tiene_tag,...
       │ P-123ABC,Juan Pérez,juan@email.com,50212345678,...
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ AWS S3 Bucket: guatepass-data-dev-{account}           │
│                                                        │
│ Object Key: clientes.csv                              │
│ Size: ~10KB (100 usuarios)                            │
│ Event: s3:ObjectCreated:Put                           │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ S3 Event Notification
                    │ {
                    │   "Records": [{
                    │     "s3": {
                    │       "bucket": {"name": "guatepass-data-dev-..."},
                    │       "object": {"key": "clientes.csv"}
                    │     }
                    │   }]
                    │ }
                    ▼

PASO 2: Trigger Lambda
┌────────────────────────────────────────────────────────┐
│ Lambda: ImportUsersFunction                           │
│                                                        │
│ Input Event:                                           │
│   - bucket: guatepass-data-dev-123456789012           │
│   - key: clientes.csv                                  │
│                                                        │
│ PROCESO:                                               │
│ 1. s3.get_object(Bucket=bucket, Key=key)             │
│    ↓                                                   │
│    CSV Content (bytes)                                 │
│                                                        │
│ 2. csv.DictReader(decoded_content)                    │
│    ↓                                                   │
│    [                                                   │
│      {                                                 │
│        "placa": "P-123ABC",                           │
│        "nombre": "Juan Pérez",                        │
│        "email": "juan@email.com",                     │
│        "telefono": "50212345678",                     │
│        "tipo_usuario": "registrado",                  │
│        "tiene_tag": "false",                          │
│        "saldo_disponible": "100.00"                   │
│      },                                                │
│      {...}, {...}  // más usuarios                    │
│    ]                                                   │
│                                                        │
│ 3. Validación de datos                                │
│    - placa no vacía                                    │
│    - formato de email válido                           │
│    - tipo_usuario en ['registrado', 'no_registrado']  │
│    - saldo_disponible es número                        │
│                                                        │
│ 4. Transformación a formato DynamoDB                   │
│    {                                                   │
│      "placa": {"S": "P-123ABC"},                      │
│      "nombre": {"S": "Juan Pérez"},                   │
│      "email": {"S": "juan@email.com"},                │
│      "telefono": {"S": "50212345678"},                │
│      "tipo_usuario": {"S": "registrado"},             │
│      "tiene_tag": {"BOOL": false},                    │
│      "saldo_disponible": {"N": "100.00"},             │
│      "estado": {"S": "activo"}                        │
│    }                                                   │
│                                                        │
│ 5. Batch Write (25 items por batch)                   │
│    dynamodb.batch_write_item(                         │
│      RequestItems={                                    │
│        'GuatepassUsers-dev': [                        │
│          {'PutRequest': {'Item': item1}},             │
│          {'PutRequest': {'Item': item2}},             │
│          ...  // hasta 25 items                       │
│        ]                                               │
│      }                                                 │
│    )                                                   │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ BatchWriteItem (max 25 items/request)
                    │ Consumo: ~1 WCU por item
                    │
                    ▼

PASO 3: Almacenamiento
┌────────────────────────────────────────────────────────┐
│ DynamoDB: GuatepassUsers-dev                          │
│                                                        │
│ Datos Almacenados:                                     │
│ {                                                      │
│   "placa": "P-123ABC",                                │
│   "nombre": "Juan Pérez",                             │
│   "email": "juan@email.com",                          │
│   "telefono": "50212345678",                          │
│   "tipo_usuario": "registrado",                       │
│   "tiene_tag": false,                                 │
│   "saldo_disponible": 100.00,                         │
│   "estado": "activo"                                  │
│ }                                                      │
│                                                        │
│ Índices Actualizados:                                 │
│   - Primary Key Index (placa)                         │
│   - TagIndex GSI (si tiene tag_id)                    │
│                                                        │
│ DynamoDB Streams:                                      │
│   - Evento NEW_IMAGE generado                         │
│   - Disponible para procesamiento posterior           │
└────────────────────────────────────────────────────────┘

PASO 4: Logging y Monitoreo
┌────────────────────────────────────────────────────────┐
│ CloudWatch Logs: /aws/lambda/guatepass-import-users-dev│
│                                                        │
│ [INFO] Iniciando importación de usuarios              │
│ [INFO] CSV descargado: 10KB, 100 líneas              │
│ [INFO] Validación completada: 100 válidos, 0 errores │
│ [INFO] Batch 1/4: 25 usuarios escritos               │
│ [INFO] Batch 2/4: 25 usuarios escritos               │
│ [INFO] Batch 3/4: 25 usuarios escritos               │
│ [INFO] Batch 4/4: 25 usuarios escritos               │
│ [SUCCESS] Importación completada                      │
│   Total: 100, Success: 100, Errors: 0                │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ CloudWatch Metrics                                     │
│   - Lambda Invocations: +1                            │
│   - Lambda Duration: ~3500ms                          │
│   - Lambda Errors: 0                                  │
│   - DynamoDB ConsumedWriteCapacityUnits: +100         │
└────────────────────────────────────────────────────────┘

RESULTADO FINAL:
✅ 100 usuarios importados
✅ Disponibles para consulta via API
✅ Listos para procesamiento de transacciones
```

---

## 🚗 Flujo 2: Consulta de Usuario via API REST

### Descripción
Usuario o sistema externo consulta información de un vehículo por su placa.

### Flujo Paso a Paso

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO 2: CONSULTA DE USUARIO POR PLACA                          │
└─────────────────────────────────────────────────────────────────┘

PASO 1: Request HTTP
┌──────────────┐
│   Cliente    │
│  (curl/app)  │
└──────┬───────┘
       │ GET https://api-url/dev/users/P-123ABC
       │
       │ Headers:
       │   Accept: application/json
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ API Gateway: guatepass-api (Stage: dev)               │
│                                                        │
│ Request:                                               │
│   Method: GET                                          │
│   Path: /users/{placa}                                │
│   PathParameters: { "placa": "P-123ABC" }             │
│                                                        │
│ Procesamiento:                                         │
│ 1. CORS Preflight (si viene de browser)               │
│ 2. Validación de ruta                                 │
│ 3. Rate limiting check (10,000 req/sec burst)         │
│ 4. Transformación a evento Lambda                     │
│                                                        │
│ Lambda Event:                                          │
│ {                                                      │
│   "resource": "/users/{placa}",                       │
│   "path": "/users/P-123ABC",                          │
│   "httpMethod": "GET",                                │
│   "pathParameters": {                                 │
│     "placa": "P-123ABC"                               │
│   },                                                   │
│   "headers": { ... },                                 │
│   "requestContext": { ... }                           │
│ }                                                      │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ Lambda Integration (Proxy)
                    │ Latency: ~20ms
                    │
                    ▼

PASO 2: Procesamiento Lambda
┌────────────────────────────────────────────────────────┐
│ Lambda: GetUserByPlacaFunction                        │
│                                                        │
│ PROCESO:                                               │
│ 1. Extraer placa del evento                           │
│    placa = event['pathParameters']['placa']           │
│    placa = placa.strip().upper()  # "P-123ABC"       │
│                                                        │
│ 2. Consultar DynamoDB                                  │
│    response = dynamodb.get_item(                      │
│      TableName='GuatepassUsers-dev',                  │
│      Key={'placa': {'S': 'P-123ABC'}}                │
│    )                                                   │
│                                                        │
│    Consumo: ~0.5 RCU (eventually consistent)          │
│    Latency: ~15ms                                      │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ GetItem Request
                    │
                    ▼

PASO 3: Query DynamoDB
┌────────────────────────────────────────────────────────┐
│ DynamoDB: GuatepassUsers-dev                          │
│                                                        │
│ Query:                                                 │
│   Operation: GetItem                                   │
│   Key: placa = "P-123ABC"                             │
│   ConsistentRead: false                                │
│                                                        │
│ Resultado:                                             │
│ {                                                      │
│   "Item": {                                            │
│     "placa": {"S": "P-123ABC"},                       │
│     "nombre": {"S": "Juan Pérez"},                    │
│     "email": {"S": "juan@email.com"},                 │
│     "telefono": {"S": "50212345678"},                 │
│     "tipo_usuario": {"S": "registrado"},              │
│     "tiene_tag": {"BOOL": false},                     │
│     "saldo_disponible": {"N": "100.00"},              │
│     "estado": {"S": "activo"}                         │
│   }                                                    │
│ }                                                      │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ Return Item
                    │
                    ▼

PASO 4: Formatear Respuesta
┌────────────────────────────────────────────────────────┐
│ Lambda: GetUserByPlacaFunction (continuación)         │
│                                                        │
│ 3. Transformar respuesta DynamoDB a JSON              │
│    user = {                                            │
│      "placa": "P-123ABC",                             │
│      "nombre": "Juan Pérez",                          │
│      "email": "juan@email.com",                       │
│      "telefono": "50212345678",                       │
│      "tipo_usuario": "registrado",                    │
│      "tiene_tag": false,                              │
│      "saldo_disponible": 100.00,                      │
│      "estado": "activo"                               │
│    }                                                   │
│                                                        │
│ 4. Construir respuesta HTTP                           │
│    return {                                            │
│      'statusCode': 200,                               │
│      'headers': {                                      │
│        'Content-Type': 'application/json',            │
│        'Access-Control-Allow-Origin': '*'             │
│      },                                                │
│      'body': json.dumps({                             │
│        'user': user,                                   │
│        'message': 'Usuario P-123ABC encontrado'       │
│      })                                                │
│    }                                                   │
│                                                        │
│ Duration: ~120ms                                       │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ HTTP Response
                    │
                    ▼

PASO 5: Respuesta al Cliente
┌────────────────────────────────────────────────────────┐
│ API Gateway Response                                   │
│                                                        │
│ HTTP/1.1 200 OK                                        │
│ Content-Type: application/json                         │
│ Access-Control-Allow-Origin: *                         │
│                                                        │
│ {                                                      │
│   "user": {                                            │
│     "placa": "P-123ABC",                              │
│     "nombre": "Juan Pérez",                           │
│     "email": "juan@email.com",                        │
│     "telefono": "50212345678",                        │
│     "tipo_usuario": "registrado",                     │
│     "tiene_tag": false,                               │
│     "saldo_disponible": 100.00,                       │
│     "estado": "activo"                                │
│   },                                                   │
│   "message": "Usuario P-123ABC encontrado exitosamente"│
│ }                                                      │
│                                                        │
│ Total Latency: ~150ms                                  │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌──────────────┐
│   Cliente    │
│  (recibe OK) │
└──────────────┘

MÉTRICAS GENERADAS:
┌────────────────────────────────────────────────────────┐
│ CloudWatch Metrics                                     │
│   • API Gateway Count: +1                             │
│   • API Gateway Latency: 150ms                        │
│   • Lambda Invocations: +1                            │
│   • Lambda Duration: 120ms                            │
│   • DynamoDB ConsumedReadCapacityUnits: +0.5          │
└────────────────────────────────────────────────────────┘
```

---

## 🚦 Flujo 3: Procesamiento de Transacción de Peaje (Completo)

### Descripción
Flujo completo desde que un vehículo pasa por un peaje hasta la generación de factura y notificación.

### Flujo Paso a Paso

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO 3: PROCESAMIENTO COMPLETO DE TRANSACCIÓN DE PEAJE         │
└─────────────────────────────────────────────────────────────────┘

PASO 1: Evento de Peaje
┌──────────────┐
│   Sistema    │
│    Peaje     │
│   (sensor)   │
└──────┬───────┘
       │ POST https://api-url/dev/webhook/toll
       │
       │ Body:
       │ {
       │   "placa": "P-123ABC",
       │   "toll_id": "PEAJE001",
       │   "timestamp": "2025-11-11T15:00:00Z"
       │ }
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ API Gateway → Lambda: IngestTollFunction              │
│                                                        │
│ PROCESO:                                               │
│ 1. Validar payload                                     │
│    - placa no vacía                                    │
│    - toll_id existe                                    │
│    - timestamp válido                                  │
│                                                        │
│ 2. Enriquecer evento                                   │
│    event_detail = {                                    │
│      "placa": "P-123ABC",                             │
│      "toll_id": "PEAJE001",                           │
│      "timestamp": "2025-11-11T15:00:00Z",             │
│      "event_id": "evt-uuid-generated",                │
│      "received_at": "2025-11-11T15:00:01Z"            │
│    }                                                   │
│                                                        │
│ 3. Publicar a EventBridge                             │
│    eventbridge.put_events(                            │
│      Entries=[{                                        │
│        'Source': 'guatepass.toll',                    │
│        'DetailType': 'Toll Event',                    │
│        'Detail': json.dumps(event_detail),            │
│        'EventBusName': 'guatepass-event-bus-dev'      │
│      }]                                                │
│    )                                                   │
│                                                        │
│ 4. Responder inmediatamente (202 Accepted)            │
│    return {                                            │
│      'statusCode': 202,                               │
│      'body': json.dumps({                             │
│        'message': 'Evento recibido y procesando',     │
│        'event_id': 'evt-uuid-generated'               │
│      })                                                │
│    }                                                   │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ PutEvents
                    │
                    ▼

PASO 2: EventBridge Bus
┌────────────────────────────────────────────────────────┐
│ EventBridge: guatepass-event-bus-dev                  │
│                                                        │
│ Evento Recibido:                                       │
│ {                                                      │
│   "source": "guatepass.toll",                         │
│   "detail-type": "Toll Event",                        │
│   "detail": {                                          │
│     "placa": "P-123ABC",                              │
│     "toll_id": "PEAJE001",                            │
│     "timestamp": "2025-11-11T15:00:00Z",              │
│     "event_id": "evt-uuid-generated"                  │
│   }                                                    │
│ }                                                      │
│                                                        │
│ Rule Matched: ProcessTollEventRule                     │
│   Target: Step Functions State Machine                │
└───────────────────┬────────────────────────────────────┘
                    │
                    │ StartExecution
                    │
                    ▼

PASO 3: Step Functions - Estado 1 (ResolveUser)
┌────────────────────────────────────────────────────────┐
│ Step Functions: guatepass-process-toll-dev            │
│ Execution: exec-20251111150001-uuid                   │
│                                                        │
│ Estado 1: ResolveUserProfile                          │
│ ──────────────────────────────────────────────        │
│ Lambda: ResolveUserProfileFunction                    │
│                                                        │
│ Input:                                                 │
│   { "placa": "P-123ABC", "toll_id": "PEAJE001" }     │
│                                                        │
│ Proceso:                                               │
│   1. Query DynamoDB Users por placa                    │
│   2. Determinar modalidad:                            │
│      - tipo_usuario == "registrado" → Modalidad 2     │
│      - tipo_usuario == "no_registrado" → Modalidad 1  │
│   3. Verificar saldo (si Modalidad 2)                 │
│                                                        │
│ Output:                                                │
│ {                                                      │
│   "user_profile": {                                    │
│     "placa": "P-123ABC",                              │
│     "nombre": "Juan Pérez",                           │
│     "email": "juan@email.com",                        │
│     "modalidad": 2,                                    │
│     "tiene_tag": false,                               │
│     "saldo_disponible": 100.00                        │
│   },                                                   │
│   "toll_id": "PEAJE001",                              │
│   "timestamp": "2025-11-11T15:00:00Z"                 │
│ }                                                      │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼

PASO 4: Step Functions - Estado 2 (CalculateFare)
┌────────────────────────────────────────────────────────┐
│ Estado 2: CalculateTollFare                           │
│ ──────────────────────────────────────────────        │
│ Lambda: CalculateTollFareFunction                     │
│                                                        │
│ Input: (output del estado anterior)                   │
│                                                        │
│ Proceso:                                               │
│   1. Query DynamoDB Tolls por toll_id                 │
│      → base_price: 15.00                              │
│   2. Aplicar multiplicador según modalidad:           │
│      - Modalidad 1: 1.5 (recargo 50%)                │
│      - Modalidad 2: 1.0 (sin recargo)                │
│   3. Calcular monto final                             │
│      amount_charged = base_price * multiplier         │
│      = 15.00 * 1.0 = 15.00                           │
│                                                        │
│ Output:                                                │
│ {                                                      │
│   ...user_profile...,                                 │
│   "fare_calculation": {                               │
│     "base_fare": 15.00,                               │
│     "multiplier": 1.0,                                │
│     "amount_charged": 15.00,                          │
│     "toll_name": "Carretera Norte"                    │
│   }                                                    │
│ }                                                      │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼

PASO 5: Step Functions - Estado 3 (RecordTransaction)
┌────────────────────────────────────────────────────────┐
│ Estado 3: RecordTransaction                           │
│ ──────────────────────────────────────────────        │
│ Lambda: RecordTransactionFunction                     │
│                                                        │
│ Proceso:                                               │
│   1. Generar transaction_id único                     │
│      transaction_id = f"TXN-{toll_id}-{placa}-{ts}"  │
│   2. Crear registro de transacción                    │
│   3. PutItem en GuatepassTransactions                 │
│                                                        │
│ Datos Guardados:                                       │
│ {                                                      │
│   "transaction_id": "TXN-PEAJE001-P-123ABC-20251111T150000Z",│
│   "placa": "P-123ABC",                                │
│   "toll_id": "PEAJE001",                              │
│   "toll_name": "Carretera Norte",                     │
│   "modalidad": 2,                                      │
│   "base_fare": 15.00,                                 │
│   "multiplier": 1.0,                                  │
│   "amount_charged": 15.00,                            │
│   "timestamp": "2025-11-11T15:00:00Z",                │
│   "created_at": "2025-11-11T15:00:02Z",               │
│   "status": "completed"                               │
│ }                                                      │
│                                                        │
│ ✅ Guardado en DynamoDB (0.5 WCU)                     │
│ ✅ Disponible en GSI PlacaTimestampIndex               │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼

PASO 6: Step Functions - Estado 4 (UpdateBalance)
┌────────────────────────────────────────────────────────┐
│ Estado 4: UpdateBalance (Solo Modalidad 2)           │
│ ──────────────────────────────────────────────        │
│ Lambda: UpdateBalanceFunction                         │
│                                                        │
│ Proceso:                                               │
│   IF modalidad == 2:                                  │
│     1. UpdateItem en GuatepassUsers                   │
│        SET saldo_disponible = saldo_disponible - amount│
│        WHERE placa = "P-123ABC"                       │
│                                                        │
│     Antes: saldo_disponible = 100.00                  │
│     Después: saldo_disponible = 85.00                 │
│                                                        │
│     2. Verificar saldo bajo (< 50)                    │
│        → Marcar para alerta                           │
│                                                        │
│   ELSE (modalidad == 1):                              │
│     → Skip (no registrados no tienen saldo)           │
│                                                        │
│ ✅ Saldo actualizado (1 WCU)                          │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼

PASO 7: Step Functions - Estado 5 (GenerateInvoice)
┌────────────────────────────────────────────────────────┐
│ Estado 5: GenerateInvoice                             │
│ ──────────────────────────────────────────────        │
│ Lambda: GenerateInvoiceFunction                       │
│                                                        │
│ Proceso:                                               │
│   1. Generar invoice_id único                         │
│      invoice_id = f"FAC-{timestamp}"                  │
│                                                        │
│   2. Calcular monto según modalidad                   │
│      IF modalidad == 1:                               │
│        monto_base = 15.00                             │
│        multa = 7.50 (50%)                             │
│        total = 22.50                                  │
│        estado = "pendiente"                           │
│      ELSE:                                             │
│        monto_base = 15.00                             │
│        multa = 0.00                                   │
│        total = 15.00                                  │
│        estado = "pagada"                              │
│                                                        │
│   3. PutItem en GuatepassInvoices                     │
│                                                        │
│ Factura Generada:                                      │
│ {                                                      │
│   "invoice_id": "FAC-20251111150002",                 │
│   "placa": "P-123ABC",                                │
│   "transaction_id": "TXN-PEAJE001-P-123ABC-...",      │
│   "toll_name": "Carretera Norte",                     │
│   "modalidad": 2,                                      │
│   "monto_base": 15.00,                                │
│   "multa": 0.00,                                      │
│   "total": 15.00,                                     │
│   "estado": "pagada",                                 │
│   "concepto": "Paso por peaje - Carretera Norte",    │
│   "created_at": "2025-11-11T15:00:02Z",               │
│   "contribuyente": {                                  │
│     "nombre": "Juan Pérez",                           │
│     "email": "juan@email.com"                         │
│   }                                                    │
│ }                                                      │
│                                                        │
│ ✅ Guardado en DynamoDB (0.5 WCU)                     │
│ ✅ Disponible en GSI PlacaCreatedIndex                 │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼

PASO 8: Step Functions - Estado 6 (NotifyUser)
┌────────────────────────────────────────────────────────┐
│ Estado 6: NotifyUser                                  │
│ ──────────────────────────────────────────────        │
│ Lambda: NotifyUserFunction                            │
│                                                        │
│ Proceso:                                               │
│   1. Determinar tipo de notificación según modalidad  │
│                                                        │
│   IF modalidad == 1:                                  │
│     Template: "Invitación a Registrarse"             │
│     Subject: "🚗 Invitación GuatePass"                │
│     Content:                                           │
│       - Factura pendiente: Q22.50                     │
│       - Incluye multa 50%                             │
│       - Link para registrarse                         │
│                                                        │
│   ELSE (modalidad == 2):                              │
│     Template: "Notificación de Cobro"                │
│     Subject: "✅ Cobro por peaje realizado"           │
│     Content:                                           │
│       - Monto cobrado: Q15.00                         │
│       - Nuevo saldo: Q85.00                           │
│       - Número de factura: FAC-20251111150002         │
│       - Alerta si saldo < Q50                         │
│                                                        │
│   2. Simular envío de email (log en CloudWatch)       │
│      print(f"[EMAIL SIMULADO]")                       │
│      print(f"To: {email}")                            │
│      print(f"Subject: {subject}")                     │
│      print(f"Body: {body}")                           │
│                                                        │
│ ✅ Notificación "enviada" (simulada)                  │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼

PASO 9: Step Functions - Success
┌────────────────────────────────────────────────────────┐
│ Estado Final: ProcessingSuccess                       │
│                                                        │
│ Execution Output:                                      │
│ {                                                      │
│   "status": "success",                                │
│   "placa": "P-123ABC",                                │
│   "transaction_id": "TXN-PEAJE001-P-123ABC-...",      │
│   "invoice_id": "FAC-20251111150002",                 │
│   "amount_charged": 15.00,                            │
│   "notification_sent": true,                          │
│   "execution_time": "2.5 seconds"                     │
│ }                                                      │
│                                                        │
│ ✅ Ejecución completada exitosamente                  │
└────────────────────────────────────────────────────────┘

LOGS Y MÉTRICAS GENERADAS:
┌────────────────────────────────────────────────────────┐
│ CloudWatch Logs                                        │
│                                                        │
│ /aws/lambda/guatepass-ingest-toll-dev:                │
│   [INFO] Evento de peaje recibido: P-123ABC           │
│   [INFO] Publicado a EventBridge: evt-uuid            │
│                                                        │
│ /aws/stepfunctions/guatepass-process-toll-dev:        │
│   [INFO] Execution started: exec-uuid                 │
│   [INFO] ResolveUser: Modalidad 2 determinada         │
│   [INFO] CalculateFare: Q15.00 calculado              │
│   [INFO] RecordTransaction: TXN-xxx guardada          │
│   [INFO] UpdateBalance: Saldo: Q100→Q85               │
│   [INFO] GenerateInvoice: FAC-xxx creada              │
│   [INFO] NotifyUser: Email enviado a juan@email.com   │
│   [SUCCESS] Execution completed                       │
│                                                        │
│ /aws/lambda/guatepass-notify-user-dev:                │
│   [EMAIL SIMULADO]                                     │
│   To: juan@email.com                                   │
│   Subject: ✅ Cobro por peaje realizado                │
│   Body: Hola Juan Pérez...                            │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ CloudWatch Metrics                                     │
│   • API Gateway Count: +1                             │
│   • Lambda Invocations: +7 (1 ingest + 6 step fns)   │
│   • EventBridge Events: +1                            │
│   • Step Functions ExecutionsStarted: +1              │
│   • Step Functions ExecutionsSucceeded: +1            │
│   • DynamoDB Reads: +3 (users, tolls, verify)        │
│   • DynamoDB Writes: +3 (transaction, user, invoice) │
└────────────────────────────────────────────────────────┘

RESULTADO FINAL:
✅ Transacción registrada
✅ Saldo actualizado (si Modalidad 2)
✅ Factura generada
✅ Usuario notificado
✅ Datos disponibles para historial
✅ Total time: ~2.5 segundos
```

---

## 📊 Flujo 4: Consulta de Historial

### Descripción
Usuario consulta su historial de pagos o facturas a través de los nuevos endpoints.

### Flujo Paso a Paso

```
┌─────────────────────────────────────────────────────────────────┐
│ FLUJO 4: CONSULTA DE HISTORIAL (PAGOS O FACTURAS)               │
└─────────────────────────────────────────────────────────────────┘

Cliente Request:
  GET /history/payments/P-123ABC?limit=10
       │
       ▼
API Gateway
       │
       ▼
Lambda: GetPaymentsByPlateFunction
       │
       ├─→ DynamoDB Query usando GSI PlacaTimestampIndex
       │   WHERE placa = "P-123ABC"
       │   ORDER BY timestamp DESC
       │   LIMIT 10
       │
       │   Resultado: [
       │     {transaction_id: "TXN-...", amount: 15.00, ...},
       │     {transaction_id: "TXN-...", amount: 12.00, ...},
       │     ...
       │   ]
       │
       ├─→ Calcular estadísticas:
       │   total_transactions = count(results)
       │   total_amount = sum(amount_charged)
       │
       └─→ Return formatted response
           {
             "placa": "P-123ABC",
             "total_transactions": 10,
             "total_amount": 150.00,
             "transactions": [...]
           }

Consumo: ~0.5 RCU por query
Latency: ~100ms total
```

---

## 📈 Resumen de Flujos de Datos

### Métricas de Performance por Flujo

| Flujo | Lambdas Invocadas | DynamoDB Ops | Latencia | Costo Aprox |
|-------|------------------|--------------|----------|-------------|
| Carga CSV (100 users) | 1 | 100 writes | ~3.5s | $0.00004 |
| Consulta Usuario | 1 | 1 read | ~150ms | $0.000001 |
| Transacción Completa | 7 | 6 reads, 3 writes | ~2.5s | $0.00003 |
| Consulta Historial | 1 | 1 query | ~100ms | $0.000001 |

### Flujo de Datos Total Diario (Ejemplo: 1,000 vehículos)

```
1,000 transacciones/día:
  → 7,000 invocaciones Lambda
  → 6,000 lecturas DynamoDB
  → 3,000 escrituras DynamoDB
  → 1,000 ejecuciones Step Functions
  → Costo estimado: $0.30/día = $9/mes
```

---

**Última actualización:** Noviembre 11, 2025  
**Estado:** Documentación Completa

