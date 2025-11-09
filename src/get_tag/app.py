"""
Lambda Function: Get Tag by Tag ID
Consulta información de un usuario por su tag_id.
Usa el índice secundario global (GSI) TagIndex.
"""

import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
users_table_name = os.environ['USERS_TABLE_NAME']
users_table = dynamodb.Table(users_table_name)


def lambda_handler(event, context):
    """
    Handler principal del Lambda.
    
    Input esperado:
    GET /tags/{tag_id}
    
    Output:
    {
        "statusCode": 200,
        "body": {
            "tag_id": "TAG-12345",
            "tag_status": "active",
            "user": {
                "placa": "P123ABC",
                "nombre": "Juan Pérez",
                "tipo_usuario": "registrado",
                "saldo_disponible": "100.00"
            }
        }
    }
    """
    
    try:
        print(f"Evento recibido: {json.dumps(event)}")
        
        # Extraer tag_id del path
        tag_id = event.get('pathParameters', {}).get('tag_id')
        
        if not tag_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Tag ID no proporcionado',
                    'message': 'El tag_id es requerido en el path'
                })
            }
        
        # Consultar usando el GSI TagIndex
        response = users_table.query(
            IndexName='TagIndex',
            KeyConditionExpression='tag_id = :tid',
            ExpressionAttributeValues={':tid': tag_id}
        )
        
        if response.get('Count', 0) == 0:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Tag no encontrado',
                    'message': f'No existe un usuario con el tag {tag_id}',
                    'tag_id': tag_id
                })
            }
        
        user = response['Items'][0]
        
        # Formatear respuesta
        response_data = {
            'tag_id': user.get('tag_id'),
            'tag_status': user.get('tag_status', 'active'),
            'tag_created_at': user.get('tag_created_at'),
            'tag_updated_at': user.get('tag_updated_at'),
            'user': {
                'placa': user.get('placa'),
                'nombre': user.get('nombre'),
                'email': user.get('email'),
                'telefono': user.get('telefono'),
                'tipo_usuario': user.get('tipo_usuario'),
                'saldo_disponible': str(user.get('saldo_disponible', '0.00')),
                'estado': user.get('estado', 'activo')
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error consultando tag: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Error interno del servidor',
                'message': str(e)
            })
        }

