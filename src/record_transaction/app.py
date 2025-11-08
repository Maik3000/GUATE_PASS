"""
Lambda Function: Record Transaction
Registra la transacción de peaje en la tabla de transacciones.
"""

import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
transactions_table_name = os.environ['TRANSACTIONS_TABLE_NAME']
transactions_table = dynamodb.Table(transactions_table_name)


def lambda_handler(event, context):
    """
    Handler principal del Lambda.
    
    Input esperado:
    {
        "user_data": {...},
        "toll_data": {...},
        "fare_calculation": {
            "final_fare": "15.00",
            "modality": 1,
            ...
        }
    }
    
    Output:
    {
        ...input,
        "transaction": {
            "transaction_id": "TXN-...",
            "status": "recorded"
        }
    }
    """
    
    try:
        print(f"Evento recibido: {json.dumps(event)}")
        
        # Extraer datos
        user_data = event.get('user_data', {})
        toll_data = event.get('toll_data', {})
        fare_calc = event.get('fare_calculation', {})
        
        placa = user_data.get('placa', 'UNKNOWN')
        peaje_id = toll_data.get('peaje_id')
        timestamp = toll_data.get('timestamp', datetime.utcnow().isoformat())
        
        # Generar transaction_id único
        transaction_id = f"TXN-{peaje_id}-{placa}-{timestamp.replace(':', '').replace('-', '')}"
        
        # Preparar item para DynamoDB
        transaction_item = {
            'transaction_id': transaction_id,
            'placa': placa,
            'peaje_id': peaje_id,
            'nombre_peaje': toll_data.get('nombre_peaje', ''),
            'lane_id': toll_data.get('lane_id', ''),
            'timestamp': timestamp,
            'modalidad': fare_calc.get('modality'),
            'base_fare': Decimal(fare_calc.get('base_fare', '0')),
            'final_fare': Decimal(fare_calc.get('final_fare', '0')),
            'currency': fare_calc.get('currency', 'GTQ'),
            'tag_id': toll_data.get('tag_id'),
            'is_registered': user_data.get('is_registered', False),
            'has_tag': user_data.get('has_tag', False),
            'payment_status': 'pending',  # pending, completed, failed
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Guardar en DynamoDB
        transactions_table.put_item(Item=transaction_item)
        
        print(f"Transacción registrada: {transaction_id}")
        
        # Retornar evento enriquecido
        result = {
            **event,
            'transaction': {
                'transaction_id': transaction_id,
                'status': 'recorded',
                'payment_status': 'pending'
            }
        }
        
        return result
        
    except Exception as e:
        print(f"Error registrando transacción: {str(e)}")
        raise
