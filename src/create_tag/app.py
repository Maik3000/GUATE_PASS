"""
Lambda Function: Create/Associate Tag
Asocia un Tag a un usuario registrado por su placa.
Actualiza los campos tiene_tag y tag_id en la tabla GuatepassUsers.
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
    POST /users/{placa}/tag
    Body:
    {
        "tag_id": "TAG-12345",
        "tag_status": "active"  // optional, default: active
    }
    
    Output:
    {
        "statusCode": 200,
        "body": {
            "message": "Tag asociado exitosamente",
            "placa": "P123ABC",
            "tag_id": "TAG-12345",
            "tag_status": "active",
            "updated_at": "2024-01-15T10:30:00Z"
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
        
        # Parsear body
        body = json.loads(event.get('body', '{}'))
        tag_id = body.get('tag_id')
        tag_status = body.get('tag_status', 'active')
        
        if not tag_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Tag ID no proporcionado',
                    'message': 'El campo tag_id es requerido'
                })
            }
        
        # Validar formato de tag_id
        if not tag_id.startswith('TAG-'):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Formato de Tag ID inválido',
                    'message': 'El tag_id debe comenzar con TAG-'
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
        
        # Verificar si el usuario ya tiene un tag
        if user.get('tiene_tag', False):
            return {
                'statusCode': 409,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Usuario ya tiene tag',
                    'message': f'El usuario ya tiene el tag {user.get("tag_id")} asociado',
                    'current_tag_id': user.get('tag_id'),
                    'hint': 'Use PUT para actualizar o DELETE para eliminar primero'
                })
            }
        
        # Verificar si el tag_id ya está en uso por otro usuario
        # Usamos el GSI TagIndex para buscar
        try:
            tag_check = users_table.query(
                IndexName='TagIndex',
                KeyConditionExpression='tag_id = :tid',
                ExpressionAttributeValues={':tid': tag_id}
            )
            
            if tag_check.get('Count', 0) > 0:
                existing_user = tag_check['Items'][0]
                return {
                    'statusCode': 409,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Tag ya está en uso',
                        'message': f'El tag {tag_id} ya está asociado a la placa {existing_user.get("placa")}',
                        'existing_placa': existing_user.get('placa')
                    })
                }
        except Exception as e:
            print(f"Error verificando tag duplicado: {str(e)}")
            # Continuar si el índice no existe o hay error
        
        # Asociar el tag al usuario
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        users_table.update_item(
            Key={'placa': placa},
            UpdateExpression='SET tiene_tag = :has_tag, tag_id = :tid, tag_status = :status, tag_created_at = :created',
            ExpressionAttributeValues={
                ':has_tag': True,
                ':tid': tag_id,
                ':status': tag_status,
                ':created': timestamp
            }
        )
        
        print(f"Tag {tag_id} asociado exitosamente a la placa {placa}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Tag asociado exitosamente',
                'placa': placa,
                'tag_id': tag_id,
                'tag_status': tag_status,
                'updated_at': timestamp
            })
        }
        
    except json.JSONDecodeError as e:
        print(f"Error parseando JSON: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'JSON inválido',
                'message': str(e)
            })
        }
    
    except Exception as e:
        print(f"Error asociando tag: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Error interno del servidor',
                'message': str(e)
            })
        }

