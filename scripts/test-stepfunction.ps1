#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script de pruebas para Step Function de GuatePass (Slice #4)

.DESCRIPTION
    Ejecuta pruebas end-to-end del flujo completo de procesamiento de peajes.
    Envía eventos de peaje al webhook y verifica que la Step Function se ejecute correctamente.
#>

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "GUATEPASS - Test Step Function (Slice 4)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Obtener outputs del stack
Write-Host "[INFO] Obteniendo información del stack..." -ForegroundColor Yellow
$STACK_NAME = "guatepass-dev"

try {
    $stackOutputs = aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs" | ConvertFrom-Json
    
    $API_URL = ($stackOutputs | Where-Object { $_.OutputKey -eq "WebhookTollEndpoint" }).OutputValue
    $STATE_MACHINE_ARN = ($stackOutputs | Where-Object { $_.OutputKey -eq "StateMachineArn" }).OutputValue
    
    Write-Host "[OK] API URL: $API_URL" -ForegroundColor Green
    Write-Host "[OK] State Machine ARN: $STATE_MACHINE_ARN`n" -ForegroundColor Green
    
} catch {
    Write-Host "[ERROR] No se pudo obtener la información del stack" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Función para ejecutar tests
function Test-TollProcessing {
    param(
        [string]$TestName,
        [hashtable]$Payload,
        [string]$ExpectedModality
    )
    
    Write-Host "`n--- Test: $TestName ---" -ForegroundColor Cyan
    Write-Host "Payload: " -NoNewline
    Write-Host ($Payload | ConvertTo-Json -Compress) -ForegroundColor Gray
    
    try {
        # Enviar evento al webhook
        $response = Invoke-RestMethod -Uri $API_URL -Method Post -Body ($Payload | ConvertTo-Json) -ContentType "application/json"
        
        Write-Host "[OK] Evento enviado exitosamente" -ForegroundColor Green
        Write-Host "Event ID: $($response.event_id)" -ForegroundColor Gray
        
        # Esperar un momento para que se inicie la Step Function
        Start-Sleep -Seconds 3
        
        # Buscar la ejecución más reciente de la Step Function
        Write-Host "[INFO] Buscando ejecución de Step Function..." -ForegroundColor Yellow
        
        $executions = aws stepfunctions list-executions `
            --state-machine-arn $STATE_MACHINE_ARN `
            --max-results 1 `
            --query "executions[0]" | ConvertFrom-Json
        
        if ($executions) {
            $executionArn = $executions.executionArn
            $status = $executions.status
            
            Write-Host "[INFO] Ejecución encontrada: $($executions.name)" -ForegroundColor Gray
            Write-Host "[INFO] Estado: $status" -ForegroundColor Gray
            
            # Si está corriendo, esperar un poco más
            if ($status -eq "RUNNING") {
                Write-Host "[INFO] Esperando que termine la ejecución..." -ForegroundColor Yellow
                Start-Sleep -Seconds 5
                
                $execution = aws stepfunctions describe-execution `
                    --execution-arn $executionArn | ConvertFrom-Json
                
                $status = $execution.status
            }
            
            # Verificar resultado
            if ($status -eq "SUCCEEDED") {
                Write-Host "[SUCCESS] Step Function ejecutada correctamente" -ForegroundColor Green
                
                # Obtener output de la ejecución
                $execution = aws stepfunctions describe-execution `
                    --execution-arn $executionArn | ConvertFrom-Json
                
                $output = $execution.output | ConvertFrom-Json
                
                Write-Host "`nResultado:" -ForegroundColor Cyan
                Write-Host "  - Placa: $($output.user_data.placa)" -ForegroundColor White
                Write-Host "  - Modalidad: $($output.user_data.modalidad)" -ForegroundColor White
                Write-Host "  - Tarifa Base: Q$($output.fare_calculation.base_fare)" -ForegroundColor White
                Write-Host "  - Tarifa Final: Q$($output.fare_calculation.final_fare)" -ForegroundColor White
                Write-Host "  - Transaction ID: $($output.transaction.transaction_id)" -ForegroundColor White
                
                if ($output.balance_update.updated) {
                    Write-Host "  - Balance Anterior: Q$($output.balance_update.previous_balance)" -ForegroundColor White
                    Write-Host "  - Balance Nuevo: Q$($output.balance_update.new_balance)" -ForegroundColor White
                } else {
                    Write-Host "  - Balance: $($output.balance_update.message)" -ForegroundColor White
                }
                
                return $true
            } elseif ($status -eq "FAILED") {
                Write-Host "[ERROR] Step Function falló" -ForegroundColor Red
                
                # Obtener detalles del error
                $execution = aws stepfunctions describe-execution `
                    --execution-arn $executionArn | ConvertFrom-Json
                
                Write-Host "Error: $($execution.cause)" -ForegroundColor Red
                return $false
            } else {
                Write-Host "[WARNING] Ejecución aún en progreso: $status" -ForegroundColor Yellow
                return $false
            }
        } else {
            Write-Host "[WARNING] No se encontró ejecución de Step Function" -ForegroundColor Yellow
            return $false
        }
        
    } catch {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================
# TESTS
# ============================================

$testResults = @()

# Test 1: Usuario registrado CON tag (Modalidad 1)
$testResults += Test-TollProcessing -TestName "Usuario CON Tag (Modalidad 1)" `
    -Payload @{
        placa = "P123ABC"
        peaje_id = "PEAJE001"
        peaje_nombre = "carretera_norte"
        tag_id = "TAG-001"
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        lane_id = "LANE-01"
    } -ExpectedModality "1"

# Test 2: Usuario registrado SIN tag (Modalidad 2)
$testResults += Test-TollProcessing -TestName "Usuario SIN Tag (Modalidad 2)" `
    -Payload @{
        placa = "P999XYZ"
        peaje_id = "PEAJE001"
        peaje_nombre = "carretera_sur"
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        lane_id = "LANE-02"
    } -ExpectedModality "2"

# Test 3: Usuario NO registrado (Modalidad 3)
$testResults += Test-TollProcessing -TestName "Usuario NO registrado (Modalidad 3)" `
    -Payload @{
        placa = "NOREGISTRADO"
        peaje_id = "PEAJE001"
        peaje_nombre = "autopista_palin"
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        lane_id = "LANE-03"
    } -ExpectedModality "3"

# ============================================
# RESUMEN
# ============================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESUMEN DE PRUEBAS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passed = ($testResults | Where-Object { $_ -eq $true }).Count
$total = $testResults.Count

Write-Host "`nTests ejecutados: $total" -ForegroundColor White
Write-Host "Tests exitosos: $passed" -ForegroundColor Green
Write-Host "Tests fallidos: $($total - $passed)" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Red" })

if ($passed -eq $total) {
    Write-Host "`n[SUCCESS] Todas las pruebas pasaron correctamente!" -ForegroundColor Green
} else {
    Write-Host "`n[WARNING] Algunas pruebas fallaron. Revisar logs." -ForegroundColor Yellow
}

# Mostrar enlaces útiles
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ENLACES UTILES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ver Step Function en consola:" -ForegroundColor White
Write-Host "https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines" -ForegroundColor Blue

Write-Host "`nVer transacciones en DynamoDB:" -ForegroundColor White
Write-Host "aws dynamodb scan --table-name GuatepassTransactions-dev --max-items 10" -ForegroundColor Gray

Write-Host "`nVer logs de Step Function:" -ForegroundColor White
Write-Host "aws logs tail /aws/stepfunctions/guatepass-process-toll-dev --follow" -ForegroundColor Gray

Write-Host ""

