import py_compile
import os

# Diretório atual
current_dir = os.getcwd()

# Lista todos os arquivos .py no diretório atual
for file in os.listdir(current_dir):
    if file.endswith(".py") and file != "generate_pycache.py":
        print(f"Compilando {file}...")
        py_compile.compile(file, cfile=f"__pycache__/{file}c")

print("Compilação concluída! Os arquivos estão no diretório __pycache__.")
