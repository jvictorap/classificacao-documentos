from pathlib import Path

for pasta in Path(r'W:\CLIENTES\PRODUTOR RURAL PEQUENO').iterdir():
    if pasta.is_dir():
        print(pasta.name)