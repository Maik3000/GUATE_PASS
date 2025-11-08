# 🔄 GUATEPASS - Slice #4: Step Functions

## 📋 Descripción General

El **Slice #4** implementa la **orquestación del procesamiento de transacciones de peaje** utilizando **AWS Step Functions**. Esta máquina de estados coordina todo el flujo desde el cálculo de la tarifa hasta el registro de la transacción y actualización del balance del usuario.

## 🏗️ Arquitectura

```
┌─────────────────┐
│  EventBridge    │
│  (Toll Event)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ResolveUser     │
│ Lambda          │ ← Slice #3
└────────┬────────┘
         │ Inicia Step Function
         ▼
┌─────────────────────────────────────────┐
│    Step Function: ProcessTollTransaction │
│                                          │
│  1. CalculateTollFare                   │
│     ↓                                    │
│  2. RecordTransaction                   │
│     ↓                                    │
│  3. UpdateBalance                       │
│     ↓                                    │
│  4. Success                              │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  DynamoDB       │
│  - Transactions │
│  - Users (saldo)│
└─────────────────┘
```

## 🎯 Objetivos del Slice #4

- ✅ Orquestar el procesamiento completo de transacciones de peaje
- ✅ Calcular tarifas dinámicamente según modalidad del usuario
- ✅ Registrar todas las transacciones en DynamoDB
- ✅ Actualizar balances de usuarios registrados
- ✅ Implementar reintentos automáticos y manejo de errores
- ✅ Trazabilidad completa del flujo con logs y X-Ray

## 📦 Componentes Creados

### 1. **Tabla DynamoDB: GuatepassTransactions**

Almacena todas las transacciones de peaje.

**Esquema:**
```
- transaction_id (HASH KEY): Identificador único de la transacción
- placa: Placa del vehículo
- timestamp: Fecha y hora del paso
- peaje_id: ID del peaje
- modalidad: 1, 2 o 3
- base_fare: Tarifa base (Decimal)
- final_fare: Tarifa final aplicada (Decimal)
- payment_status: pending, completed, failed
- ... otros campos
```

**Índices:**
- `PlacaTimestampIndex`: Para consultar transacciones por placa y rango de fechas

### 2. **Lambda: CalculateTollFareFunction**

Calcula la tarifa del peaje según la modalidad del usuario.

**Tarifas Base:**
- Carretera Norte: Q15.00
- Carretera Sur: Q12.00
- Autopista Palín: Q10.00
- Anillo Periférico: Q8.00
- Default: Q10.00

**Multiplicadores por Modalidad:**
- Modalidad 1 (Con Tag): x1.00 (sin recargo)
- Modalidad 2 (Sin Tag): x1.20 (+20%)
- Modalidad 3 (No registrado): x1.50 (+50%)

**Input:**
```json
{
  "user_data": {
    "placa": "P123ABC",
    "modalidad": 1,
    "is_registered": true,
    "has_tag": true
  },
  "toll_data": {
    "peaje_id": "PEAJE001",
    "nombre_peaje": "carretera_norte",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Output:**
```json
{
  "user_data": {...},
  "toll_data": {...},
  "fare_calculation": {
    "base_fare": "15.00",
    "modality": 1,
    "multiplier": "1.00",
    "final_fare": "15.00",
    "currency": "GTQ",
    "toll_name": "carretera_norte"
  }
}
```

### 3. **Lambda: RecordTransactionFunction**

Registra la transacción en la tabla `GuatepassTransactions`.

**Funcionalidad:**
- Genera un `transaction_id` único
- Guarda todos los detalles de la transacción
- Establece `payment_status` inicial como "pending"
- Registra timestamp de creación

### 4. **Lambda: UpdateBalanceFunction**

Actualiza el saldo del usuario después de la transacción.

**Lógica:**
- **Modalidad 1 o 2 (Usuarios registrados)**: Descuenta el monto del saldo
  - Verifica que haya saldo suficiente
  - Actualiza la tabla `GuatepassUsers`
- **Modalidad 3 (No registrados)**: No actualiza balance (pago en efectivo)

**Output:**
```json
{
  "balance_update": {
    "updated": true,
    "previous_balance": "100.00",
    "new_balance": "85.00",
    "amount_charged": "15.00",
    "message": "Balance actualizado exitosamente"
  }
}
```

### 5. **Step Function: GuatepassProcessTollStateMachine**

Máquina de estados que orquesta el flujo completo.

**Estados:**
1. **CalculateTollFare**: Calcula la tarifa
2. **MergeCalculateResult**: Normaliza el resultado
3. **RecordTransaction**: Registra la transacción
4. **MergeRecordResult**: Normaliza el resultado
5. **UpdateBalance**: Actualiza el saldo
6. **MergeBalanceResult**: Normaliza el resultado
7. **ProcessingSuccess**: Estado de éxito

**Manejo de Errores:**
- Cada Lambda tiene reintentos automáticos (3 intentos con backoff exponencial)
- Estados de error dedicados: `HandleCalculateError`, `HandleRecordError`, `HandleBalanceError`
- Estado final de fallo: `ProcessingFailed`

**Trazabilidad:**
- Logs completos en CloudWatch: `/aws/stepfunctions/guatepass-process-toll-dev`
- AWS X-Ray habilitado para trazas distribuidas
- Cada ejecución se nombra con: `toll-{event_id}-{placa}`

## 🚀 Flujo Completo End-to-End

```
1. Webhook recibe evento de peaje
   POST /webhook/toll
   
2. IngestTollFunction publica a EventBridge
   Source: guatepass.toll
   DetailType: TollDetected
   
3. ResolveUserProfileFunction consume el evento
   - Busca usuario en DynamoDB
   - Determina modalidad (1, 2, o 3)
   - Inicia Step Function
   
4. Step Function ejecuta:
   a. CalculateTollFare
      - Tarifa base según peaje
      - Aplica multiplicador por modalidad
   
   b. RecordTransaction
      - Genera transaction_id
      - Guarda en DynamoDB
   
   c. UpdateBalance
      - Descuenta saldo (si aplica)
      - Actualiza tabla Users
   
5. Step Function termina exitosamente
   - Estado: SUCCEEDED
   - Output completo con toda la información
```

## 🛠️ Deployment

### Prerequisitos
- AWS CLI configurado
- SAM CLI instalado
- Slices #1, #2 y #3 ya desplegados

### Paso 1: Build
```powershell
cd C:\Users\Mayco\Documents\GitHub\GUATE_PASS
sam build --use-container
```

### Paso 2: Deploy
```powershell
sam deploy
```

Esto actualizará el stack existente `guatepass-dev` con los nuevos recursos.

### Paso 3: Verificar Deployment
```powershell
# Ver outputs del stack
aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs"

# Verificar Step Function
aws stepfunctions list-state-machines --query "stateMachines[?name=='guatepass-process-toll-dev']"

# Verificar tabla de transacciones
aws dynamodb describe-table --table-name GuatepassTransactions-dev
```

## 🧪 Testing

### Opción 1: Script Automatizado (Recomendado)
```powershell
.\scripts\test-stepfunction.ps1
```

Este script ejecuta 3 tests:
- ✅ Test 1: Usuario CON Tag (Modalidad 1)
- ✅ Test 2: Usuario SIN Tag (Modalidad 2)
- ✅ Test 3: Usuario NO registrado (Modalidad 3)

### Opción 2: Test Manual

#### Test 1: Usuario CON Tag (Modalidad 1)
```powershell
$API_URL = "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/webhook/toll"

$payload = @{
    placa = "P123ABC"
    peaje_id = "PEAJE001"
    peaje_nombre = "carretera_norte"
    tag_id = "TAG-001"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    lane_id = "LANE-01"
} | ConvertTo-Json

Invoke-RestMethod -Uri $API_URL -Method Post -Body $payload -ContentType "application/json"
```

#### Verificar Ejecución
```powershell
# Ver ejecuciones recientes
aws stepfunctions list-executions --state-machine-arn arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:guatepass-process-toll-dev --max-results 5

# Ver detalles de una ejecución
aws stepfunctions describe-execution --execution-arn "ARN_DE_EJECUCION"

# Ver logs
aws logs tail /aws/stepfunctions/guatepass-process-toll-dev --follow
```

#### Verificar Transacciones
```powershell
# Escanear transacciones recientes
aws dynamodb scan --table-name GuatepassTransactions-dev --max-items 10

# Consultar transacciones de una placa específica
aws dynamodb query `
  --table-name GuatepassTransactions-dev `
  --index-name PlacaTimestampIndex `
  --key-condition-expression "placa = :placa" `
  --expression-attribute-values '{":placa":{"S":"P123ABC"}}'
```

#### Verificar Balances
```powershell
# Ver saldo de un usuario
aws dynamodb get-item `
  --table-name GuatepassUsers-dev `
  --key '{"placa":{"S":"P123ABC"}}' `
  --projection-expression "placa,nombre,saldo"
```

## 📊 Monitoreo

### Consola de Step Functions
```
https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines
```

Aquí puedes ver:
- Ejecuciones en progreso
- Historial de ejecuciones
- Gráfico visual del flujo
- Detalles de cada paso (input/output)
- Errores y reintentos

### CloudWatch Logs

**Logs de Step Function:**
```powershell
aws logs tail /aws/stepfunctions/guatepass-process-toll-dev --follow
```

**Logs de cada Lambda:**
```powershell
# Calculate Fare
aws logs tail /aws/lambda/guatepass-calculate-fare-dev --follow

# Record Transaction
aws logs tail /aws/lambda/guatepass-record-transaction-dev --follow

# Update Balance
aws logs tail /aws/lambda/guatepass-update-balance-dev --follow
```

### AWS X-Ray

Ver trazas distribuidas en:
```
https://console.aws.amazon.com/xray/home?region=us-east-1#/service-map
```

## 🔍 Troubleshooting

### Problem 1: Step Function no se inicia
**Síntomas:** El evento llega al webhook pero no se ejecuta la Step Function

**Solución:**
1. Verificar que `ResolveUserProfileFunction` tiene permisos para iniciar la Step Function
2. Verificar logs de `ResolveUserProfileFunction`:
```powershell
aws logs tail /aws/lambda/guatepass-resolve-user-dev --since 5m
```
3. Verificar que la variable de entorno `STATE_MACHINE_ARN` está configurada

### Problem 2: Error "Lambda.ServiceException"
**Síntomas:** La Step Function falla en algún paso con error de Lambda

**Solución:**
1. Ver logs del Lambda específico que falló
2. Verificar que el Lambda tiene los permisos necesarios (DynamoDB, etc.)
3. Verificar que las variables de entorno están configuradas

### Problem 3: Balance no se actualiza
**Síntomas:** La transacción se registra pero el saldo no cambia

**Solución:**
1. Verificar que el usuario tiene saldo suficiente
2. Ver logs de `UpdateBalanceFunction`:
```powershell
aws logs tail /aws/lambda/guatepass-update-balance-dev --since 5m
```
3. Verificar modalidad del usuario (solo modalidad 1 y 2 actualizan balance)

### Problem 4: Transacciones duplicadas
**Síntomas:** Se crean múltiples transacciones para el mismo paso

**Solución:**
1. Verificar que el `event_id` es único en cada evento
2. Revisar configuración de EventBridge (puede estar enviando duplicados)
3. Implementar idempotencia en `RecordTransactionFunction`

## 📈 Métricas Importantes

### Step Functions
- **Executions Started**: Número de ejecuciones iniciadas
- **Executions Succeeded**: Ejecuciones exitosas
- **Executions Failed**: Ejecuciones fallidas
- **Execution Time**: Tiempo promedio de ejecución

### Lambdas
- **Invocations**: Número de invocaciones
- **Duration**: Tiempo de ejecución
- **Errors**: Errores durante la ejecución
- **Throttles**: Invocaciones rechazadas por límite

### DynamoDB
- **Read/Write Capacity**: Capacidad consumida
- **Throttled Requests**: Peticiones rechazadas
- **Item Count**: Número de items en la tabla

## 🎯 Próximos Pasos

El Slice #4 sienta las bases para las siguientes funcionalidades:

### Slice #5: CRUD de Tags
- POST `/users/{placa}/tag` - Asociar tag
- PUT `/users/{placa}/tag` - Actualizar tag
- DELETE `/users/{placa}/tag` - Desasociar tag

### Slice #6: Notificaciones
- SNS para envío de notificaciones
- Emails de confirmación de transacción
- SMS para saldo bajo
- Integración con Step Function (nuevo estado al final)

### Slice #7: Facturación
- Generación de facturas mensuales
- Agregación de transacciones
- PDF generation con Lambda
- Almacenamiento en S3

## 📚 Referencias

- [AWS Step Functions - Documentación Oficial](https://docs.aws.amazon.com/step-functions/)
- [Amazon States Language](https://states-language.net/spec.html)
- [AWS SAM - StateMachine](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-statemachine.html)
- [Best Practices for Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html)

## 🏆 Logros del Slice #4

✅ **Orquestación Completa**: Flujo end-to-end coordinado por Step Functions  
✅ **Cálculo Dinámico**: Tarifas calculadas según modalidad y tipo de peaje  
✅ **Persistencia**: Todas las transacciones guardadas en DynamoDB  
✅ **Actualización de Balances**: Saldos actualizados automáticamente  
✅ **Resiliencia**: Reintentos automáticos y manejo de errores  
✅ **Trazabilidad**: Logs completos y X-Ray habilitado  
✅ **Testing**: Scripts automatizados para verificación  

---

**Slice #4 completado** 🎉  
Ahora GuatePass puede procesar transacciones de peaje de forma completamente automatizada y resiliente.
