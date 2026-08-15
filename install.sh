curl -LsSf https://astral.sh/uv/install.sh | sh
# Reboot the shell
mkdir h10box && cd h10box
uv init
uv python pin 3.14
uv add bleakheart
# add the HR belt to the trusted devices via bluetoothctl
bluetoothctl
power on
agent on
default-agent
scan on
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
scan off
exit
# This exits bluetoothctl

# Testing the readout of the HR Belt
uv run python smoketest1.py
uv run python smoketest2.py

# Set up the database location
sudo mkdir -p /var/lib/h10box
sudo chown $USER:$USER /var/lib/h10box

# run the recorder
uv run python smoketest2.py

# install sqlite bash command and check database content
sudo apt install sqlite3
sqlite3 /var/lib/h10box/sessions.db "SELECT session_id, COUNT(*), SUM(n) FROM ecg_frames GROUP BY session_id;"
