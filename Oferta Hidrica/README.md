# Modelo de Dinámica de Sistemas - Gestión de Agua Caudal Regante

## 📋 Descripción General

Este proyecto implementa un **modelo de dinámica de sistemas** para simular la gestión del caudal regante, con control de apertura/cierre de canal, calendarios de turnos y mantenimiento.

**Basado en el diagrama causal proporcionado, incluye:**
- Filtración y pérdidas de conducción
- Coeficiente de pérdida en filtración
- Derechos de agua superficial y subterránea
- Calendario de turnos (cada 9 días)
- Paradas de mantenimiento (3 en el año: inicio, mitad, final)
- Variable binaria de apertura del canal
- Duración configurable del mantenimiento

---

## 🏗️ Estructura del Proyecto

```
Modelo/
├── data/
│   ├── inputs/                          # Calendarios de entrada (CSV)
│   │   ├── CalendarioTurnosCanal.csv    # Turnos cada 9 días
│   │   ├── CalendarioParadas.csv        # 3 paradas de mantenimiento
│   │   └── CalendarioApertura.csv       # Estado programado de apertura
│   │
│   └── outputs/                         # Resultados generados
│       ├── CalendarioOferta_Opcion1.csv # Output: Oferta calculada (Opción 1)
│       ├── CalendarioOferta_Opcion2.csv # Output: Oferta calculada (Opción 2)
│       ├── Comparacion_Opciones.csv     # Comparación de resultados
│       ├── Graficos_Opcion1.png         # Gráficos de simulación (Opción 1)
│       └── Graficos_Opcion2.png         # Gráficos de simulación (Opción 2)
│
├── src/
│   └── initial_values.py                # Parámetros y valores iniciales
│
├── models/                              # (Reservado para modelos adicionales)
│
├── modelo_sistema_agua.py               # Modelo principal
├── create_data.py                       # Script para generar datos de entrada
└── README.md                            # Este archivo
```

---

## ⚙️ Parámetros del Sistema

Los parámetros se configuran en `src/initial_values.py`:

### Parámetros Clave
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `DURACION_MANTENIMIENTO` | 3 días | Días que permanece cerrado el canal durante mantenimiento |
| `COEFICIENTE_PERDIDA_FILTRACION` | 0.05 | Fracción de pérdida en filtración (5%) |
| `COEFICIENTE_PERDIDA_CONDUCCION` | 0.08 | Fracción de pérdida en conducción (8%) |
| `DURACION_TURNO` | 9 días | Duración de cada turno de riego |
| `TIEMPO_TOTAL` | 365 días | Período de simulación |

### Stocks Iniciales
| Stock | Valor | Unidad |
|-------|-------|--------|
| `STOCK_INICIAL_CAUDAL` | 1000.0 | m³ |
| `STOCK_INICIAL_RECARGA` | 5000.0 | m³ |

### Derechos de Agua
| Derecho | Valor | Descripción |
|---------|-------|-------------|
| `DERECHOS_AGUA_SUPERFICIAL` | 40.0 | m³/día (superficial) |
| `DERECHOS_AGUA_SUBTERRANEA` | 30.0 | m³/día (subterránea) |

---

## 📊 Variables del Sistema

### Calendarios de Entrada
1. **CalendarioTurnosCanal.csv**
   - `Dia`: Número de día (1-365)
   - `NumeroTurno`: Número secuencial del turno
   - `DiaEnTurno`: Día dentro del turno actual (1-9)
   - `TurnoActivo`: Indicador de turno activo (1=sí, 0=no)

2. **CalendarioParadas.csv**
   - `Dia`: Número de día
   - `EnParada`: Indicador de parada (1=sí, 0=no)
   - `DuracionMantenimiento`: Duración de la parada (días)

3. **CalendarioApertura.csv**
   - `Dia`: Número de día
   - `CanalAbiertoProgramado`: Estado programado (1=abierto, 0=cerrado)

### Variables Calculadas (Output)
- **AperturaCanal**: Variable binaria (0/1)
  - AperturaCanal = CanalAbiertoProgramado AND NOT(EnParada)
  - Si en parada: canal cerrado durante `DURACION_MANTENIMIENTO` días

- **CaudalRegante**: Stock de agua en canal (m³)
  - Entrada: Flujo de turnos
  - Salida: Derechos superficial + pérdidas

- **Recarga**: Stock de agua en recarga (m³)
  - Entrada: Derechos superficial
  - Salida: Derechos subterránea

- **OfertaAgua**: Oferta total calculada (m³/día)
  - OfertaAgua = CaudalRegante × DERECHOS_SUPERFICIAL/100 + Recarga × DERECHOS_SUBTERRANEA/100

---

## 🎯 Opciones de Desmarque

El modelo se ejecuta **2 veces** con diferentes estrategias:

### Opción 1: Desmarque al Inicio del Turno
- Entrada de agua: **Días 1, 10, 19, 28, ...** (inicio de cada turno de 9 días)
- Flujo: `FLUJO_INICIAL_ENTRADA` en esos días
- **Archivo Output**: `CalendarioOferta_Opcion1.csv`

### Opción 2: Desmarque al Final del Turno
- Entrada de agua: **Días 9, 18, 27, 36, ...** (final de cada turno)
- Flujo: `FLUJO_INICIAL_ENTRADA` en esos días
- **Archivo Output**: `CalendarioOferta_Opcion2.csv`

---

## 🔬 Ecuaciones Diferenciales del Modelo

El sistema se modela mediante ecuaciones diferenciales ordinarias (ODEs):

```
d(CaudalRegante)/dt = Entrada_Turno - Flujo_Superficial - Pérdidas

d(Recarga)/dt = Flujo_Superficial - Flujo_Subterráneo

Donde:
  Entrada_Turno = FLUJO_INICIAL si AperturaCanal=1 y es día de desmarque
  Flujo_Superficial = CaudalRegante × DERECHOS_AGUA_SUPERFICIAL%
  Flujo_Subterráneo = Recarga × DERECHOS_AGUA_SUBTERRANEA%
  Pérdidas = CaudalRegante × (COEF_FILTRACION + COEF_CONDUCCION)
```

---

## 🚀 Ejecución

### 1. Generar datos de entrada
```bash
python create_data.py
```
Crea los 3 calendarios CSV en `data/inputs/`

### 2. Ejecutar el modelo
```bash
python modelo_sistema_agua.py
```

Salida esperada:
- 2 archivos CSV: `CalendarioOferta_Opcion1.csv` y `CalendarioOferta_Opcion2.csv`
- 2 gráficos PNG: `Graficos_Opcion1.png` y `Graficos_Opcion2.png`
- 1 tabla de comparación: `Comparacion_Opciones.csv`

---

## 📈 Interpretación de Resultados

### Gráficos Generados (3 paneles por opción)

**Panel 1: Evolución de Stocks**
- Caudal Regante (azul): volumen en el canal
- Recarga (verde): volumen en zona de recarga

**Panel 2: Estado del Canal**
- Área sombreada (cyan): canal abierto
- Vacío: canal cerrado por mantenimiento

**Panel 3: Oferta de Agua**
- Línea roja: cantidad de agua disponible (m³/día)

### Comparación de Opciones
```
               Métrica | Opción 1 (Inicio) | Opción 2 (Final)
Caudal Regante Promedio |      17.23        |      16.98
Oferta Promedio         |      28.96        |      28.78
```

**Interpretación:**
- Opción 1 (desmarque inicial) tiende a mantener stocks ligeramente mayores
- Diferencias mínimas indican que el sistema es robusto ante ambas estrategias

---

## 🔧 Modificación de Parámetros

Para ajustar el modelo:

1. **Editar `src/initial_values.py`**:
   ```python
   DURACION_MANTENIMIENTO = 5  # Cambiar a 5 días
   DERECHOS_AGUA_SUPERFICIAL = 50.0  # Cambiar derechos
   ```

2. **Editar turnos en `create_data.py`**:
   ```python
   dias_parada = [20, 150, 300]  # Cambiar fechas de parada
   ```

3. **Ejecutar nuevamente**:
   ```bash
   python create_data.py
   python modelo_sistema_agua.py
   ```

---

## 📦 Dependencias

```
pysd          # Dinámica de sistemas
pandas        # Manejo de datos
matplotlib    # Visualización
numpy         # Computación numérica
scipy         # Funciones científicas (odeint)
```

Instalar:
```bash
pip install pysd pandas matplotlib numpy scipy
```

---

## 📝 Notas

- El canal se cierra automáticamente durante paradas de mantenimiento (no acepta entrada)
- Pérdidas se aplican continuamente cuando hay agua en el canal
- Flujo de desmarque solo ocurre si: canal abierto Y es día de desmarque
- La oferta se calcula como porcentaje de los stocks según derechos de agua

---

## 👤 Autor
Capstone - Modelo de Gestión de Agua

**Fecha de creación**: 29 de abril de 2026

---
