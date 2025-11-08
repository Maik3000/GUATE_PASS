# Script para probar el endpoint del webhook de peajes
# Slice #3: Webhook de peajes

param(
    [string]$StackName = "guatepass-dev"
)

Write-Host "Probando Webhook de Peajes - GUATEPASS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Obtener URL de la API
Write-Host "Obteniendo URL del webhook..." -ForegroundColor Yellow

$WebhookUrl = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='WebhookTollEndpoint'].OutputValue" `
    --output text

if ([string]::IsNullOrEmpty($WebhookUrl)) {
    Write-Host "Error: No se pudo obtener la URL del webhook" -ForegroundColor Red
    exit 1
}

Write-Host "Webhook URL: $WebhookUrl" -ForegroundColor Green
Write-Host ""

# =======================================
# Test 1: Usuario con Tag
# =======================================
Write-Host "Test 1: Paso por peaje - Usuario con Tag (P-456DEF)" -ForegroundColor Yellow

$payload1 = @{
    placa = "P-456DEF"
    peaje_id = "PEAJE_ZONA10"
    tag_id = "TAG-001"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

Write-Host "Payload:" -ForegroundColor Gray
Write-Host $payload1 -ForegroundColor Gray
Write-Host ""

try {
    $response1 = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $payload1 -ContentType "application/json"
    Write-Host "Exito! Evento recibido:" -ForegroundColor Green
    Write-Host "  Event ID: $($response1.event_id)" -ForegroundColor White
    Write-Host "  Placa: $($response1.placa)" -ForegroundColor White
    Write-Host "  Peaje: $($response1.peaje_id)" -ForegroundColor White
    Write-Host "  Mensaje: $($response1.message)" -ForegroundColor White
} catch {
    Write-Host "Error en Test 1" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
Write-Host ""

# =======================================
# Test 2: Usuario SIN Tag
# =======================================
Write-Host "Test 2: Paso por peaje - Usuario sin Tag (P-123ABC)" -ForegroundColor Yellow

$payload2 = @{
    placa = "P-123ABC"
    peaje_id = "PEAJE_CALZADA_SUR"
    tag_id = $null
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

Write-Host "Payload:" -ForegroundColor Gray
Write-Host $payload2 -ForegroundColor Gray
Write-Host ""

try {
    $response2 = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $payload2 -ContentType "application/json"
    Write-Host "Exito! Evento recibido:" -ForegroundColor Green
    Write-Host "  Event ID: $($response2.event_id)" -ForegroundColor White
    Write-Host "  Placa: $($response2.placa)" -ForegroundColor White
    Write-Host "  Peaje: $($response2.peaje_id)" -ForegroundColor White
} catch {
    Write-Host "Error en Test 2" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
Write-Host ""

# =======================================
# Test 3: Usuario NO registrado
# =======================================
Write-Host "Test 3: Paso por peaje - Usuario NO registrado (P-999ZZZ)" -ForegroundColor Yellow

$payload3 = @{
    placa = "P-999ZZZ"
    peaje_id = "PEAJE_CARRETERA_SALVADOR"
    tag_id = $null
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

Write-Host "Payload:" -ForegroundColor Gray
Write-Host $payload3 -ForegroundColor Gray
Write-Host ""

try {
    $response3 = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $payload3 -ContentType "application/json"
    Write-Host "Exito! Evento recibido:" -ForegroundColor Green
    Write-Host "  Event ID: $($response3.event_id)" -ForegroundColor White
    Write-Host "  Placa: $($response3.placa)" -ForegroundColor White
    Write-Host "  Peaje: $($response3.peaje_id)" -ForegroundColor White
} catch {
    Write-Host "Error en Test 3" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
Write-Host ""

# =======================================
# Test 4: Payload invalido (sin placa)
# =======================================
Write-Host "Test 4: Payload invalido - debe dar error 400" -ForegroundColor Yellow

$payload4 = @{
    peaje_id = "PEAJE_ZONA10"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

try {
    $response4 = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $payload4 -ContentType "application/json"
    Write-Host "ERROR: Deberia haber dado error 400" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 400) {
        Write-Host "Exito! Error 400 devuelto correctamente" -ForegroundColor Green
        Write-Host "  Mensaje: Campo requerido faltante" -ForegroundColor White
    } else {
        Write-Host "Error inesperado: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    }
}
Write-Host ""

# =======================================
# Verificar EventBridge y Lambda
# =======================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Verificando procesamiento asincrono..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Esperando 3 segundos para que EventBridge procese..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Write-Host ""

# Ver logs de ResolveUserProfile
Write-Host "Logs de ResolveUserProfile (ultimos 2 minutos):" -ForegroundColor Cyan
Write-Host "Para ver logs detallados ejecuta:" -ForegroundColor White
Write-Host "  sam logs -n ResolveUserProfileFunction --stack-name $StackName --start-time '2m ago'" -ForegroundColor Yellow
Write-Host ""

# =======================================
# Resumen
# =======================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Pruebas del webhook completadas!" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoint disponible:" -ForegroundColor Cyan
Write-Host "  POST $WebhookUrl" -ForegroundColor White
Write-Host ""
Write-Host "Flujo completo:" -ForegroundColor Cyan
Write-Host "  1. Webhook recibe evento → IngestToll Lambda" -ForegroundColor White
Write-Host "  2. Evento publicado → EventBridge Bus" -ForegroundColor White
Write-Host "  3. EventBridge dispara → ResolveUserProfile Lambda" -ForegroundColor White
Write-Host "  4. Modalidad determinada y loggeada" -ForegroundColor White
Write-Host ""
Write-Host "Siguiente paso: Implementar Step Functions (Slice #4) para procesar el cobro" -ForegroundColor Yellow
Write-Host ""

