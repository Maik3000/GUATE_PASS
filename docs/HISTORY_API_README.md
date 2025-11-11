# 📊 GUATEPASS - API de Historial de Transacciones y Facturas

Documentación de los endpoints REST para consultar el historial de pagos (transacciones) y facturas de los usuarios.

---

## 🎯 Descripción

Estos endpoints permiten consultar el historial completo de:
- **Transacciones/Pagos**: Todos los pasos por peaje registrados
- **Facturas**: Todas las facturas generadas (pagadas y pendientes)

### Componentes

✅ **API Gateway** - Endpoints REST públicos  
✅ **Lambda GetPaymentsByPlate** - Consulta historial de transacciones  
✅ **Lambda GetInvoicesByPlate** - Consulta historial de facturas  
✅ **DynamoDB Tables** - GuatepassTransactions + GuatepassInvoices (con GSI)  

---

## 📡 Endpoints Disponibles

### Base URL

```
https://{api-id}.execute-api.us-east-1.amazonaws.com/dev
```

Para obtener tu URL específica:
```powershell
aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
```

---

## 1️⃣ GET /history/payments/{placa}

Consulta el historial completo de transacciones/pagos por placa.

### Request

```bash
GET /history/payments/P-123ABC
```

### Query Parameters (Opcionales)

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Número máximo de resultados |
| `from_date` | string | - | Fecha inicio (ISO 8601: YYYY-MM-DDTHH:MM:SS) |
| `to_date` | string | - | Fecha fin (ISO 8601: YYYY-MM-DDTHH:MM:SS) |

### Ejemplos de Uso

```bash
# Consulta básica
GET /history/payments/P-123ABC

# Limitar resultados
GET /history/payments/P-123ABC?limit=10

# Filtrar por rango de fechas
GET /history/payments/P-123ABC?from_date=2025-11-01T00:00:00&to_date=2025-11-30T23:59:59

# Combinación
GET /history/payments/P-123ABC?limit=5&from_date=2025-11-01T00:00:00
```

### Response Exitoso (200)

```json
{
  "placa": "P-123ABC",
  "total_transactions": 5,
  "total_amount": 75.00,
  "transactions": [
    {
      "transaction_id": "TX-20251109103015-P111JKL",
      "placa": "P-123ABC",
      "toll_id": "PEAJE001",
      "toll_name": "Carretera Norte",
      "modalidad": 2,
      "amount_charged": 15.00,
      "base_fare": 15.00,
      "multiplier": 1.0,
      "timestamp": "2025-11-09T10:30:15Z",
      "created_at": "2025-11-09T10:30:15Z",
      "status": "completed"
    },
    {
      "transaction_id": "TX-20251108150000-P123ABC",
      "placa": "P-123ABC",
      "toll_id": "PEAJE002",
      "toll_name": "Carretera Sur",
      "modalidad": 2,
      "amount_charged": 20.00,
      "base_fare": 20.00,
      "multiplier": 1.0,
      "timestamp": "2025-11-08T15:00:00Z",
      "created_at": "2025-11-08T15:00:00Z",
      "status": "completed"
    }
  ],
  "message": "Historial de pagos para P-123ABC obtenido exitosamente"
}
```

### Response Sin Transacciones (200)

```json
{
  "placa": "P-999ZZZ",
  "total_transactions": 0,
  "transactions": [],
  "message": "No se encontraron transacciones para la placa P-999ZZZ"
}
```

### Response Error (400)

```json
{
  "error": "Parámetro placa es requerido",
  "statusCode": 400
}
```

---

## 2️⃣ GET /history/invoices/{placa}

Consulta el historial completo de facturas por placa.

### Request

```bash
GET /history/invoices/P-123ABC
```

### Query Parameters (Opcionales)

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Número máximo de resultados |
| `status` | string | - | Filtrar por estado: `pendiente` o `pagada` |

### Ejemplos de Uso

```bash
# Consulta básica
GET /history/invoices/P-123ABC

# Limitar resultados
GET /history/invoices/P-123ABC?limit=10

# Solo facturas pendientes
GET /history/invoices/P-123ABC?status=pendiente

# Solo facturas pagadas
GET /history/invoices/P-123ABC?status=pagada

# Combinación
GET /history/invoices/P-123ABC?limit=5&status=pendiente
```

### Response Exitoso (200)

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
      "placa": "P-123ABC",
      "modalidad": 2,
      "monto_base": 15.00,
      "multa": 0.00,
      "total": 15.00,
      "estado": "pagada",
      "concepto": "Paso por peaje - Carretera Norte",
      "transaction_id": "TX-20251109103015-P123ABC",
      "toll_name": "Carretera Norte",
      "created_at": "2025-11-09T10:30:15Z",
      "contribuyente": {
        "nombre": "Juan Pérez",
        "nit": "12345678",
        "direccion": "Ciudad de Guatemala"
      }
    },
    {
      "invoice_id": "FAC-20251108150000",
      "placa": "P-123ABC",
      "modalidad": 1,
      "monto_base": 20.00,
      "multa": 10.00,
      "total": 30.00,
      "estado": "pendiente",
      "concepto": "Paso por peaje - Carretera Sur (Pago pendiente + Multa por pago tardío)",
      "transaction_id": "TX-20251108150000-P123ABC",
      "toll_name": "Carretera Sur",
      "created_at": "2025-11-08T15:00:00Z",
      "contribuyente": {
        "nombre": "N/A",
        "nit": "CF",
        "direccion": "N/A"
      }
    }
  ],
  "message": "Historial de facturas para P-123ABC obtenido exitosamente"
}
```

### Response Sin Facturas (200)

```json
{
  "placa": "P-999ZZZ",
  "summary": {
    "total_invoices": 0,
    "pending_invoices": 0,
    "paid_invoices": 0,
    "total_amount": 0,
    "total_pending": 0,
    "total_paid": 0
  },
  "invoices": [],
  "message": "No se encontraron facturas para la placa P-999ZZZ"
}
```

---

## 📊 Estructura de Datos

### Transaction Object

```typescript
{
  transaction_id: string,      // ID único de la transacción
  placa: string,                // Placa del vehículo
  toll_id: string,              // ID del peaje
  toll_name: string,            // Nombre del peaje
  modalidad: number,            // 1=No registrado, 2=Registrado
  amount_charged: number,       // Monto cobrado
  base_fare: number,            // Tarifa base
  multiplier: number,           // Multiplicador aplicado
  timestamp: string,            // Timestamp del evento
  created_at: string,           // Fecha de creación (ISO 8601)
  status: string                // Estado: "completed"
}
```

### Invoice Object

```typescript
{
  invoice_id: string,           // Número de factura
  placa: string,                // Placa del vehículo
  modalidad: number,            // 1=No registrado, 2=Registrado
  monto_base: number,           // Cargo base
  multa: number,                // Multa (solo modalidad 1)
  total: number,                // Total a pagar
  estado: string,               // "pendiente" o "pagada"
  concepto: string,             // Descripción del cobro
  transaction_id: string,       // ID de la transacción relacionada
  toll_name: string,            // Nombre del peaje
  created_at: string,           // Fecha de emisión (ISO 8601)
  contribuyente: {              // Datos del contribuyente
    nombre: string,
    nit: string,
    direccion: string
  }
}
```

---

## 🧪 Testing

### Script Automatizado

```powershell
.\scripts\test-history.ps1
```

Este script prueba:
1. ✅ Consulta de historial de pagos
2. ✅ Consulta de historial de facturas
3. ✅ Filtros opcionales (limit, status, fechas)
4. ✅ Manejo de placas sin historial

### Pruebas Manuales con curl

```powershell
# Obtener URL
$API_URL = aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text

# Test 1: Historial de pagos
curl "$API_URL/history/payments/P-123ABC"

# Test 2: Historial de facturas
curl "$API_URL/history/invoices/P-123ABC"

# Test 3: Con filtros
curl "$API_URL/history/payments/P-123ABC?limit=5"
curl "$API_URL/history/invoices/P-123ABC?status=pendiente"
```

### Pruebas con PowerShell

```powershell
# Historial de pagos
$response = Invoke-RestMethod -Uri "$API_URL/history/payments/P-123ABC" -Method Get
$response | ConvertTo-Json -Depth 10

# Historial de facturas
$response = Invoke-RestMethod -Uri "$API_URL/history/invoices/P-123ABC" -Method Get
$response | ConvertTo-Json -Depth 10
```

---

## 📈 Casos de Uso

### 1. Dashboard de Usuario

Mostrar al usuario su historial completo de transacciones y facturas pendientes.

```javascript
// Frontend: Obtener historial completo
async function getUserDashboard(placa) {
  const [payments, invoices] = await Promise.all([
    fetch(`${API_URL}/history/payments/${placa}`),
    fetch(`${API_URL}/history/invoices/${placa}`)
  ]);
  
  const paymentsData = await payments.json();
  const invoicesData = await invoices.json();
  
  return {
    totalSpent: paymentsData.total_amount,
    totalTransactions: paymentsData.total_transactions,
    pendingInvoices: invoicesData.summary.pending_invoices,
    amountDue: invoicesData.summary.total_pending
  };
}
```

### 2. Reporte Mensual

Generar reporte de gastos del mes actual.

```powershell
# Obtener transacciones del mes actual
$startDate = (Get-Date -Day 1).ToString("yyyy-MM-ddT00:00:00")
$endDate = (Get-Date).ToString("yyyy-MM-ddT23:59:59")

curl "$API_URL/history/payments/P-123ABC?from_date=$startDate&to_date=$endDate"
```

### 3. Alertas de Facturas Pendientes

Verificar si hay facturas pendientes y enviar notificación.

```javascript
async function checkPendingInvoices(placa) {
  const response = await fetch(
    `${API_URL}/history/invoices/${placa}?status=pendiente`
  );
  const data = await response.json();
  
  if (data.summary.pending_invoices > 0) {
    sendAlert({
      message: `Tienes ${data.summary.pending_invoices} facturas pendientes`,
      amount: data.summary.total_pending
    });
  }
}
```

### 4. Exportar a Excel

```powershell
# PowerShell: Exportar historial a CSV
$API_URL = "https://xxx.execute-api.us-east-1.amazonaws.com/dev"
$placa = "P-123ABC"

$payments = Invoke-RestMethod -Uri "$API_URL/history/payments/$placa"
$payments.transactions | Export-Csv -Path "historial_$placa.csv" -NoTypeInformation

Write-Host "Historial exportado a historial_$placa.csv"
```

---

## 🔍 Consultas Avanzadas

### Filtrar Transacciones del Último Mes

```bash
# Últimos 30 días
from_date=$(date -u -d '30 days ago' +%Y-%m-%dT00:00:00)
to_date=$(date -u +%Y-%m-%dT23:59:59)

curl "$API_URL/history/payments/P-123ABC?from_date=$from_date&to_date=$to_date"
```

### Consultar Solo Facturas Pendientes

```bash
curl "$API_URL/history/invoices/P-123ABC?status=pendiente"
```

### Obtener Últimas 5 Transacciones

```bash
curl "$API_URL/history/payments/P-123ABC?limit=5"
```

---

## 📊 Monitoreo

### Ver Logs

```powershell
# Logs de pagos
aws logs tail /aws/lambda/guatepass-get-payments-by-plate-dev --follow

# Logs de facturas
aws logs tail /aws/lambda/guatepass-get-invoices-by-plate-dev --follow

# Filtrar errores
aws logs tail /aws/lambda/guatepass-get-payments-by-plate-dev --filter-pattern "ERROR"
```

### Métricas de CloudWatch

```powershell
# Invocaciones del endpoint de pagos
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Invocations `
  --dimensions Name=FunctionName,Value=guatepass-get-payments-by-plate-dev `
  --start-time $(Get-Date).AddHours(-1).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time $(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss") `
  --period 300 `
  --statistics Sum
```

---

## ⚡ Performance

### Latencias Esperadas

| Endpoint | Latencia Típica | Latencia P95 |
|----------|-----------------|--------------|
| GET /history/payments/{placa} | 50-100ms | 150-200ms |
| GET /history/invoices/{placa} | 50-100ms | 150-200ms |

### Optimizaciones Implementadas

✅ **GSI en DynamoDB**: Consultas O(1) por placa  
✅ **PAY_PER_REQUEST**: Escalamiento automático  
✅ **Lambda con 256MB**: Balance costo/performance  
✅ **Límite de resultados**: Default 20 items para respuestas rápidas  
✅ **Orden descendente**: Resultados más recientes primero  

---

## 🔒 Seguridad

### CORS Habilitado

```yaml
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Recomendaciones para Producción

1. **Autenticación**: Implementar AWS Cognito o API Keys
2. **Rate Limiting**: Configurar throttling en API Gateway
3. **CORS Específico**: Cambiar `*` por dominios permitidos
4. **Encriptación**: Usar HTTPS (ya implementado por API Gateway)

---

## 🐛 Troubleshooting

### Error: "No se encontraron transacciones"

**Causa**: La placa no tiene transacciones registradas.

**Solución**: Verifica que la placa esté correcta y que haya pasado por peajes.

```powershell
# Verificar si la placa existe en usuarios
aws dynamodb get-item `
  --table-name GuatepassUsers-dev `
  --key '{"placa": {"S": "P-123ABC"}}'
```

### Error 500: "Error interno"

**Diagnóstico**:
```powershell
aws logs tail /aws/lambda/guatepass-get-payments-by-plate-dev --start-time '10m ago'
```

**Causas comunes**:
- Tabla DynamoDB no existe
- Permisos IAM incorrectos
- Variable de entorno mal configurada

### Respuesta Vacía o Timeout

**Causa**: DynamoDB lento o tabla muy grande.

**Solución**: Usa el parámetro `limit` para reducir resultados.

```bash
curl "$API_URL/history/payments/P-123ABC?limit=10"
```

---

## 📚 Integración con Otros Slices

### Con Slice #4 (Step Functions)

Las transacciones son creadas por `RecordTransactionFunction` dentro de la Step Function.

### Con Slice #6 (Notificaciones)

Las facturas son generadas por `GenerateInvoiceFunction` dentro de la Step Function.

### Flujo Completo

```
1. Usuario pasa por peaje
   ↓
2. Webhook recibe evento (Slice #3)
   ↓
3. Step Function procesa (Slice #4)
   ├─ RecordTransaction → GuatepassTransactions
   └─ GenerateInvoice → GuatepassInvoices
   ↓
4. Usuario consulta historial ⭐ (Este módulo)
   ├─ GET /history/payments/{placa}
   └─ GET /history/invoices/{placa}
```

---

## 🎉 Conclusión

Los endpoints de historial permiten a los usuarios y administradores consultar el historial completo de transacciones y facturas de forma eficiente y escalable.

**Características principales:**
- ✅ Consultas rápidas con GSI
- ✅ Filtros flexibles (límite, fechas, estado)
- ✅ Respuestas con estadísticas agregadas
- ✅ Ordenamiento por fecha descendente
- ✅ Manejo robusto de errores

---

**Última actualización:** Noviembre 11, 2025  
**Estado:** ✅ FUNCIONAL Y LISTO PARA PRODUCCIÓN

