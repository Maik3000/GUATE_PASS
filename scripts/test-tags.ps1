# ========================================
# Script de Testing - Slice #5: Gestión de Tags
# ========================================

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "GUATEPASS - Test Slice #5: Gestión de Tags" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Obtener la URL de la API desde los outputs del stack
Write-Host "[1/7] Obteniendo información del stack..." -ForegroundColor Yellow
$API_URL = aws cloudformation describe-stacks `
    --stack-name guatepass-dev `
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
    --output text

if (-not $API_URL) {
    Write-Host "❌ Error: No se pudo obtener la URL de la API" -ForegroundColor Red
    Write-Host "Verifica que el stack 'guatepass-dev' esté desplegado correctamente." -ForegroundColor Red
    exit 1
}

Write-Host "✅ API URL: $API_URL" -ForegroundColor Green
Write-Host ""

# Variables de prueba (usando un usuario real de la base de datos)
$TEST_PLACA = "P-111JKL"  # Usuario: Ana Torres (sin tag)
$TEST_TAG_ID = "TAG-TEST-$(Get-Date -Format 'yyyyMMddHHmmss')"
$TEST_TAG_ID_2 = "TAG-TEST2-$(Get-Date -Format 'yyyyMMddHHmmss')"

# ========================================
# TEST 1: Verificar que el usuario existe
# ========================================
Write-Host "[2/7] TEST 1: Verificando que existe el usuario $TEST_PLACA..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_URL/users/$TEST_PLACA" -Method Get
    Write-Host "✅ Usuario encontrado: $($response.nombre)" -ForegroundColor Green
    Write-Host "   - Placa: $($response.placa)" -ForegroundColor Gray
    Write-Host "   - Tiene Tag: $($response.tiene_tag)" -ForegroundColor Gray
    
    if ($response.tiene_tag -eq $true) {
        Write-Host "⚠️  Usuario ya tiene tag: $($response.tag_id)" -ForegroundColor Yellow
        Write-Host "   Eliminando tag existente primero..." -ForegroundColor Yellow
        
        $deleteResponse = Invoke-RestMethod -Uri "$API_URL/users/$TEST_PLACA/tag" -Method Delete
        Write-Host "✅ Tag eliminado: $($deleteResponse.removed_tag_id)" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Error consultando usuario: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ========================================
# TEST 2: Crear/Asociar Tag (POST)
# ========================================
Write-Host "[3/7] TEST 2: Creando tag $TEST_TAG_ID..." -ForegroundColor Yellow

$createPayload = @{
    tag_id = $TEST_TAG_ID
    tag_status = "active"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod `
        -Uri "$API_URL/users/$TEST_PLACA/tag" `
        -Method Post `
        -Body $createPayload `
        -ContentType "application/json"
    
    Write-Host "✅ Tag creado exitosamente" -ForegroundColor Green
    Write-Host "   - Placa: $($response.placa)" -ForegroundColor Gray
    Write-Host "   - Tag ID: $($response.tag_id)" -ForegroundColor Gray
    Write-Host "   - Estado: $($response.tag_status)" -ForegroundColor Gray
    Write-Host "   - Fecha: $($response.updated_at)" -ForegroundColor Gray
}
catch {
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "❌ Error: $($errorDetails.message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ========================================
# TEST 3: Intentar crear tag duplicado (debe fallar)
# ========================================
Write-Host "[4/7] TEST 3: Intentando crear tag duplicado (debe fallar)..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod `
        -Uri "$API_URL/users/$TEST_PLACA/tag" `
        -Method Post `
        -Body $createPayload `
        -ContentType "application/json"
    
    Write-Host "❌ ERROR: No debería permitir crear tag duplicado" -ForegroundColor Red
}
catch {
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
    if ($errorDetails.error -eq "Usuario ya tiene tag") {
        Write-Host "✅ Validación correcta: $($errorDetails.message)" -ForegroundColor Green
        Write-Host "   - Hint: $($errorDetails.hint)" -ForegroundColor Gray
    }
    else {
        Write-Host "❌ Error inesperado: $($errorDetails.message)" -ForegroundColor Red
    }
}

Write-Host ""

# ========================================
# TEST 4: Consultar Tag por Placa (GET)
# ========================================
Write-Host "[5/7] TEST 4: Consultando tag por placa..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_URL/users/$TEST_PLACA/tag" -Method Get
    
    Write-Host "✅ Tag consultado exitosamente" -ForegroundColor Green
    Write-Host "   - Placa: $($response.placa)" -ForegroundColor Gray
    Write-Host "   - Tag ID: $($response.tag_id)" -ForegroundColor Gray
    Write-Host "   - Estado: $($response.tag_status)" -ForegroundColor Gray
    Write-Host "   - Usuario: $($response.nombre)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Error consultando tag: $_" -ForegroundColor Red
}

Write-Host ""

# ========================================
# TEST 5: Actualizar Tag (PUT)
# ========================================
Write-Host "[6/7] TEST 5: Actualizando tag..." -ForegroundColor Yellow

$updatePayload = @{
    tag_id = $TEST_TAG_ID_2
    tag_status = "inactive"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod `
        -Uri "$API_URL/users/$TEST_PLACA/tag" `
        -Method Put `
        -Body $updatePayload `
        -ContentType "application/json"
    
    Write-Host "✅ Tag actualizado exitosamente" -ForegroundColor Green
    Write-Host "   - Tag anterior: $($response.old_tag_id)" -ForegroundColor Gray
    Write-Host "   - Tag nuevo: $($response.new_tag_id)" -ForegroundColor Gray
    Write-Host "   - Estado anterior: $($response.old_status)" -ForegroundColor Gray
    Write-Host "   - Estado nuevo: $($response.new_status)" -ForegroundColor Gray
    Write-Host "   - Fecha: $($response.updated_at)" -ForegroundColor Gray
}
catch {
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "❌ Error: $($errorDetails.message)" -ForegroundColor Red
}

Write-Host ""

# ========================================
# TEST 6: Consultar Tag por Tag ID (GET /tags/{tag_id})
# ========================================
Write-Host "[7/7] TEST 6: Consultando usuario por Tag ID..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_URL/tags/$TEST_TAG_ID_2" -Method Get
    
    Write-Host "✅ Usuario encontrado por Tag ID" -ForegroundColor Green
    Write-Host "   - Tag ID: $($response.tag_id)" -ForegroundColor Gray
    Write-Host "   - Placa: $($response.user.placa)" -ForegroundColor Gray
    Write-Host "   - Nombre: $($response.user.nombre)" -ForegroundColor Gray
    Write-Host "   - Estado del Tag: $($response.tag_status)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Error consultando por Tag ID: $_" -ForegroundColor Red
}

Write-Host ""

# ========================================
# TEST 7: Eliminar Tag (DELETE)
# ========================================
Write-Host "OPCIONAL: Eliminar Tag (DELETE)" -ForegroundColor Yellow
$confirmDelete = Read-Host "¿Deseas eliminar el tag de prueba? (Y/N)"

if ($confirmDelete -eq "Y" -or $confirmDelete -eq "y") {
    Write-Host "Eliminando tag..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$API_URL/users/$TEST_PLACA/tag" `
            -Method Delete
        
        Write-Host "✅ Tag eliminado exitosamente" -ForegroundColor Green
        Write-Host "   - Placa: $($response.placa)" -ForegroundColor Gray
        Write-Host "   - Tag eliminado: $($response.removed_tag_id)" -ForegroundColor Gray
        Write-Host "   - Fecha: $($response.deleted_at)" -ForegroundColor Gray
        Write-Host "   - Nota: $($response.note)" -ForegroundColor Gray
    }
    catch {
        $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "❌ Error: $($errorDetails.message)" -ForegroundColor Red
    }
}
else {
    Write-Host "⏭️  Tag no eliminado. Puedes eliminarlo manualmente después." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "✅ Testing del Slice #5 completado" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resumen de endpoints probados:" -ForegroundColor White
Write-Host "  POST   /users/{placa}/tag       - Crear/Asociar tag" -ForegroundColor Gray
Write-Host "  GET    /users/{placa}/tag       - Consultar tag por placa" -ForegroundColor Gray
Write-Host "  PUT    /users/{placa}/tag       - Actualizar tag" -ForegroundColor Gray
Write-Host "  DELETE /users/{placa}/tag       - Eliminar tag" -ForegroundColor Gray
Write-Host "  GET    /tags/{tag_id}           - Consultar usuario por tag" -ForegroundColor Gray
Write-Host ""

