"""
GUATEPASS - Ingest Toll Function
=================================
Lambda function que recibe eventos de paso por peaje desde el sistema de cámaras.

Endpoint: POST /webhook/toll
"""

import json
import os
import boto3
from typing import Dict, Any
from datetime import datetime
import uuid

# Cliente EventBridge
eventbridge = boto3.client('events')

# Variables de entorno
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal que recibe eventos de paso por peaje.
    
    Payload esperado:
    {
        "placa": "P-123ABC",
        "peaje_id": "PEAJE_ZONA10",
        "tag_id": "TAG-001",  # Puede ser null
        "timestamp": "2025-11-07T14:30:00Z"
    }
    
    Args:
        event: Evento de API Gateway con el payload del webhook
        context: Contexto de ejecución Lambda
        
    Returns:
        Response HTTP 200 (aceptado) o 400 (error de validación)
    """
    print(f"[INFO] POST /webhook/toll - Event: {json.dumps(event)}")
    
    try:
        # Parsear body del request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event  # Para pruebas directas
        
        # Validar campos requeridos
        validation_error = validate_toll_event(body)
        if validation_error:
            return error_response(400, validation_error)
        
        # Enriquecer evento con metadata
        enriched_event = enrich_toll_event(body)
        
        print(f"[INFO] Evento validado y enriquecido: {json.dumps(enriched_event)}")
        
        # Publicar evento a EventBridge
        publish_to_eventbridge(enriched_event)
        
        print(f"[SUCCESS] Evento de peaje procesado: placa={enriched_event['placa']}, peaje={enriched_event['peaje_id']}")
        
        return success_response(200, {
            'message': 'Evento de peaje recibido exitosamente',
            'event_id': enriched_event['event_id'],
            'placa': enriched_event['placa'],
            'peaje_id': enriched_event['peaje_id']
        })
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON inválido: {str(e)}")
        return error_response(400, f"JSON inválido: {str(e)}")
    
    except Exception as e:
        print(f"[ERROR] Error procesando evento: {str(e)}")
        return error_response(500, f"Error interno: {str(e)}")


def validate_toll_event(body: Dict[str, Any]) -> str:
    """
    Valida que el evento tenga todos los campos requeridos.
    
    Args:
        body: Payload del webhook
        
    Returns:
        String con mensaje de error, o None si es válido
    """
    # Campos requeridos
    required_fields = ['placa', 'peaje_id', 'timestamp']
    
    for field in required_fields:
        if field not in body or not body[field]:
            return f"Campo requerido faltante: {field}"
    
    # Validar formato de placa (básico)
    placa = body['placa'].strip()
    if len(placa) < 5:
        return f"Formato de placa inválido: {placa}"
    
    # Validar timestamp (formato ISO 8601)
    try:
        datetime.fromisoformat(body['timestamp'].replace('Z', '+00:00'))
    except ValueError:
        return f"Formato de timestamp inválido: {body['timestamp']}"
    
    return None  # Válido


def enrich_toll_event(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriquece el evento con metadata adicional.
    
    Args:
        body: Payload original del webhook
        
    Returns:
        Evento enriquecido con campos adicionales
    """
    # Manejar tag_id que puede ser None o string
    tag_id = body.get('tag_id')
    if tag_id:
        tag_id = tag_id.strip() if isinstance(tag_id, str) else None
    else:
        tag_id = None
    
    return {
        'event_id': str(uuid.uuid4()),
        'event_type': 'toll.detected',
        'placa': body['placa'].upper().strip(),
        'peaje_id': body['peaje_id'].strip(),
        'tag_id': tag_id,
        'timestamp': body['timestamp'],
        'received_at': datetime.utcnow().isoformat() + 'Z',
        'environment': ENVIRONMENT
    }


def publish_to_eventbridge(toll_event: Dict[str, Any]) -> None:
    """
    Publica el evento a EventBridge para procesamiento asíncrono.
    
    Args:
        toll_event: Evento enriquecido de peaje
    """
    try:
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'guatepass.toll',
                    'DetailType': 'TollDetected',
                    'Detail': json.dumps(toll_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        if response['FailedEntryCount'] > 0:
            raise Exception(f"Error publicando a EventBridge: {response['Entries']}")
        
        print(f"[INFO] Evento publicado a EventBridge: event_id={toll_event['event_id']}")
        
    except Exception as e:
        print(f"[ERROR] Error publicando a EventBridge: {str(e)}")
        raise


def success_response(status_code: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera respuesta exitosa HTTP."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(data, ensure_ascii=False)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Genera respuesta de error HTTP."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
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

