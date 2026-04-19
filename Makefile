# Variables - Update these for your project
ADDON_NAME = anki_greek
SRC_DIR = src/addon
LIB_DIR = src/libs
BUILD_DIR = build
# macOS path
ANKI_ADDON_DIR = ~/Library/Application\ Support/Anki2/addons21

MODEL_DIR = ~/models
# MODEL_NAME = Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
# MODEL_REGEX = "qwen2.5-coder-7b-instruct-q4_k_m*.gguf"

MODEL_NAME = unsloth/Qwen3.5-4B-GGUF
MODEL_REGEX = "Qwen3.5-4B-Q4_K_M*.gguf"
MODEL_FILE = Qwen3.5-4B-Q4_K_M.gguf

# Use this for Linux:
# ANKI_ADDON_DIR = ~/.local/share/Anki2/addons21
# Use this for Windows (Git Bash/WSL):
# ANKI_ADDON_DIR = /c/Users/$(USER)/AppData/Roaming/Anki2/addons21

.PHONY: all clean install zip

all: install

build:
	rm -rf $(BUILD_DIR) && mkdir -p $(BUILD_DIR)/libs
	mkdir -p $(ANKI_ADDON_DIR)/$(ADDON_NAME)
	cp -r $(SRC_DIR)/* $(BUILD_DIR)
	cp -r $(LIB_DIR)/* $(BUILD_DIR)/libs
	find $(BUILD_DIR) -name "__pycache__" -type d -exec rm -r {} +

# Create the .ankiaddon package (which is just a ZIP file)
zip: build
	cd $(BUILD_DIR) && zip -r ../$(ADDON_NAME).ankiaddon .

setup:
	python -m pip install -r requirements.txt

# Install directly to Anki's addon folder for development
install: build 
	cp -rv $(BUILD_DIR)/* $(ANKI_ADDON_DIR)/$(ADDON_NAME)/
	@echo "Done! Restart Anki to see changes."

download-agent:
	HF_HUB_ENABLE_HF_TRANSFER=1 HF_XET_HIGH_PERFORMANCE=1 hf download $(MODEL_NAME) --include "$(MODEL_REGEX)" --local-dir $(MODEL_DIR)

run-agent:
	llama-server -m ~/models/$(MODEL_FILE) --cache-reuse 256 --port 8080 --ctx-size 8192 --context-shift

# Wipe the build folder and the installed addon
clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(ANKI_ADDON_DIR)/$(ADDON_NAME)