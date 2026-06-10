PYTHON = python
PIP = pip
MAIN = main.py
APP_NAME = cheat


all: run

run:
	$(PYTHON) $(MAIN)

install:
	$(PIP) install Flask flask-cors pywebview DrissionPage stockfish colorama pyinstaller

build:
	pyinstaller --noconfirm --onefile --windowed --name "$(APP_NAME)" \
		--icon="cheat.ico" \
		--add-data "web;web" \
		--add-binary "stockfish-windows-x86-64-avx2.exe;." \
		$(MAIN)

clean:
	rm -rf __pycache__
	rm -rf build
	rm -rf dist
	rm -rf *.spec


.PHONY: all run install clean build