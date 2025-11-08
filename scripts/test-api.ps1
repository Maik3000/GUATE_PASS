# Script para probar los endpoints de la API de GUATEPASS
# Slice #2: API de consulta de usuarios

param(
    [string]$StackName = "guatepass-dev"
)

Write-Host "Probando API de GUATEPASS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Obtener URL base de la API
Write-Host "Obteniendo URL de la API..." -ForegroundColor Yellow

$ApiUrl = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
    --output text

if ([string]::IsNullOrEmpty($ApiUrl)) {
    Write-Host "Error: No se pudo obtener la URL de la API" -ForegroundColor Red
    Write-Host "Asegurate de que el stack '$StackName' esta desplegado con el Slice #2" -ForegroundColor Red
    exit 1
}

Write-Host "API URL: $ApiUrl" -ForegroundColor Green
Write-Host ""

# =======================================
# Test 1: GET /users/{placa} - Usuario con Tag
# =======================================
Write-Host "Test 1: Consultar usuario P-456DEF (tiene Tag)" -ForegroundColor Yellow
Write-Host "GET $ApiUrl/users/P-456DEF" -ForegroundColor Gray

$response1 = curl.exe -s -X GET "$ApiUrl/users/P-456DEF"
$json1 = $response1 | ConvertFrom-Json

if ($json1.user) {
    Write-Host "Exito! Usuario encontrado:" -ForegroundColor Green
    Write-Host "  Placa: $($json1.user.placa)" -ForegroundColor White
    Write-Host "  Nombre: $($json1.user.nombre)" -ForegroundColor White
    Write-Host "  Email: $($json1.user.email)" -ForegroundColor White
    Write-Host "  Tiene Tag: $($json1.user.tiene_tag)" -ForegroundColor White
    Write-Host "  Tag ID: $($json1.user.tag_id)" -ForegroundColor White
    Write-Host "  Saldo: Q$($json1.user.saldo_disponible)" -ForegroundColor White
} else {
    Write-Host "Error en Test 1" -ForegroundColor Red
    Write-Host $response1 -ForegroundColor Red
}
Write-Host ""

# =======================================
# Test 2: GET /users/{placa} - Usuario sin Tag
# =======================================
Write-Host "Test 2: Consultar usuario P-123ABC (sin Tag)" -ForegroundColor Yellow
Write-Host "GET $ApiUrl/users/P-123ABC" -ForegroundColor Gray

$response2 = curl.exe -s -X GET "$ApiUrl/users/P-123ABC"
$json2 = $response2 | ConvertFrom-Json

if ($json2.user) {
    Write-Host "Exito! Usuario encontrado:" -ForegroundColor Green
    Write-Host "  Placa: $($json2.user.placa)" -ForegroundColor White
    Write-Host "  Nombre: $($json2.user.nombre)" -ForegroundColor White
    Write-Host "  Email: $($json2.user.email)" -ForegroundColor White
    Write-Host "  Tiene Tag: $($json2.user.tiene_tag)" -ForegroundColor White
    Write-Host "  Saldo: Q$($json2.user.saldo_disponible)" -ForegroundColor White
} else {
    Write-Host "Error en Test 2" -ForegroundColor Red
    Write-Host $response2 -ForegroundColor Red
}
Write-Host ""

# =======================================
# Test 3: GET /users/{placa}/tag - Usuario con Tag
# =======================================
Write-Host "Test 3: Consultar Tag de usuario P-456DEF" -ForegroundColor Yellow
Write-Host "GET $ApiUrl/users/P-456DEF/tag" -ForegroundColor Gray

$response3 = curl.exe -s -X GET "$ApiUrl/users/P-456DEF/tag"
$json3 = $response3 | ConvertFrom-Json

if ($json3.tag) {
    Write-Host "Exito! Tag encontrado:" -ForegroundColor Green
    Write-Host "  Placa: $($json3.tag.placa)" -ForegroundColor White
    Write-Host "  Tiene Tag: $($json3.tag.tiene_tag)" -ForegroundColor White
    Write-Host "  Tag ID: $($json3.tag.tag_id)" -ForegroundColor White
    Write-Host "  Saldo: Q$($json3.tag.saldo_disponible)" -ForegroundColor White
} else {
    Write-Host "Error en Test 3" -ForegroundColor Red
    Write-Host $response3 -ForegroundColor Red
}
Write-Host ""

# =======================================
# Test 4: GET /users/{placa}/tag - Usuario sin Tag
# =======================================
Write-Host "Test 4: Consultar Tag de usuario P-123ABC (sin Tag)" -ForegroundColor Yellow
Write-Host "GET $ApiUrl/users/P-123ABC/tag" -ForegroundColor Gray

$response4 = curl.exe -s -X GET "$ApiUrl/users/P-123ABC/tag"
$json4 = $response4 | ConvertFrom-Json

if ($json4.tiene_tag -eq $false) {
    Write-Host "Exito! Usuario sin Tag detectado correctamente:" -ForegroundColor Green
    Write-Host "  Placa: $($json4.placa)" -ForegroundColor White
    Write-Host "  Tiene Tag: $($json4.tiene_tag)" -ForegroundColor White
    Write-Host "  Mensaje: $($json4.message)" -ForegroundColor White
} else {
    Write-Host "Error en Test 4" -ForegroundColor Red
    Write-Host $response4 -ForegroundColor Red
}
Write-Host ""

# =======================================
# Test 5: GET /users/{placa} - Usuario inexistente (404)
# =======================================
Write-Host "Test 5: Consultar usuario inexistente P-999ZZZ (debe dar 404)" -ForegroundColor Yellow
Write-Host "GET $ApiUrl/users/P-999ZZZ" -ForegroundColor Gray

$response5 = curl.exe -s -X GET "$ApiUrl/users/P-999ZZZ"
$json5 = $response5 | ConvertFrom-Json

if ($json5.statusCode -eq 404) {
    Write-Host "Exito! Error 404 devuelto correctamente:" -ForegroundColor Green
    Write-Host "  Error: $($json5.error)" -ForegroundColor White
} else {
    Write-Host "Error en Test 5 - Se esperaba 404" -ForegroundColor Red
    Write-Host $response5 -ForegroundColor Red
}
Write-Host ""

# =======================================
# Resumen
# =======================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Pruebas completadas!" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoints disponibles:" -ForegroundColor Cyan
Write-Host "  GET $ApiUrl/users/{placa}" -ForegroundColor White
Write-Host "  GET $ApiUrl/users/{placa}/tag" -ForegroundColor White
Write-Host ""
Write-Host "Prueba manualmente con curl:" -ForegroundColor Cyan
Write-Host "  curl $ApiUrl/users/P-123ABC" -ForegroundColor White
Write-Host ""

