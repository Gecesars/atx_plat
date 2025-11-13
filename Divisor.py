import tkinter as tk
from tkinter import ttk
import math

# Função para calcular o divisor coaxial de RF
def calcular_divisor():
    try:
        frequencia_mhz = float(entry_frequencia.get())
        diametro_externo = float(entry_diametro_externo.get())
        espessura_parede = float(entry_espessura_parede.get())
        numero_saidas = int(entry_numero_saidas.get())
        epsilon_r = float(entry_epsilon_r.get())  # Novo campo para constante dielétrica relativa

        # Calcula o comprimento do transformador e o diâmetro interno (exemplo simplificado)
        velocidade_luz = 299792458  # em metros por segundo
        comprimento_onda = velocidade_luz / (frequencia_mhz * 1e6) / math.sqrt(epsilon_r)  # Considerando a constante dielétrica
        comprimento_transformador = ((comprimento_onda * 0.98) / 4) * 1000  # comprimento do transformador em mm
        dia_interno_do_tubo = diametro_externo - 2 * espessura_parede
        z_end = 50 / numero_saidas
        z_tr = math.sqrt(50 * z_end)

        print(z_tr)
        relacao = pow(10, z_tr / 138)
        diametro_interno = dia_interno_do_tubo / relacao

        # Atualiza os resultados na interface
        resultado_comprimento['text'] = f"Comprimento do Transformador: {comprimento_transformador:.2f} mm"
        resultado_diametro['text'] = f"Diametro Interno do Transformador: {diametro_interno:.2f} mm"
    except Exception as e:
        resultado_comprimento['text'] = "Erro nos cálculos."
        resultado_diametro['text'] = str(e)

# Configuração da janela principal
root = tk.Tk()
root.title("Cálculo de Divisores de RF")

# Labels e entries para as entradas de dados
label_frequencia = ttk.Label(root, text="Frequência em MHz:")
label_frequencia.grid(row=0, column=0, padx=10, pady=10)
entry_frequencia = ttk.Entry(root)
entry_frequencia.grid(row=0, column=1, padx=10, pady=10)

label_diametro_externo = ttk.Label(root, text="Diâmetro do Tubo Externo (mm):")
label_diametro_externo.grid(row=1, column=0, padx=10, pady=10)
entry_diametro_externo = ttk.Entry(root)
entry_diametro_externo.grid(row=1, column=1, padx=10, pady=10)

label_espessura_parede = ttk.Label(root, text="Espessura da Parede (mm):")
label_espessura_parede.grid(row=2, column=0, padx=10, pady=10)
entry_espessura_parede = ttk.Entry(root)
entry_espessura_parede.grid(row=2, column=1, padx=10, pady=10)

label_numero_saidas = ttk.Label(root, text="Número de Saídas:")
label_numero_saidas.grid(row=3, column=0, padx=10, pady=10)
entry_numero_saidas = ttk.Entry(root)
entry_numero_saidas.grid(row=3, column=1, padx=10, pady=10)

# Novo label e entry para a constante dielétrica relativa
label_epsilon_r = ttk.Label(root, text="Constante Dielétrica Relativa (εr):")
label_epsilon_r.grid(row=4, column=0, padx=10, pady=10)
entry_epsilon_r = ttk.Entry(root)
entry_epsilon_r.grid(row=4, column=1, padx=10, pady=10)

# Botão para calcular
botao_calcular = ttk.Button(root, text="Calcular", command=calcular_divisor)
botao_calcular.grid(row=5, column=0, columnspan=2, pady=10)

# Labels para mostrar os resultados
resultado_comprimento = ttk.Label(root, text="Comprimento do Transformador: --")
resultado_comprimento.grid(row=6, column=0, columnspan=2)

resultado_diametro = ttk.Label(root, text="Diametro Interno do Transformador: --")
resultado_diametro.grid(row=7, column=0, columnspan=2)

root.mainloop()
