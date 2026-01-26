#!/usr/bin/env python3
# ============================================================================
# SCRIPT DE MIGRACIÓN: Migrar todos los clientes al nuevo sistema
# ============================================================================
"""
Este script migra todos los clientes existentes al nuevo sistema de transacciones.
Ejecutar UNA SOLA VEZ después de crear la tabla transacciones_puntos.

IMPORTANTE: 
- Hacer backup de la base de datos antes de ejecutar
- Ejecutar en horario de bajo tráfico
- Monitorear el proceso

USO:
    python migrar_todos_clientes.py
"""

import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path para importar app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Puntos_Clientes, Usuario
from utils_puntos import migrar_datos_historicos

def migrar_todos_los_clientes():
    """
    Migra todos los clientes al nuevo sistema de transacciones.
    """
    with app.app_context():
        print("=" * 80)
        print("MIGRACIÓN DE CLIENTES AL NUEVO SISTEMA DE PUNTOS")
        print("=" * 80)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Obtener todos los clientes con puntos
        clientes = Puntos_Clientes.query.all()
        total_clientes = len(clientes)
        
        print(f"📊 Total de clientes a migrar: {total_clientes}")
        print()
        
        if total_clientes == 0:
            print("⚠️ No hay clientes para migrar")
            return
        
        # Confirmar antes de proceder
        respuesta = input(f"¿Deseas migrar {total_clientes} clientes? (si/no): ")
        if respuesta.lower() not in ['si', 'sí', 's', 'yes', 'y']:
            print("❌ Migración cancelada")
            return
        
        print()
        print("🚀 Iniciando migración...")
        print("-" * 80)
        
        exitosos = 0
        fallidos = 0
        errores = []
        
        for i, cliente in enumerate(clientes, 1):
            documento = cliente.documento
            
            try:
                print(f"[{i}/{total_clientes}] Migrando cliente {documento}...", end=" ")
                
                # Migrar datos históricos
                resumen = migrar_datos_historicos(documento)
                
                # Verificar si hubo errores
                if resumen['errores']:
                    print(f"⚠️ CON ERRORES")
                    fallidos += 1
                    errores.append({
                        'documento': documento,
                        'errores': resumen['errores']
                    })
                else:
                    print(f"✅ OK")
                    exitosos += 1
                
                # Mostrar resumen del cliente
                if resumen['compras_migradas'] > 0:
                    print(f"    └─ Compras: {resumen['compras_migradas']} puntos")
                if resumen['redenciones_migradas'] > 0:
                    print(f"    └─ Redenciones: {resumen['redenciones_migradas']} puntos")
                if resumen['referidos_migrados'] > 0:
                    print(f"    └─ Referidos: {resumen['referidos_migrados']} puntos")
                if resumen['regalos_migrados'] > 0:
                    print(f"    └─ Regalos: {resumen['regalos_migrados']} puntos")
                
                # Commit cada 10 clientes para evitar transacciones muy largas
                if i % 10 == 0:
                    db.session.commit()
                    print(f"    💾 Checkpoint guardado ({i}/{total_clientes})")
                
            except Exception as e:
                print(f"❌ ERROR")
                fallidos += 1
                errores.append({
                    'documento': documento,
                    'errores': [str(e)]
                })
                db.session.rollback()
                print(f"    └─ Error: {str(e)}")
        
        # Commit final
        try:
            db.session.commit()
            print()
            print("💾 Guardando cambios finales...")
        except Exception as e:
            print(f"❌ Error en commit final: {e}")
            db.session.rollback()
        
        # Resumen final
        print()
        print("=" * 80)
        print("RESUMEN DE MIGRACIÓN")
        print("=" * 80)
        print(f"✅ Exitosos: {exitosos}")
        print(f"❌ Fallidos: {fallidos}")
        print(f"📊 Total: {total_clientes}")
        print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Mostrar errores si los hay
        if errores:
            print()
            print("⚠️ ERRORES ENCONTRADOS:")
            print("-" * 80)
            for error in errores:
                print(f"Documento: {error['documento']}")
                for err in error['errores']:
                    print(f"  - {err}")
                print()
        
        print()
        print("✅ Migración completada")
        print("=" * 80)


def migrar_cliente_individual(documento):
    """
    Migra un cliente específico (útil para pruebas o correcciones).
    """
    with app.app_context():
        print(f"🔄 Migrando cliente {documento}...")
        
        try:
            resumen = migrar_datos_historicos(documento)
            db.session.commit()
            
            print("✅ Migración exitosa")
            print(f"   Compras: {resumen['compras_migradas']} puntos")
            print(f"   Redenciones: {resumen['redenciones_migradas']} puntos")
            print(f"   Referidos: {resumen['referidos_migrados']} puntos")
            print(f"   Regalos: {resumen['regalos_migrados']} puntos")
            
            if resumen['errores']:
                print("⚠️ Errores:")
                for error in resumen['errores']:
                    print(f"   - {error}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()


def verificar_migracion():
    """
    Verifica que la migración se haya realizado correctamente.
    """
    from models_puntos import Transacciones_Puntos
    
    with app.app_context():
        print("=" * 80)
        print("VERIFICACIÓN DE MIGRACIÓN")
        print("=" * 80)
        
        # Contar transacciones por tipo
        tipos = ['ACUMULACION', 'REDENCION', 'REGALO', 'REFERIDO']
        
        for tipo in tipos:
            count = Transacciones_Puntos.query.filter_by(tipo_transaccion=tipo).count()
            print(f"{tipo}: {count} transacciones")
        
        # Total de transacciones
        total = Transacciones_Puntos.query.count()
        print(f"\nTotal de transacciones: {total}")
        
        # Clientes con transacciones
        clientes_con_transacciones = db.session.query(
            Transacciones_Puntos.documento
        ).distinct().count()
        print(f"Clientes con transacciones: {clientes_con_transacciones}")
        
        # Total de clientes
        total_clientes = Puntos_Clientes.query.count()
        print(f"Total de clientes: {total_clientes}")
        
        print("=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrar clientes al nuevo sistema de puntos')
    parser.add_argument('--cliente', type=str, help='Migrar un cliente específico (documento)')
    parser.add_argument('--verificar', action='store_true', help='Verificar la migración')
    parser.add_argument('--todos', action='store_true', help='Migrar todos los clientes')
    
    args = parser.parse_args()
    
    if args.verificar:
        verificar_migracion()
    elif args.cliente:
        migrar_cliente_individual(args.cliente)
    elif args.todos:
        migrar_todos_los_clientes()
    else:
        print("Uso:")
        print("  python migrar_todos_clientes.py --todos          # Migrar todos los clientes")
        print("  python migrar_todos_clientes.py --cliente 123456 # Migrar un cliente específico")
        print("  python migrar_todos_clientes.py --verificar      # Verificar la migración")
