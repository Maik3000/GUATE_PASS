# 🔌 GUATEPASS - Slice #2: API de Consulta

Documentación del API REST para consultar información de usuarios y tags.

---

## 🎯 Descripción

El Slice #2 implementa una API REST serverless que permite consultar la información de usuarios almacenada en DynamoDB desde el Slice #1.

### Componentes

✅ **API Gateway** - Endpoint REST público  
✅ **Lambda GetUserByPlaca** - Consulta usuario por placa  
✅ **Lambda GetTagByPlaca** - Consulta tag asociado  
✅ **DynamoDB** - Usa la tabla `GuatepassUsers` del Slice #1  

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

### 1. GET /users/{placa}

Consulta la información completa de un usuario por su placa.

**Request:**
```bash
GET /users/P-123ABC
```

**Response exitoso (200):**
```json
{
  "user": {
    "placa": "P-123ABC",
    "nombre": "Juan Pérez",
    "email": "juan@email.com",
    "telefono": "50212345678",
    "tipo_usuario": "registrado",
    "tiene_tag": false,
    "saldo_disponible": 100.0,
    "estado": "activo"
  },
  "message": "Usuario P-123ABC encontrado exitosamente"
}
```

**Response error (404):**
```json
{
  "error": "Usuario con placa P-999ZZZ no encontrado",
  "statusCode": 404
}
```

---

### 2. GET /users/{placa}/tag

Consulta la información del Tag asociado a una placa.

**Request:**
```bash
GET /users/P-456DEF/tag
```

**Response - Usuario con Tag (200):**
```json
{
  "tag": {
    "placa": "P-456DEF",
    "tiene_tag": true,
    "tag_id": "TAG-001",
    "nombre": "María López",
    "email": "maria@email.com",
    "telefono": "50298765432",
    "saldo_disponible": 250.0,
    "estado": "activo"
  },
  "message": "Tag encontrado para vehículo P-456DEF"
}
```

**Response - Usuario sin Tag (200):**
```json
{
  "placa": "P-123ABC",
  "tiene_tag": false,
  "tag_id": null,
  "message": "El vehículo P-123ABC no tiene dispositivo Tag asociado"
}
```

**Response error (404):**
```json
{
  "error": "Usuario con placa P-999ZZZ no encontrado",
  "statusCode": 404
}
```

---

## 🚀 Despliegue

### Prerequisitos

- Slice #1 debe estar desplegado (tabla DynamoDB con datos)
- AWS CLI configurado
- SAM CLI instalado

### Pasos

```powershell
cd "C:\Users\Mayco\Documents\GitHub\GUATE_PASS"

# 1. Build
sam build -t infrastructure/template.yaml

# 2. Deploy (actualiza el mismo stack)
sam deploy

# 3. Obtener URL de la API
aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
```

---

## 🧪 Pruebas

### Script Automatizado

```powershell
.\scripts\test-api.ps1
```

Este script ejecuta 5 tests automáticos:
1. ✅ Usuario con Tag
2. ✅ Usuario sin Tag
3. ✅ Consulta Tag (usuario con Tag)
4. ✅ Consulta Tag (usuario sin Tag)
5. ✅ Usuario inexistente (404)

### Pruebas Manuales con curl

```powershell
# Obtener URL
$API_URL = aws cloudformation describe-stacks --stack-name guatepass-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text

# Test 1: Usuario con Tag
curl "$API_URL/users/P-456DEF"

# Test 2: Usuario sin Tag
curl "$API_URL/users/P-123ABC"

# Test 3: Consultar Tag (con Tag)
curl "$API_URL/users/P-456DEF/tag"

# Test 4: Consultar Tag (sin Tag)
curl "$API_URL/users/P-123ABC/tag"

# Test 5: Usuario inexistente
curl "$API_URL/users/P-999ZZZ"
```

### Pruebas con Postman

1. Importa collection (puedes crearla manualmente)
2. Variable de entorno: `{{API_URL}}` = tu URL base
3. Requests:
   - GET `{{API_URL}}/users/P-123ABC`
   - GET `{{API_URL}}/users/P-456DEF/tag`

---

## 📊 Monitoreo

### Ver Logs

```powershell
# Logs de GetUserByPlaca
sam logs -n GetUserByPlacaFunction --stack-name guatepass-dev --tail

# Logs de GetTagByPlaca
sam logs -n GetTagByPlacaFunction --stack-name guatepass-dev --tail

# Logs de API Gateway
aws logs tail /aws/apigateway/guatepass-api-dev --follow
```

### Métricas de CloudWatch

```powershell
# Invocaciones de API Gateway
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=guatepass-api-dev \
  --start-time $(Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") \
  --end-time $(Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") \
  --period 300 \
  --statistics Sum
```

---

## 🔒 Seguridad

### CORS

La API tiene CORS habilitado:
- **AllowOrigin:** `*` (cualquier origen - ajustar en producción)
- **AllowMethods:** GET, POST, PUT, DELETE, OPTIONS
- **AllowHeaders:** Content-Type, Authorization, etc.

### Autenticación

**Actual:** Sin autenticación (público)

**Recomendación para producción:**
- API Key
- AWS Cognito
- IAM Authorization

---

## ⚡ Performance

### Latencias Esperadas

| Endpoint | Latencia Típica |
|----------|-----------------|
| GET /users/{placa} | 50-150ms |
| GET /users/{placa}/tag | 50-150ms |

### Límites

- **API Gateway:** 10,000 requests/segundo (burst)
- **Lambda:** 1,000 ejecuciones concurrentes (default)
- **DynamoDB:** PAY_PER_REQUEST (sin límite práctico)

---

## 🐛 Troubleshooting

### Error: "Usuario no encontrado" pero el usuario existe

**Causa:** Placa en minúsculas o con espacios.

**Solución:** La API normaliza a mayúsculas, pero verifica:
```powershell
aws dynamodb get-item --table-name GuatepassUsers-dev --key '{"placa": {"S": "P-123ABC"}}'
```

### Error 500: "Error interno"

**Diagnóstico:**
```powershell
sam logs -n GetUserByPlacaFunction --stack-name guatepass-dev --start-time '10m ago'
```

**Causas comunes:**
- Tabla DynamoDB no existe
- Permisos IAM incorrectos
- Variable de entorno `USERS_TABLE_NAME` mal configurada

### API Gateway devuelve 403

**Causa:** Posible problema con permisos de Lambda.

**Solución:**
```powershell
# Verificar permisos
aws lambda get-policy --function-name guatepass-get-user-dev
```

---

## 📚 Ejemplos de Uso

### Integración en Frontend (JavaScript)

```javascript
const API_URL = 'https://xxx.execute-api.us-east-1.amazonaws.com/dev';

// Consultar usuario
async function getUser(placa) {
  const response = await fetch(`${API_URL}/users/${placa}`);
  const data = await response.json();
  
  if (response.ok) {
    console.log('Usuario:', data.user);
  } else {
    console.error('Error:', data.error);
  }
}

// Consultar tag
async function getTag(placa) {
  const response = await fetch(`${API_URL}/users/${placa}/tag`);
  const data = await response.json();
  
  if (data.tiene_tag) {
    console.log('Tag ID:', data.tag.tag_id);
  } else {
    console.log('Usuario sin tag');
  }
}

// Usar
getUser('P-123ABC');
getTag('P-456DEF');
```

---

## 🔄 Próximos Pasos

Una vez que el Slice #2 esté funcionando:

- ✅ **Slice #3:** Webhook de peajes (POST /webhook/toll)
- ✅ **Slice #4:** Step Functions para procesamiento
- ✅ **Slice #5:** Endpoints CRUD de tags
- ✅ **Slice #6:** Sistema de notificaciones

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs de Lambda
2. Verifica que la tabla DynamoDB tiene datos
3. Confirma que la URL de API es correcta
4. Revisa los outputs del stack CloudFormation

---

**Slice #2 COMPLETADO** ✅  
**Fecha:** Noviembre 2025

