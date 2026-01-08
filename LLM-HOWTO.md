# LLM HOWTO

## Local Ollama setup on Ubuntu with docker

### Prerequisites
Install docker on your system.

You can now choose between CPU and GPU version of Ollama. We recommend using the GPU version if you have a compatible NVIDIA GPU.


### GPU Docker Ollama

Make sure you have the NVIDIA Container Toolkit installed.

```bash
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
```
Then restart the docker service:

```bash
sudo systemctl restart docker
```

Now you can run the Ollama docker container with GPU support:

```bash
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama-gpu ollama/ollama
```

### CPU Docker Ollama

If you want to use the CPU version of Ollama, you can run the following command:

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama-cpu ollama/ollama
```

### Download the required models

The project uses two models: `granite-embedding:278m` for embeddings and `gpt-oss:120b` for the main LLM tasks. You need to download these models into your local Ollama instance.

```bash
docker exec -it ollama-gpu ollama pull granite-embedding:278m
docker exec -it ollama-gpu ollama pull gpt-oss:120b
```

If you want to use the CPU version of Ollama, replace `ollama-gpu` with `ollama-cpu` in the commands above.

### Verify the models are installed
```bash
docker exec -it ollama-gpu ollama list
```
This should show you the list of installed models, including `granite-embedding:278m` and `gpt-oss:120b`.


## Connect to Ollama from the application

In the application's configuration file (e.g., `config.yaml`), set the LLM backend to Ollama and specify the host and port where the Ollama instance is running.
Now make sure the ollama instance is running. Run the following command to start the docker container if it's not already running:

```bash
docker start ollama-gpu
```