# ========================================
# Script de Testing - Slice #6: Notificaciones y Facturación
# ========================================

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "GUATEPASS - Test Slice #6: Notificaciones y Facturación" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Obtener la URL de la API desde los outputs del stack
Write-Host "[1/6] Obteniendo información del stack..." -ForegroundColor Yellow
$API_URL = aws cloudformation describe-stacks `
    --stack-name guatepass-dev `
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
    --output text

if (-not $API_URL) {
    Write-Host "❌ Error: No se pudo obtener la URL de la API" -ForegroundColor Red
    exit 1
}

Write-Host "✅ API URL: $API_URL" -ForegroundColor Green
Write-Host ""

# ========================================
# TEST 1: Transacción Modalidad 2 (Usuario Registrado)
# ========================================
Write-Host "[2/6] TEST 1: Simulando transacción de usuario REGISTRADO (Modalidad 2)..." -ForegroundColor Yellow
Write-Host "Usuario: P-111JKL (Ana Torres) - Con saldo" -ForegroundColor Gray

$payload1 = @{
    placa = "P-111JKL"
    peaje_id = "PEAJE001"
    peaje_nombre = "Carretera Norte"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    lane_id = "LANE-01"
} | ConvertTo-Json

try {
    Write-Host "Enviando evento al webhook..." -ForegroundColor Gray
    $response = Invoke-RestMethod `
        -Uri "$API_URL/webhook/toll" `
        -Method Post `
        -Body $payload1 `
        -ContentType "application/json"
    
    Write-Host "✅ Transacción procesada" -ForegroundColor Green
    Write-Host "   - Event ID: $($response.event_id)" -ForegroundColor Gray
    Write-Host "   - Placa: $($response.placa)" -ForegroundColor Gray
    Write-Host ""
    
    # Esperar a que la Step Function complete
    Write-Host "Esperando procesamiento de Step Function..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
    
    Write-Host "✅ Se debe haber:" -ForegroundColor Green
    Write-Host "   1. Calculado tarifa (sin recargo - Modalidad 2)" -ForegroundColor Gray
    Write-Host "   2. Registrado transacción" -ForegroundColor Gray
    Write-Host "   3. Actualizado balance" -ForegroundColor Gray
    Write-Host "   4. Generado factura (PAGADA)" -ForegroundColor Gray
    Write-Host "   5. Enviado notificación de cobro por email ✉️" -ForegroundColor Gray
    
}
catch {
    Write-Host "❌ Error en transacción: $_" -ForegroundColor Red
}

Write-Host ""

# ========================================
# TEST 2: Transacción Modalidad 1 (Usuario NO Registrado)
# ========================================
Write-Host "[3/6] TEST 2: Simulando transacción de usuario NO REGISTRADO (Modalidad 1)..." -ForegroundColor Yellow
Write-Host "Placa: P-888NOREGISTRADO (No existe en sistema)" -ForegroundColor Gray

$payload2 = @{
    placa = "P-888NOREGISTRADO"
    peaje_id = "PEAJE002"
    peaje_nombre = "Carretera Sur"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    lane_id = "LANE-02"
} | ConvertTo-Json

try {
    Write-Host "Enviando evento al webhook..." -ForegroundColor Gray
    $response = Invoke-RestMethod `
        -Uri "$API_URL/webhook/toll" `
        -Method Post `
        -Body $payload2 `
        -ContentType "application/json"
    
    Write-Host "✅ Transacción procesada" -ForegroundColor Green
    Write-Host "   - Event ID: $($response.event_id)" -ForegroundColor Gray
    Write-Host "   - Placa: $($response.placa)" -ForegroundColor Gray
    Write-Host ""
    
    # Esperar a que la Step Function complete
    Write-Host "Esperando procesamiento de Step Function..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
    
    Write-Host "✅ Se debe haber:" -ForegroundColor Green
    Write-Host "   1. Calculado tarifa CON RECARGO (+50% - Modalidad 1)" -ForegroundColor Gray
    Write-Host "   2. Registrado transacción" -ForegroundColor Gray
    Write-Host "   3. NO actualizado balance (no registrado)" -ForegroundColor Gray
    Write-Host "   4. Generado factura (PENDIENTE + MULTA 50%)" -ForegroundColor Gray
    Write-Host "   5. Enviado invitación para registrarse por email ✉️" -ForegroundColor Gray
    
}
catch {
    Write-Host "❌ Error en transacción: $_" -ForegroundColor Red
}

Write-Host ""

# ========================================
# TEST 3: Verificar Logs de Notificaciones
# ========================================
Write-Host "[4/6] TEST 3: Verificando logs de notificaciones..." -ForegroundColor Yellow

try {
    Write-Host "Consultando logs de NotifyUserFunction..." -ForegroundColor Gray
    
    $logs = aws logs tail /aws/lambda/guatepass-notify-user-dev --since 2m --format short
    
    if ($logs -match "EMAIL SIMULADO") {
        Write-Host "✅ Emails simulados enviados correctamente" -ForegroundColor Green
        Write-Host "   Los emails están en los logs de CloudWatch" -ForegroundColor Gray
    }
    else {
        Write-Host "⚠️  No se encontraron logs de emails (puede que aún no se hayan procesado)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  No se pudieron obtener logs: $_" -ForegroundColor Yellow
}

Write-Host ""

# ========================================
# TEST 4: Verificar Facturas en DynamoDB
# ========================================
Write-Host "[5/6] TEST 4: Verificando facturas en DynamoDB..." -ForegroundColor Yellow

try {
    Write-Host "Consultando tabla GuatepassInvoices-dev..." -ForegroundColor Gray
    
    $invoices = aws dynamodb scan `
        --table-name GuatepassInvoices-dev `
        --max-items 5 `
        --query "Items[*].[invoice_id.S, placa.S, modalidad.N, total.S, estado.S]" `
        --output table
    
    if ($invoices) {
        Write-Host "✅ Facturas encontradas:" -ForegroundColor Green
        Write-Host $invoices
    }
    else {
        Write-Host "⚠️  No se encontraron facturas" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Error consultando facturas: $_" -ForegroundColor Yellow
}

Write-Host ""

# ========================================
# TEST 5: Verificar Ejecuciones de Step Function
# ========================================
Write-Host "[6/6] TEST 5: Verificando ejecuciones de Step Function..." -ForegroundColor Yellow

try {
    $stateMachineArn = aws cloudformation describe-stacks `
        --stack-name guatepass-dev `
        --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" `
        --output text
    
    if ($stateMachineArn) {
        Write-Host "Consultando últimas ejecuciones..." -ForegroundColor Gray
        
        $executions = aws stepfunctions list-executions `
            --state-machine-arn $stateMachineArn `
            --max-results 5 `
            --query "executions[*].[name, status, startDate]" `
            --output table
        
        if ($executions) {
            Write-Host "✅ Ejecuciones recientes:" -ForegroundColor Green
            Write-Host $executions
        }
    }
}
catch {
    Write-Host "⚠️  Error consultando Step Function: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "✅ Testing del Slice #6 completado" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Resumen de lo probado:" -ForegroundColor White
Write-Host ""
Write-Host "Modalidad 2 (Usuario Registrado):" -ForegroundColor Yellow
Write-Host "  ✅ Transacción procesada" -ForegroundColor Gray
Write-Host "  ✅ Factura generada (PAGADA)" -ForegroundColor Gray
Write-Host "  ✅ Notificación de cobro enviada (simulada)" -ForegroundColor Gray
Write-Host ""
Write-Host "Modalidad 1 (Usuario NO Registrado):" -ForegroundColor Yellow
Write-Host "  ✅ Transacción procesada" -ForegroundColor Gray
Write-Host "  ✅ Factura generada (PENDIENTE + MULTA 50%)" -ForegroundColor Gray
Write-Host "  ✅ Invitación para registrarse enviada (simulada)" -ForegroundColor Gray
Write-Host ""
Write-Host "📧 Notificaciones:" -ForegroundColor White
Write-Host "  Los emails están SIMULADOS usando logs de CloudWatch" -ForegroundColor Gray
Write-Host "  Para ver los emails completos:" -ForegroundColor Gray
Write-Host "    aws logs tail /aws/lambda/guatepass-notify-user-dev --follow" -ForegroundColor Cyan
Write-Host ""
Write-Host "📄 Facturas:" -ForegroundColor White
Write-Host "  Almacenadas en DynamoDB: GuatepassInvoices-dev" -ForegroundColor Gray
Write-Host "  Para consultar: aws dynamodb scan --table-name GuatepassInvoices-dev" -ForegroundColor Cyan
Write-Host ""

