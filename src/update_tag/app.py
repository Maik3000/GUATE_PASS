"""
Lambda Function: Update Tag
Actualiza la información del Tag asociado a un usuario.
Permite cambiar el tag_id o el tag_status.
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
    PUT /users/{placa}/tag
    Body:
    {
        "tag_id": "TAG-67890",  // optional
        "tag_status": "inactive"  // optional: active, inactive, blocked
    }
    
    Output:
    {
        "statusCode": 200,
        "body": {
            "message": "Tag actualizado exitosamente",
            "placa": "P123ABC",
            "old_tag_id": "TAG-12345",
            "new_tag_id": "TAG-67890",
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
        new_tag_id = body.get('tag_id')
        new_tag_status = body.get('tag_status')
        
        if not new_tag_id and not new_tag_status:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Sin datos para actualizar',
                    'message': 'Debe proporcionar al menos tag_id o tag_status'
                })
            }
        
        # Validar formato de tag_id si se proporciona
        if new_tag_id and not new_tag_id.startswith('TAG-'):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Formato de Tag ID inválido',
                    'message': 'El tag_id debe comenzar con TAG-'
                })
            }
        
        # Validar tag_status si se proporciona
        valid_statuses = ['active', 'inactive', 'blocked', 'lost', 'stolen']
        if new_tag_status and new_tag_status not in valid_statuses:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Estado de tag inválido',
                    'message': f'El tag_status debe ser uno de: {", ".join(valid_statuses)}'
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
                    'hint': 'Use POST /users/{placa}/tag para crear uno'
                })
            }
        
        old_tag_id = user.get('tag_id')
        old_tag_status = user.get('tag_status', 'active')
        
        # Si se está cambiando el tag_id, verificar que no esté en uso
        if new_tag_id and new_tag_id != old_tag_id:
            try:
                tag_check = users_table.query(
                    IndexName='TagIndex',
                    KeyConditionExpression='tag_id = :tid',
                    ExpressionAttributeValues={':tid': new_tag_id}
                )
                
                if tag_check.get('Count', 0) > 0:
                    existing_user = tag_check['Items'][0]
                    return {
                        'statusCode': 409,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'error': 'Tag ya está en uso',
                            'message': f'El tag {new_tag_id} ya está asociado a la placa {existing_user.get("placa")}',
                            'existing_placa': existing_user.get('placa')
                        })
                    }
            except Exception as e:
                print(f"Error verificando tag duplicado: {str(e)}")
        
        # Construir la expresión de actualización
        timestamp = datetime.utcnow().isoformat() + 'Z'
        update_expression = 'SET tag_updated_at = :updated'
        expression_values = {':updated': timestamp}
        
        if new_tag_id:
            update_expression += ', tag_id = :tid'
            expression_values[':tid'] = new_tag_id
        
        if new_tag_status:
            update_expression += ', tag_status = :status'
            expression_values[':status'] = new_tag_status
        
        # Actualizar el tag
        users_table.update_item(
            Key={'placa': placa},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        print(f"Tag actualizado para la placa {placa}: {old_tag_id} -> {new_tag_id or old_tag_id}")
        
        response_data = {
            'message': 'Tag actualizado exitosamente',
            'placa': placa,
            'updated_at': timestamp
        }
        
        if new_tag_id:
            response_data['old_tag_id'] = old_tag_id
            response_data['new_tag_id'] = new_tag_id
        else:
            response_data['tag_id'] = old_tag_id
        
        if new_tag_status:
            response_data['old_status'] = old_tag_status
            response_data['new_status'] = new_tag_status
        else:
            response_data['tag_status'] = old_tag_status
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
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
        print(f"Error actualizando tag: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Error interno del servidor',
                'message': str(e)
            })
        }

