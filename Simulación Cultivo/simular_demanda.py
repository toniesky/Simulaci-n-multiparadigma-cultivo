"""
Archivo de compatibilidad — el codigo ha sido reorganizado en los siguientes modulos:

  simulacion_cultivo.py          <- punto de entrada principal (main + imports)

  modulos/
    __init__.py                  <- marca el directorio como paquete Python
    objetos.py                   <- constantes internas: paletas de color, listas de
                                    meses, metadatos de etapas FAO-56, filas de ranking
    fao56.py                     <- coeficientes Kcb diario y Kcmax (FAO-56)
    simulacion.py                <- balance hidrico diario (simular_cultivo,
                                    simular_multi_particion)
    carga_datos.py               <- lectura de CSV: oferta, regantes, clima,
                                    productividad
    calidad.py                   <- mes de cosecha y evaluacion de calidad de
                                    produccion (modelo deterministico)
    kpis.py                      <- indicadores de desempeno: KPIs hidricos,
                                    economicos y por combinacion de cultivos
    graficos.py                  <- graficos diarios del balance hidrico (PNG base64)
    reportes.py                  <- generacion de reportes HTML (particiones y
                                    comparativa global)
    funciones.py                 <- barrel: re-exporta todo lo anterior para
                                    compatibilidad con importaciones existentes

Ejecutar directamente:
  python simulacion_cultivo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from simulacion_cultivo import main

if __name__ == '__main__':
    main()
