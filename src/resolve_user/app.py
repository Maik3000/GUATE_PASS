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
stepfunctions = boto3.client('stepfunctions')

# Variables de entorno
USERS_TABLE_NAME = os.environ['USERS_TABLE_NAME']
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')
users_table = dynamodb.Table(USERS_TABLE_NAME)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler que procesa eventos de EventBridge y determina la modalidad del usuario.
    
    Modalidades:
    - Modalidad 1: Usuario registrado CON Tag (descuento)
    - Modalidad 2: Usuario registrado SIN Tag (normal)
    - Modalidad 3: Usuario NO registrado (premium + multa)
    
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
        peaje_nombre = detail.get('peaje_nombre', 'Desconocido')
        event_id = detail.get('event_id')
        
        if not placa:
            raise ValueError("Placa no encontrada en el evento")
        
        print(f"[INFO] Resolviendo perfil para placa: {placa}, tag_id: {tag_id}")
        
        # Buscar usuario en DynamoDB
        user_data = find_user(placa, tag_id)
        
        # Determinar modalidad
        modalidad_info = determine_modality(user_data, tag_id)
        
        # Construir perfil completo del usuario
        user_profile = {
            'placa': placa,
            'modalidad': modalidad_info['modalidad'],
            'is_registered': user_data is not None,
            'has_tag': modalidad_info['modalidad'] == 3,
            'tag_id': user_data.get('tag_id') if user_data else None,
            'nombre': user_data.get('nombre') if user_data else None,
            'email': user_data.get('email') if user_data else None,
            'tipo_cobro': modalidad_info['tipo_cobro'],
            'descripcion': modalidad_info['descripcion']
        }
        
        # Construir información del peaje
        peaje_info = {
            'peaje_id': peaje_id,
            'nombre_peaje': peaje_nombre,
            'lane_id': detail.get('lane_id', 'LANE-01'),
            'tag_id': tag_id,
            'timestamp': detail.get('timestamp')
        }
        
        # Payload para Step Function (formato esperado por los Lambdas siguientes)
        step_function_input = {
            'event_id': event_id,
            'user_data': user_profile,
            'toll_data': peaje_info,
            'original_event': detail
        }
        
        print(f"[SUCCESS] Modalidad determinada: {modalidad_info['modalidad']} para placa {placa}")
        print(f"[INFO] Iniciando Step Function con input: {json.dumps(step_function_input)}")
        
        # Iniciar ejecución de Step Function
        if STATE_MACHINE_ARN:
            execution_name = f"toll-{event_id}-{placa}".replace(':', '-').replace('.', '-')[:80]
            
            sf_response = stepfunctions.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=execution_name,
                input=json.dumps(step_function_input)
            )
            
            execution_arn = sf_response['executionArn']
            print(f"[SUCCESS] Step Function iniciada: {execution_arn}")
            
            return {
                'statusCode': 200,
                'execution_arn': execution_arn,
                'event_id': event_id,
                'placa': placa,
                'modalidad': modalidad_info['modalidad']
            }
        else:
            print("[WARNING] STATE_MACHINE_ARN no configurado, solo se resolvió el perfil")
            return step_function_input
        
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
    
    Modalidades:
    - Modalidad 1: Usuario NO registrado (tarifa más alta, +50%)
    - Modalidad 2: Usuario registrado SIN Tag (tarifa intermedia, +20%)
    - Modalidad 3: Usuario registrado CON Tag (tarifa más baja, tarifa base)
    
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
            'tipo_cobro': 'sin_cuenta',
            'recargo_aplica': True,
            'descripcion': 'Usuario no registrado - Tarifa más alta (+50%)',
            'debe_invitar': True
        }
    
    # Modalidad 3: Usuario registrado CON Tag
    if user_profile.get('tiene_tag') and tag_id:
        # Verificar que el tag_id coincida con el del usuario
        if user_profile.get('tag_id') == tag_id:
            return {
                'modalidad': 3,
                'tipo_cobro': 'express',
                'recargo_aplica': False,
                'descripcion': 'Usuario registrado con Tag - Tarifa base (sin recargo)',
                'debe_invitar': False
            }
        else:
            print(f"[WARNING] Tag ID no coincide: usuario={user_profile.get('tag_id')}, detectado={tag_id}")
    
    # Modalidad 2: Usuario registrado SIN Tag (o Tag no detectado)
    return {
        'modalidad': 2,
        'tipo_cobro': 'digital',
        'recargo_aplica': True,
        'descripcion': 'Usuario registrado sin Tag - Tarifa intermedia (+20%)',
        'debe_invitar': False
    }


if __name__ == "__main__":
    # Para pruebas locales
    print("Esta función debe ejecutarse en AWS Lambda")

