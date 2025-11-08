"""
GUATEPASS - Get Tag By Placa Function
======================================
Lambda function para consultar información del Tag asociado a una placa.

Endpoint: GET /users/{placa}/tag
"""

import json
import os
import boto3
from typing import Dict, Any
from decimal import Decimal

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
USERS_TABLE_NAME = os.environ['USERS_TABLE_NAME']
users_table = dynamodb.Table(USERS_TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """Helper para serializar Decimals de DynamoDB a JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal de la función Lambda.
    
    Args:
        event: Evento de API Gateway con path parameter {placa}
        context: Contexto de ejecución Lambda
        
    Returns:
        Response HTTP con información del Tag o error
    """
    print(f"[INFO] GET /users/{{placa}}/tag - Event: {json.dumps(event)}")
    
    try:
        # Extraer placa del path parameter
        placa = event.get('pathParameters', {}).get('placa')
        
        if not placa:
            return error_response(400, "Placa no proporcionada en la URL")
        
        # Normalizar placa a mayúsculas
        placa = placa.upper().strip()
        
        print(f"[INFO] Consultando Tag para placa: {placa}")
        
        # Consultar DynamoDB
        response = users_table.get_item(Key={'placa': placa})
        
        # Verificar si el usuario existe
        if 'Item' not in response:
            return error_response(404, f"Usuario con placa {placa} no encontrado")
        
        user = response['Item']
        
        # Verificar si el usuario tiene Tag
        if not user.get('tiene_tag', False):
            return success_response(200, {
                'placa': placa,
                'tiene_tag': False,
                'tag_id': None,
                'message': f'El vehículo {placa} no tiene dispositivo Tag asociado'
            })
        
        # Usuario tiene Tag
        tag_info = {
            'placa': placa,
            'tiene_tag': True,
            'tag_id': user.get('tag_id'),
            'nombre': user.get('nombre'),
            'email': user.get('email'),
            'telefono': user.get('telefono'),
            'saldo_disponible': user.get('saldo_disponible', 0),
            'estado': user.get('estado', 'activo')
        }
        
        print(f"[SUCCESS] Tag encontrado para placa {placa}: {tag_info.get('tag_id')}")
        
        return success_response(200, {
            'tag': tag_info,
            'message': f'Tag encontrado para vehículo {placa}'
        })
        
    except Exception as e:
        print(f"[ERROR] Error consultando Tag: {str(e)}")
        return error_response(500, f"Error interno del servidor: {str(e)}")


def success_response(status_code: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera una respuesta exitosa HTTP.
    
    Args:
        status_code: Código HTTP (200, 201, etc.)
        data: Datos a retornar en el body
        
    Returns:
        Response en formato API Gateway
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # CORS
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(data, cls=DecimalEncoder, ensure_ascii=False)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Genera una respuesta de error HTTP.
    
    Args:
        status_code: Código HTTP (400, 404, 500, etc.)
        message: Mensaje de error
        
    Returns:
        Response en formato API Gateway
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # CORS
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({
            'error': message,
            'statusCode': status_code
        }, ensure_ascii=False)
    }


if __name__ == "__main__":
    # Para pruebas locales
    print("Esta función debe ejecutarse en AWS Lambda")

