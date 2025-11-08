# 🚦 GUATEPASS - Slice #3: Webhook de Peajes

Documentación del sistema de ingesta de eventos de paso por peaje y enrutamiento con EventBridge.

---

## 🎯 Descripción

El Slice #3 implementa el **core del sistema GUATEPASS**: recibir eventos de paso por peaje desde el sistema de cámaras y determinar la modalidad de cobro del usuario.

### Componentes

✅ **POST /webhook/toll** - Endpoint REST para recibir eventos  
✅ **Lambda IngestToll** - Valida y publica a EventBridge  
✅ **EventBridge Bus** - Bus de eventos `guatepass-bus-dev`  
✅ **EventBridge Rule** - Regla para eventos `TollDetected`  
✅ **Lambda ResolveUserProfile** - Determina modalidad del usuario  
✅ **Tabla GuatepassTolls** - Catálogo de peajes (preparada para Slice #4)

---

## 🏗️ Arquitectura

```
Sistema de Cámaras
        ↓
   POST /webhook/toll
        ↓
[Lambda IngestToll]
  - Valida payload
  - Enriquece evento
  - Publica a EventBridge
        ↓
[EventBridge Bus]
  - guatepass-bus-dev
  - Event: guatepass.toll.TollDetected
        ↓
[EventBridge Rule]
  - Pattern matching
        ↓
[Lambda ResolveUserProfile]
  - Consulta DynamoDB Users
  - Determina Modalidad 1, 2 o 3
  - Loggea resultado
        ↓
   (Slice #4: Step Functions)
```

---

## 📡 Endpoint: POST /webhook/toll

### Request

**URL:**
```
POST https://{api-id}.execute-api.us-east-1.amazonaws.com/dev/webhook/toll
```

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "placa": "P-123ABC",
  "peaje_id": "PEAJE_ZONA10",
  "tag_id": "TAG-001",
  "timestamp": "2025-11-07T14:30:00Z"
}
```

### Campos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `placa` | String | ✅ | Placa del vehículo (ej: P-123ABC) |
| `peaje_id` | String | ✅ | ID del peaje (ej: PEAJE_ZONA10) |
| `tag_id` | String | ❌ | ID del Tag (null si no tiene) |
| `timestamp` | String | ✅ | ISO 8601 (ej: 2025-11-07T14:30:00Z) |

### Response Exitoso (200)

```json
{
  "message": "Evento de peaje recibido exitosamente",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "placa": "P-123ABC",
  "peaje_id": "PEAJE_ZONA10"
}
```

### Response Error (400)

```json
{
  "error": "Campo requerido faltante: placa",
  "statusCode": 400
}
```

---

## 🔄 Flujo de Procesamiento

### 1. Ingesta (Síncrona)

**Lambda: IngestToll**

1. Recibe evento HTTP del webhook
2. Valida campos requeridos
3. Normaliza placa (uppercase)
4. Genera `event_id` único (UUID)
5. Enriquece con metadata (`received_at`, `environment`)
6. Publica evento a EventBridge
7. Retorna 200 OK **inmediatamente** (< 300ms)

### 2. Enrutamiento (Asíncrono)

**EventBridge Bus**

- **Source:** `guatepass.toll`
- **DetailType:** `TollDetected`
- **EventBusName:** `guatepass-bus-dev`

**Evento publicado:**
```json
{
  "source": "guatepass.toll",
  "detail-type": "TollDetected",
  "detail": {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "toll.detected",
    "placa": "P-123ABC",
    "peaje_id": "PEAJE_ZONA10",
    "tag_id": "TAG-001",
    "timestamp": "2025-11-07T14:30:00Z",
    "received_at": "2025-11-07T14:30:01Z",
    "environment": "dev"
  }
}
```

### 3. Determinación de Modalidad (Asíncrono)

**Lambda: ResolveUserProfile**

1. EventBridge Rule dispara Lambda
2. Extrae `placa` y `tag_id` del evento
3. Busca usuario en DynamoDB:
   - Por `placa` (PK)
   - Por `tag_id` (GSI TagIndex) si no se encuentra
4. Determina modalidad según lógica de negocio
5. Loggea resultado en CloudWatch

**Modalidades:**

| Modalidad | Condición | Tipo Cobro | Recargo |
|-----------|-----------|------------|---------|
| **1** | Usuario NO registrado | Tradicional | ✅ Premium + multa |
| **2** | Usuario registrado (sin Tag) | Digital | ❌ Tarifa normal |
| **3** | Usuario con Tag activo | Express | ❌ Tarifa preferente |

---

## 🧪 Pruebas

### Script Automatizado

```powershell
cd "C:\Users\Mayco\Documents\GitHub\GUATE_PASS"
.\scripts\test-webhook.ps1
```

**Tests incluidos:**
1. ✅ Usuario con Tag (Modalidad 3)
2. ✅ Usuario sin Tag (Modalidad 2)
3. ✅ Usuario NO registrado (Modalidad 1)
4. ✅ Payload inválido (Error 400)

### Prueba Manual con curl

```powershell
# Obtener URL
$API_URL = aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text

# Test: Usuario con Tag
$body = @{
    placa = "P-456DEF"
    peaje_id = "PEAJE_ZONA10"
    tag_id = "TAG-001"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

Invoke-RestMethod -Uri "$API_URL/webhook/toll" -Method Post -Body $body -ContentType "application/json"
```

### Ver Resultados en CloudWatch

```powershell
# Logs de IngestToll (recepción del webhook)
sam logs -n IngestTollFunction --stack-name guatepass-dev --start-time '5m ago'

# Logs de ResolveUserProfile (determinación de modalidad)
sam logs -n ResolveUserProfileFunction --stack-name guatepass-dev --start-time '5m ago'
```

**Buscar en logs:**
```
[SUCCESS] Modalidad determinada: 3 para placa P-456DEF
```

---

## 📊 Ejemplos de Modalidades

### Modalidad 1: Usuario NO Registrado

**Input:**
```json
{
  "placa": "P-999ZZZ",
  "peaje_id": "PEAJE_ZONA10",
  "tag_id": null,
  "timestamp": "2025-11-07T14:30:00Z"
}
```

**Resultado en Logs:**
```json
{
  "modalidad": 1,
  "tipo_cobro": "tradicional",
  "recargo_aplica": true,
  "descripcion": "Usuario no registrado - Cobro premium + multa",
  "debe_invitar": true
}
```

### Modalidad 2: Usuario Registrado (Sin Tag)

**Input:**
```json
{
  "placa": "P-123ABC",
  "peaje_id": "PEAJE_ZONA10",
  "tag_id": null,
  "timestamp": "2025-11-07T14:30:00Z"
}
```

**Resultado en Logs:**
```json
{
  "modalidad": 2,
  "tipo_cobro": "digital",
  "recargo_aplica": false,
  "descripcion": "Usuario registrado - Cobro automático digital"
}
```

### Modalidad 3: Usuario con Tag

**Input:**
```json
{
  "placa": "P-456DEF",
  "peaje_id": "PEAJE_ZONA10",
  "tag_id": "TAG-001",
  "timestamp": "2025-11-07T14:30:00Z"
}
```

**Resultado en Logs:**
```json
{
  "modalidad": 3,
  "tipo_cobro": "express",
  "recargo_aplica": false,
  "descripcion": "Usuario con Tag - Cobro automático express"
}
```

---

## 🔍 Verificación en AWS Console

### 1. API Gateway

**Ir a:** https://console.aws.amazon.com/apigateway/

1. Click en `guatepass-api-dev`
2. **Resources** → Deberías ver `/webhook/toll` con método POST
3. **Stages** → `dev` → URL invoke

### 2. EventBridge

**Ir a:** https://console.aws.amazon.com/events/

1. **Event buses** → `guatepass-bus-dev`
2. **Rules** → Regla asociada a `ResolveUserProfileFunction`
3. **Event pattern:**
```json
{
  "source": ["guatepass.toll"],
  "detail-type": ["TollDetected"]
}
```

### 3. Lambda Functions

**Ir a:** https://console.aws.amazon.com/lambda/

1. `guatepass-ingest-toll-dev`
   - **Triggers:** API Gateway (POST /webhook/toll)
   - **Destinations:** EventBridge Bus
   
2. `guatepass-resolve-user-dev`
   - **Triggers:** EventBridge Rule
   - **Permissions:** DynamoDB Read

### 4. CloudWatch Logs

**Logs de IngestToll:**
```
[INFO] POST /webhook/toll - Event: {...}
[INFO] Evento validado y enriquecido: {...}
[INFO] Evento publicado a EventBridge: event_id=...
[SUCCESS] Evento de peaje procesado: placa=P-123ABC, peaje=PEAJE_ZONA10
```

**Logs de ResolveUserProfile:**
```
[INFO] ResolveUserProfile - Event: {...}
[INFO] Resolviendo perfil para placa: P-123ABC, tag_id: None
[INFO] Usuario encontrado por placa: P-123ABC
[SUCCESS] Modalidad determinada: 2 para placa P-123ABC
```

---

## ⚡ Performance y Escalabilidad

### Latencias

| Componente | Latencia Típica |
|------------|-----------------|
| POST /webhook/toll | 100-300ms (síncrono) |
| EventBridge routing | < 100ms |
| ResolveUserProfile | 50-150ms (asíncrono) |
| **Total (percibido por usuario)** | **100-300ms** |

### Throughput

- **API Gateway:** 10,000 req/s (burst)
- **EventBridge:** 10,000 eventos/s por bus
- **Lambda:** 1,000 concurrentes (default)
- **DynamoDB:** PAY_PER_REQUEST (sin límite práctico)

**Capacidad estimada:** >5,000 vehículos/segundo

---

## 🐛 Troubleshooting

### Webhook devuelve 200 pero no hay logs en ResolveUserProfile

**Causa:** EventBridge no está publicando o la regla no coincide.

**Diagnóstico:**
```powershell
# Ver logs de IngestToll
sam logs -n IngestTollFunction --stack-name guatepass-dev --start-time '10m ago' | Select-String "publicado a EventBridge"

# Ver eventos de EventBridge
aws events list-rules --event-bus-name guatepass-bus-dev
```

### Error: "Campo requerido faltante"

**Causa:** Payload incompleto.

**Solución:** Verifica que incluyas `placa`, `peaje_id` y `timestamp`.

### Usuario no encontrado aunque existe

**Causa:** Placa con formato diferente (espacios, minúsculas).

**Solución:** La Lambda normaliza a mayúsculas y trim, pero verifica:
```powershell
aws dynamodb get-item --table-name GuatepassUsers-dev --key '{"placa": {"S": "P-123ABC"}}'
```

---

## 🔗 Integración con Slice #4

Este slice prepara el terreno para el **Slice #4: Step Functions**.

**Siguiente paso:**
- Lambda `ResolveUserProfile` invocará una Step Functions State Machine
- State Machine procesará el cobro completo:
  1. Obtener precio del peaje
  2. Aplicar reglas de negocio
  3. Procesar pago
  4. Generar factura
  5. Notificar usuario

---

## 📈 Métricas Clave

### CloudWatch Metrics

```powershell
# Invocaciones de IngestToll
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=guatepass-ingest-toll-dev \
  --start-time (Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") \
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") \
  --period 300 \
  --statistics Sum

# Eventos publicados a EventBridge
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=EventBusName,Value=guatepass-bus-dev \
  --start-time (Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") \
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") \
  --period 300 \
  --statistics Sum
```

---

## 🎯 Resumen

✅ **Slice #3 COMPLETADO**

**Funcionalidad:**
- ✅ Webhook recibe eventos de peajes
- ✅ EventBridge enruta eventos asíncronamente
- ✅ Sistema determina modalidad de cobro
- ✅ Arquitectura desacoplada y escalable

**Próximo Slice:**
- 🔜 **Slice #4:** Step Functions para procesamiento de cobros

---

**Slice #3 COMPLETADO** ✅  
**Fecha:** Noviembre 2025

