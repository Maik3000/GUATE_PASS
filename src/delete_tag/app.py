"""
Lambda Function: Delete Tag
Desasocia un Tag de un usuario.
Marca tiene_tag como False y limpia tag_id.
"""

import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
users_table_name = os.environ['USERS_TABLE_NAME']
users_table = dynamodb.Table(users_table_name)


def lambda_handler(event, context):
    """
    Handler principal del Lambda.
    
    Input esperado:
    DELETE /users/{placa}/tag
    
    Output:
    {
        "statusCode": 200,
        "body": {
            "message": "Tag desasociado exitosamente",
            "placa": "P123ABC",
            "removed_tag_id": "TAG-12345",
            "deleted_at": "2024-01-15T10:30:00Z"
        }
    }
    """
    
    try:
        print(f"Evento recibido: {json.dumps(event)}")
        
        # Extraer placa del path
        placa = event.get('pathParameters', {}).get('placa')
        
        if not placa:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Placa no proporcionada',
                    'message': 'La placa es requerida en el path'
                })
            }
        
        # Verificar si el usuario existe
        response = users_table.get_item(Key={'placa': placa})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Usuario no encontrado',
                    'message': f'No existe un usuario con la placa {placa}'
                })
            }
        
        user = response['Item']
        
        # Verificar si el usuario tiene un tag
        if not user.get('tiene_tag', False):
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Usuario no tiene tag',
                    'message': f'El usuario con placa {placa} no tiene un tag asociado',
                    'current_state': {
                        'tiene_tag': False,
                        'tag_id': user.get('tag_id')
                    }
                })
            }
        
        removed_tag_id = user.get('tag_id')
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Desasociar el tag del usuario
        # En lugar de eliminar el atributo, lo marcamos como vacío
        # para mantener el historial en tag_deleted_at
        users_table.update_item(
            Key={'placa': placa},
            UpdateExpression='SET tiene_tag = :has_tag, tag_id = :empty, tag_status = :empty_str, tag_deleted_at = :deleted',
            ExpressionAttributeValues={
                ':has_tag': False,
                ':empty': '',  # String vacío para mantener el tipo
                ':empty_str': '',
                ':deleted': timestamp
            }
        )
        
        print(f"Tag {removed_tag_id} desasociado exitosamente de la placa {placa}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Tag desasociado exitosamente',
                'placa': placa,
                'removed_tag_id': removed_tag_id,
                'deleted_at': timestamp,
                'note': 'El usuario puede volver a asociar un tag usando POST /users/{placa}/tag'
            })
        }
        
    except Exception as e:
        print(f"Error desasociando tag: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Error interno del servidor',
                'message': str(e)
            })
        }

