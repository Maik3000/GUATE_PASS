"""
GUATEPASS - Import Users Function
===================================
Lambda function que importa usuarios desde un archivo CSV en S3 a DynamoDB.

Trigger: S3 ObjectCreated evento cuando se sube un archivo clientes*.csv
"""

import json
import csv
import os
import boto3
from typing import Dict, Any, List
from decimal import Decimal
from io import StringIO

# Clientes AWS
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
USERS_TABLE_NAME = os.environ['USERS_TABLE_NAME']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# Tabla DynamoDB
users_table = dynamodb.Table(USERS_TABLE_NAME)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal de la función Lambda.
    
    Args:
        event: Evento S3 con información del archivo subido
        context: Contexto de ejecución Lambda
        
    Returns:
        Respuesta con estadísticas de la importación
    """
    print(f"[INFO] Iniciando importación de usuarios - Environment: {ENVIRONMENT}")
    print(f"[INFO] Evento recibido: {json.dumps(event)}")
    
    try:
        # Extraer información del bucket y archivo
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']
        object_key = s3_event['object']['key']
        
        print(f"[INFO] Procesando archivo: s3://{bucket_name}/{object_key}")
        
        # Descargar y procesar el archivo CSV
        csv_content = download_csv_from_s3(bucket_name, object_key)
        users = parse_csv(csv_content)
        
        print(f"[INFO] Total de usuarios en CSV: {len(users)}")
        
        # Importar usuarios a DynamoDB
        result = import_users_to_dynamodb(users)
        
        print(f"[SUCCESS] Importación completada: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Usuarios importados exitosamente',
                'stats': result
            })
        }
        
    except Exception as e:
        print(f"[ERROR] Error durante la importación: {str(e)}")
        raise


def download_csv_from_s3(bucket: str, key: str) -> str:
    """
    Descarga el archivo CSV desde S3.
    
    Args:
        bucket: Nombre del bucket S3
        key: Key del objeto en S3
        
    Returns:
        Contenido del archivo CSV como string
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        print(f"[INFO] Archivo descargado exitosamente. Tamaño: {len(csv_content)} bytes")
        return csv_content
    except Exception as e:
        print(f"[ERROR] Error descargando archivo de S3: {str(e)}")
        raise


def parse_csv(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parsea el contenido CSV y convierte a lista de diccionarios.
    
    Args:
        csv_content: Contenido del archivo CSV como string
        
    Returns:
        Lista de diccionarios con información de usuarios
    """
    users = []
    csv_file = StringIO(csv_content)
    csv_reader = csv.DictReader(csv_file)
    
    for row_number, row in enumerate(csv_reader, start=2):  # Start at 2 (header is line 1)
        try:
            user = parse_user_row(row, row_number)
            users.append(user)
        except Exception as e:
            print(f"[WARNING] Error parseando fila {row_number}: {str(e)}. Fila: {row}")
            continue
    
    return users


def parse_user_row(row: Dict[str, str], row_number: int) -> Dict[str, Any]:
    """
    Parsea una fila del CSV y la convierte a formato DynamoDB.
    
    Args:
        row: Diccionario con datos de la fila
        row_number: Número de fila para logging
        
    Returns:
        Diccionario con datos del usuario en formato DynamoDB
    """
    # Validar campo obligatorio: placa
    placa = row.get('placa', '').strip()
    if not placa:
        raise ValueError(f"Placa vacía en fila {row_number}")
    
    # Convertir tiene_tag a booleano
    tiene_tag_str = row.get('tiene_tag', 'false').strip().lower()
    tiene_tag = tiene_tag_str in ['true', '1', 'yes', 'si', 'sí']
    
    # Convertir saldo a Decimal (DynamoDB requiere Decimal para números)
    saldo_str = row.get('saldo_disponible', '0').strip()
    try:
        saldo_disponible = Decimal(saldo_str) if saldo_str else Decimal('0')
    except:
        print(f"[WARNING] Saldo inválido '{saldo_str}' en fila {row_number}, usando 0")
        saldo_disponible = Decimal('0')
    
    # Determinar tipo de usuario
    tipo_usuario = row.get('tipo_usuario', '').strip()
    if not tipo_usuario:
        # Si no viene el campo, inferir del email/telefono
        email = row.get('email', '').strip()
        telefono = row.get('telefono', '').strip()
        tipo_usuario = 'registrado' if (email or telefono) else 'no_registrado'
    
    # Tag ID
    tag_id = row.get('tag_id', '').strip()
    if not tag_id:
        tag_id = None  # DynamoDB no almacena strings vacíos
    
    # Construir objeto usuario
    user = {
        'placa': placa.upper(),  # Normalizar a mayúsculas
        'nombre': row.get('nombre', '').strip() or 'Sin Nombre',
        'email': row.get('email', '').strip() or None,
        'telefono': row.get('telefono', '').strip() or None,
        'tipo_usuario': tipo_usuario,
        'tiene_tag': tiene_tag,
        'tag_id': tag_id,
        'saldo_disponible': saldo_disponible,
        'estado': 'activo',  # Campo adicional para control
        'fecha_creacion': None  # Se llenará en el batch write
    }
    
    # Limpiar None values (DynamoDB no acepta None)
    user = {k: v for k, v in user.items() if v is not None}
    
    return user


def import_users_to_dynamodb(users: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Importa usuarios a DynamoDB usando batch write.
    
    Args:
        users: Lista de diccionarios con información de usuarios
        
    Returns:
        Diccionario con estadísticas de la importación
    """
    success_count = 0
    error_count = 0
    
    # DynamoDB BatchWrite maneja hasta 25 items por batch
    batch_size = 25
    
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        
        try:
            with users_table.batch_writer() as batch_writer:
                for user in batch:
                    try:
                        batch_writer.put_item(Item=user)
                        success_count += 1
                    except Exception as e:
                        print(f"[ERROR] Error insertando usuario {user.get('placa')}: {str(e)}")
                        error_count += 1
        except Exception as e:
            print(f"[ERROR] Error en batch write: {str(e)}")
            error_count += len(batch)
    
    return {
        'total': len(users),
        'success': success_count,
        'errors': error_count
    }


if __name__ == "__main__":
    # Para pruebas locales
    print("Esta función debe ejecutarse en AWS Lambda")

