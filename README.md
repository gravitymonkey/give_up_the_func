<IMG src="https://raw.githubusercontent.com/gravitymonkey/give_up_the_func/main/assets/recraft_ai_flying-saucer-70s-album-cover.png" width=400 alt="square image resembling a 70s album cover by Funkadelic, made by recraft.ai">

## Give Up The Func

#### A library that manages tools (functions) for Local LLMs

### Example With Ollama

#### Install it from [pypi](https://pypi.org/project/give-up-the-func/):
`pip install give_up_the_func` 

#### Import it:

Add the library, adding the `toolbox` decorator and the function `use_tools`, and we'll use OpenAI's client.

```
from give_up_the_func import toolbox, use_tools 
from openai import OpenAI 
```

#### Define some functions:

Define a function that you'd like to use, and use the `@toolbox` decorator on it.
Make sure you add a robust description and info on the params as this is important
for the model to receive information about it, and thus to know whether to call it.

Note - There are no other steps to include the functions for evaluation for usage for this library beyond using the decorator.  This is unlike the implementation with OpenAI [where you add `tools` to the chat request](https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models).

```
@toolbox
def list_local_files(
    directory: str    
) -> list:
    """
    Returns a list of all file names in a file system directory.
    
    @param directory: The file system directory to list file names from.
    """
    with os.scandir(directory) as entries:
        return [entry.name for entry in entries if entry.is_file()]    
```

#### Set up the OpenAI API Client, but for local use

Here we instantiate the [OpenAI client](https://platform.openai.com/docs/api-reference?lang=python), but set up to call [Ollama](https://ollama.com/).  Make sure you have Ollama running on your local machine if you're using the base_url `localhost:11434/v1`.

```
    client = OpenAI(
        base_url = 'http://localhost:11434/v1',
        api_key='ollama', # required, but unused        
    )
```

#### Send a prompt through

Calling the convenience method `use_tools` with the model name and prompt will return an actual response from the LLM, informed by the function's output,
if any of the functions you've marked with `@toolbox` were able to run 
and return an answer.  `None` will return if it was unable to identify
a matching function, or if another exception occured along the way.

The params you need to pass would be - a reference to the `client` created (above), the name of model you want to use (in this case, in my Ollama, I'm using `mistral`), and then the prompt.

```
answer = use_tools(client, "mistral", "Is readme.txt in the local directory ./?")
print(answer)
```

which returns:

```
Based on the data provided, there is no 'readme.txt' file in the current directory './'. The only .md (Markdown) file mentioned is 'README.md', not 'readme.txt'.
```

See [example.py](./example.py) for a complete example.

<HR>

### Problem Statement

In an LLM API call, you can describe functions and have the model intelligently choose to output a JSON object containing arguments to call one or many functions. This JSON object can then be used to execute 
those functions in whatever manner you choose.

Typically, say with OpenAI, you tackle this by adding tools to your chat request, and then monitor the response for
a JSON response that includes the function name and parameters.  You can then code it up to trigger the function and return the response, or you can use an existing framework like AutoGen that handles all of that for you.

#### Therein lies the rub

What happens if you'd like to run this on a local LLM, say, through Ollama (which manages to be both easy and amazing) in order to protect your privacy and reduce cost?  Well, you'll find that this really doesn't work at all (as of 5/24).  I believe function calling with local LLMs will all work nicely and seamlessly in the not-too-distant future as development continues -- so perhaps [Give Up The Func](https://github.com/gravitymonkey/give_up_the_func)'s duration of utility will be limited, which, that's totally cool by me -- but in the meantime, this will give me a good way to build and prototype with function calling on local LLMs today, ideally in a way that will be relatively future proof when local function calling is more reliable.

#### So what's different here?

The core problem can be quite tricky, as you're basically asking the LLM to be able to go from plain-language and extrapolate a matching function and parameters without needing to exactly ask for that function.  In the example, above, _"is readme.txt in this directory?"_ can trip up some simpler models because there isn't a function that looks like `is_file_in_directory(directory_name, file_name)` -- I've only provided a way to list the files in a directory with `list_local_files(directory_name)`.  So we'll start from a place acknowledging that this isn't exactly easy.  

What's happening inside of `use_tools`?  
 * We pass the functions and detailed instructions into the chat.
 * The detailed instructions (see `_make_admin_functions_prompt` in `give_up_the_func/core.py`) request a response with the function name and parameters, if applicable.
 * We look to see if there was any returned functions, if so, if they are actually within our `toolbox` (to avoid having the model hallucinate functions that don't exist).
 * Then we attempt to execute the function, then taking the response from the function back to the chat to attempt to integrate the response with the original prompt.


#### Additional Thoughts/References

 * The folks at [Gorilla](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html) have done all the hard work, it's worth checking them out.
 * (May 2024) Mistral7b is getting there.  Mistral's addition of function calling in version 0.3 requires using the `RAW` param in Ollama ([here's a simple CURL based on the examples in the docs](https://gist.githubusercontent.com/gravitymonkey/04393648c7f8f6a116a2e4d331e6d60b/raw/f3df20c6fd0527756aeb4a0845a0d3156436f91d/gistfile1.txt)).  I considered building an adapter from the OpenAI API to using Ollama's RAW instead, but found the approach here worked better and more reliably for now.
 * So in trying to solve this problem I found this example (shoutout [@Jamb9876 on Reddit](https://www.reddit.com/user/Jamb9876/)) with a prompt that was very close to what I wanted to achieve [https://github.com/namuan/llm-playground/blob/main/local-llm-tools-simple.py](https://github.com/namuan/llm-playground/blob/main/local-llm-tools-simple.py), with the flexibility of being able to tweak the prompt and impact results.
 * [Functionary](https://github.com/MeetKai/functionary) is very interesting - basically taking the approach of building focused improvement on function calling directly into a model.  
 * And of course, this library is named after [the 1975 song by P-Funk](https://www.youtube.com/watch?v=gBWH3OWfT2Y).  Ingenious reference or Dad-Joke: you decide.
  

