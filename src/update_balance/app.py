"""
Lambda Function: Update Balance
Actualiza el balance del usuario registrado (si aplica).
Para usuarios registrados (modalidad 2 o 3), se descuenta del saldo prepago.
Para usuarios no registrados (modalidad 1), no se actualiza balance.
"""

import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
users_table_name = os.environ['USERS_TABLE_NAME']
users_table = dynamodb.Table(users_table_name)


def lambda_handler(event, context):
    """
    Handler principal del Lambda.
    
    Input esperado:
    {
        "user_data": {
            "placa": "P123ABC",
            "modalidad": 1,
            "is_registered": true
        },
        "fare_calculation": {
            "final_fare": "15.00"
        },
        "transaction": {
            "transaction_id": "TXN-..."
        }
    }
    
    Output:
    {
        ...input,
        "balance_update": {
            "updated": true/false,
            "previous_balance": "100.00",
            "new_balance": "85.00",
            "message": "..."
        }
    }
    """
    
    try:
        print(f"Evento recibido: {json.dumps(event)}")
        
        user_data = event.get('user_data', {})
        fare_calc = event.get('fare_calculation', {})
        transaction = event.get('transaction', {})
        
        placa = user_data.get('placa')
        modalidad = user_data.get('modalidad')
        is_registered = user_data.get('is_registered', False)
        final_fare = Decimal(fare_calc.get('final_fare', '0'))
        
        balance_update = {
            'updated': False,
            'message': 'No se actualizó balance'
        }
        
        # Solo actualizar balance si es usuario registrado (modalidad 2 o 3)
        if is_registered and modalidad in [2, 3]:
            
            # Obtener usuario actual
            response = users_table.get_item(Key={'placa': placa})
            
            if 'Item' in response:
                user = response['Item']
                current_balance = Decimal(str(user.get('saldo_disponible', 0)))
                
                # Verificar si tiene saldo suficiente
                if current_balance >= final_fare:
                    new_balance = current_balance - final_fare
                    
                    # Actualizar saldo en DynamoDB
                    users_table.update_item(
                        Key={'placa': placa},
                        UpdateExpression='SET saldo_disponible = :new_balance',
                        ExpressionAttributeValues={
                            ':new_balance': new_balance
                        }
                    )
                    
                    balance_update = {
                        'updated': True,
                        'previous_balance': str(current_balance),
                        'new_balance': str(new_balance),
                        'amount_charged': str(final_fare),
                        'message': 'Balance actualizado exitosamente'
                    }
                    
                    print(f"Balance actualizado para {placa}: {current_balance} -> {new_balance}")
                    
                else:
                    balance_update = {
                        'updated': False,
                        'previous_balance': str(current_balance),
                        'amount_required': str(final_fare),
                        'message': 'Saldo insuficiente',
                        'warning': 'Se requiere recarga'
                    }
                    
                    print(f"Saldo insuficiente para {placa}: {current_balance} < {final_fare}")
            else:
                balance_update['message'] = 'Usuario no encontrado en base de datos'
                
        elif modalidad == 1:
            balance_update['message'] = 'Usuario no registrado - Pago en efectivo'
        
        # Retornar evento enriquecido
        result = {
            **event,
            'balance_update': balance_update
        }
        
        return result
        
    except Exception as e:
        print(f"Error actualizando balance: {str(e)}")
        raise
