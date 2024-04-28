@echo off
REM This batch file installs all the dependencies required for the project.

REM Install each dependency using pip
pip install toml
pip install tqdm
pip install pillow
pip install unidecode

@echo Dependencies have been successfully installed.
pause
