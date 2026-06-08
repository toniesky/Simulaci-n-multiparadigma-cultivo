"""Re-exporta todas las funciones de los submódulos (compatibilidad)."""
from .fao56 import calcular_kcb, calcular_kcmax  # noqa: F401
from .simulacion import _dias_hasta_proximo_turno, simular_cultivo, simular_multi_particion  # noqa: F401
from .carga_datos import cargar_oferta_superficial_m3, listar_escenarios, cargar_productividad, cargar_regante  # noqa: F401
from .calidad import _mes_cosecha, _calcular_calidad  # noqa: F401
from .kpis import _kpis_economicos, _simular_combinacion, _kpis_de_df_sim  # noqa: F401
from .graficos import _graficos_b64, _grafico_canal_b64, _grafico_agua_cultivos_b64, _grafico_estanque_b64, _grafico_sub_b64  # noqa: F401
from .reportes import _fmt_clp, _fmt_num, _generar_html_particiones, _generar_html  # noqa: F401
