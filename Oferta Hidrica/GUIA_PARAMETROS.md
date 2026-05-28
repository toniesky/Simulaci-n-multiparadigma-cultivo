"""
GUÍA DE PARÁMETROS - initial_values.py
================================

Este archivo contiene TODOS los parámetros configurables del modelo.
Edita aquí para cambiar el comportamiento sin modificar el código principal.


� PARÁMETROS MÁS IMPORTANTES (los que probablemente cambiarás)
================================================================

1. DESMARQUE - Porcentaje de derechos en cada opción
   ────────────────────────────────────────────────
   
   PORCENTAJE_DESMARQUE_OPCION1 = 0.45  # Cambiar: 0.30, 0.40, 0.50, 0.60
   → Opción 1: Desmarque INICIO turno (días 1-5)
   → Ejemplo: 45% × 60 m³/día = 27 m³/día
   
   PORCENTAJE_DESMARQUE_OPCION2 = 0.35  # Cambiar: 0.25, 0.30, 0.40, 0.50
   → Opción 2: Desmarque FINAL turno (días 5-9)
   → Ejemplo: 35% × 60 m³/día = 21 m³/día


2. DERECHOS DE AGUA - Volúmenes disponibles
   ─────────────────────────────────────────
   
   DERECHOS_AGUA_SUPERFICIAL = 60.0  # Cambiar: 40, 50, 70, 80, 100
   → Máximo disponible cuando hay desmarque
   → Afecta entrada: DESMARQUE% × Este valor
   
   DERECHOS_AGUA_SUBTERRANEA = 15.0  # Cambiar: 10, 20, 25, 30
   → CONSTANTE todos los días
   → No depende de nada, siempre disponible
   → Es el "fondo garantizado" del sistema


3. PÉRDIDAS - Agua que se pierde en el sistema
   ────────────────────────────────────────────
   
   COEFICIENTE_PERDIDA_FILTRACION = 0.02  # Cambiar: 0.01, 0.03, 0.05
   → Agua que se pierde por filtración (2% del caudal)
   
   COEFICIENTE_PERDIDA_CONDUCCION = 0.03  # Cambiar: 0.02, 0.04, 0.05
   → Agua que se pierde en conducción (3% del caudal)


4. STOCKS Y TIEMPO
   ────────────────
   
   STOCK_INICIAL_CAUDAL = 200.0  # Cambiar: 100, 150, 300, 500
   → Agua en el canal al inicio
   → Mayor = sistema más resiliente al inicio
   
   TIEMPO_TOTAL = 365  # Cambiar: 180, 365, 730 (multiples de 9)
   → Días a simular
   
   DURACION_TURNO = 9  # Cambiar: 7, 9, 10, 15
   → Días por turno de riego


5. MANTENIMIENTO
   ──────────────
   
   DURACION_MANTENIMIENTO = 3  # Cambiar: 1, 2, 3, 5, 7
   → Días que el canal permanece cerrado por mantenimiento
   → Aplica a días 20, 150, 300


📊 EJEMPLOS DE CAMBIOS Y SUS EFECTOS
====================================

ESCENARIO 1: Aumentar disponibilidad
───────────────────────────────────
PORCENTAJE_DESMARQUE_OPCION1 = 0.50  # Subir de 45% a 50%
DERECHOS_AGUA_SUPERFICIAL = 80.0     # Subir de 60 a 80
DERECHOS_AGUA_SUBTERRANEA = 20.0     # Subir de 15 a 20
Resultado: Más agua disponible, menos déficit


ESCENARIO 2: Reducir pérdidas
──────────────────────────────
COEFICIENTE_PERDIDA_FILTRACION = 0.01  # Bajar de 2% a 1%
COEFICIENTE_PERDIDA_CONDUCCION = 0.02  # Bajar de 3% a 2%
Resultado: Menos pérdidas, mejor eficiencia


ESCENARIO 3: Turnos más largos
───────────────────────────────
DURACION_TURNO = 15  # Cambiar de 9 a 15 días
Resultado: Menos rotaciones (del año 40 turnos → 24 turnos)


ESCENARIO 4: Más conservador
──────────────────────────────
PORCENTAJE_DESMARQUE_OPCION1 = 0.30  # Bajar desmarque
PORCENTAJE_DESMARQUE_OPCION2 = 0.25  # Bajar desmarque
DURACION_MANTENIMIENTO = 5           # Aumentar mantenimiento
Resultado: Sistema más conservador


✅ CÓMO USAR
============

1. Edita initial_values.py con los valores que desees
2. Guarda el archivo
3. Ejecuta: python modelo_sistema_agua.py
4. Mira los resultados en: data/outputs/CalendarioOferta_*.csv


🎯 VALIDAR TUS CAMBIOS
======================

Después de cambiar parámetros, revisa:

1. ¿La oferta promedio es realista?
   → Ver: Comparacion_Opciones.csv
   
2. ¿El caudal es positivo o negativo?
   → Si es muy negativo, aumenta derechos o reduce pérdidas
   
3. ¿La diferencia entre opciones es significativa?
   → Verifica que los porcentajes sean diferentes
   
4. ¿Los gráficos muestran patrones lógicos?
   → Ver: Graficos_Opcion1.png y Graficos_Opcion2.png


⚠️ ERRORES COMUNES
==================

❌ Parámetros demasiado altos:
   → Resultado: Caudal negativo muy bajo
   → Solución: Aumenta DERECHOS_AGUA_SUPERFICIAL o baja pérdidas

❌ Parámetros demasiado bajos:
   → Resultado: Oferta muy baja
   → Solución: Aumenta PORCENTAJE_DESMARQUE

❌ Desmarques iguales en ambas opciones:
   → Resultado: Opciones casi idénticas
   → Solución: Asegúrate que OPCION1 ≠ OPCION2


🔄 FLUJO DE TRABAJO RECOMENDADO
================================

1. Comenzar con valores por defecto
2. Ejecutar modelo
3. Revisar Comparacion_Opciones.csv
4. Si necesitas cambios, editar initial_values.py
5. Re-ejecutar modelo
6. Comparar resultados anteriores vs nuevos
7. Documentar qué cambios funcionaron
"""

# Valores de referencia (no editar)
print(__doc__)
