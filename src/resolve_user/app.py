"""
GUATEPASS - Resolve User Profile Function
==========================================
Lambda function que determina la modalidad del usuario al pasar por peaje.

Trigger: EventBridge rule (guatepass.toll.detected)
"""

import json
import os
import boto3
from typing import Dict, Any, Optional

# Clientes AWS
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
USERS_TABLE_NAME = os.environ['USERS_TABLE_NAME']
users_table = dynamodb.Table(USERS_TABLE_NAME)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler que procesa eventos de EventBridge y determina la modalidad del usuario.
    
    Modalidades:
    - Modalidad 1: Usuario NO registrado (cobro tradicional + multa)
    - Modalidad 2: Usuario registrado en app (cobro digital)
    - Modalidad 3: Usuario con Tag (cobro express)
    
    Args:
        event: Evento de EventBridge con información del peaje
        context: Contexto de ejecución Lambda
        
    Returns:
        Diccionario con información del usuario y modalidad
    """
    print(f"[INFO] ResolveUserProfile - Event: {json.dumps(event)}")
    
    try:
        # Extraer detail del evento de EventBridge
        detail = event.get('detail', {})
        
        placa = detail.get('placa')
        tag_id = detail.get('tag_id')
        peaje_id = detail.get('peaje_id')
        event_id = detail.get('event_id')
        
        if not placa:
            raise ValueError("Placa no encontrada en el evento")
        
        print(f"[INFO] Resolviendo perfil para placa: {placa}, tag_id: {tag_id}")
        
        # Buscar usuario en DynamoDB
        user_profile = find_user(placa, tag_id)
        
        # Determinar modalidad
        modalidad_info = determine_modality(user_profile, tag_id)
        
        # Construir resultado
        result = {
            'event_id': event_id,
            'placa': placa,
            'peaje_id': peaje_id,
            'tag_id': tag_id,
            'user_profile': user_profile,
            'modalidad': modalidad_info['modalidad'],
            'tipo_cobro': modalidad_info['tipo_cobro'],
            'recargo_aplica': modalidad_info['recargo_aplica'],
            'timestamp': detail.get('timestamp')
        }
        
        print(f"[SUCCESS] Modalidad determinada: {modalidad_info['modalidad']} para placa {placa}")
        print(f"[INFO] Resultado: {json.dumps(result)}")
        
        # TODO: En Slice #4, aquí se invocará Step Functions
        # Por ahora solo loggeamos
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error resolviendo perfil de usuario: {str(e)}")
        raise


def find_user(placa: str, tag_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Busca al usuario en DynamoDB por placa o tag_id.
    
    Args:
        placa: Placa del vehículo
        tag_id: ID del Tag (puede ser None)
        
    Returns:
        Diccionario con información del usuario o None si no existe
    """
    try:
        # Primero buscar por placa
        response = users_table.get_item(Key={'placa': placa})
        
        if 'Item' in response:
            user = response['Item']
            print(f"[INFO] Usuario encontrado por placa: {placa}")
            
            # Convertir Decimal a float para JSON
            if 'saldo_disponible' in user:
                user['saldo_disponible'] = float(user['saldo_disponible'])
            
            return user
        
        # Si no se encontró por placa y hay tag_id, buscar por tag
        if tag_id:
            response = users_table.query(
                IndexName='TagIndex',
                KeyConditionExpression='tag_id = :tid',
                ExpressionAttributeValues={':tid': tag_id}
            )
            
            if response['Items']:
                user = response['Items'][0]
                print(f"[INFO] Usuario encontrado por tag_id: {tag_id}")
                
                # Convertir Decimal a float
                if 'saldo_disponible' in user:
                    user['saldo_disponible'] = float(user['saldo_disponible'])
                
                return user
        
        print(f"[INFO] Usuario no encontrado: placa={placa}, tag_id={tag_id}")
        return None
        
    except Exception as e:
        print(f"[ERROR] Error buscando usuario: {str(e)}")
        raise


def determine_modality(user_profile: Optional[Dict[str, Any]], tag_id: Optional[str]) -> Dict[str, Any]:
    """
    Determina la modalidad de cobro según el perfil del usuario.
    
    Args:
        user_profile: Información del usuario (puede ser None)
        tag_id: ID del Tag detectado
        
    Returns:
        Diccionario con modalidad y tipo de cobro
    """
    # Modalidad 1: Usuario NO registrado
    if not user_profile:
        return {
            'modalidad': 1,
            'tipo_cobro': 'tradicional',
            'recargo_aplica': True,
            'descripcion': 'Usuario no registrado - Cobro premium + multa',
            'debe_invitar': True  # Debe enviar invitación si tiene email/teléfono
        }
    
    # Modalidad 3: Usuario con Tag
    if user_profile.get('tiene_tag') and tag_id:
        # Verificar que el tag_id coincida con el del usuario
        if user_profile.get('tag_id') == tag_id:
            return {
                'modalidad': 3,
                'tipo_cobro': 'express',
                'recargo_aplica': False,
                'descripcion': 'Usuario con Tag - Cobro automático express',
                'debe_invitar': False
            }
        else:
            print(f"[WARNING] Tag ID no coincide: usuario={user_profile.get('tag_id')}, detectado={tag_id}")
    
    # Modalidad 2: Usuario registrado (sin Tag o Tag no detectado)
    if user_profile.get('tipo_usuario') == 'registrado':
        return {
            'modalidad': 2,
            'tipo_cobro': 'digital',
            'recargo_aplica': False,
            'descripcion': 'Usuario registrado - Cobro automático digital',
            'debe_invitar': False
        }
    
    # Por defecto, tratar como no registrado
    return {
        'modalidad': 1,
        'tipo_cobro': 'tradicional',
        'recargo_aplica': True,
        'descripcion': 'Usuario no registrado - Cobro premium + multa',
        'debe_invitar': True
    }


if __name__ == "__main__":
    # Para pruebas locales
    print("Esta función debe ejecutarse en AWS Lambda")

