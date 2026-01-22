#!/usr/bin/env python3
"""
Script de prueba para verificar que la blacklist de vendedores funciona correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blacklist_vendedores import BlacklistVendedores, verificar_blacklist_vendedor

def test_conexion_ofima():
    """Probar conexión a OFIMA y consulta de vendedores"""
    print("🔍 PRUEBA 1: Conexión a OFIMA")
    print("=" * 50)
    
    try:
        blacklist = BlacklistVendedores()
        vendedores = blacklist.consultar_vendedores_ofima()
        
        if vendedores:
            print(f"✅ Conexión exitosa a OFIMA")
            print(f"📊 Total vendedores encontrados: {len(vendedores)}")
            print(f"📋 Primeros 5 vendedores: {vendedores[:5]}")
            return True, vendedores
        else:
            print("❌ No se encontraron vendedores")
            return False, []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, []

def test_blacklist_funcionamiento():
    """Probar el funcionamiento de la blacklist"""
    print("\n🔍 PRUEBA 2: Funcionamiento de blacklist")
    print("=" * 50)
    
    try:
        # Actualizar blacklist
        blacklist = BlacklistVendedores()
        exito = blacklist.actualizar_blacklist()
        
        if exito:
            print("✅ Blacklist actualizada correctamente")
            
            # Obtener estadísticas
            stats = blacklist.obtener_estadisticas()
            print(f"📊 Estadísticas:")
            print(f"   - Total vendedores: {stats['total_vendedores']}")
            print(f"   - Última actualización: {stats['ultima_actualizacion']}")
            print(f"   - Necesita actualización: {stats['necesita_actualizacion']}")
            
            return True, stats
        else:
            print("❌ Error al actualizar blacklist")
            return False, {}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, {}

def test_verificacion_cedulas(vendedores_muestra):
    """Probar verificación de cédulas específicas"""
    print("\n🔍 PRUEBA 3: Verificación de cédulas")
    print("=" * 50)
    
    # Probar con algunos vendedores de la muestra
    if vendedores_muestra:
        for i, cedula in enumerate(vendedores_muestra[:3]):
            es_vendedor = verificar_blacklist_vendedor(cedula)
            print(f"   Cédula {cedula}: {'🚫 ES VENDEDOR' if es_vendedor else '✅ NO ES VENDEDOR'}")
    
    # Probar con una cédula que probablemente NO sea vendedor
    cedula_test = "1000000000"  # Cédula de prueba
    es_vendedor = verificar_blacklist_vendedor(cedula_test)
    print(f"   Cédula {cedula_test} (prueba): {'🚫 ES VENDEDOR' if es_vendedor else '✅ NO ES VENDEDOR'}")

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DE BLACKLIST DE VENDEDORES")
    print("=" * 60)
    
    # Prueba 1: Conexión a OFIMA
    exito_conexion, vendedores = test_conexion_ofima()
    
    if not exito_conexion:
        print("\n❌ FALLO: No se pudo conectar a OFIMA. Verifica:")
        print("   - Conexión a internet")
        print("   - Credenciales de base de datos")
        print("   - Tabla vmaestrodevendedores existe")
        return
    
    # Prueba 2: Funcionamiento de blacklist
    exito_blacklist, stats = test_blacklist_funcionamiento()
    
    if not exito_blacklist:
        print("\n❌ FALLO: Error en funcionamiento de blacklist")
        return
    
    # Prueba 3: Verificación de cédulas
    test_verificacion_cedulas(vendedores)
    
    print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS")
    print("=" * 60)
    print("✅ La blacklist de vendedores está funcionando correctamente")
    print(f"📊 {stats.get('total_vendedores', 0)} vendedores en blacklist")

if __name__ == "__main__":
    main()