# 🛠️ Comandos Útiles - GUATEPASS

Referencia rápida de comandos más usados en el proyecto.

---

## 📦 SAM CLI

### Validar Template

```bash
sam validate -t infrastructure/template.yaml
```

### Build

```bash
# Build normal
sam build -t infrastructure/template.yaml

# Build con cache (más rápido)
sam build -t infrastructure/template.yaml --cached

# Build en paralelo
sam build -t infrastructure/template.yaml --parallel
```

### Deploy

```bash
# Primera vez (guiado)
sam deploy --guided

# Despliegues siguientes
sam deploy

# Deploy con parámetros específicos
sam deploy --parameter-overrides Environment=prod

# Deploy sin confirmación (CI/CD)
sam deploy --no-confirm-changeset
```

### Logs

```bash
# Ver logs en tiempo real
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail

# Ver logs de los últimos 10 minutos
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --start-time '10min ago'

# Ver logs con filtro
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --filter "ERROR"
```

### Delete

```bash
# Eliminar stack
sam delete --stack-name guatepass-slice1

# Sin confirmación
sam delete --stack-name guatepass-slice1 --no-prompts
```

---

## 🪣 S3

### Operaciones Básicas

```bash
# Listar buckets
aws s3 ls

# Listar contenido de un bucket
aws s3 ls s3://guatepass-data-dev-123456789012/

# Subir archivo
aws s3 cp data/clientes.csv s3://BUCKET_NAME/clientes.csv

# Descargar archivo
aws s3 cp s3://BUCKET_NAME/clientes.csv data/clientes_backup.csv

# Eliminar archivo
aws s3 rm s3://BUCKET_NAME/clientes.csv

# Vaciar bucket completo
aws s3 rm s3://BUCKET_NAME/ --recursive

# Sincronizar carpeta
aws s3 sync data/ s3://BUCKET_NAME/data/
```

---

## 🗄️ DynamoDB

### Operaciones de Lectura

```bash
# Obtener un item por clave
aws dynamodb get-item \
  --table-name GuatepassUsers-dev \
  --key '{"placa": {"S": "P-123ABC"}}'

# Scan (leer todos los items) - limitado
aws dynamodb scan \
  --table-name GuatepassUsers-dev \
  --max-items 10

# Contar items
aws dynamodb scan \
  --table-name GuatepassUsers-dev \
  --select "COUNT"

# Query en GSI (buscar por tag)
aws dynamodb query \
  --table-name GuatepassUsers-dev \
  --index-name TagIndex \
  --key-condition-expression "tag_id = :tid" \
  --expression-attribute-values '{":tid": {"S": "TAG-001"}}'
```

### Operaciones de Escritura

```bash
# Put item
aws dynamodb put-item \
  --table-name GuatepassUsers-dev \
  --item '{
    "placa": {"S": "P-999ZZZ"},
    "nombre": {"S": "Test Usuario"},
    "tipo_usuario": {"S": "registrado"},
    "tiene_tag": {"BOOL": false},
    "saldo_disponible": {"N": "100.00"},
    "estado": {"S": "activo"}
  }'

# Update item
aws dynamodb update-item \
  --table-name GuatepassUsers-dev \
  --key '{"placa": {"S": "P-123ABC"}}' \
  --update-expression "SET saldo_disponible = :s" \
  --expression-attribute-values '{":s": {"N": "200.00"}}'

# Delete item
aws dynamodb delete-item \
  --table-name GuatepassUsers-dev \
  --key '{"placa": {"S": "P-999ZZZ"}}'
```

### Operaciones de Tabla

```bash
# Describir tabla
aws dynamodb describe-table \
  --table-name GuatepassUsers-dev

# Listar todas las tablas
aws dynamodb list-tables

# Export tabla a S3 (backup)
aws dynamodb export-table-to-point-in-time \
  --table-arn arn:aws:dynamodb:region:account:table/GuatepassUsers-dev \
  --s3-bucket guatepass-backups \
  --export-format DYNAMODB_JSON
```

---

## 🔧 Lambda

### Información y Logs

```bash
# Listar todas las funciones
aws lambda list-functions

# Describir función
aws lambda get-function \
  --function-name guatepass-import-users-dev

# Ver configuración
aws lambda get-function-configuration \
  --function-name guatepass-import-users-dev

# Invocar función manualmente (test)
aws lambda invoke \
  --function-name guatepass-import-users-dev \
  --payload '{"test": true}' \
  response.json
```

---

## 📊 CloudWatch

### Logs

```bash
# Listar log groups
aws logs describe-log-groups

# Ver streams de un log group
aws logs describe-log-streams \
  --log-group-name /aws/lambda/guatepass-import-users-dev

# Tail logs en tiempo real
aws logs tail /aws/lambda/guatepass-import-users-dev --follow

# Ver logs de las últimas horas
aws logs tail /aws/lambda/guatepass-import-users-dev --since 2h

# Filtrar logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/guatepass-import-users-dev \
  --filter-pattern "ERROR"

# Log Insights query
aws logs start-query \
  --log-group-name /aws/lambda/guatepass-import-users-dev \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'
```

### Métricas

```bash
# Ver métricas de Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=guatepass-import-users-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Ver errores
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=guatepass-import-users-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Ver duración
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=guatepass-import-users-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

### Alarmas

```bash
# Listar alarmas
aws cloudwatch describe-alarms

# Ver estado de una alarma
aws cloudwatch describe-alarms \
  --alarm-names guatepass-import-users-errors-dev

# Deshabilitar alarma temporalmente
aws cloudwatch disable-alarm-actions \
  --alarm-names guatepass-import-users-errors-dev

# Habilitar alarma
aws cloudwatch enable-alarm-actions \
  --alarm-names guatepass-import-users-errors-dev
```

---

## 🏗️ CloudFormation

### Stack Operations

```bash
# Listar stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Describir stack
aws cloudformation describe-stacks \
  --stack-name guatepass-slice1

# Ver solo outputs
aws cloudformation describe-stacks \
  --stack-name guatepass-slice1 \
  --query 'Stacks[0].Outputs'

# Ver recursos del stack
aws cloudformation describe-stack-resources \
  --stack-name guatepass-slice1

# Ver eventos (útil para debug)
aws cloudformation describe-stack-events \
  --stack-name guatepass-slice1 \
  --max-items 20

# Validar template
aws cloudformation validate-template \
  --template-body file://infrastructure/template.yaml

# Detectar drift (cambios manuales)
aws cloudformation detect-stack-drift \
  --stack-name guatepass-slice1
```

---

## 🔐 IAM

```bash
# Ver usuario actual
aws sts get-caller-identity

# Listar roles
aws iam list-roles | grep guatepass

# Ver policies de un rol
aws iam list-attached-role-policies \
  --role-name guatepass-slice1-ImportUsersFunctionRole-XXXXX

# Ver inline policies
aws iam list-role-policies \
  --role-name guatepass-slice1-ImportUsersFunctionRole-XXXXX
```

---

## 🎯 Variables de Entorno Útiles

```bash
# Obtener nombre del bucket
export BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name guatepass-slice1 \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text)

# Obtener nombre de la tabla
export TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name guatepass-slice1 \
  --query 'Stacks[0].Outputs[?OutputKey==`UsersTableName`].OutputValue' \
  --output text)

# Obtener ARN de la función
export FUNCTION_ARN=$(aws cloudformation describe-stacks \
  --stack-name guatepass-slice1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ImportUsersFunctionArn`].OutputValue' \
  --output text)

# Usar las variables
echo "Bucket: $BUCKET_NAME"
echo "Table: $TABLE_NAME"
aws s3 ls s3://$BUCKET_NAME/
aws dynamodb scan --table-name $TABLE_NAME --max-items 5
```

---

## 🧪 Testing

### Generar Datos de Prueba

```bash
# CSV pequeño (100 usuarios)
python scripts/generate_test_csv.py --users 100 --output data/test_100.csv

# CSV mediano (1,000 usuarios)
python scripts/generate_test_csv.py --users 1000 --output data/test_1k.csv

# CSV grande (10,000 usuarios)
python scripts/generate_test_csv.py --users 10000 --output data/test_10k.csv
```

### Pruebas de Carga

```bash
# Subir y medir tiempo
time aws s3 cp data/test_1k.csv s3://$BUCKET_NAME/test_1k.csv

# Ver logs inmediatamente
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail

# Contar registros insertados
aws dynamodb scan --table-name $TABLE_NAME --select COUNT
```

---

## 📝 Desarrollo Local

### Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Linux/Mac)
source venv/bin/activate

# Activar (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r src/import_users/requirements.txt

# Ejecutar tests (cuando estén disponibles)
pytest tests/
```

---

## 🔄 Git (Buenas Prácticas)

```bash
# Inicializar repo
git init
git add .
git commit -m "feat: Slice #1 - Carga inicial de datos"

# Crear rama para nuevo slice
git checkout -b slice-2-api-consulta

# Ver estado
git status

# Commit con mensaje descriptivo
git commit -m "feat(slice2): Add API Gateway for user queries"

# Push
git push origin main
```

### Mensajes de Commit Recomendados

- `feat(slice1): Add S3 bucket and Lambda function`
- `fix(lambda): Handle empty email fields correctly`
- `docs(readme): Update deployment instructions`
- `refactor(dynamo): Improve batch write logic`
- `test(import): Add test for CSV parsing`

---


### Verificar Permisos IAM

```bash
# Ver qué puede hacer tu usuario
aws iam get-user
aws iam list-attached-user-policies --user-name TU_USUARIO
```


---

## 📚 Referencias Rápidas

- **AWS CLI Reference:** https://awscli.amazonaws.com/v2/documentation/api/latest/index.html
- **SAM CLI Reference:** https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html
- **Boto3 Docs:** https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

---


