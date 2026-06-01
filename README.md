# Modelo de Soporte a la Toma de Decisiones en la Agricultura Basado en Simulación Multiparadigma

> **Proyecto:** Capstone — Simulación Multiparadigma para la Gestión del Agua de Riego 
> **Paradigmas:** Dinámica de Sistemas (Oferta Hídrica) · Simulación de Eventos Discretos (Demanda de Cultivo) 

---

## Tabla de Contenidos

1. [Objetivo del Sistema](#1-objetivo-del-sistema)
 - 1.1 Necesidad de la modelación: el trade-off agua–calidad–presupuesto
2. [Arquitectura General](#2-arquitectura-general)
3. [Módulo 1 — Oferta Hídrica (Dinámica de Sistemas)](#3-módulo-1--oferta-hídrica-dinámica-de-sistemas)
 - 3.1 Parámetros configurables
 - 3.2 Generación de escenarios de desmarque
 - 3.3 Condición de activación del flujo de entrada al predio
 - 3.4 Modelado estocástico de pérdidas y oferta neta
 - 3.5 Salida: CalendarioOferta.csv
4. [Módulo 2 — Simulación de Cultivo (Eventos Discretos)](#4-módulo-2--simulación-de-cultivo-eventos-discretos)
 - 4.1 Balance hídrico FAO-56 doble coeficiente
 - 4.2 Distribución de calidad y respuesta al estrés hídrico acumulado
 - 4.3 Política de Riego
 - 4.4 Restricciones estacionales de siembra
 - 4.5 Optimización combinatoria de portafolio
 - 4.6 KPIs y reporte HTML
5. [Flujo de Datos end-to-end](#5-flujo-de-datos-end-to-end)
6. [Paradigmas de Simulación e Implementación Computacional](#6-paradigmas-de-simulación-e-implementación-computacional)
7. [Guía de Ejecución](#7-guía-de-ejecución)
8. [Archivos de Entrada y Salida](#8-archivos-de-entrada-y-salida)
9. [Referencias Bibliográficas](#9-referencias-bibliográficas)
10. [Fuentes de Datos](#10-fuentes-de-datos)

---

## 1. Objetivo del Sistema

El presente repositorio implementa la **plataforma de simulación computacional** de un modelo multiparadigma en desarrollo, diseñado para generar evidencia experimental en el contexto de una investigación sobre soporte a la toma de decisiones para regantes con derechos de agua en canal superficial y acceso optativo a fuentes subterráneas. La plataforma permite explorar, mediante corridas de simulación bajo distintos escenarios de disponibilidad hídrica, dos interrogantes centrales de la planificación agrícola:

1. **¿Cuánta agua llega al predio?** — El subsistema de Oferta Hídrica modela el canal de distribución como un sistema de **stocks y flujos** mediante Dinámica de Sistemas. Las **variables de estado** (acumulaciones de agua) evolucionan temporalmente bajo la acción de tasas de entrada (desmarque) y salida (consumo y pérdidas estocásticas), lo que permite capturar la **dinámica acumulativa** de la oferta superficial a lo largo del horizonte de planificación, incluyendo paradas de mantenimiento y E escenarios de desmarque final.

2. **¿Qué cultivos plantar y cuándo regar?** — El subsistema de Demanda de Cultivo emplea **Simulación de Eventos Discretos** para representar el ciclo agronómico de cada parcela como una secuencia de **transiciones de estado** (siembra → desarrollo → madurez → cosecha) disparadas por **eventos** programados en el calendario de eventos del motor SimPy. La **asignación de recursos hídricos** —canal, estanque predial y fuente subterránea— se ejecuta en cada evento de riego mediante una lógica de despacho por prioridad.

La elección de un enfoque **multiparadigma** responde a la naturaleza fenomenológicamente distinta de ambos subsistemas: la oferta hídrica exhibe comportamiento **continuo y acumulativo** con retroalimentación (propio de la Dinámica de Sistemas), mientras que la demanda agrícola está gobernada por **eventos discretos** que marcan transiciones fenológicas y decisiones de riego. Ambos subsistemas están **desacoplados**: se comunican exclusivamente mediante el archivo intermedio `CalendarioOferta.csv`, lo que permite re-ejecutar cada módulo de forma independiente.

### 1.1 Necesidad de la modelación: el trade-off agua–calidad–presupuesto

La complejidad del problema de planificación agrícola bajo restricción hídrica radica en la existencia de **tres tensiones simultáneas** que no pueden resolverse de forma independiente:

| Dimensión | Variable | Tensión |
|---|---|---|
| **Hídrica** | Volumen disponible en canal, estanque y acuífero | La oferta es incierta (desmarque) y discontinua (turnos, paradas) |
| **Agronómica** | Estrés hídrico $K_s(t)$, humedad radicular $D_r(t)$ | El déficit de riego reduce el rendimiento y la calidad del producto |
| **Económica** | Precio de venta (estacional), costo de producción, presupuesto total | El precio varía según el mes de cosecha; el presupuesto limita qué cultivos son viables |

El **trade-off central** surge de la interacción entre estas tres dimensiones: regar más reduce el estrés ($K_s \to 1$) y protege el rendimiento, pero consume el stock de agua disponible para el resto de la temporada y puede comprometer cultivos posteriores o en parcelas vecinas. Por otro lado, plantar cultivos de mayor valor económico suele requerir mayor demanda hídrica y mayor inversión inicial, lo que eleva la exposición al riesgo ante una temporada de desmarque bajo.

Una decisión de portafolio que ignore la dinámica hídrica puede sobreestimar los márgenes esperados; una que ignore la estacionalidad de precios puede suboptimizar el momento de cosecha; y una que ignore la restricción de presupuesto puede generar planes no ejecutables. La plataforma de simulación multiparadigma busca **generar la evidencia cuantitativa necesaria para analizar este trade-off** bajo E escenarios de oferta hídrica, facilitando la exploración de comportamientos del sistema como insumo para la etapa posterior de análisis e investigación.

---

## 2. Arquitectura General

La plataforma experimental está compuesta por dos subsistemas de simulación desacoplados que intercambian estado a través de un archivo CSV intermedio, permitiendo ejecutar corridas de simulación independientes para cada módulo y analizar el comportamiento del sistema bajo distintos escenarios de entrada. La selección del paradigma de simulación para cada subsistema responde a la estructura causal y temporal del fenómeno que representa: la Dinámica de Sistemas captura la evolución continua de stocks hídricos con estructura de retroalimentación, mientras que la Simulación de Eventos Discretos representa con fidelidad los procesos agronómicos gobernados por eventos discretos y transiciones de estado.

```mermaid
flowchart LR
 classDef ext fill:#f1f5f9,stroke:#64748b,color:#1e293b,stroke-dasharray:5 4
 classDef param fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
 classDef engine fill:#dcfce7,stroke:#16a34a,color:#14532d
 classDef csv fill:#fef9c3,stroke:#ca8a04,color:#713f12
 classDef out fill:#fce7f3,stroke:#db2777,color:#831843

 %% Fuentes externas
 EXT1(["CEAZAMet\nClima histórico"]):::ext
 EXT2(["CEAZA Nieve\nSWE cuenca"]):::ext
 EXT3(["DGA\nBoletines hídricos"]):::ext

 %% Módulo 1
 subgraph M1["① Oferta Hídrica — Dinámica de Sistemas"]
 direction TB
 P1["initial_values.py\nParámetros del canal"]:::param
 SD["modelo_simulacion_oferta_hidrica.py\nE escenarios × T días\nPérdidas U(min,max)"]:::engine
 P1 --> SD
 end

 %% Módulo 2
 subgraph M2["② Simulación de Cultivo — Eventos Discretos"]
 direction TB
 P2["parametros.py\nCultivos · Regantes · Clima"]:::param
 DE["simular_demanda.py\nBalance FAO-56 + despacho\nCombinaciones C(n+P-1,P)"]:::engine
 P2 --> DE
 end

 %% Archivo intermedio
 CSV[("CalendarioOferta.csv\noferta diaria × escenario")]:::csv

 %% Salidas finales
 O1["SimulacionDemanda.csv"]:::out
 O2["ReporteEscenarios.html"]:::out

 %% Flujos
 EXT1 & EXT2 & EXT3 --> P2
 EXT2 & EXT3 --> P1
 SD --> CSV
 CSV --> DE
 DE --> O1
 DE --> O2
```

> **Principio de desacoplamiento:** ambos subsistemas son autónomos. La re-ejecución del Módulo 1 —ante una revisión del desmarque estimado— no requiere re-ejecutar el Módulo 2, y viceversa. El intercambio de estado entre subsistemas ocurre exclusivamente a través de `CalendarioOferta.csv`, lo que facilita la experimentación sistemática bajo escenarios alternativos de oferta hídrica.

---

## 3. Módulo 1 — Oferta Hídrica (Dinámica de Sistemas)

El subsistema de Oferta Hídrica modela la evolución temporal del volumen de agua disponible en el predio a lo largo de un horizonte de T días. La **variable de estado** central es la oferta superficial neta diaria, cuya trayectoria resulta de la interacción entre las tasas de entrada (desmarque) y las tasas de salida estocásticas (pérdidas por conducción y filtración). La incertidumbre sobre el desmarque final se incorpora mediante E escenarios paralelos que exploran el espacio de realizaciones posibles.

```mermaid
flowchart TD
 classDef param fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
 classDef proc fill:#dcfce7,stroke:#16a34a,color:#14532d
 classDef out fill:#fef9c3,stroke:#ca8a04,color:#713f12
 classDef dec fill:#fff7ed,stroke:#ea580c,color:#7c2d12

 D0["PORCENTAJE_DESMARQUE_FINAL → d₀\nSALTO_DESMARQUE → Δd\nNUM_ESCENARIOS → E\nDIA_INICIO → t₀\nHORIZONTE → T"]:::param
 PL["PERDIDA_CONDUCCION ~ U(min,max)\nPERDIDA_FILTRACION ~ U(min,max)"]:::param
 CA["CALENDARIO_PARADAS\nFRECUENCIA_TURNO\nDURACION_MANTENIMIENTO"]:::param

 D0 --> ESC["escenarios.py\nd₋₂, d₋₁, d₀, d₊₁, d₊₂\n(E escenarios fijos, valores = d₀ ± i·Δd)"]:::proc

 ESC --> ESCLOOP["eᵢ = e₀"]:::proc
 CA --> ESCLOOP
 PL --> ESCLOOP

 ESCLOOP --> LOOP["tᵢ = t₀"]:::proc

 LOOP --> T{"¿TurnoActivo\nAND\nNO EnParada?"}:::dec
 T -->|"No"| Z["OfertaSuperficial = 0 m³"]:::out
 T -->|"Sí"| Q["Pcond ~ U(·), Pfilt ~ U(·)\nQ_bruta = N_acc × V_acc × dₑ\nQ_neta = Q_bruta · (1 − Pcond − Pfilt)"]:::proc
 Q --> REC["Registrar fila (tᵢ, eᵢ, Q_neta, flags)"]:::proc
 Z --> REC

 REC --> NEXTD{"¿tᵢ < T?"}:::dec
 NEXTD -->|"Sí: tᵢ = tᵢ + 1"| LOOP
 NEXTD -->|"No: tᵢ = t₀"| NEXTE{"¿eᵢ < E?"}:::dec
 NEXTE -->|"Sí: eᵢ = eᵢ + 1"| ESCLOOP
 NEXTE -->|"No"| CO

 CO[("CalendarioOferta.csv\nT días × E escenarios\nOfertaSuperficial, Pérdidas, Flags")]:::out
```

### 3.1 Parámetros configurables

Todos los parámetros se definen en `src/initial_values.py`:

| Parámetro | Variable | Descripción |
|---|---|---|
| Acciones de agua | `NUMERO_ACCIONES` | Derechos del regante (unidades) |
| Volumen por acción | `VALOR_ACCION` | m³ por turno por acción (1 L/s × 12 h = 43.2 m³) |
| Desmarque inicial | `PORCENTAJE_DESMARQUE_INICIAL` | % del canal habilitado en la temporada actual (valor **conocido**) |
| Desmarque final | `PORCENTAJE_DESMARQUE_FINAL` | % del canal esperado tras el cambio de temporada (valor **incierto** — ver §3.2) |
| Fecha de cambio | `FECHA_DESMARQUE` | Formato `MM-DD` (ej. `09-01` = 1 sep) |
| **Salto de escenarios** | `SALTO_DESMARQUE` | Paso entre escenarios de desmarque (ej. 0.025 = 2.5%) |
| Pérdida filtración | `PERDIDA_FILTRACION` | Rango uniforme `(min, max)` como fracción del flujo |
| Pérdida conducción | `PERDIDA_CONDUCCION` | Rango uniforme `(min, max)` como fracción del flujo |
| Paradas de mantenimiento | `CALENDARIO_PARADAS` | Lista de días de inicio de cada parada |
| Duración mantenimiento | `DURACION_MANTENIMIENTO` | Días consecutivos de cierre por parada |
| Recargas subterráneas | `RECARGAS_AGUA_SUBTERRANEA` | Lista de tuplas `(MM-DD, m³)` |

#### Naturaleza de los parámetros de desmarque

El **desmarque inicial** corresponde al porcentaje de canal habilitado durante la temporada en curso: es un valor **conocido y fijo**, establecido por la organización de usuarios del canal al inicio de la temporada en función del agua disponible al momento.

El **desmarque final** es el porcentaje esperado para la siguiente temporada, que entra en vigencia a partir de `FECHA_DESMARQUE`. Este valor es **incierto al momento de la planificación**, ya que depende de variables hidrológicas que solo se conocerán con certeza al cierre del año. Las principales variables predictoras son:

- **Nivel de nieve** en la cuenca del río Elqui (indicador de recarga futura por deshielo)
- **Nivel del embalse Puclaro** (principal reservorio regulador del valle)
- **Caudal del río Elqui** (caudal actual como proxy de la disponibilidad hídrica corriente)

La estimación precisa del desmarque final debería provenir de un **modelo de regresión** entrenado con series históricas de esas tres variables como predictores y el desmarque observado como variable respuesta. Las fuentes de datos disponibles para construir ese modelo son (ver §9):

- Nivel de nieve: **CEAZA — Plataforma de monitoreo de nieves** (https://nieve.ceaza.cl)
- Nivel embalse Puclaro y caudal río Elqui: **DGA — Boletines hidrométricos** (https://dga.mop.gob.cl/servicios-de-informacion/boletines)
- Variables climáticas del modelo de demanda (`datosclima.csv`, `datos_clima_365dias.csv`) y complementarias para el modelo de desmarque: **CEAZAMet** (https://www.ceazamet.cl)

En la versión actual del modelo, el regante ingresa su mejor estimación como `PORCENTAJE_DESMARQUE_FINAL`, y el análisis de escenarios (§3.2) permite explorar el riesgo ante desvíos respecto de esa estimación.

### 3.2 Generación de escenarios de desmarque

Dado que el desmarque final es incierto, el modelo genera **E escenarios** que cubren un rango de posibles realizaciones alrededor de la estimación central del regante, variando en pasos de `SALTO_DESMARQUE`:

$$
d(i) = d_0 + i \cdot \Delta d, \quad i \in \{-2,\,-1,\,0,\,+1,\,+2\}
$$

donde $d_0$ = `PORCENTAJE_DESMARQUE_FINAL` y $\Delta d$ = `SALTO_DESMARQUE`.

Ejemplo con base = 15 % y salto = 2.5 %:

| Escenario | Desmarque final | Interpretación |
|---|---|---|
| −2 | 10 % | Temporada muy seca — embalse bajo, poca nieve |
| −1 | 12.5 % | Temporada moderadamente seca |
| 0 (base) | 15 % | Estimación central del regante |
| +1 | 17.5 % | Temporada moderadamente húmeda |
| +2 | 20 % | Temporada húmeda — buen nivel de nieve y embalse |

La estructura de generación de escenarios está codificada en `modulos/escenarios.py → generar_escenarios(iv)`. El escenario 0 se denomina *Principal*.

### 3.3 Condición de activación del flujo de entrada al predio

Para cada paso de integración $t$ y para cada escenario $e_i$, el **flujo de entrada** al predio es positivo únicamente cuando se satisfacen simultáneamente dos condiciones booleanas:

```
AperturaCanal = TurnoActivo AND NOT EnParada
```

- **TurnoActivo**: el paso temporal $t$ corresponde a un día de turno del regante (múltiplo de `FRECUENCIA_TURNO`).
- **EnParada**: $t$ cae dentro de una ventana de mantenimiento definida por `CALENDARIO_PARADAS` + `DURACION_MANTENIMIENTO`.

Cuando la condición no se satisface, el flujo de entrada es nulo y la **variable de nivel** del stock predial no experimenta acumulación en ese paso de integración: $Q_{neta}(t) = 0$.

### 3.4 Modelado estocástico de pérdidas y oferta neta

Cuando el flujo de entrada está activo, la oferta bruta del regante constituye la **tasa de entrada** —flujo positivo— que alimenta la acumulación en el stock predial:

$$
Q_{bruta} = N_{acc} \times V_{acc} \times d
$$

donde $N_{acc}$ = `NUMERO_ACCIONES`, $V_{acc}$ = `VALOR_ACCION`, $d$ = porcentaje de desmarque.

Las pérdidas de conducción y filtración se modelan como **variables aleatorias** con distribución uniforme, muestreadas independientemente en cada paso temporal:

$$
P_{cond} \sim U(\text{min}_{cond},\, \text{max}_{cond}), \quad P_{filt} \sim U(\text{min}_{filt},\, \text{max}_{filt})
$$

$$
P_{total} = P_{cond} + P_{filt}, \qquad Q_{neta} = Q_{bruta}\,(1 - P_{total})
$$

La **recarga subterránea** se incorpora como una **perturbación exógena** puntual al stock de agua subterránea únicamente en la fecha exacta especificada en `RECARGAS_AGUA_SUBTERRANEA` (efecto no acumulativo entre períodos de integración).

### 3.5 Salida: CalendarioOferta.csv

El archivo resultante tiene una fila por día × escenario con las columnas:

| Columna | Descripción |
|---|---|
| `Dia` | Día del año (1–365) |
| `Fecha` | Fecha calendario |
| `TurnoActivo` | Booleano — el turno corresponde a este regante |
| `EnParada` | Booleano — el canal está en mantenimiento |
| `AperturaCanal` | Booleano — el agua efectivamente llega al predio |
| `OfertaSuperficial` | m³ netos disponibles en el predio ese día |
| `PerdidaConduccion` | m³ perdidos por conducción |
| `PerdidaFiltracion` | m³ perdidos por filtración |
| `PerdidaTotal` | m³ totales perdidos |
| `PorcentajeDesmarque` | % de desmarque aplicado ese día |
| `RecargaSubterranea` | m³ recargados al acuífero (solo en fecha puntual) |
| `Escenario` | Identificador del escenario (−2 a +2) |

**Figura 1.** Ejemplo de salida del Módulo 1: calendario de oferta superficial (panel superior) y recargas de agua subterránea (panel inferior) para el escenario base, con pérdidas estocásticas y período de mantenimiento señalado.

![Calendario de Oferta Hídrica](docs/oferta_hidrica_calendario.png)

---

## 4. Módulo 2 — Simulación de Cultivo (Eventos Discretos)

El subsistema de Demanda de Cultivo determina la combinación óptima de cultivos y la estrategia de **asignación de recursos hídricos** que maximiza el margen económico, condicionada a la oferta superficial provista por el Módulo 1 vía `CalendarioOferta.csv`. Cada parcela se representa como una **entidad** SimPy que transita entre **estados fenológicos** (siembra → establecimiento → desarrollo → madurez → cosecha) mediante **eventos discretos** programados en el **calendario de eventos** del motor de simulación. La ejecución orientada a eventos (**event-driven execution**) avanza el reloj de simulación de evento en evento, sin procesar pasos temporales inactivos.

```mermaid
flowchart TD
 classDef param fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
 classDef proc fill:#dcfce7,stroke:#16a34a,color:#14532d
 classDef out fill:#fce7f3,stroke:#db2777,color:#831843
 classDef data fill:#fef9c3,stroke:#ca8a04,color:#713f12
 classDef dec fill:#fff7ed,stroke:#ea580c,color:#7c2d12

 CO[("CalendarioOferta.csv\nE escenarios")]:::data
 CLI["datosclima.csv\nETo(t), PP(t)"]:::param
 DC["data_cultivos.csv\nKcb, fases fenológicas"]:::param
 CAL["calendario_siembra.csv\nfiltro de cultivos por mes"]:::param
 REG["regantes.csv\nha, capacidad estanque"]:::param
 PROD["productividad_cultivos.csv\nprecios CLP/ha, costos, rendimientos"]:::param
 PAR["parametros.py\nα, f_drain, Dr₀, presupuesto…"]:::param

 subgraph SIMPY["DES — proceso por parcela, ciclo agronómico"]
 FAO["Balance FAO-56\nET_real = Ks·Kcb·ET₀·Hᵅ + Es\nActualizar Dr y De"]:::proc
 DISP["Despacho de agua\n① Canal ② Estanque ③ Subterráneo"]:::proc
 FAO --> DISP
 end

 CLI --> FAO
 DC --> FAO
 PAR --> FAO
 CO --> DISP
 REG --> DISP

 subgraph OPT["Optimización combinatoria"]
 COMB["Enumerar C(n+P−1, P) combinaciones\nde cultivos filtrados por mes"]:::proc
 BEST["Combinación ganadora\nmax Σ Margen_real s.a. Σ Costo ≤ Presupuesto"]:::proc
 COMB --> BEST
 end

 CAL --> COMB
 PROD --> COMB
 SIMPY --> OPT

 BEST --> HTML["ReporteParticiones.html\nKPIs hídricos + económicos por escenario"]:::out
 BEST --> CSV["SimulacionDemanda.csv\nReporteEscenarios.csv"]:::out
```

### 4.1 Balance hídrico FAO-56 doble coeficiente

#### Formulación base (potencial)

El enfoque de doble coeficiente FAO-56 (Allen et al., 1998) separa la evapotranspiración del cultivo en dos flujos físicamente distintos:

$$
ET_c = (K_{cb} + K_e)\cdot ET_0
$$

donde $ET_0$ es la evapotranspiración de referencia (mm/día) y los coeficientes escalan ese potencial climatológico: $K_{cb}$ para la **transpiración** de la planta y $K_e$ para la **evaporación** del suelo desnudo o húmedo entre plantas. Desagregando ambos flujos explícitamente:

$$
ET_c = \underbrace{K_{cb}\cdot ET_0}_{T_p \;(\text{transpiración potencial})} \;+\; \underbrace{K_e\cdot ET_0}_{E_s \;(\text{evaporación superficial})}
$$

- $K_{cb}(t)$ varía linealmente a lo largo de las fases fenológicas `ini → des → med → fin` según las duraciones `L_ini, L_des, L_med, L_fin` de `data_cultivos.csv`.
- $K_e(t)$ se rige por un balance de la capa superficial (energía disponible limitada por $K_{cb,max}$ y agua disponible en el estrato evaporativo $Ze$), con coeficiente de reducción $K_r$ cuando esa capa se ha secado.

**Figura 2.** Trayectorias de $K_{cb}(t)$ (panel izquierdo) y $K_{c,max}(t)$ (panel derecho) para los ocho cultivos simulados, calculadas a partir de los parámetros fenológicos de `data_cultivos.csv` y la serie climática de 365 días. La progresion sigmoidal de $K_{cb}$ refleja las fases ini → des → med → fin; $K_{c,max}$ fluctua con el viento y la humedad relativa diaria.

![Kcb y Kcmax diario por cultivo](docs/kcb_kcmax_cultivos.png)

#### Extensión 1 — estrés hídrico radicular ($K_s$)

La ecuación anterior es **potencial**: supone suelo a capacidad de campo. Cuando el déficit radicular $D_r$ supera el agotamiento fácilmente aprovechable (AFA), la planta ya no puede transpirar a tasa plena. FAO-56 introduce $K_s \in [0,1]$ que **pondera únicamente la transpiración** (la evaporación tiene su propio mecanismo de reducción a través de $K_r$ y el balance AET/AFE):

$$
T_{real}(t) = K_s(t)\cdot K_{cb}(t)\cdot ET_0(t)
$$

$$
K_s(t)=\begin{cases}
1 & D_r(t-1)\le \text{AFA} \\
\dfrac{\text{ADT}-D_r(t-1)}{\text{ADT}-\text{AFA}} & D_r(t-1)>\text{AFA}
\end{cases}
$$

con $\text{AFA} = p\cdot\text{ADT}$ (fracción de agotamiento sin estrés, parámetro $p$ del cultivo) y $\text{ADT} = 1\,000\cdot(CC - PMP)\cdot Z_r$ (agua disponible total en zona radicular, mm).

La $ET$ real bajo estrés —pero aún con reducción lineal en $D_r$— queda:

$$
ET_{real}(t) = K_s(t)\cdot K_{cb}(t)\cdot ET_0(t) + E_s(t)
$$

#### Extensión 2 — retención no lineal por textura ($f(H) = H^\alpha$)

$K_s$ lineal es una simplificación operativa reconocida por el propio FAO-56: asume que toda el agua entre AFA y el punto de marchitez es igualmente accesible. En suelos finos (franco, arcilloso), una fracción significativa queda retenida a tensiones matriciales que la planta no puede vencer, haciendo que la transpiración caiga **más rápido** que de forma lineal al secarse el perfil.

Para capturar ese comportamiento sin requerir los parámetros completos de Van Genuchten ($\theta_r$, $\theta_s$, $n$), se introduce un factor potencial análogo a la curva de Brooks & Corey (1964):

$$
f(H(t)) = H(t)^{\,\alpha}, \qquad H(t) = 1 - \frac{D_r(t-1)}{\text{ADT}} \in [0,1]
$$

donde $H$ es la humedad relativa de la zona radicular (1 = campo a capacidad, 0 = marchitez permanente). Aplicado solo a la transpiración, la ecuación implementada resulta:

$$
\boxed{ET_{real}(t) = K_s(t)\cdot K_{cb}(t)\cdot ET_0(t)\cdot H(t)^{\alpha} + E_s(t)}
$$

**Interpretación de $\alpha$:**

| Textura | Rango sugerido $\alpha$ | Comportamiento |
|---|---|---|
| Arenoso | 1.2 – 1.5 | Caída casi lineal; poca retención capilar |
| Franco | 1.5 – 2.0 | Caída moderadamente acelerada |
| Franco-arcilloso | 2.0 – 3.0 | Caída marcada antes del punto de marchitez |
| Arcilloso | 3.0 – 5.0 | Caída muy abrupta; alto agua retenida no disponible |

Con $\alpha = 1$ la expresión se reduce a $K_s \cdot K_{cb} \cdot ET_0 \cdot H$, que es equivalente al comportamiento FAO-56 estándar multiplicado por la humedad relativa. El parámetro se configura con `ALPHA_SUELO` en `parametros.py`.

#### Extensión 3 — estado del suelo post-riego con fracción de drenaje ($f_{drain}$)

El balance FAO-56 estándar supone que toda el agua aplicada queda disponible en la zona radicular hasta que se alcanza CC (cubeta perfecta). En la realidad, suelos con alta conductividad hidráulica (arena, franco-arenoso) drenan una fracción del agua aplicada **por debajo de la zona radicular el mismo día**, resultando en un estado de humedad final menor que el predicho por la cubeta simple.

La actualización del déficit radicular incorpora este efecto mediante una **fracción de drenaje inmediato** $f_{drain} \in [0, 1)$:

$$
D_r(t) = D_r(t-1) - PP(t)\cdot(1-f_{drain}) - R(t)\cdot(1-f_{drain}) + ET_{real}(t)
$$

Solo la fracción $(1-f_{drain})$ del agua aplicada (riego $R$ y precipitación $PP$) reduce efectivamente el déficit radicular. La capa superficial evaporante (balance de $D_e$) **no se modifica**, ya que el drenaje ocurre en profundidades mayores a $Z_e$.

| Textura | Rango sugerido $f_{drain}$ | Descripción |
|---|---|---|
| Arenoso | 0.30 – 0.45 | Drena rápido; retiene poca agua post-riego |
| Franco | 0.10 – 0.20 | Drenaje moderado |
| Franco-arcilloso | 0.02 – 0.08 | Drenaje lento |
| Arcilloso | 0.00 – 0.02 | Retiene casi toda el agua aplicada |

El parámetro `FRACCION_DRENAJE` en `parametros.py` es **calibrable con sensor volumétrico**: se mide $\theta$ antes y ~24 h después de un riego de volumen conocido (sin planta activa para eliminar la transpiración), y se ajusta $f_{drain}$ hasta que el modelo reproduce el $\theta$ final observado.

Los parámetros de suelo (`CC`, `PMP`, `Ze_evap`, `AET`, `AFE`) se definen en `parametros.py`. Las condiciones iniciales de déficit (`De0`, `Dr0`) se fijan en cero (suelo a capacidad de campo al inicio de la siembra).

### 4.2 Distribución de calidad y respuesta al estrés hídrico acumulado

Una vez completada la simulación del balance hídrico diario (§4.1), el modelo evalúa el **impacto acumulado del estrés hídrico percibido durante el ciclo de vida del cultivo** sobre la distribución de calidad del producto. El procedimiento es determinístico y opera sobre dos señales de estrés derivadas directamente de las trayectorias de $K_s(t)$ y $H(t)$ registradas durante la simulación.

#### Señales de estrés integradas durante el ciclo

**S1 — Fracción de agua no cubierta** (déficit hídrico integrado):

$$
S_1 = \frac{\text{Deficit}_{m3}}{\text{Deficit}_{m3} + \text{Aplicado}_{m3}}
$$

Captura la proporción del volumen total demandado que no fue satisfecha por ninguna fuente. Un $S_1 = 0$ indica cobertura completa; $S_1 = 1$ indica que el cultivo no recibió riego.

**S2 — Déficit continuo de humedad relativa** (estrés percibido en zona radicular):

$$
S_2 = \max\!\left(0,\; 1 - \frac{\bar{H}}{70\,\%}\right)
$$

donde $\bar{H}$ es la humedad relativa media de la zona radicular durante el ciclo ($H = 1 - D_r/\text{ADT}$). El umbral del 70 % corresponde al límite de agotamiento fácilmente aprovechable (AFA); por encima de él $S_2 = 0$ (sin estrés percibido). Esta métrica continua es más robusta que contar días discretos bajo el umbral AFA, ya que los riegos de emergencia pueden producir muchos días bajo el umbral aunque el cultivo se recupere —el conteo binario inflaría artificialmente la señal de estrés.

**Estrés efectivo combinado:**

$$
S_{eff} = 0.6\cdot S_1 + 0.4\cdot S_2
$$

con una corrección de curvatura $S_{eff}^{corr} = S_{eff}^{1.3}$ que penaliza más severamente los estrés altos.

#### Factor de respuesta al estrés $K_y$

El coeficiente de respuesta al rendimiento $K_y$ (Allen et al., 1998) pondera el impacto del estrés efectivo según la sensibilidad del cultivo:

$$
K_y = \begin{cases} 1.1 & \text{cultivos de fruto (tomate, choclo, brócoli, repollo)} \\ 1.0 & \text{cultivos de hoja (lechuga, apio, acelga)} \end{cases}
$$

La reducción relativa del rendimiento potencial respecto al ideal queda representada por $R = \max(0,\, 1 - K_y \cdot S_{eff}^{corr})$, que opera como indicador interno de penalización.

#### Distribución de calidad

El modelo clasifica la producción simulada en tres categorías:

| Categoría | Factor de valorización | Descripción |
|---|---|---|
| **Primera** | 1.0 × precio | Producto sin estrés significativo; cumple estándares de calidad plenos |
| **Segunda** | 0.6 × precio | Producto con estrés moderado; comercializable con descuento |
| **Pérdida** | 0.05 × precio | Producto con estrés severo; descartado o sin valor comercial relevante |

Las proporciones de cada categoría se calculan mediante funciones sigmoidal y exponencial del estrés efectivo:

$$
\text{Primera}_{base} = e^{-1.5\, S_{eff}^{corr}}, \qquad \text{P\'{e}rdida}_{base} = \min\!\left(0.4,\; \frac{1}{1 + e^{-3(S_{eff}^{corr} - 0.6)}}\right)
$$

$$
\text{Segunda}_{base} = \max(0,\; 1 - \text{Primera}_{base} - \text{P\'{e}rdida}_{base})
$$

Las proporciones se ajustan además según la **condición óptima de cultivo** (cobertura $\geq 95\,\%$, $\bar{H} \geq 70\,\%$, $S_{eff} \leq 0.60$) y por **caps escalonados de pérdida** según el nivel de humedad media: a mayor $\bar{H}$, el techo de pérdida admisible es más bajo (desde 0.15 cuando $\bar{H} \geq 80\,\%$ hasta sin cap cuando $\bar{H} < 35\,\%$). Al final se aplica una normalización para garantizar $\text{Primera} + \text{Segunda} + \text{Pérdida} = 1$.

#### Ingreso real ajustado por calidad

El ingreso real que la simulación registra como salida del modelo se obtiene ponderando el ingreso ideal (precio de mercado por producción potencial completa) por el factor de calidad compuesto:

$$
F = p_1 \cdot 1.0 + p_2 \cdot 0.6 + p_{loss} \cdot 0.05
$$

$$
I_{real} = I_{ideal} \cdot F, \qquad \text{Margen}_{real} = I_{real} - \text{Costo}
$$

donde $p_1$, $p_2$, $p_{loss}$ son las proporciones de Primera, Segunda y Pérdida respectivamente. Esta cadena — balance hídrico diario → señales de estrés acumulado → distribución de calidad → ingreso real — constituye el mecanismo central por el que el estrés hídrico percibido durante el ciclo se traduce en una penalización económica cuantificable, que es la variable que el optimizador combinatorio maximiza en la selección del portafolio.

### 4.3 Política de Riego

En cada **evento de riego** el proceso de despacho satisface la demanda neta del cultivo ($D_N = \max(0,\; ET_r - PP)$, donde $ET_r$ es la evapotranspiración real bajo estrés) asignando los **recursos hídricos disponibles** en el siguiente orden de prioridad:

```
1. CANAL (eventos de turno con flujo activo):
 a. Riego directo: min(OfertaCanal, DemandaNeta) → aplicado en el evento actual
 b. Almacenamiento: excedente del canal → estanque predial (hasta capacidad máxima)
 c. Pérdida: excedente que supera capacidad del estanque

2. ESTANQUE (cualquier evento, si nivel > 0):
 - Extracción para completar la demanda neta no cubierta por el canal

3. SUBTERRÁNEO (si han transcurrido ≥ DIAS_SIN_RIEGO_PARA_SUBTERRANEA sin riego):
 - Extracción del stock subterráneo para cubrir el déficit hídrico residual
```

El **stock del estanque** se actualiza en cada evento de acuerdo con la ecuación de balance:

$$
N_{est}(t) = N_{est}(t-1) + A(t) - E(t)
$$

donde $A(t)$ = volumen almacenado y $E(t)$ = volumen extraído del estanque ese día.

con $N_{est} \in [0,\, C_{est}]$, donde $C_{est}$ es la capacidad máxima del **recurso de almacenamiento** predial, configurada en `regantes.csv`.

Las salidas de este bloque registran el estado de la **asignación de recursos** en las columnas `Canal_Riego_m3`, `Canal_Estanque_m3`, `Aplicado_m3`, `Subterranea_Usada_m3` y `Perdida_m3` del CSV de simulación diaria.

### 4.4 Restricciones estacionales de siembra

El archivo `inputs/calendario_siembra.csv` define, para cada **entidad cultivo**, en qué meses es posible **iniciar el proceso de simulación** (1 = disponible, 0 = restringido):

| nombre | enero | febrero | … | diciembre |
|---|---|---|---|---|
| lechuga_escarola | 0 | 1 | … | 0 |
| tomate | 1 | 0 | … | 1 |
| … | … | … | … | … |

Al programarse el evento de inicio de temporada, el calendario de eventos convierte `DIA_INICIO_SIMULACION + DIA_SIEMBRA` a mes calendario y selecciona únicamente las entidades cultivo con valor 1 en esa columna. El filtro se aplica **antes** de construir las combinaciones del evaluador exhaustivo, reduciendo el espacio de búsqueda combinatorio.

### 4.5 Optimización combinatoria de portafolio

El regante divide su superficie en `PARTICIONES` parcelas iguales ($ha_{part} = ha_{total} / P$). Para cada escenario de oferta, la evaluación exhaustiva del espacio combinatorio determina la **combinación óptima de $P$ entidades cultivo** (con repetición permitida) que maximiza el margen económico total.

**Espacio de búsqueda:**

El número de combinaciones es la combinación con repetición de $n$ cultivos en $P$ posiciones:

$$
\binom{n + P - 1}{P}
$$

Por ejemplo con $n = 8$ cultivos disponibles y $P = 4$ particiones → $\binom{11}{4} = 330$ combinaciones. Con $n = 6$ cultivos (restricción estacional de agosto) y $P = 4$ → $\binom{9}{4} = 126$ combinaciones.

**Algoritmo de búsqueda exhaustiva:**

Para un portafolio de $P$ particiones, se evalúan de forma exhaustiva **todas** las combinaciones del espacio de búsqueda (enumeración completa). La combinación ganadora es aquella que maximiza:

$$
\text{score} = \sum_{i=1}^{P} \text{Margen}_{real,i} \quad \text{sujeto a} \quad \sum_{i=1}^{P} \text{Costo}_i \le \text{Presupuesto}
$$

donde el margen real considera tanto el margen de comercialización como el costo de los insumos hídricos.

### 4.6 KPIs y reporte HTML

#### Fuentes y metodología de los parámetros económicos

Los datos de `productividad_cultivos.csv` provienen de dos fuentes oficiales del ODEPA, con ajuste por IPC:

**Precios de venta (columnas `enero`–`diciembre`, CLP/ha):**

Obtenidos del sistema [Series de tiempo — Precios Hortalizas](https://aplicativos.odepa.gob.cl/series-precios/series-tiempo) (ODEPA). Para cada cultivo se consultó con la siguiente configuración:

- Tipo de precios: *Precios mayoristas*
- Subsector: *Hortalizas y tubérculos*
- Tipo de precios: *Reales* (ajustados por IPC a la fecha de consulta)
- Tipo consulta: *Serie anual*

Para cada cultivo se descargó la serie mensual 2014–2025 con precios ya ajustados por IPC a base 04/2026 (opción *Reales* del sistema ODEPA). A partir de esa serie se calculó el **promedio interanual por mes**: se promedian todos los valores de enero de 2014 a 2025, luego todos los febreros, y así para cada mes del año. El resultado es un vector de 12 precios representativos que captura la estacionalidad típica del cultivo sin estar distorsionado por años atípicos.

> **Por qué este procedimiento:** al expresar todos los precios en pesos de abril de 2026 (misma base IPC) y luego promediar por mes a lo largo de 11 años, todos los cultivos quedan en la **misma escala monetaria real**. Esto permite comparar directamente, por ejemplo, si la lechuga escarola genera mayor margen que el repollo en marzo, sin que la comparación se vea afectada por la inflación de distintos períodos. Es la única forma robusta de ordenar cultivos por rentabilidad relativa cuando sus precios tienen estacionalidades distintas.

El precio unitario (CLP por unidad comercial) se multiplicó por el rendimiento (`rendimiento`) para convertirlo a **CLP/ha**, que es el valor almacenado en cada columna mensual. La unidad comercial de cada cultivo queda registrada en la columna `unidad` (`kg` para tomate, `unidad` para el resto).

**Rendimiento y costo (columnas `rendimiento`, `costo`, CLP/ha y unidades/ha ó kg/ha):**

Extraídos de las [Fichas de Costo de Hortalizas](https://www.odepa.gob.cl/fichas-de-costo-de-hortalizas) (ODEPA). Los valores de ficha están en pesos nominales del año de publicación; se aplicó el **mismo ajuste IPC (base 04/2026)** para llevar costos y rendimientos a valores reales comparables con los precios — garantizando que el margen calculado sea consistente en todas las columnas.

**Figura 3.** Precio promedio mensual por unidad comercial para los ocho cultivos, calculado como promedio interanual de los 11 años de la serie ODEPA 2014–2025, con todos los valores ajustados a pesos reales de abril de 2026 (IPC base 04/2026). Al estar en la misma base real, la figura permite comparar directamente qué cultivo es más rentable que otro en cada mes del año. La estacionalidad aquí graficada es la que el modelo aplica como precio de venta según el mes de cosecha en la optimización combinatoria.

![Precio Promedio Mensual Hortalizas](docs/precios_hortalizas.png)

Por cada combinación óptima la simulación registra los siguientes indicadores:

**Hídricos:**

| KPI | Descripción |
|---|---|
| `OfertaCanal_total_m3` | Agua total llegada del canal (riego + estanque + pérdida) |
| `Canal_Riego_m3` | Fracción del canal usada directamente en riego |
| `Canal_Estanque_m3` | Fracción del canal almacenada en estanque |
| `Perdida_m3` | Agua del canal desperdiciada (desborde de estanque) |
| `Subterranea_m3` | Agua extraída del acuífero |
| `Theta_vol_med_%` | Humedad volumétrica media en zona radicular |
| `Estanque_medio_m3` | Nivel medio del estanque durante la temporada |
| `Cobertura_ETc_%` | Fracción de la demanda de ET cubierta efectivamente |

**Económicos:**

| KPI | Descripción |
|---|---|
| `Ingreso_ideal_clp` | Ingreso potencial = precio mes cosecha × rendimiento × ha (sin descuento por calidad) |
| `Ingreso_real_clp` | Ingreso ajustado por distribución de calidad: $I_{real} = I_{ideal} \cdot F$ (ver §4.2) |
| `Costo_clp` | Costo de producción total (CLP/ha, ajustado IPC 04/2026) |
| `Margen_real_clp` | $I_{real} - Costo$ — variable objetivo de la optimización combinatoria |
| `Primera_%` | Fraccion de producción de categoría primera calidad (%) |
| `Segunda_%` | Fracción de categoría segunda calidad (%) |
| `Perdida_%` | Fracción de producción descartada por estrés (%) |
| `Produccion_real` | Producción física ajustada = rendimiento × ha × (1 - Perdida_%) |

El reporte `ReporteParticiones.html` organiza, para cada escenario simulado, las siguientes salidas del modelo destinadas al análisis posterior:
- Indicadores clave (KPI cards) con la descomposición del volumen del canal (riego / almacenamiento / pérdida con porcentajes)
- Trayectoria temporal de la humedad volumétrica en la zona radicular
- Calendario de riego en dos paneles: *llegadas del canal* (desglose por destino) y *agua aplicada* (desglose por fuente)

### 4.7 Archivos de entrada — formatos de columnas

A continuación se describe la estructura exacta que deben tener los CSV de entrada del módulo 2. Cada fila de los archivos de múltiples regantes/cultivos representa un elemento independiente.

#### `datosclima.csv` — serie climática diaria

| Columna | Tipo | Descripción |
|---|---|---|
| `Fecha` | `YYYY-MM-DD` | Fecha del registro |
| `[Min] % Humedad Relativa` | float | Humedad relativa mínima diaria (%) |
| `[Prom] m/s Velocidad de Viento` | float | Velocidad media del viento (m/s) |
| `[Prom] mm Precipitación` | float | Precipitación media diaria (mm) |
| `[Prom] mm Evapotranspiración` | float | ET₀ de referencia diaria (mm) |

Fuente: CEAZAMet (estaciones meteorológicas del valle de Elqui).

#### `data_cultivos.csv` — parámetros fenológicos FAO-56

| Columna | Tipo | Descripción |
|---|---|---|
| `nombre` | str | Identificador del cultivo (clave de unión con otros CSV) |
| `L_ini`, `L_des`, `L_med`, `L_fin` | int | Duración de cada fase fenológica (días) |
| `Kc_ini`, `Kc_med`, `Kc_fin` | float | Coeficiente de cultivo $K_c$ por fase |
| `Kcb_ini`, `Kcb_med`, `Kcb_fin` | float | Coeficiente basal $K_{cb}$ por fase |
| `h` | float | Altura máxima del cultivo (m), para calcular $K_{cb,max}$ |
| `p` | float | Fracción de agotamiento sin estrés (FAO-56 Tabla 22) |
| `Ze` | float | Profundidad de la capa evaporante (m) |
| `few` | float | Fracción del suelo expuesto al sol y húmedo |

#### `productividad_cultivos.csv` — parámetros económicos

| Columna | Tipo | Descripción |
|---|---|---|
| `nombre` | str | Identificador del cultivo |
| `enero` … `diciembre` | float | Precio mayorista mensual (CLP/ha, ajustado IPC 04/2026) |
| `costo` | float | Costo de producción total (CLP/ha) |
| `rendimiento` | float | Rendimiento esperado (kg/ha o unidades/ha) |
| `unidad` | str | `"kg"` o `"unidad"` — determina la unidad de `rendimiento` |

#### `regantes.csv` — características prediales

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador único del regante |
| `nombre` | str | Nombre descriptivo |
| `frecuencia_dias` | int | Días entre turnos de riego |
| `hectareas` | float | Superficie total del predio (ha) |
| `fraccion_cultivada` | float | Fracción de la superficie efectivamente cultivada (0–1) |
| `capacidad_estanque_m3` | float | Capacidad máxima del estanque predial (m³) |
| `nivel_estanque_inicial_m3` | float | Nivel inicial del estanque al comenzar la simulación (m³) |

#### `calendario_siembra.csv` — restricciones estacionales

| Columna | Tipo | Descripción |
|---|---|---|
| `nombre` | str | Identificador del cultivo |
| `enero` … `diciembre` | int | `1` = siembra permitida ese mes; `0` = restringida |

---

## 5. Flujo de Datos end-to-end

```mermaid
flowchart TD
 classDef src fill:#f0fdf4,stroke:#15803d,color:#14532d
 classDef cfg fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
 classDef proc fill:#dcfce7,stroke:#16a34a,color:#14532d
 classDef data fill:#fef9c3,stroke:#ca8a04,color:#713f12
 classDef out fill:#fce7f3,stroke:#db2777,color:#831843

 %% Fuentes de datos externas 
 CEAZAMET["CEAZAMet\nestaciones meteorológicas\nhist. valle Elqui"]:::src
 NIEVE["CEAZA Nieve\nnivel de nieve\ncuenca Elqui"]:::src
 DGA["DGA Boletines\nnivel Puclaro\ncaudal río Elqui"]:::src

 %% Preparación de entradas 
 CEAZAMET -->|"serie histórica\nETo + clima"| CLIMA["datosclima.csv\ndatos_clima_365dias.csv"]:::data
 NIEVE -->|"predictores\nhidrológicos"| EST["Estimación desmarque\nPORCENTAJE_DESMARQUE_FINAL"]:::cfg
 DGA -->|"predictores\nhidrológicos"| EST

 %% Módulo 1: Oferta Hídrica 
 EST --> IV["initial_values.py\n± SALTO_DESMARQUE"]:::cfg

 subgraph MOH["Módulo 1 — Oferta Hídrica (Dinámica de Sistemas)"]
 MSA["modelo_simulacion_oferta_hidrica.py\nE escenarios de desmarque\npérdidas aleatorias · paradas"]:::proc
 end

 IV --> MSA
 MSA --> CO[("CalendarioOferta.csv\nDía × Escenario")]:::data

 %% Módulo 2: Simulación de Cultivo 
 PAR["parametros.py"]:::cfg
 INP["data_cultivos.csv\nregantes.csv\ncalendario_siembra.csv\nproductividad_cultivos.csv"]:::cfg

 subgraph MSC["Módulo 2 — Simulación de Cultivo (Eventos Discretos)"]
 SIM["simular_demanda.py\nFAO-56 dual coef. + f(H)=Hᵅ\ndespacho canal / estanque / sub\nC(n+P−1, P) combinaciones"]:::proc
 end

 CO --> SIM
 CLIMA --> SIM
 PAR --> SIM
 INP --> SIM

 SIM --> HTML["ReporteParticiones.html"]:::out
 SIM --> R1["ReporteEscenarios.csv"]:::out
 SIM --> R2["SimulacionDemanda.csv"]:::out
```

---

## 6. Paradigmas de Simulación e Implementación Computacional

El proyecto implementa dos paradigmas de simulación, cada uno seleccionado por su adecuación estructural al fenómeno representado. En cada caso se describe primero el modelo conceptual y luego la herramienta computacional que lo implementa.

### Dinámica de Sistemas — Módulo de Oferta Hídrica

La **Dinámica de Sistemas** (System Dynamics) es el paradigma adecuado para representar fenómenos con comportamiento dinámico continuo, estructura causal de retroalimentación y acumulaciones. En el subsistema hidrológico, la variable de nivel central —el volumen disponible en el predio— evoluciona temporalmente bajo la acción de flujos de entrada (desmarque) y flujos de salida (pérdidas estocásticas y consumo), con perturbaciones exógenas puntuales (recargas). Esta estructura causal de stocks y tasas, propia de la simulación continua, no puede representarse de forma natural mediante eventos discretos.

| | |
|---|---|
| **Paradigma** | Dinámica de Sistemas (System Dynamics) — simulación continua de variables de nivel y flujos |
| **Implementación** | [`pysd`](https://pysd.readthedocs.io) v3.14.3 |
| **Aplicación** | Modela el subsistema hidrológico como un sistema de **variables de nivel** (stocks de agua) y **tasas** (flujos de entrada y salida) con **estructura de retroalimentación**. Las acumulaciones evolucionan bajo incertidumbre hidrológica estocástica, capturando el comportamiento dinámico del agotamiento hídrico a lo largo del horizonte de planificación. |

La implementación en pysd permite codificar el modelo de Dinámica de Sistemas directamente en Python sin requerir un diagrama Vensim/Stella externo. El módulo `modelo_simulacion_oferta_hidrica.py` define explícitamente las **variables de nivel** (stocks), las **tasas** (flujos) y las ecuaciones de evolución temporal del subsistema hidrológico.

### Simulación de Eventos Discretos — Módulo de Simulación de Cultivo

La **Simulación de Eventos Discretos** (Discrete-Event Simulation, DES) es el paradigma adecuado para sistemas cuyo estado cambia únicamente en instantes discretos definidos por la ocurrencia de eventos. El ciclo de vida del cultivo —con sus transiciones fenológicas, eventos de riego y decisiones de asignación de recursos— es inherentemente discreto: entre eventos el sistema permanece en un estado constante. La simulación dirigida por eventos representa este comportamiento con fidelidad sin procesar estados inactivos.

| | |
|---|---|
| **Paradigma** | Simulación de Eventos Discretos (Discrete-Event Simulation) — simulación dirigida por eventos |
| **Implementación** | [`simpy`](https://simpy.readthedocs.io) ≥ 4.0.0 |
| **Aplicación** | Modela el **ciclo de vida del cultivo** de cada parcela como una **entidad** con **procesos** concurrentes que ejecutan **transiciones de estado** fenológicas e hídricas al ocurrir **eventos** programados en el **calendario de eventos**. La ejecución dirigida por eventos avanza el reloj de simulación únicamente ante la ocurrencia de un evento, sin procesar estados intermedios inactivos. |

### Instalación de dependencias

```powershell
# Desde la raíz del proyecto
& ".venv\Scripts\python.exe" -m pip install -r "Oferta Hidrica\requirements.txt"
& ".venv\Scripts\python.exe" -m pip install -r "Simulación Cultivo\requirements.txt"
```

---

## 7. Guía de Ejecución

### Paso 1 — Ejecutar la Oferta Hídrica

```powershell
# Desde la raíz del proyecto
$env:PYTHONIOENCODING='utf-8'
cd "Oferta Hidrica"
echo "si" | & "..\\.venv\Scripts\python.exe" modelo_simulacion_oferta_hidrica.py
```

Parámetros clave a ajustar en `src/initial_values.py`:
- `PORCENTAJE_DESMARQUE_FINAL` — desmarque base del escenario central
- `SALTO_DESMARQUE` — diferencia entre escenarios consecutivos (ej. 0.025)
- `CALENDARIO_PARADAS` — días de inicio de mantenimiento

### Paso 2 — Ejecutar la Simulación de Cultivo

```powershell
cd "..\Simulación Cultivo"
& "..\\.venv\Scripts\python.exe" simular_demanda.py
```

Parámetros clave en `parametros.py`:
- `DIA_INICIO_SIMULACION` — día del año en que arranca la simulación (1 = 1 ene, 213 = 1 ago)
- `REGANTE_ID` — selecciona el regante desde `regantes.csv`
- `PARTICIONES` — número de parcelas en que se divide la superficie
- `ALPHA_SUELO` — factor de retención por textura (1.5 franco, 2.0 franco-arcilloso)
- `STOCK_SUBTERRANEO_INICIAL_M3` — volumen inicial del acuífero disponible
- `DIAS_SIN_RIEGO_PARA_SUBTERRANEA` — umbral de días secos para habilitar el pozo

### Paso 3 — Ver resultados

Abrir `Simulación Cultivo/outputs/ReporteParticiones.html` en cualquier navegador.

---

## 8. Archivos de Entrada y Salida

### Entradas del Módulo de Oferta Hídrica

| Archivo | Descripción |
|---|---|
| `src/initial_values.py` | Todos los parámetros del canal |
| `data/inputs/CalendarioParadas.csv` | Generado automáticamente desde `CALENDARIO_PARADAS` |

### Entradas del Módulo de Cultivo

| Archivo | Columnas clave | Descripción |
|---|---|---|
| `inputs/data_cultivos.csv` | `nombre, L_ini/des/med/fin, Kcb_ini/med/fin, h, p, Ze, few` | Coeficientes FAO-56 por cultivo |
| `inputs/datosclima.csv` | `Dia, ETo_mm, PP_mm, Tmax, Tmin` | ETo y precipitación diaria (365 días) |
| `inputs/regantes.csv` | `id, hectareas, fraccion_cultivada, frecuencia_turno, capacidad_estanque_m3` | Datos del regante |
| `inputs/calendario_siembra.csv` | `nombre, enero, …, diciembre` | Disponibilidad mensual por cultivo (binario) |
| `inputs/productividad_cultivos.csv` | `nombre, precio_clp_kg, rendimiento_kg_ha, costo_clp_ha` | Parámetros económicos |
| `../Oferta Hidrica/data/outputs/CalendarioOferta.csv` | Ver §3.5 | Oferta superficial diaria por escenario |

### Salidas

| Archivo | Descripción |
|---|---|
| `Oferta Hidrica/data/outputs/CalendarioOferta.csv` | Oferta diaria por escenario (365 × E filas) |
| `Simulación Cultivo/outputs/ReporteParticiones.html` | Reporte interactivo con KPIs y gráficos |
| `Simulación Cultivo/outputs/ReporteParticiones.csv` | KPIs por escenario × partición |
| `Simulación Cultivo/outputs/SimulacionParticiones.csv` | Balance hídrico diario detallado |

---

## 9. Referencias Bibliográficas

- **Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998).** *Crop evapotranspiration — Guidelines for computing crop water requirements.* FAO Irrigation and Drainage Paper 56. Food and Agriculture Organization of the United Nations, Rome.

- **Brooks, R.H., Corey, A.T. (1964).** *Hydraulic properties of porous media.* Hydrology Papers No. 3. Colorado State University, Fort Collins.

- **Van Genuchten, M.Th. (1980).** A closed-form equation for predicting the hydraulic conductivity of unsaturated soils. *Soil Science Society of America Journal*, 44(5), 892–898.

---

## 10. Fuentes de Datos

- **ODEPA — Series de tiempo, precios hortalizas.** Sistema de consulta de precios mayoristas por subsector. Oficina de Estudios y Políticas Agrarias, Ministerio de Agricultura, Chile. Disponible en: https://aplicativos.odepa.gob.cl/series-precios/series-tiempo. Consulta: mayo 2026. Configuración utilizada: precios mayoristas, hortalizas y tubérculos, precios reales (IPC base 04/2026), serie anual 2014–2025.

- **ODEPA — Fichas de costo de hortalizas.** Fichas técnicas con rendimientos y costos de producción por cultivo. Oficina de Estudios y Políticas Agrarias, Ministerio de Agricultura, Chile. Disponible en: https://www.odepa.gob.cl/fichas-de-costo-de-hortalizas. Consulta: mayo 2026. Valores actualizados a precios reales mediante el mismo índice IPC utilizado en las series de tiempo.

- **CEAZA — Plataforma de monitoreo de nieves.** Cobertura y equivalente en agua de la nieve en la cuenca del río Elqui. Centro de Estudios Avanzados en Zonas Áridas (CEAZA), La Serena. Disponible en: https://nieve.ceaza.cl. Consulta: mayo 2026. Fuente principal para el predictor *nivel de nieve* del modelo de regresión de desmarque.

- **CEAZAMet — Estaciones meteorológicas.** Series históricas de variables climáticas de la red de estaciones del valle del Elqui. Centro de Estudios Avanzados en Zonas Áridas (CEAZA). Disponible en: https://www.ceazamet.cl. Consulta: mayo 2026. Fuente utilizada para construir los archivos de datos climáticos del modelo de demanda (`datosclima.csv`, `datos_clima_365dias.csv`), y fuente de variables climáticas complementarias para el modelo predictivo de desmarque.

- **DGA — Boletines hidrométricos.** Series históricas de nivel del embalse Puclaro y caudal del río Elqui. Dirección General de Aguas, Ministerio de Obras Públicas, Chile. Disponible en: https://dga.mop.gob.cl/servicios-de-informacion/boletines. Consulta: mayo 2026. Fuentes de los predictores *nivel embalse Puclaro* y *caudal río Elqui* para el modelo de regresión de desmarque.
