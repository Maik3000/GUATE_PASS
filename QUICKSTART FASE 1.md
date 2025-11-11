# 🚀 Quick Start - GUATEPASS Fase 1

Guía rápida para desplegar y probar el sistema en menos de 10 minutos.

---

## ⚡ Despliegue Rápido (3 comandos)

### 1️⃣ Validar y construir

```bash
sam validate -t infrastructure/template.yaml && sam build -t infrastructure/template.yaml
```

### 2️⃣ Desplegar

```bash
sam deploy --guided
```

**Respuestas recomendadas:**
- Stack Name: `guatepass-slice1`
- AWS Region: `us-east-1`
- Parameter Environment: `dev`
- Confirm changes: `y`
- Allow IAM role creation: `Y`
- Authorization not defined: `y`
- Save config: `Y`

### 3️⃣ Cargar datos

```bash
# Obtener nombre del bucket
BUCKET=$(aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' --output text)

# Subir CSV
aws s3 cp data/clientes.csv s3://$BUCKET/clientes.csv
```

---

## ✅ Verificación

### Ver logs de importación

```bash
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail
```

**Buscar:**
```
[SUCCESS] Importación completada: {'total': 10, 'success': 10, 'errors': 0}
```

### Consultar usuarios importados

```bash
# Obtener nombre de tabla
TABLE=$(aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].Outputs[?OutputKey==`UsersTableName`].OutputValue' --output text)

# Ver primeros 5 usuarios
aws dynamodb scan --table-name $TABLE --max-items 5
```

### Acceder al Dashboard

```bash
aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' --output text
```

---

## 🛠️ Scripts Útiles (Opcional)

Si prefieres usar scripts automatizados:

```bash
# Dar permisos de ejecución (Linux/Mac)
chmod +x scripts/*.sh

# Desplegar todo
./scripts/deploy.sh

# Cargar CSV
./scripts/upload-csv.sh

# Verificar datos
./scripts/check-data.sh

# Limpiar todo
./scripts/cleanup.sh
```

---

## 🧪 Testing de Escalabilidad

### Generar CSV grande

```bash
# Generar 1,000 usuarios
python scripts/generate_test_csv.py --users 1000 --output data/clientes_1k.csv

# Subir
aws s3 cp data/clientes_1k.csv s3://$BUCKET/clientes_1k.csv

# Monitorear duración
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail
```

---

### Métricas clave a mostrar

- ✅ Lambda: Invocations, Errors (debe ser 0), Duration
- ✅ DynamoDB: Items count, Write capacity consumed
- ✅ Logs: Mensaje de SUCCESS con estadísticas

---

## 🧹 Limpiar Recursos

```bash
# Vaciar bucket
aws s3 rm s3://$BUCKET --recursive

# Eliminar stack
sam delete --stack-name guatepass-slice1
```
