Running a local LLM for social engineering.
For the following I chose ollama.
<br>
<img src="https://ollama.com/public/ollama.png">


# Windows Setup
Windows 11 Laptop with GPU. If you already have a Linux distro at hand, feel free to skip steps.

Using `wsl`, enter in powershell:
```
wsl
```

For lightweight system choose Debian. Any other Linux distro will do too.:
```
wsl --install -d Debian
```

After installing enter the username of your choice as well as your password.

Next, update and upgrade the system:
```
sudo apt update && sudo apt upgrade -y && sudo apt install curl python3-flask python3-requests git -y
```

# Pulling Ollama
Downloading ollama.
```
curl -fsSL https://ollama.com/install.sh | sh
```
```
>>> Installing ollama to /usr/local
>>> Downloading Linux amd64 bundle
######################################################################## 100.0%
>>> Creating ollama user...
>>> Adding ollama user to render group...
>>> Adding ollama user to video group...
>>> Adding current user to ollama group...
>>> Creating ollama systemd service...
>>> Enabling and starting ollama service...
Created symlink /etc/systemd/system/default.target.wants/ollama.service → /etc/systemd/system/ollama.service.
>>> Nvidia GPU detected.
>>> The Ollama API is now available at 127.0.0.1:11434.
>>> Install complete. Run "ollama" from the command line.
```
# Pulling/Running Mistral
In order to make this most accessible and given the use-case, the Mistral model was chosen. 
```
ollama run mistral
```
This downloads a model size of 4.4 GB, which is okay in size.

After finishing the pulling of the model we can start using the model. Test it by asking some questions in the terminal you just ran it in!

# (Optional) - Integrating GPU
If your laptop has a Geforce GPU, feel free to install the cuda drivers as well:
https://www.nvidia.com/en-us/drivers/
Fill out the specs and download the `Game Ready Driver`. The cuda driver is not directly mentioned but included in the standard bundle of gaming drivers.
After installing the app, install the newest version.
Now to confirm if the GPU can correctly be used paste the following in your `wsl` terminal.
```
nvidia-smi
```
# Testing Performance
If you want to test the performance of your model use the following:
```
time echo "Give me a short explanation about quantum entanglement." | ollama run mistral
```

# API
The API endpoint can be talked to over port 11434 of your local network.
```
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Gib mir eine kurze Erklärung zur Quantenverschränkung.",
  "stream": false
}'
```
If you want to try different things when talking to the AI, here is the corresponding documentation:
https://github.com/ollama/ollama/blob/main/docs/api.md

# GUI
We will do a custom app for running this using Flask. This is a python web framework.
Install the requirements for the app. Which we already installed in a prior step.
```
sudo apt install python3-flask python3-requests
```
For a prettier usage I would recommend conda, but this will do for now.

Next retrieve the directory phishing-ai, move inside the directory and open a terminal for the current folder. Next enter in the retrieved directory:
```
python3 app.py
```
This launches the web-ui, which can be accessed at:
http://127.0.0.1:5000/
