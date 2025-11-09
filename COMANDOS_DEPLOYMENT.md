# 🚀 GUATEPASS - Comandos de Deployment Slice #5

## 📋 Checklist Pre-Deployment

- [x] Todas las Lambdas creadas en `src/`
- [x] Template.yaml actualizado con nuevas funciones
- [x] Requirements.txt en cada directorio de Lambda
- [x] Log Groups configurados
- [x] Outputs definidos
- [x] Script de testing creado

## 🛠️ Deployment del Slice #5

### Paso 1: Validar el Template

```powershell
cd "C:\Users\Mayco\Desktop\UFM\semestre 10\cloud\Nueva carpeta\GUATE_PASS"
sam validate -t infrastructure/template.yaml
```

**Salida esperada:**
```
infrastructure/template.yaml is a valid SAM Template
```

---

### Paso 2: Build

```powershell
sam build -t infrastructure/template.yaml
```

**Salida esperada:**
```
Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml

Functions        : 12 functions
```

---

### Paso 3: Deploy

```powershell
sam deploy
```

Este comando:
- Usa la configuración guardada en `samconfig.toml`
- Actualiza el stack `guatepass-dev` existente
- Crea las nuevas funciones Lambda
- Configura los endpoints en API Gateway
- Crea los Log Groups

**Tiempo estimado:** 3-5 minutos

---

### Paso 4: Verificar Deployment

```powershell
# Ver outputs del stack (incluyendo nuevos endpoints)
aws cloudformation describe-stacks `
    --stack-name guatepass-dev `
    --query "Stacks[0].Outputs" `
    --output table
```

**Buscar estos outputs:**
- `CreateTagEndpoint`
- `UpdateTagEndpoint`
- `DeleteTagEndpoint`
- `GetTagByIdEndpoint`

---

### Paso 5: Verificar Funciones Lambda

```powershell
# Listar todas las funciones Lambda del proyecto
aws lambda list-functions `
    --query "Functions[?contains(FunctionName, 'guatepass')].FunctionName" `
    --output table
```

**Funciones nuevas esperadas:**
- `guatepass-create-tag-dev`
- `guatepass-update-tag-dev`
- `guatepass-delete-tag-dev`
- `guatepass-get-tag-by-id-dev`

---

### Paso 6: Verificar API Gateway

```powershell
# Obtener URL de la API
$API_URL = aws cloudformation describe-stacks `
    --stack-name guatepass-dev `
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
    --output text

Write-Host "API URL: $API_URL"
```

**Endpoints disponibles:**
```
GET    /users/{placa}           - Consultar usuario
GET    /users/{placa}/tag       - Consultar tag por placa
POST   /users/{placa}/tag       - Crear/asociar tag
PUT    /users/{placa}/tag       - Actualizar tag
DELETE /users/{placa}/tag       - Eliminar tag
GET    /tags/{tag_id}           - Consultar usuario por tag
POST   /webhook/toll            - Recibir eventos de peaje
```

---

### Paso 7: Testing Inicial

```powershell
# Test rápido: Consultar usuario existente
$API_URL = aws cloudformation describe-stacks `
    --stack-name guatepass-dev `
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
    --output text

Invoke-RestMethod -Uri "$API_URL/users/P123ABC" -Method Get
```

---

### Paso 8: Ejecutar Suite de Tests Completa

```powershell
.\scripts\test-tags.ps1
```

Este script probará:
1. ✅ Verificar usuario existente
2. ✅ Crear tag (POST)
3. ✅ Validar error de duplicado
4. ✅ Consultar tag por placa (GET)
5. ✅ Actualizar tag (PUT)
6. ✅ Consultar usuario por tag ID (GET)
7. ✅ Eliminar tag (DELETE)

---

## 🔍 Verificación de Logs

### Ver logs en tiempo real

```powershell
# Create Tag
aws logs tail /aws/lambda/guatepass-create-tag-dev --follow

# Update Tag
aws logs tail /aws/lambda/guatepass-update-tag-dev --follow

# Delete Tag
aws logs tail /aws/lambda/guatepass-delete-tag-dev --follow

# Get Tag by ID
aws logs tail /aws/lambda/guatepass-get-tag-by-id-dev --follow
```

### Ver logs de los últimos 10 minutos

```powershell
aws logs tail /aws/lambda/guatepass-create-tag-dev --since 10m
```

---

## 🧪 Tests Manuales Adicionales

### Test 1: Crear Tag con formato inválido (debe fallar)

```powershell
$API_URL = "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev"

$payload = @{
    tag_id = "INVALID-FORMAT"  # No empieza con TAG-
    tag_status = "active"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "$API_URL/users/P123ABC/tag" `
    -Method Post `
    -Body $payload `
    -ContentType "application/json"
```

**Resultado esperado:** Error 400 - Formato inválido

---

### Test 2: Actualizar solo el estado

```powershell
$payload = @{
    tag_status = "blocked"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "$API_URL/users/P123ABC/tag" `
    -Method Put `
    -Body $payload `
    -ContentType "application/json"
```

**Resultado esperado:** 200 OK - Estado actualizado

---

### Test 3: Consultar tag que no existe

```powershell
Invoke-RestMethod -Uri "$API_URL/tags/TAG-NOEXISTE" -Method Get
```

**Resultado esperado:** Error 404 - Tag no encontrado

---

## 📊 Monitoreo Post-Deployment

### CloudWatch Metrics

```powershell
# Ver invocaciones de CreateTag
aws cloudwatch get-metric-statistics `
    --namespace AWS/Lambda `
    --metric-name Invocations `
    --dimensions Name=FunctionName,Value=guatepass-create-tag-dev `
    --start-time (Get-Date).AddHours(-1).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss") `
    --end-time (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss") `
    --period 300 `
    --statistics Sum
```

### Ver errores

```powershell
aws logs filter-log-events `
    --log-group-name /aws/lambda/guatepass-create-tag-dev `
    --filter-pattern "ERROR" `
    --start-time $((Get-Date).AddHours(-1).Ticks / 10000)
```

---

## 🔄 Rollback (Si es necesario)

Si algo sale mal, puedes hacer rollback al stack anterior:

```powershell
# Ver historial de cambios
aws cloudformation describe-stack-events `
    --stack-name guatepass-dev `
    --max-items 20 `
    --output table

# Rollback al cambeset anterior
aws cloudformation cancel-update-stack --stack-name guatepass-dev
```

---

## 📝 Checklist Post-Deployment

- [ ] Todas las funciones Lambda desplegadas correctamente
- [ ] API Gateway endpoints respondiendo
- [ ] Tests automatizados pasando
- [ ] Logs visibles en CloudWatch
- [ ] Sin errores 5xx en las primeras invocaciones
- [ ] Documentación actualizada
- [ ] PROJECT_STATUS.md actualizado

---

## 🎉 ¡Deployment Completado!

El Slice #5 está ahora en producción (dev). Los usuarios pueden:
- ✅ Asociar tags a sus cuentas
- ✅ Actualizar información de tags
- ✅ Desasociar tags
- ✅ Consultar usuarios por Tag ID

**Siguiente paso:** Implementar Slice #6 (Notificaciones)

---

## 📞 Troubleshooting

### Error: "Stack does not exist"

**Solución:** Verifica el nombre del stack:
```powershell
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

### Error: "No changes to deploy"

**Solución:** Forza un nuevo deployment:
```powershell
sam deploy --force-upload
```

### Error: Lambda "ResourceConflictException"

**Solución:** La función ya existe. Actualiza con:
```powershell
sam deploy --no-fail-on-empty-changeset
```

---

**Última actualización:** Noviembre 9, 2025  
**Slice:** #5 - Gestión de Tags  
**Estado:** ✅ COMPLETADO

