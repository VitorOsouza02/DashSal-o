# -*- coding: utf-8 -*-
import pandas as pd
import random

# --- Lista dos códigos dos clientes ---
clientes = [
    147271, 5081537, 5751900, 3583196, 5592970, 12694674, 4362657, 9919854,
    3257065, 6446814, 4924231, 4768978, 3059090, 3340863, 11409938, 6911655,
    3663535, 6035559, 7607304, 16438143, 9675128, 3586914, 11518385, 2853936,
    11512053, 7083259, 16825532, 4486164, 11023365, 17660499, 16375109, 5978725,
    403809, 16795583, 17736206, 18307831, 12909387, 9572629, 4657924, 11134876,
    9963923, 18268732, 6912240, 17163476, 9944905, 11085847, 14555075, 16488839,
    16512520, 16982459, 17855455, 18609852, 16724542
]

# --- Criar DataFrame ---
df = pd.DataFrame({"CodigoCliente": clientes})

# --- Divisão aleatória entre AL e MF ---
df["Assessor"] = [random.choice(["AL", "MF"]) for _ in range(len(df))]

# --- Contagem de cada grupo ---
contagem = df["Assessor"].value_counts()

# --- Criar resumo ---
resumo = pd.DataFrame({
    "Assessor": contagem.index,
    "Quantidade de Clientes": contagem.values
})

# --- Salvar em planilha Excel ---
nome_arquivo = "divisao_clientes_aleatoria_AL_MF.xlsx"
with pd.ExcelWriter(nome_arquivo, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Clientes_Divididos")
    resumo.to_excel(writer, index=False, sheet_name="Resumo")

# --- Mostrar resumo no terminal ---
print("✅ Planilha gerada com sucesso!")
print(df.head())
print("\nResumo:")
print(resumo)
print(f"\nArquivo salvo como: {nome_arquivo}")
