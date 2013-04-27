from cx_Freeze import setup,Executable
import sys

includefiles = []
includes = ["re"]
excludes = []
packages = []

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name = "Loo Queue",
    version = '1.0',
    description = "",
    options = {'build_exe': {'excludes':excludes,'packages':packages,'include_files':includefiles}}, 
    executables = [Executable('toiletsim.py')]
)
