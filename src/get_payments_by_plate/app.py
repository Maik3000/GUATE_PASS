"""
Lambda Function: Get Payments by Plate
Consulta el historial de transacciones/pagos de un vehículo específico.

GET /history/payments/{placa}
"""

import json
import os
from decimal import Decimal
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
TRANSACTIONS_TABLE = os.environ.get('TRANSACTIONS_TABLE_NAME', 'GuatepassTransactions-dev')


class DecimalEncoder(json.JSONEncoder):
    """Helper para serializar Decimal a JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Handler principal para consultar historial de pagos por placa.
    
    Event esperado:
    {
        "pathParameters": {
            "placa": "P-123ABC"
        },
        "queryStringParameters": {
            "limit": "10",      # Opcional: número de resultados (default: 20)
            "from_date": "",     # Opcional: fecha inicio (ISO 8601)
            "to_date": ""        # Opcional: fecha fin (ISO 8601)
        }
    }
    """
    print(f"[INFO] Event recibido: {json.dumps(event)}")
    
    try:
        # Extraer placa del path
        placa = event.get('pathParameters', {}).get('placa', '').strip().upper()
        
        if not placa:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Parámetro placa es requerido',
                    'statusCode': 400
                })
            }
        
        print(f"[INFO] Consultando historial de pagos para placa: {placa}")
        
        # Extraer query parameters opcionales
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 20))
        from_date = query_params.get('from_date')
        to_date = query_params.get('to_date')
        
        # Consultar transacciones
        transactions = query_transactions_by_plate(
            placa, 
            limit=limit,
            from_date=from_date,
            to_date=to_date
        )
        
        if not transactions:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'placa': placa,
                    'total_transactions': 0,
                    'transactions': [],
                    'message': f'No se encontraron transacciones para la placa {placa}'
                }, cls=DecimalEncoder)
            }
        
        # Calcular estadísticas
        total_amount = sum(float(t.get('amount_charged', 0)) for t in transactions)
        
        response_data = {
            'placa': placa,
            'total_transactions': len(transactions),
            'total_amount': round(total_amount, 2),
            'transactions': transactions,
            'message': f'Historial de pagos para {placa} obtenido exitosamente'
        }
        
        print(f"[SUCCESS] {len(transactions)} transacciones encontradas para {placa}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"[ERROR] Error al consultar historial de pagos: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Error interno al consultar historial de pagos',
                'details': str(e),
                'statusCode': 500
            })
        }


def query_transactions_by_plate(placa, limit=20, from_date=None, to_date=None):
    """
    Consulta transacciones de una placa usando el GSI PlacaCreatedIndex.
    
    Args:
        placa (str): Placa del vehículo
        limit (int): Número máximo de resultados
        from_date (str): Fecha inicio (ISO 8601) - opcional
        to_date (str): Fecha fin (ISO 8601) - opcional
    
    Returns:
        list: Lista de transacciones ordenadas por fecha descendente
    """
    table = dynamodb.Table(TRANSACTIONS_TABLE)
    
    try:
        # Query usando el GSI
        query_params = {
            'IndexName': 'PlacaTimestampIndex',
            'KeyConditionExpression': Key('placa').eq(placa),
            'Limit': limit,
            'ScanIndexForward': False  # Orden descendente (más recientes primero)
        }
        
        # Si hay filtro de fechas, agregar FilterExpression
        if from_date or to_date:
            filter_expressions = []
            expression_values = {}
            
            if from_date:
                filter_expressions.append('#ts >= :from_date')
                expression_values[':from_date'] = from_date
                query_params['ExpressionAttributeNames'] = {'#ts': 'timestamp'}
            
            if to_date:
                filter_expressions.append('#ts <= :to_date')
                expression_values[':to_date'] = to_date
                query_params['ExpressionAttributeNames'] = {'#ts': 'timestamp'}
            
            if filter_expressions:
                query_params['FilterExpression'] = ' AND '.join(filter_expressions)
                query_params['ExpressionAttributeValues'] = expression_values
        
        response = table.query(**query_params)
        transactions = response.get('Items', [])
        
        print(f"[INFO] {len(transactions)} transacciones encontradas para placa {placa}")
        
        # Formatear transacciones para respuesta
        formatted_transactions = []
        for tx in transactions:
            timestamp_val = tx.get('timestamp', tx.get('created_at', ''))
            formatted_tx = {
                'transaction_id': tx.get('transaction_id'),
                'placa': tx.get('placa'),
                'toll_id': tx.get('toll_id'),
                'toll_name': tx.get('toll_name', 'N/A'),
                'modalidad': tx.get('modalidad'),
                'amount_charged': float(tx.get('amount_charged', 0)),
                'base_fare': float(tx.get('base_fare', 0)),
                'multiplier': float(tx.get('multiplier', 1.0)),
                'timestamp': timestamp_val,
                'created_at': timestamp_val,
                'status': tx.get('status', 'completed')
            }
            formatted_transactions.append(formatted_tx)
        
        return formatted_transactions
        
    except Exception as e:
        print(f"[ERROR] Error al consultar DynamoDB: {str(e)}")
        raise

