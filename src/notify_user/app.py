"""
Lambda Function: Notify User
Envía notificaciones por email según la modalidad del usuario.
- Modalidad 1 (No Registrado): Invitación para registrarse en GuatePass
- Modalidad 2 (Registrado): Notificación de cobro realizado
"""

import json
import os
from datetime import datetime


def format_currency(amount):
    """Formatea un monto a formato de moneda guatemalteca"""
    return f"Q{float(amount):.2f}"


def format_datetime(iso_datetime):
    """Formatea una fecha ISO a formato legible"""
    try:
        dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %I:%M %p')
    except:
        return iso_datetime


def get_invitation_email_template(user_data, toll_data, invoice):
    """
    Template para invitación a usuarios NO registrados (Modalidad 1)
    """
    subject = "🚗 Invitación GuatePass - Evita multas y cobra automático"
    
    body = f"""
Hola,

Hemos detectado el paso de tu vehículo (placa {user_data.get('placa', 'N/A')}) por el peaje {toll_data.get('nombre_peaje', 'N/A')}.

⚠️ FACTURA PENDIENTE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Número de factura: {invoice.get('invoice_number', 'N/A')}
Fecha: {format_datetime(invoice.get('fecha_emision', ''))}
Peaje: {toll_data.get('nombre_peaje', 'N/A')}

Cargo base:        {format_currency(invoice.get('monto_base', '0'))}
Multa (50%):       {format_currency(invoice.get('multa', '0'))}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL A PAGAR:     {format_currency(invoice.get('total', '0'))}
Estado: PENDIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 ¡REGÍSTRATE EN GUATEPASS Y AHORRA!

Beneficios de registrarte:
✅ Sin multas por pago tardío
✅ Cobro automático al pasar
✅ Descuento del 50% vs. pago tradicional
✅ Control total de tus gastos
✅ Historial de transacciones

🔗 REGÍSTRATE AQUÍ: https://guatepass.com/registro

Una vez registrado, podrás:
• Asociar un método de pago
• Obtener un TAG RFID gratuito
• Pasar por peajes sin detenerte
• Pagar menos que el cobro tradicional

═══════════════════════════════════════════
GuatePass - Sistema de Cobro Automatizado de Peajes
📧 Soporte: soporte@guatepass.com
🌐 Web: https://guatepass.com
═══════════════════════════════════════════

Este es un correo automático, por favor no responder.
"""
    
    return subject, body


def get_charge_notification_template(user_data, toll_data, fare_calc, balance_update, invoice):
    """
    Template para notificación de cobro a usuarios registrados (Modalidad 2)
    """
    subject = "✅ Cobro por peaje realizado - GuatePass"
    
    new_balance = balance_update.get('new_balance', '0.00') if balance_update else '0.00'
    
    body = f"""
Hola {user_data.get('nombre', 'Usuario')},

Confirmamos tu paso por el peaje {toll_data.get('nombre_peaje', 'N/A')}.

📍 DETALLE DE LA TRANSACCIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Peaje:             {toll_data.get('nombre_peaje', 'N/A')}
Placa:             {user_data.get('placa', 'N/A')}
Fecha y hora:      {format_datetime(invoice.get('fecha_emision', ''))}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 INFORMACIÓN DE COBRO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monto cobrado:     {format_currency(invoice.get('total', '0'))}
Saldo anterior:    {format_currency(balance_update.get('previous_balance', '0'))}
Saldo actual:      {format_currency(new_balance)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 FACTURA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Número:            {invoice.get('invoice_number', 'N/A')}
Estado:            PAGADA ✓
Concepto:          {invoice.get('concepto', 'Paso por peaje')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Advertencia si el saldo está bajo
    if float(new_balance) < 50.0:
        body += f"""
⚠️ ALERTA DE SALDO BAJO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tu saldo actual es {format_currency(new_balance)}. 
Te recomendamos recargar pronto para evitar inconvenientes.

🔗 Recarga aquí: https://guatepass.com/recargar
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    body += """
═══════════════════════════════════════════
GuatePass - Sistema de Cobro Automatizado de Peajes
📧 Soporte: soporte@guatepass.com
🌐 Web: https://guatepass.com
═══════════════════════════════════════════

Gracias por usar GuatePass.
"""
    
    return subject, body


def send_email_simulated(to_email, subject, body):
    """
    Simula el envío de email usando logs.
    En producción, esto se reemplazaría con SNS, SES o similar.
    """
    print("=" * 80)
    print("EMAIL SIMULADO")
    print("=" * 80)
    print(f"Para: {to_email}")
    print(f"Asunto: {subject}")
    print("-" * 80)
    print(body)
    print("=" * 80)
    
    return {
        'success': True,
        'to': to_email,
        'subject': subject,
        'method': 'simulated_email'
    }


def send_sms_simulated(to_phone, message):
    """
    Simula el envío de SMS usando logs.
    En producción, esto se reemplazaría con SNS SMS.
    """
    print("=" * 80)
    print("SMS SIMULADO")
    print("=" * 80)
    print(f"Para: {to_phone}")
    print("-" * 80)
    print(message)
    print("=" * 80)
    
    return {
        'success': True,
        'to': to_phone,
        'method': 'simulated_sms'
    }


def get_invitation_sms_template(placa, invoice):
    """
    Template de SMS para invitación (más corto que email)
    """
    message = f"""GuatePass: Detectamos tu vehiculo {placa} en peaje.
    
FACTURA PENDIENTE:
No. {invoice.get('invoice_number', 'N/A')}
Total: Q{invoice.get('total', '0')} (incluye multa 50%)
Estado: PENDIENTE

REGISTRATE y AHORRA:
- Sin multas
- Cobro automatico
- 50% descuento

Registrate: https://guatepass.com/registro

GuatePass - Sistema de Peajes"""
    
    return message


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
        "toll_data": {...},
        "fare_calculation": {...},
        "balance_update": {...},
        "invoice": {...}
    }
    
    Output:
    {
        ...input,
        "notification": {
            "sent": true/false,
            "email": "ana@email.com",
            "type": "invitation" o "charge_notification",
            "timestamp": "2025-11-09T10:30:00Z"
        }
    }
    """
    
    try:
        print(f"Evento recibido: {json.dumps(event, default=str)}")
        
        user_data = event.get('user_data', {})
        toll_data = event.get('toll_data', {})
        fare_calc = event.get('fare_calculation', {})
        balance_update = event.get('balance_update', {})
        invoice = event.get('invoice', {})
        
        modalidad = user_data.get('modalidad', 3)
        email = user_data.get('email', '')
        telefono = user_data.get('telefono', '')
        nombre = user_data.get('nombre', 'Usuario')
        
        notification_result = {
            'sent': False,
            'email': email,
            'telefono': telefono,
            'type': None,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'message': 'No notification sent'
        }
        
        # Modalidad 1: Invitación para registrarse
        if modalidad == 1:
            # Preferir email si está disponible
            if email and email != 'N/A':
                subject, body = get_invitation_email_template(user_data, toll_data, invoice)
                result = send_email_simulated(email, subject, body)
                
                notification_result.update({
                    'sent': True,
                    'type': 'invitation_email',
                    'subject': subject,
                    'channel': 'email',
                    'message': f'Invitación enviada a {email}'
                })
                
                print(f"✅ Invitación enviada por EMAIL a {email} (Modalidad 1)")
            
            # Si no hay email pero sí teléfono, enviar SMS
            elif telefono and telefono != 'N/A':
                sms_message = get_invitation_sms_template(user_data.get('placa'), invoice)
                result = send_sms_simulated(telefono, sms_message)
                
                notification_result.update({
                    'sent': True,
                    'type': 'invitation_sms',
                    'channel': 'sms',
                    'message': f'Invitación enviada por SMS a {telefono}'
                })
                
                print(f"✅ Invitación enviada por SMS a {telefono} (Modalidad 1)")
            
            # Sin email ni teléfono
            else:
                notification_result['message'] = 'Usuario sin email ni teléfono registrado'
                print(f"⚠️ Usuario {user_data.get('placa')} no tiene email ni teléfono")
        
        # Modalidad 2: Notificación de cobro (solo email)
        elif modalidad == 2:
            if email and email != 'N/A':
                subject, body = get_charge_notification_template(
                    user_data, toll_data, fare_calc, balance_update, invoice
                )
                result = send_email_simulated(email, subject, body)
                
                notification_result.update({
                    'sent': True,
                    'type': 'charge_notification',
                    'subject': subject,
                    'channel': 'email',
                    'message': f'Notificación de cobro enviada a {email}'
                })
                
                print(f"✅ Notificación de cobro enviada por EMAIL a {email} (Modalidad 2)")
            else:
                notification_result['message'] = 'Usuario Modalidad 2 sin email'
                print(f"⚠️ Usuario {user_data.get('placa')} Modalidad 2 sin email")
        
        # Modalidad 3: No se envía notificación
        else:
            notification_result['message'] = f'Modalidad {modalidad} - No se envía notificación'
            print(f"ℹ️ Modalidad {modalidad} - No se envía notificación")
        
        # Retornar evento enriquecido
        result = {
            **event,
            'notification': notification_result
        }
        
        return result
        
    except Exception as e:
        print(f"❌ Error enviando notificación: {str(e)}")
        # No fallar la transacción por error en notificación
        return {
            **event,
            'notification': {
                'sent': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }

