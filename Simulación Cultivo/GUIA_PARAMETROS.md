# Guía de Parámetros — Simulación de Cultivo

Referencia de todos los parámetros configurables en `parametros.py`.
Edita ese archivo para ajustar el comportamiento del modelo sin modificar el código.

---

## 1. Suelo (FAO-56)

| Parámetro | Descripción | Valor típico |
|---|---|---|
| `CC` | Capacidad de campo (humedad volumétrica) | 0.10 – 0.35 |
| `PMP` | Punto de marchitez permanente | 0.04 – 0.15 |
| `Ze_evap` | Profundidad capa evaporante (m) | 0.10 – 0.15 |
| `AFE` | Agua fácilmente evaporable (mm) | 8 – 10 |
| `De0` | Déficit evaporación inicial (mm) | 0 = suelo a CC |
| `Dr0` | Déficit zona radicular inicial (mm) | 0 = suelo a CC |
| `ALPHA_SUELO` | Penalización no lineal de transpiración por textura `f(H) = H^α` | arenoso 1.2–1.5 · franco 1.5–2.0 · arcilloso 3–5 |
| `FRACCION_DRENAJE` | Fracción del riego que drena bajo la zona radicular | arenoso 0.30–0.45 · franco 0.10–0.20 · arcilloso 0–0.02 |

---

## 2. Política de riego

| Parámetro | Descripción | Valores |
|---|---|---|
| `H_OBJETIVO_PCT` | Humedad objetivo al regar (% de agua útil). 100 = llenar hasta CC | 20 – 100 |
| `RIEGO_HASTA_CC` | Si `True`, siempre apunta a CC (equivale a `H_OBJETIVO_PCT = 100`) | `True` / `False` |
| `HUMEDAD_MINIMA_PCT` | Si la humedad cae por debajo, se fuerza riego hasta este umbral | por defecto `PMP + 2%` |

---

## 3. Estanque predial

| Parámetro | Descripción |
|---|---|
| `DIAS_SIN_RIEGO_PARA_ESTANQUE` | **Días de espera mínima entre usos del estanque.** Conta desde cualquier riego (canal o estanque). El estanque riega como máximo 1 vez cada N días y cubre el déficit acumulado. |
| `REDUCCION_ESTANQUE_PCT_POR_DIA` | **% de cobertura que se descuenta por cada día que falta para el próximo turno.** Fórmula: `cobertura = max(0, 1 − días_hasta_turno × REDUCCION / 100)`. A mayor valor, más conservador; 0 = cubre siempre el 100%. |

### Ejemplos de `REDUCCION_ESTANQUE_PCT_POR_DIA` con 5 días hasta el turno

| Valor | Cobertura | Efecto |
|---|---|---|
| 0 | 100 % | Sin ahorro, cubre todo el déficit |
| 3 | 85 % | Leve conservación |
| 5 | 75 % | **Valor por defecto** — equilibrio riego/vida útil |
| 10 | 50 % | Muy conservador |
| 20 | 0 % | El estanque no entrega nada ese día |

> **Nota:** el estanque también limita su entrega diaria al ET del día `(Kcb + Ke) × ETo × ha`, evitando vaciar el estanque de golpe por déficit acumulado de días anteriores.

---

## 4. Fuente subterránea

| Parámetro | Descripción |
|---|---|
| `STOCK_SUBTERRANEO_INICIAL_M3` | Volumen inicial del acuífero (m³) |
| `DIAS_SIN_RIEGO_PARA_SUBTERRANEA` | Días consecutivos sin regar para activar el pozo. 9999 = desactivado |

---

## 5. Optimización de portafolio

| Parámetro | Descripción |
|---|---|
| `PARTICIONES` | Número de parcelas en que se divide el terreno |
| `REGANTE_ID` | ID del regante en `regantes.csv` |
| `DIA_SIEMBRA` | Día de siembra (offset desde `DIA_INICIO_SIMULACION`) |
| `DIA_INICIO_SIMULACION` | Día del año de inicio (1 = 01 Ene, 32 = 01 Feb, etc.) |

---

## 6. Referencia rápida — combinaciones frecuentes

**Suelo arenoso, riego intenso:**
```python
ALPHA_SUELO = 1.3
FRACCION_DRENAJE = 0.35
REDUCCION_ESTANQUE_PCT_POR_DIA = 3
DIAS_SIN_RIEGO_PARA_ESTANQUE = 2
```

**Suelo franco, equilibrio riego/ahorro (por defecto):**
```python
ALPHA_SUELO = 1.5
FRACCION_DRENAJE = 0.15
REDUCCION_ESTANQUE_PCT_POR_DIA = 5
DIAS_SIN_RIEGO_PARA_ESTANQUE = 2
```

**Estanque muy conservador (temporada larga):**
```python
REDUCCION_ESTANQUE_PCT_POR_DIA = 10
DIAS_SIN_RIEGO_PARA_ESTANQUE = 3
```
