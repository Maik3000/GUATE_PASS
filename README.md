# 🚗 GUATEPASS - Sistema de Cobro Automatizado de Peajes

Sistema serverless para el cobro automatizado de peajes en la Ciudad de Guatemala, construido 100% con servicios administrados de AWS.

---

## 📋 Tabla de Contenidos

- [Estado del Proyecto](#estado-del-proyecto)
- [Arquitectura](#arquitectura)
- [Prerrequisitos](#prerrequisitos)
- [Instalación y Despliegue](#instalación-y-despliegue)
- [Uso del Sistema](#uso-del-sistema)
- [Monitoreo](#monitoreo)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Estado del Proyecto

### ✅ Slice #1: Carga Inicial de Datos (COMPLETADO)

Componentes implementados:
- ✅ Bucket S3 para almacenamiento de datos iniciales
- ✅ Tabla DynamoDB `GuatepassUsers`
- ✅ Lambda `ImportUsersFunction` con trigger S3
- ✅ Dashboard de CloudWatch
- ✅ Alarmas de monitoreo
- ✅ Infrastructure as Code (SAM)

### 🔜 Próximos Slices

- ⏳ Slice #2: API de Consulta de Usuarios
- ⏳ Slice #3: Webhook de Peajes y EventBridge
- ⏳ Slice #4: Procesamiento de Transacciones con Step Functions
- ⏳ Slice #5: Gestión de Tags
- ⏳ Slice #6: Notificaciones

---

## 🏗️ Arquitectura

### Slice #1: Carga Inicial de Datos

```
┌─────────────────┐
│  data/          │
│  clientes.csv   │
└────────┬────────┘
         │ (upload manual)
         ▼
┌─────────────────────────────┐
│  S3 Bucket                  │
│  guatepass-data-{env}       │
└────────┬────────────────────┘
         │ (trigger S3:ObjectCreated)
         ▼
┌─────────────────────────────┐
│  Lambda                     │
│  ImportUsersFunction        │
│  - Parse CSV                │
│  - Validate data            │
│  - Batch write              │
└────────┬────────────────────┘
         │ (batch write)
         ▼
┌─────────────────────────────┐
│  DynamoDB                   │
│  GuatepassUsers             │
│  PK: placa                  │
│  GSI: tag_id                │
└─────────────────────────────┘
```

---

## 📦 Prerrequisitos

### Software Necesario

1. **AWS CLI** (versión 2.x)
   ```bash
   aws --version
   # aws-cli/2.x.x o superior
   ```

2. **AWS SAM CLI**
   ```bash
   sam --version
   # SAM CLI, version 1.100.0 o superior
   ```

3. **Python 3.11**
   ```bash
   python --version
   # Python 3.11.x
   ```

4. **Git**
   ```bash
   git --version
   ```

### Configuración de AWS

1. **Credenciales configuradas**
   ```bash
   aws configure
   # AWS Access Key ID: [tu-access-key]
   # AWS Secret Access Key: [tu-secret-key]
   # Default region name: us-east-1
   # Default output format: json
   ```

2. **Verificar credenciales**
   ```bash
   aws sts get-caller-identity
   ```

### Permisos IAM Necesarios

El usuario/rol de AWS debe tener permisos para:
- CloudFormation (crear/actualizar stacks)
- S3 (crear buckets, subir objetos)
- Lambda (crear funciones, configurar triggers)
- DynamoDB (crear tablas, escribir items)
- IAM (crear roles y políticas)
- CloudWatch (crear dashboards, alarmas, log groups)

---

## 🚀 Instalación y Despliegue

### Paso 1: Clonar el Repositorio

```bash
cd /tu/directorio/de/trabajo
# Si ya estás en el directorio GUATE_PASS, continúa al siguiente paso
```

### Paso 2: Validar el Template de SAM

```bash
sam validate -t infrastructure/template.yaml
```

**Salida esperada:**
```
infrastructure/template.yaml is a valid SAM Template
```

### Paso 3: Build de la Aplicación

```bash
sam build -t infrastructure/template.yaml
```

**Salida esperada:**
```
Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
```

### Paso 4: Desplegar en AWS

#### Opción A: Despliegue Guiado (Primera vez)

```bash
sam deploy --guided
```

**Responde las preguntas:**
```
Stack Name [sam-app]: guatepass-slice1
AWS Region [us-east-1]: us-east-1
Parameter Environment [dev]: dev
Confirm changes before deploy [y/N]: y
Allow SAM CLI IAM role creation [Y/n]: Y
Disable rollback [y/N]: N
ImportUsersFunction may not have authorization defined, Is this okay? [y/N]: y
Save arguments to configuration file [Y/n]: Y
SAM configuration file [samconfig.toml]: samconfig.toml
SAM configuration environment [default]: default
```

#### Opción B: Despliegue Directo (Después de la primera vez)

```bash
sam deploy
```

### Paso 5: Verificar el Despliegue

```bash
aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].StackStatus'
```

**Salida esperada:**
```
"CREATE_COMPLETE"
```

### Paso 6: Obtener Outputs del Stack

```bash
aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].Outputs'
```

**Guardar estos valores:**
- `DataBucketName`: Nombre del bucket S3
- `UsersTableName`: Nombre de la tabla DynamoDB
- `ImportUsersFunctionArn`: ARN de la función Lambda
- `DashboardURL`: URL del dashboard de CloudWatch

---

## 💻 Uso del Sistema

### 1. Cargar Datos Iniciales

El archivo CSV de clientes está en `data/clientes.csv`. Para cargarlo al sistema:

#### Obtener el nombre del bucket

```bash
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' --output text)
echo $BUCKET_NAME
```

#### Subir el archivo CSV

```bash
aws s3 cp data/clientes.csv s3://$BUCKET_NAME/clientes.csv
```

**Salida esperada:**
```
upload: data/clientes.csv to s3://guatepass-data-dev-123456789012/clientes.csv
```

### 2. Verificar la Ejecución de la Lambda

#### Ver logs en tiempo real

```bash
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail
```

**Buscar en los logs:**
```
[INFO] Iniciando importación de usuarios
[INFO] Total de usuarios en CSV: 10
[SUCCESS] Importación completada: {'total': 10, 'success': 10, 'errors': 0}
```

#### Ver logs recientes (últimos 10 minutos)

```bash
aws logs tail /aws/lambda/guatepass-import-users-dev --since 10m
```

### 3. Verificar los Datos en DynamoDB

#### Opción A: AWS CLI

```bash
# Obtener nombre de la tabla
TABLE_NAME=$(aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].Outputs[?OutputKey==`UsersTableName`].OutputValue' --output text)

# Escanear la tabla (primeros 10 items)
aws dynamodb scan --table-name $TABLE_NAME --max-items 10
```

#### Opción B: Consultar un usuario específico

```bash
aws dynamodb get-item \
  --table-name $TABLE_NAME \
  --key '{"placa": {"S": "P-123ABC"}}'
```

**Salida esperada:**
```json
{
  "Item": {
    "placa": {"S": "P-123ABC"},
    "nombre": {"S": "Juan Pérez"},
    "email": {"S": "juan@email.com"},
    "telefono": {"S": "50212345678"},
    "tipo_usuario": {"S": "registrado"},
    "tiene_tag": {"BOOL": false},
    "saldo_disponible": {"N": "100.00"},
    "estado": {"S": "activo"}
  }
}
```

#### Opción C: Contar usuarios importados

```bash
aws dynamodb scan \
  --table-name $TABLE_NAME \
  --select "COUNT"
```

### 4. Probar con Diferentes Archivos CSV

Puedes crear tu propio CSV y subirlo:

```bash
# Crear un nuevo archivo
cat > data/clientes_test.csv << EOF
placa,nombre,email,telefono,tipo_usuario,tiene_tag,tag_id,saldo_disponible
P-999ZZZ,Usuario Test,test@email.com,50299999999,registrado,false,,500.00
EOF

# Subirlo
aws s3 cp data/clientes_test.csv s3://$BUCKET_NAME/clientes_test.csv
```

---

## 📊 Monitoreo

### Dashboard de CloudWatch

Accede al dashboard desde la consola de AWS o usa la URL del Output:

```bash
# Obtener URL del dashboard
aws cloudformation describe-stacks \
  --stack-name guatepass-slice1 \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
  --output text
```

El dashboard muestra:
- **Lambda Metrics**: Invocaciones, errores, duración
- **DynamoDB Capacity**: Unidades de lectura/escritura consumidas
- **Recent Errors**: Log query de errores recientes

### Métricas Principales

#### Invocaciones de Lambda

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=guatepass-import-users-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

#### Errores de Lambda

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=guatepass-import-users-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

### Alarmas

Una alarma está configurada para notificar si la Lambda tiene errores:

```bash
# Ver estado de la alarma
aws cloudwatch describe-alarms \
  --alarm-names guatepass-import-users-errors-dev
```

---

## 🔧 Troubleshooting

### Problema: "Template format error: [/Resources/ImportUsersFunction] ..."

**Causa:** Error de sintaxis en el template YAML.

**Solución:**
```bash
sam validate -t infrastructure/template.yaml
# Corrige los errores indicados
```

### Problema: "AccessDenied when calling S3 operation"

**Causa:** La Lambda no tiene permisos para leer el bucket.

**Solución:** Verifica que el template incluye la policy `S3ReadPolicy`.

### Problema: "CSV no se procesa / Lambda no se dispara"

**Diagnóstico:**
```bash
# 1. Verificar que el archivo existe
aws s3 ls s3://$BUCKET_NAME/

# 2. Verificar trigger de Lambda
aws lambda get-function --function-name guatepass-import-users-dev

# 3. Ver logs de errores
aws logs tail /aws/lambda/guatepass-import-users-dev --since 30m --filter-pattern ERROR
```

**Solución:** Asegúrate de que el archivo se llama `clientes*.csv` (el trigger filtra por prefijo `clientes` y sufijo `.csv`).

### Problema: "DynamoDB Throttling"

**Síntoma:** Errores de tipo `ProvisionedThroughputExceededException`.

**Causa:** Tabla en modo PAY_PER_REQUEST no debería tener throttling a menos que excedas 40,000 WCU/s.

**Solución temporal:**
```bash
# Ver métricas de throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=$TABLE_NAME \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Problema: "La importación se completa pero hay errores"

**Diagnóstico:**
```bash
# Ver logs completos de la última ejecución
sam logs -n ImportUsersFunction --stack-name guatepass-slice1

# Buscar líneas con [ERROR] o [WARNING]
```

**Causas comunes:**
- Formato de CSV incorrecto (comas faltantes, comillas mal cerradas)
- Valores inválidos en campos numéricos
- Placas duplicadas

---

## 🧹 Limpiar Recursos

Para eliminar todos los recursos creados:

### Paso 1: Vaciar el Bucket S3

```bash
aws s3 rm s3://$BUCKET_NAME --recursive
```

### Paso 2: Eliminar el Stack

```bash
sam delete --stack-name guatepass-slice1
```

O con confirmación:

```bash
aws cloudformation delete-stack --stack-name guatepass-slice1
```

### Paso 3: Verificar Eliminación

```bash
aws cloudformation describe-stacks --stack-name guatepass-slice1
# Debería mostrar: "Stack with id guatepass-slice1 does not exist"
```

---

## 📚 Estructura del Proyecto

```
GUATE_PASS/
├── README.md                           # Este archivo
├── infrastructure/
│   └── template.yaml                   # SAM template (IaC)
├── src/
│   └── import_users/
│       ├── app.py                      # Código de la Lambda
│       └── requirements.txt            # Dependencias Python
├── data/
│   └── clientes.csv                    # Datos iniciales de clientes
├── docs/
│   └── slice1-arquitectura.md          # Documentación de arquitectura
└── tests/
    └── (próximamente)
```

---

## 👥 Equipo

- **Integrante 1:** [Nombre]
- **Integrante 2:** [Nombre]
- **Integrante 3:** [Nombre]

---

## 📅 Entrega

- **Fecha límite:** 17 de noviembre de 2025, 11:59 PM
- **Presentación:** 17 de noviembre de 2025

---

## 📖 Referencias

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Serverless Patterns Collection](https://serverlessland.com/patterns)

---

## 📝 Notas Importantes

1. **Ambiente de desarrollo:** Este slice está configurado para ambiente `dev`. Para producción, despliega con `--parameter-overrides Environment=prod`.

2. **Costos:** Los servicios utilizados están en Free Tier o tienen costos muy bajos:
   - Lambda: Primeros 1M de invocaciones gratis
   - DynamoDB: 25 GB gratis en PAY_PER_REQUEST
   - S3: Primeros 5 GB gratis
   - CloudWatch: 10 métricas custom gratis

3. **Retención de logs:** Los logs se retienen por 7 días para reducir costos.

4. **Versionamiento S3:** El bucket tiene versionamiento habilitado para seguridad.

---

¡Slice #1 completado! 🎉

Continúa con el Slice #2 para agregar la API de consulta de usuarios.

