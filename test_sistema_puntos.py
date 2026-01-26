#!/usr/bin/env python3
# ============================================================================
# TESTS DEL SISTEMA DE PUNTOS
# ============================================================================
"""
Script de pruebas para verificar que el sistema de puntos funciona correctamente.

USO:
    python test_sistema_puntos.py
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models_puntos import Transacciones_Puntos
from utils_puntos import (
    calcular_puntos_disponibles,
    crear_transaccion_acumulacion,
    crear_transaccion_redencion,
    crear_transaccion_regalo,
    crear_transaccion_referido,
    obtener_historial_transacciones
)

# Cliente de prueba
DOCUMENTO_TEST = "TEST_123456"

def limpiar_datos_test():
    """Limpia los datos de prueba anteriores"""
    with app.app_context():
        Transacciones_Puntos.query.filter_by(documento=DOCUMENTO_TEST).delete()
        db.session.commit()
        print("✅ Datos de prueba limpiados")

def test_acumulacion_puntos():
    """Test 1: Acumulación de puntos por compra"""
    print("\n" + "="*80)
    print("TEST 1: Acumulación de Puntos")
    print("="*80)
    
    with app.app_context():
        try:
            # Crear transacción de acumulación
            fecha_compra = datetime.now() - timedelta(days=2)  # Hace 2 días
            transaccion = crear_transaccion_acumulacion(
                documento=DOCUMENTO_TEST,
                puntos=100,
                referencia_compra="FM-12345",
                descripcion="Compra de prueba - $100,000",
                fecha_compra=fecha_compra
            )
            db.session.commit()
            
            # Verificar
            info = calcular_puntos_disponibles(DOCUMENTO_TEST)
            
            assert info['puntos_disponibles'] == 100, f"Esperaba 100 puntos, obtuvo {info['puntos_disponibles']}"
            assert transaccion.estado == 'ACTIVO', "La transacción debe estar ACTIVA"
            assert transaccion.fecha_vencimiento is not None, "Debe tener fecha de vencimiento"
            
            print(f"✅ Puntos acumulados: {info['puntos_disponibles']}")
            print(f"✅ Fecha de vencimiento: {transaccion.fecha_vencimiento.strftime('%Y-%m-%d')}")
            print("✅ TEST 1 PASADO")
            
        except Exception as e:
            print(f"❌ TEST 1 FALLIDO: {e}")
            db.session.rollback()
            raise

def test_redencion_puntos():
    """Test 2: Redención de puntos"""
    print("\n" + "="*80)
    print("TEST 2: Redención de Puntos")
    print("="*80)
    
    with app.app_context():
        try:
            # Verificar puntos antes
            info_antes = calcular_puntos_disponibles(DOCUMENTO_TEST)
            print(f"📊 Puntos antes de redimir: {info_antes['puntos_disponibles']}")
            
            # Redimir 50 puntos
            transaccion = crear_transaccion_redencion(
                documento=DOCUMENTO_TEST,
                puntos=50,
                referencia_redencion="CUPON-TEST-001",
                descripcion="Redención de prueba - Cupón $50,000"
            )
            db.session.commit()
            
            # Verificar puntos después
            info_despues = calcular_puntos_disponibles(DOCUMENTO_TEST)
            
            assert info_despues['puntos_disponibles'] == 50, f"Esperaba 50 puntos, obtuvo {info_despues['puntos_disponibles']}"
            assert transaccion.puntos == -50, "Los puntos de redención deben ser negativos"
            
            print(f"✅ Puntos después de redimir: {info_despues['puntos_disponibles']}")
            print(f"✅ Puntos redimidos: 50")
            print("✅ TEST 2 PASADO")
            
        except Exception as e:
            print(f"❌ TEST 2 FALLIDO: {e}")
            db.session.rollback()
            raise

def test_puntos_regalo():
    """Test 3: Puntos de regalo (no vencen)"""
    print("\n" + "="*80)
    print("TEST 3: Puntos de Regalo")
    print("="*80)
    
    with app.app_context():
        try:
            # Agregar puntos de regalo
            transaccion = crear_transaccion_regalo(
                documento=DOCUMENTO_TEST,
                puntos=25,
                descripcion="Bono de bienvenida"
            )
            db.session.commit()
            
            # Verificar
            info = calcular_puntos_disponibles(DOCUMENTO_TEST)
            
            assert info['puntos_disponibles'] == 75, f"Esperaba 75 puntos (50 + 25), obtuvo {info['puntos_disponibles']}"
            assert transaccion.fecha_vencimiento is None, "Los puntos de regalo NO deben vencer"
            
            print(f"✅ Puntos totales: {info['puntos_disponibles']}")
            print(f"✅ Puntos de regalo agregados: 25")
            print(f"✅ Fecha de vencimiento: {transaccion.fecha_vencimiento} (None = no vence)")
            print("✅ TEST 3 PASADO")
            
        except Exception as e:
            print(f"❌ TEST 3 FALLIDO: {e}")
            db.session.rollback()
            raise

def test_vencimiento_puntos():
    """Test 4: Vencimiento de puntos"""
    print("\n" + "="*80)
    print("TEST 4: Vencimiento de Puntos")
    print("="*80)
    
    with app.app_context():
        try:
            # Crear puntos que ya vencieron (hace 2 años)
            fecha_antigua = datetime.now() - timedelta(days=730)  # Hace 2 años
            transaccion = crear_transaccion_acumulacion(
                documento=DOCUMENTO_TEST,
                puntos=30,
                referencia_compra="FM-ANTIGUA",
                descripcion="Compra antigua (vencida)",
                fecha_compra=fecha_antigua
            )
            db.session.commit()
            
            # Verificar que NO se cuentan en puntos disponibles
            info = calcular_puntos_disponibles(DOCUMENTO_TEST)
            
            # Los puntos vencidos NO deben sumarse
            assert info['puntos_disponibles'] == 75, f"Los puntos vencidos no deben contarse. Esperaba 75, obtuvo {info['puntos_disponibles']}"
            assert info['puntos_vencidos'] == 30, f"Debe detectar 30 puntos vencidos, obtuvo {info['puntos_vencidos']}"
            
            print(f"✅ Puntos disponibles: {info['puntos_disponibles']}")
            print(f"✅ Puntos vencidos detectados: {info['puntos_vencidos']}")
            print(f"✅ Fecha de vencimiento: {transaccion.fecha_vencimiento.strftime('%Y-%m-%d')}")
            print("✅ TEST 4 PASADO")
            
        except Exception as e:
            print(f"❌ TEST 4 FALLIDO: {e}")
            db.session.rollback()
            raise

def test_puntos_por_vencer():
    """Test 5: Puntos por vencer en 30 días"""
    print("\n" + "="*80)
    print("TEST 5: Puntos por Vencer")
    print("="*80)
    
    with app.app_context():
        try:
            # Crear puntos que vencen en 15 días
            fecha_proxima = datetime.now() - timedelta(days=350)  # Vence en 15 días
            transaccion = crear_transaccion_acumulacion(
                documento=DOCUMENTO_TEST,
                puntos=40,
                referencia_compra="FM-PROXIMA",
                descripcion="Compra próxima a vencer",
                fecha_compra=fecha_proxima
            )
            db.session.commit()
            
            # Verificar
            info = calcular_puntos_disponibles(DOCUMENTO_TEST)
            
            assert info['puntos_por_vencer_30dias'] == 40, f"Debe detectar 40 puntos por vencer, obtuvo {info['puntos_por_vencer_30dias']}"
            
            print(f"✅ Puntos disponibles: {info['puntos_disponibles']}")
            print(f"✅ Puntos por vencer en 30 días: {info['puntos_por_vencer_30dias']}")
            print(f"✅ Fecha de vencimiento: {transaccion.fecha_vencimiento.strftime('%Y-%m-%d')}")
            print("✅ TEST 5 PASADO")
            
        except Exception as e:
            print(f"❌ TEST 5 FALLIDO: {e}")
            db.session.rollback()
            raise

def test_historial_transacciones():
    """Test 6: Historial de transacciones"""
    print("\n" + "="*80)
    print("TEST 6: Historial de Transacciones")
    print("="*80)
    
    with app.app_context():
        try:
            # Obtener historial
            transacciones = obtener_historial_transacciones(DOCUMENTO_TEST, limite=100)
            
            # Verificar que hay transacciones
            assert len(transacciones) > 0, "Debe haber transacciones en el historial"
            
            # Contar por tipo
            tipos = {}
            for t in transacciones:
                tipos[t.tipo_transaccion] = tipos.get(t.tipo_transaccion, 0) + 1
            
            print(f"✅ Total de transacciones: {len(transacciones)}")
            print(f"✅ Tipos de transacciones:")
            for tipo, count in tipos.items():
                print(f"   - {tipo}: {count}")
            
            # Mostrar últimas 5 transacciones
            print(f"\n📋 Últimas 5 transacciones:")
            for t in transacciones[:5]:
                signo = "+" if t.puntos > 0 else ""
                print(f"   {t.fecha_transaccion.strftime('%Y-%m-%d')} | {t.tipo_transaccion:12} | {signo}{t.puntos:4} pts | {t.descripcion[:40]}")
            
            print("✅ TEST 6 PASADO")
            
        except Exception as e:
            print(f"❌ TEST 6 FALLIDO: {e}")
            raise

def test_redencion_insuficiente():
    """Test 7: Intentar redimir más puntos de los disponibles"""
    print("\n" + "="*80)
    print("TEST 7: Redención con Puntos Insuficientes")
    print("="*80)
    
    with app.app_context():
        try:
            # Intentar redimir más puntos de los disponibles
            info = calcular_puntos_disponibles(DOCUMENTO_TEST)
            print(f"📊 Puntos disponibles: {info['puntos_disponibles']}")
            
            try:
                crear_transaccion_redencion(
                    documento=DOCUMENTO_TEST,
                    puntos=info['puntos_disponibles'] + 100,  # Más de los disponibles
                    referencia_redencion="CUPON-INVALIDO",
                    descripcion="Intento de redención inválida"
                )
                db.session.commit()
                
                # Si llegamos aquí, el test falló
                print("❌ TEST 7 FALLIDO: Debería haber lanzado ValueError")
                assert False, "Debería haber lanzado ValueError"
                
            except ValueError as e:
                # Esto es lo esperado
                print(f"✅ Error capturado correctamente: {e}")
                print("✅ TEST 7 PASADO")
                db.session.rollback()
            
        except Exception as e:
            print(f"❌ TEST 7 FALLIDO: {e}")
            db.session.rollback()
            raise

def test_resumen_final():
    """Resumen final de todos los tests"""
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    
    with app.app_context():
        info = calcular_puntos_disponibles(DOCUMENTO_TEST)
        transacciones = obtener_historial_transacciones(DOCUMENTO_TEST)
        
        print(f"📊 Puntos disponibles: {info['puntos_disponibles']}")
        print(f"📊 Puntos vencidos: {info['puntos_vencidos']}")
        print(f"📊 Puntos por vencer (30 días): {info['puntos_por_vencer_30dias']}")
        print(f"📊 Total de transacciones: {len(transacciones)}")
        
        # Calcular balance
        total_acumulado = sum(t.puntos for t in transacciones if t.puntos > 0)
        total_gastado = abs(sum(t.puntos for t in transacciones if t.puntos < 0))
        
        print(f"\n💰 Total acumulado: {total_acumulado} puntos")
        print(f"💸 Total gastado: {total_gastado} puntos")
        print(f"💵 Balance: {total_acumulado - total_gastado} puntos")

def run_all_tests():
    """Ejecuta todos los tests"""
    print("="*80)
    print("INICIANDO TESTS DEL SISTEMA DE PUNTOS")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Cliente de prueba: {DOCUMENTO_TEST}")
    
    try:
        # Limpiar datos anteriores
        limpiar_datos_test()
        
        # Ejecutar tests
        test_acumulacion_puntos()
        test_redencion_puntos()
        test_puntos_regalo()
        test_vencimiento_puntos()
        test_puntos_por_vencer()
        test_historial_transacciones()
        test_redencion_insuficiente()
        test_resumen_final()
        
        # Resumen
        print("\n" + "="*80)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("="*80)
        
        # Limpiar datos de prueba
        respuesta = input("\n¿Deseas limpiar los datos de prueba? (si/no): ")
        if respuesta.lower() in ['si', 'sí', 's', 'yes', 'y']:
            limpiar_datos_test()
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ALGUNOS TESTS FALLARON")
        print("="*80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_all_tests()
