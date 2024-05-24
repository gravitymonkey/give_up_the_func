<IMG src="./assets/recraft_ai_flying-saucer-70s-album-cover.png" width=400 alt="square image resembling a 70s album cover by Funkadelic, made by recraft.ai">

## Give Up The Func

#### A library that manages tools (functions) for Local LLMs

### Problem Statement

In an LLM API call, you can describe functions and have the model intelligently choose to output a JSON object containing arguments to call one or many functions. This JSON object can then be used to execute 
those functions in whatever manner you choose.

Typically, say with OpenAI, you tackle this by adding tools to your chat request, and then monitor the response for
a JSON response that includes the function name and parameters.  You can then code it up to trigger the function and return the response, or you can use an existing framework like AutoGen that handles all of that for you.

#### Therein lies the rub

What happens if you'd like to run this on a local LLM, say, through Ollama (which manages to be both easy and amazing) in order to protect your privacy and reduce cost?  Well, you'll find that this really doesn't work at all (as of 5/24).

 -- even with Mistral's addition of Function calling 

So in trying to solve it - found this (shoutout @jamb)

https://github.com/namuan/llm-playground/blob/main/local-llm-tools-simple.py

### How to Install

### How to Use