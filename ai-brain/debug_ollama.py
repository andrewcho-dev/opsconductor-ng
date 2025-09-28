#!/usr/bin/env python3
import ollama

client = ollama.Client(host="http://ollama:11434")
response = client.list()
print("Type:", type(response))
print("Response:", response)
if hasattr(response, 'models'):
    print("Models attribute:", response.models)
    if response.models:
        print("First model:", response.models[0])
        print("First model type:", type(response.models[0]))
        if hasattr(response.models[0], 'model'):
            print("Model field:", response.models[0].model)
        if hasattr(response.models[0], 'name'):
            print("Name field:", response.models[0].name)