import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

df = pd.read_csv(r'C:\Users\anton\Desktop\Capstone\Modelo\Simulación Cultivo\inputs\productividad_cultivos.csv')

meses = ['enero','febrero','marzo','abril','mayo','junio',
         'julio','agosto','septiembre','octubre','noviembre','diciembre']
labels = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

colores = {
    'lechuga_escarola':  '#1f3c88',
    'lechuga_conconina': '#e07b39',
    'repollo':           '#2d6a4f',
    'apio':              '#52b788',
    'acelga':            '#d62828',
    'brocoli':           '#4ea8de',
    'tomate':            '#9b2226',
    'choclo':            '#7b2d8b',
}

nombres_display = {
    'lechuga_escarola':  'Lechuga Escarola ($/unidad)',
    'lechuga_conconina': 'Lechuga Conconina ($/unidad)',
    'repollo':           'Repollo Crespo ($/unidad)',
    'apio':              'Apio ($/unidad)',
    'acelga':            'Acelga ($/unidad)',
    'brocoli':           'Brócoli Crespo ($/unidad)',
    'tomate':            'Tomate ($/kg)',
    'choclo':            'Choclo Dulce ($/unidad)',
}

fig, ax = plt.subplots(figsize=(16, 6))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

for _, row in df.iterrows():
    nombre = row['nombre']
    rendimiento = row['rendimiento']
    precios = [row[m] / rendimiento for m in meses]
    ax.plot(range(12), precios,
            color=colores.get(nombre, 'gray'),
            linewidth=2.2,
            label=nombres_display.get(nombre, nombre),
            marker='o', markersize=5)

ax.set_title(
    'Precio Promedio Mensual Hortalizas — Promedio 2014–2025 (IPC base 04/2026)',
    fontsize=13, pad=14, fontweight='bold', color='#222'
)
ax.set_xticks(range(12))
ax.set_xticklabels(labels, fontsize=10)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f'${x:,.0f}')
)
ax.set_ylabel('CLP / unidad comercial', fontsize=10, color='#444')
ax.grid(axis='y', linestyle='--', linewidth=0.6, alpha=0.6, color='#ccc')
ax.grid(axis='x', linestyle=':', linewidth=0.4, alpha=0.4, color='#ddd')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#ccc')
ax.spines['bottom'].set_color('#ccc')
ax.tick_params(colors='#444')

ax.legend(
    loc='upper center', bbox_to_anchor=(0.5, -0.13),
    ncol=4, fontsize=9, frameon=False
)

plt.tight_layout()
outpath = r'C:\Users\anton\Desktop\Capstone\Modelo\docs\precios_hortalizas.png'
plt.savefig(outpath, dpi=150, bbox_inches='tight', facecolor='white')
print('Guardado:', outpath)
