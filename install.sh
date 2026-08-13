curl -LsSf https://astral.sh/uv/install.sh | sh
# Reboot the shell
mkdir h10box && cd h10box
uv init
uv python pin 3.14
uv add bleakheart
# Testing the readout of the HR Belt
uv run python smoketest1.py
uv run python smoketest2.py
