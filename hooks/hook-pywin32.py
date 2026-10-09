from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Recolectar datos y sub-módulos para pywin32
datas = collect_data_files('pywin32')
hiddenimports = collect_submodules('pywin32')