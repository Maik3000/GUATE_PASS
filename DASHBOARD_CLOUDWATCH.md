# 📊 GUATEPASS - Dashboard de CloudWatch Completo

## ✅ Estado: IMPLEMENTADO

Dashboard completo de monitoreo que cumple con **TODOS** los requerimientos del proyecto.

---

## 🎯 Requerimientos Cumplidos

### ✅ 5.4.1 Métricas Principales

#### **Lambda Functions**
- ✅ **Invocaciones**: Total de invocaciones por todas las funciones
- ✅ **Errores**: Total de errores + Throttles
- ✅ **Duración**: Promedio y P99 (percentil 99)
- ✅ **Concurrencia**: Ejecuciones concurrentes

#### **API Gateway**
- ✅ **Número de Requests**: Total de peticiones al API
- ✅ **Latencia**: Promedio y P99
- ✅ **Errores 4XX**: Errores del cliente
- ✅ **Errores 5XX**: Errores del servidor
- ✅ **Integration Latency**: Latencia de integración con backends

#### **DynamoDB**
- ✅ **Operaciones de Lectura**: Read Capacity Units para todas las tablas
- ✅ **Operaciones de Escritura**: Write Capacity Units para todas las tablas
- ✅ **Throttles**: Errores por throttling en todas las tablas
- ✅ **Latencia**: Latencia promedio por tabla

**Tablas Monitoreadas:**
1. GuatepassUsers
2. GuatepassTransactions
3. GuatepassInvoices
4. GuatepassTolls

### ✅ 5.4.2 Logs Centralizados

#### **CloudWatch Logs**
- ✅ Log Groups para TODAS las funciones Lambda (17 funciones)
- ✅ Retención configurada: 7 días
- ✅ Query unificada de errores de todas las funciones
- ✅ Logs organizados por componente

**Log Groups Configurados:**
1. `/aws/lambda/guatepass-import-users-dev`
2. `/aws/lambda/guatepass-get-user-by-placa-dev`
3. `/aws/lambda/guatepass-get-tag-by-placa-dev`
4. `/aws/lambda/guatepass-create-tag-dev`
5. `/aws/lambda/guatepass-update-tag-dev`
6. `/aws/lambda/guatepass-delete-tag-dev`
7. `/aws/lambda/guatepass-get-tag-by-id-dev`
8. `/aws/lambda/guatepass-ingest-toll-dev`
9. `/aws/lambda/guatepass-resolve-user-dev`
10. `/aws/lambda/guatepass-calculate-fare-dev`
11. `/aws/lambda/guatepass-record-transaction-dev`
12. `/aws/lambda/guatepass-update-balance-dev`
13. `/aws/lambda/guatepass-generate-invoice-dev`
14. `/aws/lambda/guatepass-notify-user-dev`
15. `/aws/lambda/guatepass-get-payments-by-plate-dev` ⭐
16. `/aws/lambda/guatepass-get-invoices-by-plate-dev` ⭐
17. `/aws/stepfunctions/guatepass-process-toll-dev`

### ✅ Componente Adicional: Step Functions
- ✅ **Ejecuciones Iniciadas**
- ✅ **Ejecuciones Exitosas**
- ✅ **Ejecuciones Fallidas**
- ✅ **Ejecuciones con Timeout**

---

## 📊 Estructura del Dashboard

### **Sección 1: Lambda Functions (Y: 0-12)**
- Widget 1: Invocaciones Totales
- Widget 2: Errores y Throttles
- Widget 3: Duración (Promedio y P99)
- Widget 4: Concurrencia

### **Sección 2: API Gateway (Y: 12-24)**
- Widget 5: Total Requests
- Widget 6: Latencia (Promedio y P99)
- Widget 7: Errores 4XX/5XX
- Widget 8: Integration Latency

### **Sección 3: DynamoDB (Y: 24-36)**
- Widget 9: Operaciones de Lectura (4 tablas)
- Widget 10: Operaciones de Escritura (4 tablas)
- Widget 11: Errores y Throttling (4 tablas)
- Widget 12: Latencia Promedio (4 tablas)

### **Sección 4: Step Functions (Y: 36-42)**
- Widget 13: Estado de Ejecuciones

### **Sección 5: Logs Centralizados (Y: 42-48)**
- Widget 14: Errores Recientes (Query unificada de 17 funciones)

---

## 🚀 Acceso al Dashboard

### Opción 1: Desde CloudFormation Outputs

```powershell
# Obtener URL del dashboard
aws cloudformation describe-stacks `
  --stack-name guatepass-dev `
  --query "Stacks[0].Outputs[?OutputKey=='DashboardURL'].OutputValue" `
  --output text
```

### Opción 2: Desde la Consola de AWS

1. Ir a **CloudWatch** en la consola de AWS
2. En el menú lateral, seleccionar **Dashboards**
3. Buscar: `GUATEPASS-Complete-dev`

### Opción 3: URL Directa

```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=GUATEPASS-Complete-dev
```

---

## 📈 Características del Dashboard

### ✅ **Tiempo Real**
- Actualización cada 5 minutos (300 segundos)
- Métricas en vivo de todos los componentes

### ✅ **Visualización Completa**
- 14 widgets organizados
- Layout profesional de 24 columnas
- Gráficos de series temporales
- Colores diferenciados por severidad

### ✅ **Monitoreo Proactivo**
- Detección temprana de errores
- Alertas visuales (colores rojo para errores)
- Logs centralizados para troubleshooting rápido

### ✅ **Métricas Agregadas**
- Todas las Lambdas en un solo lugar
- Todas las tablas DynamoDB monitoreadas
- Vista unificada del sistema completo

---

## 🔍 Cómo Usar el Dashboard

### 1. Monitorear Salud General del Sistema

**Qué revisar:**
- Lambda Invocations > 0 → Sistema activo
- Lambda Errors = 0 → Sin problemas
- API Gateway 4XX/5XX = 0 → APIs funcionando correctamente

### 2. Identificar Cuellos de Botella

**Qué revisar:**
- Lambda Duration: Si P99 > 5000ms → Optimizar función
- API Latency: Si > 1000ms → Revisar integraciones
- DynamoDB Throttling: Si > 0 → Considerar aumentar capacidad

### 3. Troubleshooting de Errores

**Proceso:**
1. Ver widget "Lambda - Errores y Throttles"
2. Identificar pico de errores
3. Ir al widget "Logs - Errores Recientes"
4. Ver detalles del error con timestamp
5. Usar CloudWatch Logs Insights para análisis profundo

### 4. Análisis de Costos

**Qué revisar:**
- Lambda Invocations: Mayor número → Mayor costo
- DynamoDB Read/Write: Alto consumo → Revisar queries
- Lambda Duration: Mayor duración → Mayor costo

---

## 📊 Métricas Clave por Componente

### Lambda Functions

| Métrica | Umbral Normal | Acción si Excede |
|---------|---------------|------------------|
| Errores | 0-1% | Investigar logs |
| Duration P99 | < 3000ms | Optimizar código |
| Throttles | 0 | Aumentar límites |
| Concurrencia | < 100 | Revisar configuración |

### API Gateway

| Métrica | Umbral Normal | Acción si Excede |
|---------|---------------|------------------|
| 4XX Errors | < 5% | Revisar validaciones |
| 5XX Errors | < 1% | Revisar backend |
| Latency P99 | < 1000ms | Optimizar Lambdas |

### DynamoDB

| Métrica | Umbral Normal | Acción si Excede |
|---------|---------------|------------------|
| User Errors | 0 | Revisar throttling |
| Read/Write | Según carga | Optimizar queries |
| Latency | < 50ms | Revisar índices |

---

## 🛠️ Deployment del Dashboard

### El dashboard se despliega automáticamente con:

```powershell
# 1. Build
sam build -t infrastructure/template.yaml

# 2. Deploy
sam deploy
```

### Verificar Deployment

```powershell
# Listar dashboards
aws cloudwatch list-dashboards --query "DashboardEntries[?DashboardName=='GUATEPASS-Complete-dev']"

# Ver detalles
aws cloudwatch get-dashboard --dashboard-name GUATEPASS-Complete-dev
```

---

## 📱 Alertas Configuradas

### Alarma Existente:
- ✅ **ImportUsersErrorAlarm**: Alerta cuando ImportUsers tiene errores

### Recomendaciones de Alarmas Adicionales:

```yaml
# Agregar en template.yaml si es necesario:

ApiGateway5XXErrorAlarm:
  - Umbral: > 5 errores 5XX en 5 minutos
  - Acción: Notificar SNS

DynamoDBThrottlingAlarm:
  - Umbral: > 10 throttles en 5 minutos
  - Acción: Notificar SNS

StepFunctionsFailureAlarm:
  - Umbral: > 3 fallos en 5 minutos
  - Acción: Notificar SNS
```

---

## 🎨 Personalización del Dashboard

### Para Modificar el Dashboard:

1. Editar `infrastructure/template.yaml`
2. Buscar `GuatepassDashboard:`
3. Modificar widgets en el `DashboardBody`
4. Rebuild y redeploy

### Agregar Nuevos Widgets:

```json
{
  "type": "metric",
  "x": 0,
  "y": 48,
  "width": 24,
  "height": 6,
  "properties": {
    "metrics": [
      ["AWS/Lambda", "Duration", {"stat": "Maximum"}]
    ],
    "title": "Mi Nuevo Widget"
  }
}
```

---

## 📚 Documentación de Referencia

- [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html)
- [Lambda Metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)
- [API Gateway Metrics](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-metrics-and-dimensions.html)
- [DynamoDB Metrics](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/metrics-dimensions.html)

---

## ✅ Checklist de Implementación

- [x] Dashboard con métricas de Lambda (invocaciones, errores, duración)
- [x] Dashboard con métricas de API Gateway (requests, latencia, 4XX/5XX)
- [x] Dashboard con métricas de DynamoDB (read/write, throttles)
- [x] Dashboard con métricas de Step Functions
- [x] Log Groups para todas las funciones Lambda
- [x] Retención de logs configurada (7 días)
- [x] Query centralizada de errores
- [x] Logs organizados por componente
- [x] URL del dashboard en Outputs
- [x] Documentación completa

---

## 🎉 Conclusión

El **Dashboard de CloudWatch** está **100% implementado** y cumple con **TODOS** los requerimientos del proyecto:

✅ **14 Widgets** organizados profesionalmente  
✅ **17 Log Groups** configurados  
✅ **4 Componentes** monitoreados (Lambda, API Gateway, DynamoDB, Step Functions)  
✅ **Logs Centralizados** con query unificada  
✅ **Tiempo Real** con actualización cada 5 minutos  

**El dashboard está listo para monitorear el sistema completo en producción.** 🚀

---

**Última actualización:** Noviembre 11, 2025  
**Estado:** ✅ COMPLETADO Y FUNCIONAL  
**Dashboard Name:** `GUATEPASS-Complete-dev`

