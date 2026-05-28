# Anexo metodológico — Retención no lineal de humedad del suelo

## 1. Contexto

El modelo implementado en `simular_demanda.py` sigue el procedimiento FAO-56
de doble coeficiente (Allen et al., 1998) para calcular la
evapotranspiración real del cultivo:

$$
\text{ET}_{real}(t) = K_s(t)\cdot K_{cb}(t)\cdot \text{ET}_0(t) + E_s(t)
$$

donde:
- $K_{cb}$ — coeficiente basal del cultivo (transpiración).
- $E_s$ — evaporación del suelo derivada del balance superficial
  (capa evaporante $Z_e$, déficit $D_e$, parámetros AET y AFE).
- $K_s$ — coeficiente de estrés hídrico, definido por FAO-56 como una
  reducción **lineal** a tramos:

$$
K_s(t)=\begin{cases}
1 & D_r(t-1)\le \text{AFA} \\[4pt]
\dfrac{\text{ADT}-D_r(t-1)}{\text{ADT}-\text{AFA}} & D_r(t-1)>\text{AFA}
\end{cases}
$$

Con $\text{AFA}=p\cdot\text{ADT}$. Es decir, mientras el déficit radicular
no supere $\text{AFA}$ no hay reducción, y a partir de ahí cae linealmente
hasta cero en $D_r=\text{ADT}$.

## 2. Limitación detectada

El enfoque lineal de $K_s$ asume implícitamente que la disponibilidad de
agua para la planta es **directamente proporcional** al contenido hídrico
remanente entre AFA y ADT. La física de suelos muestra que esta relación
es **fuertemente no lineal** y depende de la textura: en suelos finos
(arcillosos) buena parte del agua queda retenida a tensiones matriciales
muy altas y no es realmente extractable, mientras que en suelos gruesos
(arenosos) la disponibilidad cae más bruscamente al aproximarse al PMP.
Modelos de retención como Van Genuchten (1980) o Brooks–Corey describen
esta dependencia mediante curvas $\theta(\psi)$ no lineales.

En el modelo actual esto se traducía en descensos de humedad poco
realistas: la planta seguía transpirando casi a tasa máxima incluso
cuando el suelo se acercaba al PMP, generando caídas abruptas de $H(t)$.

## 3. Propuesta: factor de retención no lineal $f(H)$

Se introduce un factor multiplicativo de tipo potencia aplicado **solo
sobre la transpiración**:

$$
f(H) = H(t)^{\alpha}, \qquad H(t) = 1 - \dfrac{D_r(t-1)}{\text{ADT}} \in [0,1]
$$

La nueva expresión de la evapotranspiración real queda:

$$
\boxed{\text{ET}_{real}(t) = K_s(t)\cdot K_{cb}(t)\cdot \text{ET}_0(t)\cdot f(H(t)) + E_s(t)}
$$

Notar que $E_s$ **no se modifica**, ya que su comportamiento ante el
secado superficial ya está representado por $K_r$ y los reservorios
AET/AFE de la capa evaporante.

### 3.1 Interpretación del parámetro $\alpha$

- $\alpha = 1$ → reducción lineal (recupera el comportamiento original
  multiplicado por $H$, sin el quiebre en AFA).
- $\alpha > 1$ → la transpiración cae más rápido al secarse el suelo,
  efecto típico de **suelos finos** que retienen agua a tensiones altas.
- $\alpha < 1$ → la transpiración se mantiene alta hasta cerca del PMP
  (no recomendado en condiciones reales).

Valores orientativos sugeridos por textura:

| Textura          | Rango sugerido $\alpha$ |
|------------------|--------------------------|
| Arenoso          | 1.2 – 1.5               |
| Franco           | 1.5 – 2.0               |
| Franco-arcilloso | 2.0 – 3.0               |
| Arcilloso        | 3.0 – 5.0               |

### 3.2 Justificación bibliográfica resumida

- Allen et al. (1998), FAO Irrigation and Drainage Paper 56 — define
  $K_s$ lineal como simplificación operativa.
- Van Genuchten (1980) — curva $\theta(\psi)$ no lineal, base teórica
  para modelar retención en función de la textura.
- Brooks & Corey (1964) — relación potencial entre tensión y contenido
  hídrico, conceptualmente análoga a la formulación $H^\alpha$.

## 4. Trazabilidad en el código

| Lugar                                                | Cambio                                                                 |
|------------------------------------------------------|------------------------------------------------------------------------|
| `parametros.py`                                      | Nuevo parámetro `ALPHA_SUELO` (default 2.0, suelo franco).             |
| `simular_demanda.py` → `simular_cultivo()`, paso 5b  | Cálculo de `H_norm = 1 - Dr/ADT` y `f_H = H_norm**ALPHA_SUELO`.        |
| `simular_demanda.py` → paso 6                        | `Ep = Ks * Kcb * ETo * f_H` (antes: `Ks * Kcb * ETo`).                 |
| `simular_demanda.py` → paso 7                        | `Dr` se actualiza con la nueva `Etc = Ep + Es` (cadena consistente).   |

El resto del balance (De, AET/AFE, $K_e$, $K_r$, gestión de estanque,
subterránea y turno del regante) **no se modifica**.

## 5. Implicancias y advertencias

1. **Reducción más realista de la transpiración**: la curva $H(t)$ se
   suaviza al aproximarse al PMP, evitando caídas abruptas.
2. **Demanda real menor en condiciones de estrés**: la columna `Etc_m3_*`
   ahora reporta una transpiración reducida; el déficit `Deficit_m3`
   también disminuye porque la planta "demanda" menos cuando ya está
   estresada (efecto fisiológico esperable).
3. **El parámetro $\alpha$ es calibrable**: idealmente debería ajustarse
   con datos de humedad observada y/o curvas $\theta(\psi)$ del sitio.
4. **Limitación**: $f(H)=H^\alpha$ es una simplificación operativa. No
   sustituye un modelo físico completo (Van Genuchten, Richards). Es
   una aproximación práctica que captura cualitativamente el efecto de
   la textura sin requerir parámetros adicionales difíciles de medir
   ($\theta_r$, $\theta_s$, $\alpha_{vG}$, $n$).
5. **Consistencia con FAO-56**: el factor $f(H)$ **complementa** al
   coeficiente $K_s$, no lo reemplaza. Ambos se aplican en cascada:
   $K_s$ aporta el quiebre clásico al pasar AFA, y $f(H)$ añade la
   curvatura no lineal asociada a la textura.

## 6. Calibración futura

- Comparar $H(t)$ simulado contra mediciones de humedad volumétrica
  (sondas FDR/TDR) en distintos suelos del área de estudio.
- Ajustar $\alpha$ por minimización del error en períodos de secado
  prolongado (donde el efecto no lineal es más visible).
- Eventualmente, sustituir $f(H)$ por una formulación Van Genuchten
  cuando se disponga de la caracterización hidráulica completa.
