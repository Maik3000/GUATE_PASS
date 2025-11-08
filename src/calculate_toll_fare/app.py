"""
Lambda Function: Calculate Toll Fare
Calcula la tarifa del peaje según la modalidad del usuario.

Modalidades:
- Modalidad 1: Usuario NO registrado → Tarifa base + 50%
- Modalidad 2: Usuario registrado SIN tag → Tarifa base + 20%
- Modalidad 3: Usuario registrado CON tag → Tarifa base (sin recargo)
"""

import json
import os
from decimal import Decimal

# Tarifas base por tipo de peaje (en GTQ)
TOLL_BASE_RATES = {
    'carretera_norte': Decimal('15.00'),
    'carretera_sur': Decimal('12.00'),
    'autopista_palín': Decimal('10.00'),
    'anillo_periferico': Decimal('8.00'),
    'default': Decimal('10.00')
}

# Multiplicadores por modalidad
MODALITY_MULTIPLIERS = {
    1: Decimal('1.50'),    # No registrado: 150% (+50%)
    2: Decimal('1.20'),    # Sin tag: 120% (+20%)
    3: Decimal('1.00')     # Con tag: 100% (sin recargo)
}


def lambda_handler(event, context):
    """
    Handler principal del Lambda.
    
    Input esperado:
    {
        "user_data": {
            "placa": "P123ABC",
            "modalidad": 1,
            "has_tag": true,
            "is_registered": true
        },
        "toll_data": {
            "peaje_id": "PEAJE001",
            "nombre_peaje": "carretera_norte",
            "timestamp": "2024-01-15T10:30:00Z",
            "lane_id": "LANE-01"
        }
    }
    
    Output:
    {
        ...input,
        "fare_calculation": {
            "base_fare": "15.00",
            "modality": 1,
            "multiplier": "1.00",
            "final_fare": "15.00",
            "currency": "GTQ"
        }
    }
    """
    
    try:
        print(f"Evento recibido: {json.dumps(event)}")
        
        # Extraer datos del evento
        user_data = event.get('user_data', {})
        toll_data = event.get('toll_data', {})
        
        modalidad = user_data.get('modalidad')
        nombre_peaje = toll_data.get('nombre_peaje', 'default')
        
        # Validar que tenemos los datos necesarios
        if not modalidad:
            raise ValueError("Falta 'modalidad' en user_data")
        
        # Obtener tarifa base
        base_fare = TOLL_BASE_RATES.get(
            nombre_peaje.lower().replace(' ', '_'),
            TOLL_BASE_RATES['default']
        )
        
        # Obtener multiplicador por modalidad
        multiplier = MODALITY_MULTIPLIERS.get(modalidad, Decimal('1.50'))
        
        # Calcular tarifa final
        final_fare = (base_fare * multiplier).quantize(Decimal('0.01'))
        
        # Preparar resultado
        fare_calculation = {
            'base_fare': str(base_fare),
            'modality': modalidad,
            'multiplier': str(multiplier),
            'final_fare': str(final_fare),
            'currency': 'GTQ',
            'toll_name': nombre_peaje
        }
        
        print(f"Tarifa calculada: {json.dumps(fare_calculation)}")
        
        # Retornar el evento enriquecido con el cálculo
        result = {
            **event,
            'fare_calculation': fare_calculation
        }
        
        return result
        
    except Exception as e:
        print(f"Error calculando tarifa: {str(e)}")
        raise

