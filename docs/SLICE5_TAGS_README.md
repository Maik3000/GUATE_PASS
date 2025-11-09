# 🏷️ GUATEPASS - Slice #5: Gestión de Tags

## 📋 Descripción General

El **Slice #5** implementa la **gestión completa de Tags** para usuarios del sistema GUATEPASS. Los Tags son dispositivos físicos (como tarjetas RFID o stickers) que permiten identificación automática de vehículos en los peajes.

## 🎯 Objetivos del Slice #5

- ✅ Permitir crear/asociar Tags a usuarios registrados
- ✅ Actualizar información de Tags existentes
- ✅ Desasociar Tags de usuarios
- ✅ Consultar usuarios por Tag ID (usando GSI)
- ✅ Validar unicidad de Tags (no duplicados)
- ✅ Mantener trazabilidad de cambios (timestamps)

## 🏗️ Arquitectura

```
┌─────────────────────┐
│   API Gateway       │
│   /users/{placa}/tag│
└──────────┬──────────┘
           │
     ┌─────┴─────┬─────────┬─────────┐
     │           │         │         │
     ▼           ▼         ▼         ▼
┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ CREATE  │ │  GET   │ │ UPDATE │ │ DELETE │
│   Tag   │ │  Tag   │ │  Tag   │ │  Tag   │
│ Lambda  │ │ Lambda │ │ Lambda │ │ Lambda │
└────┬────┘ └────┬───┘ └────┬───┘ └────┬───┘
     │           │          │          │
     └───────────┴──────────┴──────────┘
                 │
                 ▼
         ┌───────────────┐
         │  DynamoDB     │
         │ GuatepassUsers│
         │  + TagIndex   │
         └───────────────┘
```

## 📦 Componentes Implementados

### 1. **Lambda: CreateTagFunction**

Asocia un Tag a un usuario registrado.

**Endpoint:** `POST /users/{placa}/tag`

**Request Body:**
```json
{
  "tag_id": "TAG-12345",
  "tag_status": "active"
}
```

**Response (200 OK):**
```json
{
  "message": "Tag asociado exitosamente",
  "placa": "P123ABC",
  "tag_id": "TAG-12345",
  "tag_status": "active",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Validaciones:**
- ✅ Usuario debe existir en DynamoDB
- ✅ Usuario no debe tener un tag asociado previamente
- ✅ Tag ID debe comenzar con "TAG-"
- ✅ Tag ID no debe estar en uso por otro usuario

**Errores:**
- `400`: Placa o Tag ID no proporcionado, formato inválido
- `404`: Usuario no encontrado
- `409`: Usuario ya tiene tag o Tag ID duplicado

---

### 2. **Lambda: GetTagByPlacaFunction**

Consulta información del Tag asociado a una placa.

**Endpoint:** `GET /users/{placa}/tag`

**Response (200 OK):**
```json
{
  "placa": "P123ABC",
  "tag_id": "TAG-12345",
  "tag_status": "active",
  "tag_created_at": "2024-01-15T10:30:00Z",
  "nombre": "Juan Pérez",
  "tipo_usuario": "registrado",
  "saldo_disponible": "100.00"
}
```

**Errores:**
- `404`: Usuario no encontrado o no tiene tag

---

### 3. **Lambda: UpdateTagFunction**

Actualiza la información del Tag de un usuario.

**Endpoint:** `PUT /users/{placa}/tag`

**Request Body (ambos campos opcionales, al menos uno requerido):**
```json
{
  "tag_id": "TAG-67890",
  "tag_status": "inactive"
}
```

**Estados válidos:** `active`, `inactive`, `blocked`, `lost`, `stolen`

**Response (200 OK):**
```json
{
  "message": "Tag actualizado exitosamente",
  "placa": "P123ABC",
  "old_tag_id": "TAG-12345",
  "new_tag_id": "TAG-67890",
  "old_status": "active",
  "new_status": "inactive",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Validaciones:**
- ✅ Usuario debe existir
- ✅ Usuario debe tener un tag asociado
- ✅ Si se cambia tag_id, el nuevo no debe estar en uso
- ✅ Al menos un campo debe ser proporcionado

**Errores:**
- `400`: Sin datos para actualizar, formato inválido
- `404`: Usuario no encontrado o no tiene tag
- `409`: Nuevo Tag ID ya está en uso

---

### 4. **Lambda: DeleteTagFunction**

Desasocia un Tag de un usuario.

**Endpoint:** `DELETE /users/{placa}/tag`

**Response (200 OK):**
```json
{
  "message": "Tag desasociado exitosamente",
  "placa": "P123ABC",
  "removed_tag_id": "TAG-12345",
  "deleted_at": "2024-01-15T12:00:00Z",
  "note": "El usuario puede volver a asociar un tag usando POST /users/{placa}/tag"
}
```

**Comportamiento:**
- Marca `tiene_tag` como `false`
- Limpia `tag_id` (cadena vacía)
- Registra `tag_deleted_at` para auditoría

**Errores:**
- `404`: Usuario no encontrado o no tiene tag

---

### 5. **Lambda: GetTagFunction**

Consulta información de un usuario por su Tag ID (búsqueda inversa).

**Endpoint:** `GET /tags/{tag_id}`

**Response (200 OK):**
```json
{
  "tag_id": "TAG-12345",
  "tag_status": "active",
  "tag_created_at": "2024-01-15T10:30:00Z",
  "user": {
    "placa": "P123ABC",
    "nombre": "Juan Pérez",
    "email": "juan@email.com",
    "telefono": "50212345678",
    "tipo_usuario": "registrado",
    "saldo_disponible": "100.00",
    "estado": "activo"
  }
}
```

**Implementación:**
- Usa el índice secundario global `TagIndex` de DynamoDB
- Permite búsqueda eficiente por Tag ID

**Errores:**
- `404`: Tag no encontrado

---

## 🗄️ Cambios en DynamoDB

### Nuevos Atributos en GuatepassUsers:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `tiene_tag` | Boolean | Indica si el usuario tiene tag asociado |
| `tag_id` | String | ID del tag (GSI Key) |
| `tag_status` | String | Estado: active, inactive, blocked, lost, stolen |
| `tag_created_at` | String (ISO 8601) | Fecha de creación del tag |
| `tag_updated_at` | String (ISO 8601) | Fecha de última actualización |
| `tag_deleted_at` | String (ISO 8601) | Fecha de eliminación (auditoría) |

### Índice Secundario Global (GSI):

**TagIndex:**
- Partition Key: `tag_id`
- Projection: ALL
- Permite consultar usuarios por Tag ID en O(1)

---

## 🚀 Deployment

### Paso 1: Build del proyecto

```powershell
cd C:\Users\Mayco\Desktop\UFM\semestre 10\cloud\Nueva carpeta\GUATE_PASS
sam build -t infrastructure/template.yaml
```

### Paso 2: Deploy

```powershell
sam deploy
```

Esto actualizará el stack `guatepass-dev` con las nuevas funciones Lambda.

### Paso 3: Verificar Deployment

```powershell
# Ver outputs del stack
aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs"

# Verificar funciones Lambda
aws lambda list-functions --query "Functions[?contains(FunctionName, 'tag')].FunctionName"
```

---

## 🧪 Testing

### Opción 1: Script Automatizado (Recomendado)

```powershell
.\scripts\test-tags.ps1
```

Este script ejecuta una suite completa de tests:
1. ✅ Verifica que existe el usuario de prueba
2. ✅ Crea un tag (POST)
3. ✅ Valida error de tag duplicado
4. ✅ Consulta tag por placa (GET)
5. ✅ Actualiza tag (PUT)
6. ✅ Consulta usuario por tag ID (GET)
7. ✅ Opcionalmente elimina tag (DELETE)

### Opción 2: Testing Manual

#### Test 1: Crear Tag

```powershell
$API_URL = "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev"

$payload = @{
    tag_id = "TAG-TEST-001"
    tag_status = "active"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "$API_URL/users/P123ABC/tag" `
    -Method Post `
    -Body $payload `
    -ContentType "application/json"
```

#### Test 2: Consultar Tag por Placa

```powershell
Invoke-RestMethod -Uri "$API_URL/users/P123ABC/tag" -Method Get
```

#### Test 3: Actualizar Tag

```powershell
$payload = @{
    tag_status = "inactive"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "$API_URL/users/P123ABC/tag" `
    -Method Put `
    -Body $payload `
    -ContentType "application/json"
```

#### Test 4: Consultar Usuario por Tag ID

```powershell
Invoke-RestMethod -Uri "$API_URL/tags/TAG-TEST-001" -Method Get
```

#### Test 5: Eliminar Tag

```powershell
Invoke-RestMethod -Uri "$API_URL/users/P123ABC/tag" -Method Delete
```

---

## 📊 Monitoreo

### CloudWatch Logs

Ver logs de cada Lambda:

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

### Métricas en CloudWatch

- **Invocations**: Número de llamadas a cada endpoint
- **Errors**: Errores durante la ejecución
- **Duration**: Tiempo de respuesta
- **4xx Errors**: Validaciones fallidas
- **5xx Errors**: Errores del servidor

---

## 🔍 Troubleshooting

### Problem 1: "Usuario ya tiene tag"

**Síntoma:** Error 409 al intentar crear un tag

**Solución:**
1. Verificar si el usuario tiene tag:
```powershell
Invoke-RestMethod -Uri "$API_URL/users/P123ABC/tag" -Method Get
```
2. Eliminar el tag existente primero:
```powershell
Invoke-RestMethod -Uri "$API_URL/users/P123ABC/tag" -Method Delete
```
3. O actualizar el tag existente:
```powershell
Invoke-RestMethod -Uri "$API_URL/users/P123ABC/tag" -Method Put -Body $payload
```

### Problem 2: "Tag ya está en uso"

**Síntoma:** Error 409 al crear o actualizar con un Tag ID existente

**Solución:**
1. Consultar quién tiene ese tag:
```powershell
Invoke-RestMethod -Uri "$API_URL/tags/TAG-12345" -Method Get
```
2. Elegir otro Tag ID único

### Problem 3: "Usuario no tiene tag"

**Síntoma:** Error 404 al intentar actualizar o eliminar

**Solución:**
1. Verificar el estado del usuario:
```powershell
Invoke-RestMethod -Uri "$API_URL/users/P123ABC" -Method Get
```
2. Crear un tag primero usando POST

### Problem 4: Lambda timeout o error 500

**Síntoma:** Error 500 o Lambda timeout

**Diagnóstico:**
```powershell
# Ver logs recientes
aws logs tail /aws/lambda/guatepass-create-tag-dev --since 5m

# Ver errores específicos
aws logs filter-log-events `
  --log-group-name /aws/lambda/guatepass-create-tag-dev `
  --filter-pattern "ERROR"
```

**Soluciones comunes:**
- Verificar permisos IAM de la Lambda
- Verificar que la tabla DynamoDB existe
- Verificar que el índice TagIndex está activo

---

## 🎓 Decisiones de Diseño

### ¿Por qué usar GSI (TagIndex)?

✅ **Elegido:** Global Secondary Index en `tag_id`  
❌ Descartado: Scan completo de la tabla  
❌ Descartado: Tabla separada de Tags

**Justificación:**
- Consultas O(1) por Tag ID (muy eficiente)
- No requiere tabla adicional (simplifica arquitectura)
- DynamoDB maneja la consistencia del índice automáticamente
- Costo marginal mínimo en modo PAY_PER_REQUEST

### ¿Por qué soft delete en lugar de hard delete?

✅ **Elegido:** Marcar `tiene_tag = false` y guardar `tag_deleted_at`  
❌ Descartado: Eliminar completamente el atributo

**Justificación:**
- Mantener auditoría (cuándo se eliminó)
- Permitir análisis histórico
- Facilitar restauración si es necesario
- No afecta la lógica de negocio (se valida `tiene_tag`)

### ¿Por qué validar formato TAG-*?

✅ **Elegido:** Prefijo obligatorio "TAG-"  
❌ Descartado: Cualquier formato

**Justificación:**
- Evita confusión con otros identificadores (placas, IDs de usuario)
- Facilita búsquedas y filtros
- Estándar de la industria de peajes
- Validación simple y efectiva

---

## 🔗 Integración con Otros Slices

### Slice #3: Webhook de Peajes
- El webhook puede recibir `tag_id` en el payload
- `ResolveUserProfileFunction` puede buscar usuario por Tag ID

### Slice #4: Step Functions
- La Step Function usa `has_tag` para determinar modalidad
- Modalidad 1 (con tag) tiene tarifa sin recargo

### Slice #6: Notificaciones (Futuro)
- Notificar al usuario cuando se crea/actualiza/elimina tag
- Alertar si tag cambia a estado "lost" o "stolen"

---

## 📈 Métricas de Éxito

### KPIs del Slice #5

✅ **Latencia**: < 200ms para operaciones CRUD  
✅ **Disponibilidad**: > 99.9%  
✅ **Error Rate**: < 1%  
✅ **Validaciones**: 100% de tags únicos  

### Testing Realizado

| Test | Estado | Resultado |
|------|--------|-----------|
| Crear tag nuevo | ✅ | Exitoso |
| Validar tag duplicado | ✅ | Rechazado correctamente |
| Actualizar tag existente | ✅ | Exitoso |
| Eliminar tag | ✅ | Exitoso |
| Consultar por Tag ID | ✅ | Exitoso |
| Validar formato inválido | ✅ | Rechazado correctamente |

---

## 📚 Referencias

- [DynamoDB Global Secondary Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)
- [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

---

## 🏆 Logros del Slice #5

✅ **CRUD Completo**: Create, Read, Update, Delete de Tags  
✅ **Validaciones Robustas**: Prevención de duplicados y estados inválidos  
✅ **Búsqueda Bidireccional**: Por placa o por Tag ID  
✅ **Auditoría**: Timestamps de creación, actualización y eliminación  
✅ **Testing Automatizado**: Script PowerShell completo  
✅ **Documentación**: README técnico y comentarios en código  

---

**Slice #5 completado** 🎉  
Ahora GuatePass tiene gestión completa de Tags, permitiendo a usuarios asociar dispositivos RFID para paso automático por peajes.

**Siguiente paso:** Slice #6 - Notificaciones (SNS, emails, SMS)

