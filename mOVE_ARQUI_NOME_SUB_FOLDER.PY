import os
import shutil

def move_files_to_subfolders(base_folder):
    # Define as subpastas
    subfolders = ['flage', 'linha', 'radome', 'slot', 'painel', 'parabola','tampa', 'filtro', 'refletor', 'hib','log','inner','omt','omni', 'feeder', 'tef', 'transição','tub', 'dipolo', 'outros']
    
    # Cria as subpastas se não existirem
    for subfolder in subfolders:
        os.makedirs(os.path.join(base_folder, subfolder), exist_ok=True)
    
    # Lista todos os arquivos na pasta base
    for file_name in os.listdir(base_folder):
        file_path = os.path.join(base_folder, file_name)
        
        # Verifica se é um arquivo
        if os.path.isfile(file_path):
            # Move o arquivo para a subpasta correspondente ou para 'outros'
            moved = False
            for subfolder in subfolders[:-1]:  # Exclui 'outros' da verificação
                if subfolder in file_name.lower():
                    shutil.move(file_path, os.path.join(base_folder, subfolder, file_name))
                    moved = True
                    break
            if not moved:
                shutil.move(file_path, os.path.join(base_folder, 'outros', file_name))

# Caminho da pasta de entrada
base_folder = r"C:\Users\geral\OneDrive\Área de Trabalho\GOOGLEENGINE\ATXCOVER\static\SOLID_PRT_ASM\PNGS"

# Move todos os arquivos para as subpastas apropriadas
move_files_to_subfolders(base_folder)
