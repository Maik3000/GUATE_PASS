# Script para configurar el trigger S3 -> Lambda
# Ejecutar DESPUES de sam deploy

param(
    [string]$StackName = "guatepass-dev"
)

Write-Host "Configurando trigger S3 -> Lambda" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Obtener nombres de recursos del stack
Write-Host "Obteniendo informacion del stack..." -ForegroundColor Yellow

$BucketName = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" `
    --output text

$FunctionName = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='ImportUsersFunctionName'].OutputValue" `
    --output text

if ([string]::IsNullOrEmpty($BucketName) -or [string]::IsNullOrEmpty($FunctionName)) {
    Write-Host "Error: No se pudo obtener informacion del stack" -ForegroundColor Red
    Write-Host "Asegurate de que el stack '$StackName' existe" -ForegroundColor Red
    exit 1
}

Write-Host "Bucket: $BucketName" -ForegroundColor Green
Write-Host "Function: $FunctionName" -ForegroundColor Green
Write-Host ""

# Obtener ARN de la funcion
Write-Host "Obteniendo ARN de la funcion Lambda..." -ForegroundColor Yellow
$FunctionArn = aws lambda get-function `
    --function-name $FunctionName `
    --query 'Configuration.FunctionArn' `
    --output text

if ([string]::IsNullOrEmpty($FunctionArn)) {
    Write-Host "Error: No se pudo obtener el ARN de la funcion" -ForegroundColor Red
    exit 1
}

Write-Host "ARN: $FunctionArn" -ForegroundColor Green
Write-Host ""

# Paso 1: Dar permisos a S3 para invocar la Lambda
Write-Host "Paso 1: Configurando permisos Lambda..." -ForegroundColor Yellow

# Intentar remover el permiso si existe (para evitar errores en re-ejecuciones)
aws lambda remove-permission `
    --function-name $FunctionName `
    --statement-id s3-trigger `
    2>$null | Out-Null

# Agregar el permiso
$BucketArn = "arn:aws:s3:::$BucketName"
aws lambda add-permission `
    --function-name $FunctionName `
    --statement-id s3-trigger `
    --action lambda:InvokeFunction `
    --principal s3.amazonaws.com `
    --source-arn $BucketArn | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Permisos configurados OK" -ForegroundColor Green
} else {
    Write-Host "Advertencia: Puede que el permiso ya exista" -ForegroundColor Yellow
}
Write-Host ""

# Paso 2: Configurar notificacion en el bucket
Write-Host "Paso 2: Configurando notificacion S3..." -ForegroundColor Yellow

# Crear archivo JSON temporal con la configuracion
$TempFile = New-TemporaryFile
$JsonContent = @{
    LambdaFunctionConfigurations = @(
        @{
            LambdaFunctionArn = $FunctionArn
            Events = @("s3:ObjectCreated:*")
            Filter = @{
                Key = @{
                    FilterRules = @(
                        @{
                            Name = "prefix"
                            Value = "clientes"
                        },
                        @{
                            Name = "suffix"
                            Value = ".csv"
                        }
                    )
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

# Escribir sin BOM (UTF-8 sin Byte Order Mark)
[System.IO.File]::WriteAllText($TempFile.FullName, $JsonContent)

# Aplicar configuracion
aws s3api put-bucket-notification-configuration `
    --bucket $BucketName `
    --notification-configuration "file://$($TempFile.FullName)"

# Limpiar archivo temporal
Remove-Item $TempFile.FullName -Force

if ($LASTEXITCODE -eq 0) {
    Write-Host "Notificacion S3 configurada OK" -ForegroundColor Green
} else {
    Write-Host "Error configurando notificacion" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Trigger S3 -> Lambda configurado exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora puedes probar subiendo un CSV:" -ForegroundColor Cyan
Write-Host "aws s3 cp data/clientes.csv s3://$BucketName/clientes.csv" -ForegroundColor White
Write-Host ""
Write-Host "Ver logs:" -ForegroundColor Cyan
Write-Host "sam logs -n ImportUsersFunction --stack-name $StackName --tail" -ForegroundColor White
Write-Host ""
