# Install Python and pyenv on Ubuntu 24.04 Server

To install Python and a version manager on Ubuntu 24.04 Server, set up `pyenv` to manage Python versions, and configure the `python` and `pip` commands to default to the latest Python 3 version, follow these steps. This assumes a clean Ubuntu 24.04 Server with no prior Python modifications.

## Commands to Install and Configure

```bash
# Update the system and install prerequisites
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
libffi-dev liblzma-dev git

# Install pyenv
curl https://pyenv.run | bash

# Configure shell environment for pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
source ~/.bashrc

# Install the latest Python version using pyenv (e.g., 3.12.7; adjust as needed)
pyenv install 3.12.7

# Set the global Python version
pyenv global 3.12.7

# Ensure pip is installed and upgraded
python -m ensurepip --upgrade
python -m pip install --upgrade pip

# Create aliases for python and pip (optional but recommended)
echo 'alias python="python3"' >> ~/.bashrc
echo 'alias pip="pip3"' >> ~/.bashrc
source ~/.bashrc

# Verify the setup
python --version
pip --version
```
