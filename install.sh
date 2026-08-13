curl -LsSf https://astral.sh/uv/install.sh | sh
# Reboot the shell
mkdir h10box && cd h10box
uv init
uv python pin 3.14
uv add bleakheart
