# Variables - Update these for your project
ADDON_NAME = anki_greek
SRC_DIR = src
BUILD_DIR = build
# macOS path
ANKI_ADDON_DIR = ~/Library/Application\ Support/Anki2/addons21

# Use this for Linux:
# ANKI_ADDON_DIR = ~/.local/share/Anki2/addons21
# Use this for Windows (Git Bash/WSL):
# ANKI_ADDON_DIR = /c/Users/$(USER)/AppData/Roaming/Anki2/addons21

.PHONY: all clean install zip

all: install

# Create the .ankiaddon package (which is just a ZIP file)
zip:
	mkdir -p $(BUILD_DIR)
	cd $(SRC_DIR) && zip -r ../$(BUILD_DIR)/$(ADDON_NAME).ankiaddon .

setup:
	python -m pip install -r requirements.txt

# Install directly to Anki's addon folder for development
install:
	rm -rf $(BUILD_DIR) && mkdir -p $(BUILD_DIR)
	mkdir -p $(ANKI_ADDON_DIR)/$(ADDON_NAME)
	cp -r $(SRC_DIR)/* $(BUILD_DIR)
	cp -rv $(BUILD_DIR)/* $(ANKI_ADDON_DIR)/$(ADDON_NAME)/
	@echo "Done! Restart Anki to see changes."

# Wipe the build folder and the installed addon
clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(ANKI_ADDON_DIR)/$(ADDON_NAME)