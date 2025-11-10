"""
Lambda Function: Generate Invoice
Genera facturas simuladas para transacciones de peaje.
- Modalidad 1 (No Registrado): Factura con cargo premium + multa (50%)
- Modalidad 2 (Registrado): Factura normal (ya pagada)
"""

import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
invoices_table_name = os.environ['INVOICES_TABLE_NAME']
invoices_table = dynamodb.Table(invoices_table_name)


def generate_invoice_number():
    """Genera un número de factura único basado en timestamp"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    return f"FAC-{timestamp}"


def lambda_handler(event, context):
    """
    Handler principal del Lambda.
    
    Input esperado:
    {
        "user_data": {
            "placa": "P-111JKL",
            "nombre": "Ana Torres",
            "email": "ana@email.com",
            "modalidad": 1 o 2,
            "is_registered": true/false
        },
        "toll_data": {
            "peaje_id": "PEAJE001",
            "nombre_peaje": "Carretera Norte"
        },
        "fare_calculation": {
            "base_fare": "15.00",
            "final_fare": "15.00"
        },
        "transaction": {
            "transaction_id": "TXN-123",
            "timestamp": "2025-11-09T10:30:00Z"
        }
    }
    
    Output:
    {
        ...input,
        "invoice": {
            "invoice_id": "FAC-20251109103000",
            "invoice_number": "FAC-20251109103000",
            "placa": "P-111JKL",
            "modalidad": 1,
            "monto_base": "15.00",
            "multa": "7.50",
            "total": "22.50",
            "estado": "pendiente",
            "concepto": "Paso por peaje - Carretera Norte",
            "fecha_emision": "2025-11-09T10:30:00Z",
            "contribuyente": {...}
        }
    }
    """
    
    try:
        print(f"Evento recibido: {json.dumps(event, default=str)}")
        
        user_data = event.get('user_data', {})
        toll_data = event.get('toll_data', {})
        fare_calc = event.get('fare_calculation', {})
        transaction = event.get('transaction', {})
        
        placa = user_data.get('placa')
        modalidad = user_data.get('modalidad', 3)
        nombre = user_data.get('nombre', 'Usuario Desconocido')
        email = user_data.get('email', '')
        
        peaje_nombre = toll_data.get('nombre_peaje', toll_data.get('peaje_id', 'Peaje'))
        
        final_fare = Decimal(str(fare_calc.get('final_fare', '0')))
        transaction_id = transaction.get('transaction_id', 'N/A')
        timestamp = transaction.get('timestamp', datetime.utcnow().isoformat() + 'Z')
        
        # Generar número de factura
        invoice_id = generate_invoice_number()
        
        # Calcular montos según modalidad
        if modalidad == 1:
            # Modalidad 1: No registrado - Cargo premium + Multa 50%
            monto_base = final_fare
            multa = final_fare * Decimal('0.50')  # 50% de multa
            total = monto_base + multa
            estado = "pendiente"
            concepto = f"Paso por peaje - {peaje_nombre} (Pago pendiente + Multa por pago tardío)"
            
        else:
            # Modalidad 2 o 3: Registrado - Factura normal (ya pagada)
            monto_base = final_fare
            multa = Decimal('0')
            total = monto_base
            estado = "pagada"
            concepto = f"Paso por peaje - {peaje_nombre}"
        
        # Datos del contribuyente
        contribuyente = {
            'nombre': nombre,
            'placa': placa,
            'email': email if email else 'N/A'
        }
        
        # Crear registro de factura
        invoice = {
            'invoice_id': invoice_id,
            'invoice_number': invoice_id,
            'placa': placa,
            'modalidad': modalidad,
            'monto_base': str(monto_base),
            'multa': str(multa),
            'total': str(total),
            'estado': estado,
            'concepto': concepto,
            'fecha_emision': timestamp,
            'contribuyente': contribuyente,
            'transaction_id': transaction_id,
            'peaje': {
                'peaje_id': toll_data.get('peaje_id', 'N/A'),
                'nombre': peaje_nombre
            },
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Guardar en DynamoDB
        invoices_table.put_item(Item=invoice)
        
        print(f"Factura generada: {invoice_id} - Total: Q{total} - Estado: {estado}")
        
        # Retornar evento enriquecido
        result = {
            **event,
            'invoice': invoice
        }
        
        return result
        
    except Exception as e:
        print(f"Error generando factura: {str(e)}")
        raise

