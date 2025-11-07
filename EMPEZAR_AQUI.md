# 👋 ¡Bienvenido a GUATEPASS!

## 🎯 ¿Por dónde empiezo?

Si es tu primera vez en este proyecto, sigue esta guía de 3 pasos:

---

## ⚡ Inicio Rápido (10 minutos)

### Paso 1️⃣: Lee el Quick Start

```bash
# Abre este archivo para desplegar en 10 minutos
📄 QUICKSTART.md
```

### Paso 2️⃣: Despliega el Slice #1

```bash
# Opción A: Comandos manuales
sam validate -t infrastructure/template.yaml
sam build -t infrastructure/template.yaml
sam deploy --guided

# Opción B: Script automatizado (Linux/Mac)
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Paso 3️⃣: Carga los datos

```bash
# Obtener bucket name
BUCKET=$(aws cloudformation describe-stacks --stack-name guatepass-slice1 --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' --output text)

# Subir CSV
aws s3 cp data/clientes.csv s3://$BUCKET/clientes.csv

# Ver logs
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail
```

---

## 📚 Documentación Principal

### Para Desarrolladores

1. **README.md** - Guía completa del proyecto
2. **QUICKSTART.md** - Despliegue rápido
3. **COMANDOS_UTILES.md** - Referencia de comandos
4. **PROJECT_STATUS.md** - Estado actual del proyecto

### Para Arquitectura

1. **docs/slice1-arquitectura.md** - Documentación técnica detallada
2. **docs/diagrama-slice1.txt** - Diagrama ASCII del sistema
3. **infrastructure/template.yaml** - Infrastructure as Code

---

## 🗺️ Estructura del Proyecto

```
GUATE_PASS/
│
├── 📖 Documentación
│   ├── README.md              ← Empieza aquí para visión completa
│   ├── QUICKSTART.md          ← Despliegue rápido
│   ├── COMANDOS_UTILES.md     ← Cheat sheet de comandos
│   └── PROJECT_STATUS.md      ← Estado del proyecto
│
├── 🏗️ Infraestructura
│   ├── infrastructure/
│   │   └── template.yaml      ← SAM template (IaC)
│   └── samconfig.toml         ← Configuración SAM
│
├── 💻 Código Fuente
│   └── src/
│       └── import_users/
│           ├── app.py         ← Lambda function
│           └── requirements.txt
│
├── 📊 Datos
│   └── data/
│       └── clientes.csv       ← Datos de ejemplo
│
├── 🛠️ Scripts
│   └── scripts/
│       ├── deploy.sh          ← Despliegue automatizado
│       ├── upload-csv.sh      ← Subir CSV
│       ├── check-data.sh      ← Verificar datos
│       ├── cleanup.sh         ← Limpiar recursos
│       └── generate_test_csv.py ← Generar datos de prueba
│
└── 📝 Arquitectura
    └── docs/
        ├── slice1-arquitectura.md
        └── diagrama-slice1.txt
```

---

## 🎓 Flujo de Trabajo Recomendado

### Para Desarrollo

```
1. Leer README.md completo
2. Entender la arquitectura (docs/slice1-arquitectura.md)
3. Desplegar con QUICKSTART.md
4. Experimentar con comandos (COMANDOS_UTILES.md)
5. Hacer cambios en el código
6. Re-desplegar con sam deploy
7. Ver logs y monitoreo
```

### Para Presentación

```
1. Preparar slides basados en PROJECT_STATUS.md
2. Mostrar diagrama (docs/diagrama-slice1.txt)
3. Explicar decisiones arquitectónicas
4. Demo en vivo:
   - Subir CSV
   - Mostrar logs en tiempo real
   - Mostrar dashboard CloudWatch
   - Consultar DynamoDB
5. Q&A
```

---

## ⚙️ Prerrequisitos

Antes de empezar, asegúrate de tener:

- ✅ AWS CLI instalado y configurado
- ✅ SAM CLI instalado
- ✅ Python 3.11
- ✅ Credenciales de AWS configuradas
- ✅ Permisos IAM necesarios

**Verificar:**
```bash
aws --version
sam --version
python --version
aws sts get-caller-identity
```

---

## 🚀 Comandos Más Usados

```bash
# Validar
sam validate -t infrastructure/template.yaml

# Build
sam build -t infrastructure/template.yaml

# Deploy
sam deploy

# Logs
sam logs -n ImportUsersFunction --stack-name guatepass-slice1 --tail

# Subir CSV
aws s3 cp data/clientes.csv s3://$BUCKET/clientes.csv

# Ver datos
aws dynamodb scan --table-name $TABLE --max-items 5

# Limpiar
sam delete --stack-name guatepass-slice1
```

---

## 🆘 ¿Necesitas Ayuda?

### Troubleshooting Común

1. **Error en template:** `sam validate -t infrastructure/template.yaml`
2. **Credenciales incorrectas:** `aws configure`
3. **Lambda no se dispara:** Verifica que el archivo sea `clientes*.csv`
4. **Ver errores:** `sam logs -n ImportUsersFunction --filter ERROR --tail`

### Documentación de AWS

- [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/)
- [Lambda](https://docs.aws.amazon.com/lambda/)
- [DynamoDB](https://docs.aws.amazon.com/dynamodb/)

---

## 🎯 Estado Actual

```
✅ Slice #1: Carga de Datos         COMPLETADO
⏳ Slice #2: API Consulta           PENDIENTE
⏳ Slice #3: Webhook Peajes         PENDIENTE
⏳ Slice #4: Step Functions         PENDIENTE
⏳ Slice #5: Gestión Tags           PENDIENTE
⏳ Slice #6: Notificaciones         PENDIENTE
```

---

## 📅 Próximos Pasos

1. **Probar el Slice #1** completamente
2. **Implementar Slice #2**: API de consulta de usuarios
3. **Continuar con los siguientes slices** según el roadmap
4. **Preparar presentación** con base en la documentación

---

## 💡 Tips

- 📖 Lee todo el README.md antes de empezar
- 🧪 Usa `generate_test_csv.py` para pruebas de carga
- 📊 Revisa el dashboard de CloudWatch regularmente
- 🔄 Haz commits frecuentes con mensajes descriptivos
- 🎯 Completa un slice antes de empezar el siguiente

---

## 🎉 ¡Listo para Empezar!

Ahora que sabes por dónde empezar:

1. Abre **QUICKSTART.md**
2. Sigue los 3 comandos de despliegue
3. ¡Disfruta tu sistema serverless funcionando! 🚀

---

**Última actualización:** Noviembre 7, 2025  
**Versión Slice:** #1 - Carga Inicial de Datos  
**Estado:** ✅ FUNCIONAL

