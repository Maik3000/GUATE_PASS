"""
Lambda Function: Get Invoices by Plate
Consulta el historial de facturas de un vehículo específico.

GET /history/invoices/{placa}
"""

import json
import os
from decimal import Decimal
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
INVOICES_TABLE = os.environ.get('INVOICES_TABLE_NAME', 'GuatepassInvoices-dev')


class DecimalEncoder(json.JSONEncoder):
    """Helper para serializar Decimal a JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Handler principal para consultar historial de facturas por placa.
    
    Event esperado:
    {
        "pathParameters": {
            "placa": "P-123ABC"
        },
        "queryStringParameters": {
            "limit": "10",       # Opcional: número de resultados (default: 20)
            "status": "pendiente" # Opcional: filtrar por estado (pendiente/pagada)
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
        
        print(f"[INFO] Consultando historial de facturas para placa: {placa}")
        
        # Extraer query parameters opcionales
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 20))
        status_filter = query_params.get('status')  # pendiente o pagada
        
        # Consultar facturas
        invoices = query_invoices_by_plate(
            placa, 
            limit=limit,
            status_filter=status_filter
        )
        
        if not invoices:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'placa': placa,
                    'total_invoices': 0,
                    'invoices': [],
                    'message': f'No se encontraron facturas para la placa {placa}'
                }, cls=DecimalEncoder)
            }
        
        # Calcular estadísticas
        total_amount = sum(float(inv.get('total', 0)) for inv in invoices)
        pending_invoices = [inv for inv in invoices if inv.get('estado') == 'pendiente']
        paid_invoices = [inv for inv in invoices if inv.get('estado') == 'pagada']
        
        total_pending = sum(float(inv.get('total', 0)) for inv in pending_invoices)
        total_paid = sum(float(inv.get('total', 0)) for inv in paid_invoices)
        
        response_data = {
            'placa': placa,
            'summary': {
                'total_invoices': len(invoices),
                'pending_invoices': len(pending_invoices),
                'paid_invoices': len(paid_invoices),
                'total_amount': round(total_amount, 2),
                'total_pending': round(total_pending, 2),
                'total_paid': round(total_paid, 2)
            },
            'invoices': invoices,
            'message': f'Historial de facturas para {placa} obtenido exitosamente'
        }
        
        print(f"[SUCCESS] {len(invoices)} facturas encontradas para {placa}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"[ERROR] Error al consultar historial de facturas: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Error interno al consultar historial de facturas',
                'details': str(e),
                'statusCode': 500
            })
        }


def query_invoices_by_plate(placa, limit=20, status_filter=None):
    """
    Consulta facturas de una placa usando el GSI PlacaCreatedIndex.
    
    Args:
        placa (str): Placa del vehículo
        limit (int): Número máximo de resultados
        status_filter (str): Filtrar por estado (pendiente/pagada) - opcional
    
    Returns:
        list: Lista de facturas ordenadas por fecha descendente
    """
    table = dynamodb.Table(INVOICES_TABLE)
    
    try:
        # Query usando el GSI
        query_params = {
            'IndexName': 'PlacaCreatedIndex',
            'KeyConditionExpression': Key('placa').eq(placa),
            'Limit': limit,
            'ScanIndexForward': False  # Orden descendente (más recientes primero)
        }
        
        # Si hay filtro de estado, agregar FilterExpression
        if status_filter and status_filter in ['pendiente', 'pagada']:
            query_params['FilterExpression'] = 'estado = :status'
            query_params['ExpressionAttributeValues'] = {':status': status_filter}
        
        response = table.query(**query_params)
        invoices = response.get('Items', [])
        
        print(f"[INFO] {len(invoices)} facturas encontradas para placa {placa}")
        
        # Formatear facturas para respuesta
        formatted_invoices = []
        for inv in invoices:
            formatted_inv = {
                'invoice_id': inv.get('invoice_id'),
                'placa': inv.get('placa'),
                'modalidad': inv.get('modalidad'),
                'monto_base': float(inv.get('monto_base', 0)),
                'multa': float(inv.get('multa', 0)),
                'total': float(inv.get('total', 0)),
                'estado': inv.get('estado'),
                'concepto': inv.get('concepto', 'N/A'),
                'transaction_id': inv.get('transaction_id'),
                'toll_name': inv.get('toll_name', 'N/A'),
                'created_at': inv.get('created_at'),
                'contribuyente': inv.get('contribuyente', {})
            }
            formatted_invoices.append(formatted_inv)
        
        return formatted_invoices
        
    except Exception as e:
        print(f"[ERROR] Error al consultar DynamoDB: {str(e)}")
        raise

