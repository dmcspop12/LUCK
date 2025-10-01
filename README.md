# OpenBachelorM

OpenBachelor Mod. For PvZ Online.

This project is a mod builder. If you are looking for a game server/launcher, please look at OpenBachelor Server/Client.

Discord: [https://discord.gg/W4yPMpBv8F](https://discord.gg/W4yPMpBv8F)

## How-To

### 1. Setup

1. Install Python 3.12 and add `python.exe` to path.

2. Run `setup.cmd`.

### 2. Build Mod

1. For chronosphere mod, run `build-chronosphere.cmd`. For excel editing mod, follow the writing style of `src/mods/sample_mod/main.py` and create your own mod. The generated mod will be placed inside `mod/xxx/`.

### 3. Configure Server

1. Use a game server that can load the mod, preferably OpenBachelor Server. Copy the files inside OBM's `mod/xxx/` folder to OBS's `mod/` folder. Enable `"mod"` in OBS's config.
