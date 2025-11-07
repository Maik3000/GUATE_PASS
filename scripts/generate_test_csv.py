#!/usr/bin/env python3
"""
Script para generar archivos CSV de prueba con usuarios aleatorios
Útil para testing de escalabilidad y performance
"""

import csv
import random
import argparse
from typing import List, Dict

# Datos de ejemplo para generación aleatoria
NOMBRES = [
    "Juan", "María", "Carlos", "Ana", "Luis", "Sofia", "Roberto", "Carmen",
    "Pedro", "Laura", "Jorge", "Elena", "Miguel", "Patricia", "Fernando",
    "Isabel", "Ricardo", "Monica", "Alberto", "Gabriela", "Javier", "Rosa",
    "Manuel", "Beatriz", "Diego", "Claudia", "Sergio", "Lucia", "Raul", "Silvia"
]

APELLIDOS = [
    "Pérez", "López", "García", "Rodríguez", "Hernández", "Martínez", "González",
    "Jiménez", "Ruiz", "Torres", "Morales", "Ramírez", "Flores", "Rivera",
    "Cruz", "Gómez", "Díaz", "Reyes", "Gutiérrez", "Castillo", "Sánchez",
    "Mendoza", "Vargas", "Romero", "Herrera", "Medina", "Silva", "Ortiz"
]


def generate_placa(index: int) -> str:
    """Genera una placa única"""
    letter = chr(65 + (index // 1000) % 26)  # A-Z
    number = index % 1000
    suffix = ["ABC", "DEF", "GHI", "JKL", "MNO", "PQR", "STU", "VWX", "YZA", "BCD"][index % 10]
    return f"P-{number:03d}{suffix}"


def generate_email(nombre: str, apellido: str, index: int) -> str:
    """Genera un email"""
    return f"{nombre.lower()}.{apellido.lower()}{index}@email.com"


def generate_telefono() -> str:
    """Genera un número de teléfono guatemalteco"""
    return f"502{random.randint(20000000, 99999999)}"


def generate_tag_id(index: int) -> str:
    """Genera un Tag ID"""
    return f"TAG-{index:06d}"


def generate_user(index: int) -> Dict[str, str]:
    """Genera un usuario aleatorio"""
    nombre = random.choice(NOMBRES)
    apellido = random.choice(APELLIDOS)
    placa = generate_placa(index)
    
    # 70% registrados, 30% no registrados
    es_registrado = random.random() < 0.7
    tipo_usuario = "registrado" if es_registrado else "no_registrado"
    
    # Email y teléfono solo para registrados (a veces uno solo)
    if es_registrado:
        tiene_email = random.random() < 0.9
        tiene_telefono = random.random() < 0.8
        email = generate_email(nombre, apellido, index) if tiene_email else ""
        telefono = generate_telefono() if tiene_telefono else ""
    else:
        email = ""
        telefono = ""
    
    # 30% de registrados tienen tag
    tiene_tag = es_registrado and random.random() < 0.3
    tag_id = generate_tag_id(index) if tiene_tag else ""
    
    # Saldo entre 0 y 500 para registrados
    if es_registrado:
        saldo = round(random.uniform(0, 500), 2)
    else:
        saldo = 0.00
    
    return {
        'placa': placa,
        'nombre': f"{nombre} {apellido}",
        'email': email,
        'telefono': telefono,
        'tipo_usuario': tipo_usuario,
        'tiene_tag': str(tiene_tag).lower(),
        'tag_id': tag_id,
        'saldo_disponible': f"{saldo:.2f}"
    }


def generate_csv(num_users: int, output_file: str):
    """Genera un archivo CSV con usuarios aleatorios"""
    print(f"📝 Generando {num_users} usuarios...")
    
    users = [generate_user(i) for i in range(num_users)]
    
    fieldnames = [
        'placa', 'nombre', 'email', 'telefono',
        'tipo_usuario', 'tiene_tag', 'tag_id', 'saldo_disponible'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)
    
    print(f"✅ Archivo generado: {output_file}")
    print(f"📊 Total de usuarios: {num_users}")
    
    # Estadísticas
    registrados = sum(1 for u in users if u['tipo_usuario'] == 'registrado')
    con_tag = sum(1 for u in users if u['tiene_tag'] == 'true')
    
    print(f"   - Registrados: {registrados} ({registrados/num_users*100:.1f}%)")
    print(f"   - Con Tag: {con_tag} ({con_tag/num_users*100:.1f}%)")
    print(f"   - No registrados: {num_users - registrados}")


def main():
    parser = argparse.ArgumentParser(
        description='Genera archivos CSV de prueba para GUATEPASS'
    )
    parser.add_argument(
        '--users',
        type=int,
        default=100,
        help='Número de usuarios a generar (default: 100)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/clientes_test.csv',
        help='Archivo de salida (default: data/clientes_test.csv)'
    )
    
    args = parser.parse_args()
    
    # Validaciones
    if args.users < 1:
        print("❌ Error: El número de usuarios debe ser mayor a 0")
        return
    
    if args.users > 100000:
        print("⚠️  Advertencia: Generar más de 100,000 usuarios puede tomar tiempo")
        confirm = input("¿Deseas continuar? (s/n): ")
        if confirm.lower() != 's':
            print("Operación cancelada")
            return
    
    generate_csv(args.users, args.output)


if __name__ == "__main__":
    main()

