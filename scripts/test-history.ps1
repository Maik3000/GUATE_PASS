# ==============================================================================
# GUATEPASS - Script de Testing de Endpoints de Historial
# ==============================================================================
# Prueba los endpoints:
#   - GET /history/payments/{placa} - Historial de pagos
#   - GET /history/invoices/{placa} - Historial de facturas
#
# Uso:
#   .\scripts\test-history.ps1
# ==============================================================================

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🧪 GUATEPASS - Testing de Historial" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# ==============================================================================
# 1. OBTENER URL DE LA API
# ==============================================================================
Write-Host "📡 Paso 1: Obteniendo URL de la API..." -ForegroundColor Yellow

try {
    $API_URL = aws cloudformation describe-stacks `
        --stack-name guatepass-dev `
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
        --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: No se pudo obtener la URL de la API" -ForegroundColor Red
        Write-Host "   Verifica que el stack 'guatepass-dev' esté desplegado" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ URL de la API: $API_URL" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ Error al obtener URL de la API: $_" -ForegroundColor Red
    exit 1
}

# ==============================================================================
# 2. VERIFICAR QUE HAY DATOS DE PRUEBA
# ==============================================================================
Write-Host "📊 Paso 2: Verificando datos de prueba..." -ForegroundColor Yellow

# Verificar que existen transacciones
Write-Host "   Verificando tabla de transacciones..." -ForegroundColor Gray
$transactionsCount = aws dynamodb scan `
    --table-name GuatepassTransactions-dev `
    --select "COUNT" `
    --query "Count" `
    --output text 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Transacciones encontradas: $transactionsCount" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No se encontraron transacciones. Ejecuta primero el webhook de peajes." -ForegroundColor Yellow
}

# Verificar que existen facturas
Write-Host "   Verificando tabla de facturas..." -ForegroundColor Gray
$invoicesCount = aws dynamodb scan `
    --table-name GuatepassInvoices-dev `
    --select "COUNT" `
    --query "Count" `
    --output text 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Facturas encontradas: $invoicesCount" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No se encontraron facturas. Ejecuta primero el webhook de peajes." -ForegroundColor Yellow
}

Write-Host ""

# ==============================================================================
# 3. OBTENER UNA PLACA CON DATOS
# ==============================================================================
Write-Host "🔍 Paso 3: Buscando placa con datos para testing..." -ForegroundColor Yellow

# Intentar obtener una placa de las transacciones
$testPlaca = aws dynamodb scan `
    --table-name GuatepassTransactions-dev `
    --limit 1 `
    --query "Items[0].placa.S" `
    --output text 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($testPlaca)) {
    Write-Host "   ⚠️  No se encontró ninguna placa con transacciones" -ForegroundColor Yellow
    Write-Host "   Usando placas predeterminadas..." -ForegroundColor Yellow
    
    # Placas de ejemplo del sistema
    $testPlacas = @("P-111JKL", "P-888NOREGISTRADO", "P-123ABC", "P-456DEF")
} else {
    Write-Host "   ✅ Placa encontrada: $testPlaca" -ForegroundColor Green
    $testPlacas = @($testPlaca)
}

Write-Host ""

# ==============================================================================
# 4. TEST: HISTORIAL DE PAGOS
# ==============================================================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "📝 TEST 1: Historial de Pagos" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

foreach ($placa in $testPlacas) {
    Write-Host "🚗 Testing con placa: $placa" -ForegroundColor Magenta
    Write-Host "   Endpoint: GET $API_URL/history/payments/$placa" -ForegroundColor Gray
    Write-Host ""
    
    try {
        $response = curl -s "$API_URL/history/payments/$placa"
        $jsonResponse = $response | ConvertFrom-Json
        
        if ($jsonResponse.placa) {
            Write-Host "   ✅ Respuesta exitosa:" -ForegroundColor Green
            Write-Host "      - Placa: $($jsonResponse.placa)" -ForegroundColor White
            Write-Host "      - Total Transacciones: $($jsonResponse.total_transactions)" -ForegroundColor White
            Write-Host "      - Monto Total: Q$($jsonResponse.total_amount)" -ForegroundColor White
            
            if ($jsonResponse.total_transactions -gt 0) {
                Write-Host ""
                Write-Host "   📋 Últimas transacciones:" -ForegroundColor Cyan
                $count = [Math]::Min(3, $jsonResponse.transactions.Count)
                for ($i = 0; $i -lt $count; $i++) {
                    $tx = $jsonResponse.transactions[$i]
                    Write-Host "      $($i+1). ID: $($tx.transaction_id)" -ForegroundColor White
                    Write-Host "         Peaje: $($tx.toll_name)" -ForegroundColor White
                    Write-Host "         Monto: Q$($tx.amount_charged)" -ForegroundColor White
                    Write-Host "         Fecha: $($tx.created_at)" -ForegroundColor White
                    Write-Host ""
                }
                
                # Si encontramos datos, salimos del loop
                break
            } else {
                Write-Host "      ℹ️  No hay transacciones para esta placa" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ⚠️  Respuesta no esperada" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

# ==============================================================================
# 5. TEST: HISTORIAL DE FACTURAS
# ==============================================================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "📄 TEST 2: Historial de Facturas" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

foreach ($placa in $testPlacas) {
    Write-Host "🚗 Testing con placa: $placa" -ForegroundColor Magenta
    Write-Host "   Endpoint: GET $API_URL/history/invoices/$placa" -ForegroundColor Gray
    Write-Host ""
    
    try {
        $response = curl -s "$API_URL/history/invoices/$placa"
        $jsonResponse = $response | ConvertFrom-Json
        
        if ($jsonResponse.placa) {
            Write-Host "   ✅ Respuesta exitosa:" -ForegroundColor Green
            Write-Host "      - Placa: $($jsonResponse.placa)" -ForegroundColor White
            Write-Host ""
            
            Write-Host "   📊 Resumen:" -ForegroundColor Cyan
            Write-Host "      - Total Facturas: $($jsonResponse.summary.total_invoices)" -ForegroundColor White
            Write-Host "      - Facturas Pendientes: $($jsonResponse.summary.pending_invoices)" -ForegroundColor Yellow
            Write-Host "      - Facturas Pagadas: $($jsonResponse.summary.paid_invoices)" -ForegroundColor Green
            Write-Host "      - Monto Total: Q$($jsonResponse.summary.total_amount)" -ForegroundColor White
            Write-Host "      - Total Pendiente: Q$($jsonResponse.summary.total_pending)" -ForegroundColor Yellow
            Write-Host "      - Total Pagado: Q$($jsonResponse.summary.total_paid)" -ForegroundColor Green
            
            if ($jsonResponse.summary.total_invoices -gt 0) {
                Write-Host ""
                Write-Host "   📋 Últimas facturas:" -ForegroundColor Cyan
                $count = [Math]::Min(3, $jsonResponse.invoices.Count)
                for ($i = 0; $i -lt $count; $i++) {
                    $inv = $jsonResponse.invoices[$i]
                    Write-Host "      $($i+1). Factura: $($inv.invoice_id)" -ForegroundColor White
                    Write-Host "         Estado: $($inv.estado)" -ForegroundColor $(if ($inv.estado -eq "pagada") { "Green" } else { "Yellow" })
                    Write-Host "         Monto Base: Q$($inv.monto_base)" -ForegroundColor White
                    Write-Host "         Multa: Q$($inv.multa)" -ForegroundColor $(if ($inv.multa -gt 0) { "Red" } else { "White" })
                    Write-Host "         Total: Q$($inv.total)" -ForegroundColor White
                    Write-Host "         Concepto: $($inv.concepto)" -ForegroundColor Gray
                    Write-Host ""
                }
                
                # Si encontramos datos, salimos del loop
                break
            } else {
                Write-Host "      ℹ️  No hay facturas para esta placa" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ⚠️  Respuesta no esperada" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

# ==============================================================================
# 6. TEST: FILTROS OPCIONALES
# ==============================================================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🔧 TEST 3: Filtros Opcionales" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test con límite de resultados
Write-Host "📝 Test 3.1: Límite de resultados (limit=2)" -ForegroundColor Magenta
Write-Host "   Endpoint: GET $API_URL/history/payments/$($testPlacas[0])?limit=2" -ForegroundColor Gray
Write-Host ""

try {
    $response = curl -s "$API_URL/history/payments/$($testPlacas[0])?limit=2"
    $jsonResponse = $response | ConvertFrom-Json
    
    if ($jsonResponse.transactions) {
        $count = $jsonResponse.transactions.Count
        Write-Host "   ✅ Resultados limitados: $count transacciones" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  Sin transacciones" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Write-Host ""

# Test con filtro de estado
Write-Host "📄 Test 3.2: Filtrar facturas pendientes" -ForegroundColor Magenta
Write-Host "   Endpoint: GET $API_URL/history/invoices/$($testPlacas[0])?status=pendiente" -ForegroundColor Gray
Write-Host ""

try {
    $response = curl -s "$API_URL/history/invoices/$($testPlacas[0])?status=pendiente"
    $jsonResponse = $response | ConvertFrom-Json
    
    if ($jsonResponse.invoices) {
        $pendingCount = ($jsonResponse.invoices | Where-Object { $_.estado -eq "pendiente" }).Count
        Write-Host "   ✅ Facturas pendientes encontradas: $pendingCount" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  Sin facturas pendientes" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Write-Host ""

# ==============================================================================
# 7. TEST: PLACA SIN HISTORIAL
# ==============================================================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🔍 TEST 4: Placa Sin Historial" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$nonExistentPlaca = "P-NOEXISTE"

Write-Host "📝 Test 4.1: Pagos de placa sin historial" -ForegroundColor Magenta
Write-Host "   Endpoint: GET $API_URL/history/payments/$nonExistentPlaca" -ForegroundColor Gray
Write-Host ""

try {
    $response = curl -s "$API_URL/history/payments/$nonExistentPlaca"
    $jsonResponse = $response | ConvertFrom-Json
    
    if ($jsonResponse.total_transactions -eq 0) {
        Write-Host "   ✅ Respuesta correcta: No hay transacciones" -ForegroundColor Green
        Write-Host "      Mensaje: $($jsonResponse.message)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Write-Host ""

Write-Host "📄 Test 4.2: Facturas de placa sin historial" -ForegroundColor Magenta
Write-Host "   Endpoint: GET $API_URL/history/invoices/$nonExistentPlaca" -ForegroundColor Gray
Write-Host ""

try {
    $response = curl -s "$API_URL/history/invoices/$nonExistentPlaca"
    $jsonResponse = $response | ConvertFrom-Json
    
    if ($jsonResponse.summary.total_invoices -eq 0) {
        Write-Host "   ✅ Respuesta correcta: No hay facturas" -ForegroundColor Green
        Write-Host "      Mensaje: $($jsonResponse.message)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Write-Host ""

# ==============================================================================
# RESUMEN FINAL
# ==============================================================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "✅ TESTING COMPLETADO" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Endpoints probados:" -ForegroundColor White
Write-Host "   ✅ GET /history/payments/{placa}" -ForegroundColor Green
Write-Host "   ✅ GET /history/invoices/{placa}" -ForegroundColor Green
Write-Host "   ✅ Filtros opcionales (limit, status)" -ForegroundColor Green
Write-Host "   ✅ Manejo de placas sin historial" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Documentación completa en: README.md" -ForegroundColor Cyan
Write-Host ""

# ==============================================================================
# INFORMACIÓN ADICIONAL
# ==============================================================================
Write-Host "💡 Comandos útiles:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   # Ver logs de la función de pagos:" -ForegroundColor Gray
Write-Host "   aws logs tail /aws/lambda/guatepass-get-payments-by-plate-dev --follow" -ForegroundColor White
Write-Host ""
Write-Host "   # Ver logs de la función de facturas:" -ForegroundColor Gray
Write-Host "   aws logs tail /aws/lambda/guatepass-get-invoices-by-plate-dev --follow" -ForegroundColor White
Write-Host ""
Write-Host "   # Contar transacciones:" -ForegroundColor Gray
Write-Host "   aws dynamodb scan --table-name GuatepassTransactions-dev --select COUNT" -ForegroundColor White
Write-Host ""
Write-Host "   # Contar facturas:" -ForegroundColor Gray
Write-Host "   aws dynamodb scan --table-name GuatepassInvoices-dev --select COUNT" -ForegroundColor White
Write-Host ""
