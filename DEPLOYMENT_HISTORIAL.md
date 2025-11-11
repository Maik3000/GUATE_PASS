# 🚀 DEPLOYMENT RÁPIDO - Endpoints de Historial

## ⚡ Comandos para Deployment (Copiar y Pegar)

### 1️⃣ Validar Template

```powershell
sam validate -t infrastructure/template.yaml
```

### 2️⃣ Build

```powershell
sam build -t infrastructure/template.yaml
```

### 3️⃣ Deploy

```powershell
sam deploy
```

### 4️⃣ Obtener URL de la API

```powershell
$API_URL = aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
Write-Host "`n✅ API URL: $API_URL`n"
```

### 5️⃣ Probar Endpoints

```powershell
# Test con placa de ejemplo
$placa = "P-111JKL"

Write-Host "🧪 Probando historial de pagos..."
curl "$API_URL/history/payments/$placa"

Write-Host "`n🧪 Probando historial de facturas..."
curl "$API_URL/history/invoices/$placa"
```

### 6️⃣ Ejecutar Suite de Tests Completa

```powershell
.\scripts\test-history.ps1
```

---

## 📋 Checklist de Deployment

- [ ] 1. Validar template ✅
- [ ] 2. Build exitoso ✅
- [ ] 3. Deploy exitoso ✅
- [ ] 4. API URL obtenida ✅
- [ ] 5. Tests manuales pasados ✅
- [ ] 6. Suite de tests automatizada ejecutada ✅

---

## 🔍 Verificación Post-Deployment

### Ver funciones Lambda creadas

```powershell
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'guatepass-get-')].FunctionName"
```

**Resultado esperado:**
```json
[
  "guatepass-get-payments-by-plate-dev",
  "guatepass-get-invoices-by-plate-dev"
]
```

### Ver endpoints en API Gateway

```powershell
aws cloudformation describe-stacks `
  --stack-name guatepass-dev `
  --query "Stacks[0].Outputs[?contains(OutputKey, 'History')].{Endpoint:OutputKey,URL:OutputValue}" `
  --output table
```

### Ver logs en tiempo real

```powershell
# En una ventana de PowerShell
aws logs tail /aws/lambda/guatepass-get-payments-by-plate-dev --follow

# En otra ventana
aws logs tail /aws/lambda/guatepass-get-invoices-by-plate-dev --follow
```

---

## 🧪 Comandos de Testing Rápido

### Test 1: Historial de Pagos

```powershell
$API_URL = aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
curl "$API_URL/history/payments/P-111JKL" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Test 2: Historial de Facturas

```powershell
curl "$API_URL/history/invoices/P-111JKL" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Test 3: Con Filtros

```powershell
# Limitar a 5 resultados
curl "$API_URL/history/payments/P-111JKL?limit=5"

# Solo facturas pendientes
curl "$API_URL/history/invoices/P-111JKL?status=pendiente"
```

---

## ⚠️ Troubleshooting

### Error: "Template invalid"

**Solución:**
```powershell
# Verificar sintaxis YAML
sam validate -t infrastructure/template.yaml --lint
```

### Error: "Function already exists"

**Solución:**
```powershell
# Eliminar funciones antiguas si existen
sam delete --stack-name guatepass-dev

# Volver a deployar
sam build -t infrastructure/template.yaml
sam deploy
```

### Error: "No se puede conectar a API"

**Solución:**
```powershell
# Verificar que el stack esté desplegado
aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].StackStatus"

# Debe mostrar: "CREATE_COMPLETE" o "UPDATE_COMPLETE"
```

### Las funciones no responden

**Solución:**
```powershell
# Ver logs de errores
aws logs tail /aws/lambda/guatepass-get-payments-by-plate-dev --since 10m

# Ver métricas
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Errors `
  --dimensions Name=FunctionName,Value=guatepass-get-payments-by-plate-dev `
  --start-time (Get-Date).AddHours(-1).ToUniversalTime() `
  --end-time (Get-Date).ToUniversalTime() `
  --period 300 `
  --statistics Sum
```

---

## 📊 Verificar Datos de Prueba

### ¿Hay transacciones en la base de datos?

```powershell
aws dynamodb scan --table-name GuatepassTransactions-dev --select COUNT
```

### ¿Hay facturas en la base de datos?

```powershell
aws dynamodb scan --table-name GuatepassInvoices-dev --select COUNT
```

### Si NO hay datos, generar transacciones de prueba

```powershell
# Ejecutar webhook de prueba primero
.\scripts\test-webhook.ps1

# O ejecutar step function completa
.\scripts\test-stepfunction.ps1
```

---

## 🎯 Comandos Todo-en-Uno

### Deployment Completo (Un solo comando)

```powershell
# Copiar y pegar en PowerShell
sam validate -t infrastructure/template.yaml; `
if ($?) { sam build -t infrastructure/template.yaml }; `
if ($?) { sam deploy }; `
if ($?) { 
    Write-Host "`n✅ Deployment exitoso!`n" -ForegroundColor Green;
    $API_URL = aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text;
    Write-Host "📡 API URL: $API_URL`n" -ForegroundColor Cyan;
    Write-Host "🧪 Ejecuta los tests con: .\scripts\test-history.ps1`n" -ForegroundColor Yellow
}
```

---

## 📚 Documentación

- **README completo**: `docs/HISTORY_API_README.md`
- **Resumen ejecutivo**: `ENDPOINTS_HISTORIAL_RESUMEN.md`
- **Estado del proyecto**: `PROJECT_STATUS.md`

---

## ✅ Todo Listo!

Una vez completados estos pasos, los endpoints de historial estarán **100% funcionales** y listos para usar.

**Endpoints disponibles:**
- ✅ `GET /history/payments/{placa}` - Historial de transacciones
- ✅ `GET /history/invoices/{placa}` - Historial de facturas

🎉 ¡Felicidades! El sistema GUATEPASS ahora tiene endpoints de historial completos.

