<IMG src="https://raw.githubusercontent.com/gravitymonkey/give_up_the_func/main/assets/recraft_ai_flying-saucer-70s-album-cover.png" width=400 alt="square image resembling a 70s album cover by Funkadelic, made by recraft.ai">

## Give Up The Func

#### A library that can extract tools (functions) for Local LLMs by handling logic within the prompt

### Example With Ollama

#### Install it from [pypi](https://pypi.org/project/give-up-the-func/):
`pip install give_up_the_func` 

#### Import it:

Add the library, adding the `toolbox` decorator and the function `chat_completion_with_functions_in_prompt`, and we'll use OpenAI's client.

```
from give_up_the_func import toolbox, chat_completion_with_functions_in_prompt 
from openai import OpenAI 
```

#### Define some functions:

Define a function that you'd like to use, and use the `@toolbox` decorator on it.
Make sure you add a robust description and info on the params as this is important
for the model to receive information about it, and thus to know whether to call it.

Note - There are no other steps to include the functions for evaluation for usage for this library beyond using the decorator.  This is unlike the implementation with OpenAI [where you add `tools` to the chat request](https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models).

```
@toolbox
def calculate_mortgage_payment(
    loan_amount: int, interest_rate: float, loan_term: int
) -> float:
    """
    Get the monthly mortgage payment given an interest rate percentage.

    @param loan_amount: The amount of the loan.
    @param interest_rate: The interest rate percentage.
    @param loan_term: The term of the loan in years.
    """
    monthly_interest_rate = interest_rate / 100 / 12
    number_of_payments = loan_term * 12
    mortgage_payment = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments) / ((1 + monthly_interest_rate) ** number_of_payments - 1)
    return round(mortgage_payment, 2)
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

Basically, we'll try to extract functions from our `@toolbox` by packing the prompt with all the info we need. See `ADMIN_FUNCTIONS_PROMPT` in `give_up_the_func/core.py` for details on the prompt (and you can tweak it as you need with `get/set` methods such as `set_admin_functions_prompt`).

Calling the method `chat_completion_with_functions_in_prompt` with the model name and prompt will 
return an OpenAI API compatible response from [`chat.completions.create`](https://platform.openai.com/docs/api-reference/streaming) (including values for `function_call` in `message` if one is found), and if identified, a list of `tools`, where each tool is a `dict` with `name` (of the function), and `arguments`.

The params you need to pass would be - a reference to the `client` created (above), the name of model you want to use (in this case, in my Ollama, I'm using `mistral`), and then the prompt.

```
response, tools = chat_completion_with_functions_in_prompt(client, "mistral", "What is the monthly payment for a $500,000 loan at 7.504% for 30 years?")
```

which returns, within `response` a model that matches `openai.types.chat.chat_completion.ChatCompletion`:

```
{
    "id": "chatcmpl-997",
    "choices": [
        {
            "finish_reason": "function_call",
            "index": 0,
            "logprobs": null,
            "message": {
                "content": null,
                "role": "assistant",
                "function_call": {
                    "name": "calculate_mortgage_payment",
                    "arguments": "{\"loan_amount\": 500000, \"interest_rate\": 7.504, \"loan_term\": 30}"
                },
                "tool_calls": null
            }
        }
    ],
    "created": 1717785514,
    "model": "mistral",
    "object": "chat.completion",
    "system_fingerprint": "fp_ollama",
    "usage": {
        "completion_tokens": 84,
        "prompt_tokens": 32,
        "total_tokens": 116
    }
}
```

There is a method `exec_tools` that can call the functions, and that responds here with:

```
[{'tool_name': 'calculate_mortgage_payment', 'response': 3497.44}]
```

See [example.py](./example.py) for a more complete example.

<HR>

### Problem Statement

In an LLM API call, you can describe functions and have the model intelligently choose to output a JSON object containing arguments to call one or many functions. This JSON object can then be used to execute 
those functions in whatever manner you choose.

Typically, say with OpenAI, you tackle this by adding tools to your chat request, and then monitor the response for
a JSON response that includes the function name and parameters.  You can then code it up to trigger the function and return the response, or you can use an existing framework like AutoGen that handles all of that for you.

#### Therein lies the rub

What happens if you'd like to run this on a local LLM, say, through Ollama (which manages to be both easy and amazing) in order to protect your privacy and reduce cost?  Well, you'll find that this really doesn't work very well at all (as of 5/24).  I believe function calling with local LLMs will all work nicely and seamlessly in the not-too-distant future as development continues -- so perhaps [Give Up The Func](https://github.com/gravitymonkey/give_up_the_func)'s duration of utility will be limited, which, that's totally cool by me -- but in the meantime, this will give me a good way to build and prototype with function calling on local LLMs today, ideally in a way that will be relatively future proof when local function calling is more reliable.

#### So what's different here?

The core problem can be quite tricky, as you're basically asking the LLM to be able to go from plain-language and extrapolate a matching function and parameters without needing to exactly ask for that function.  In one of the questions in `example.py`, _"is readme.txt in this directory?"_ can trip up some simpler models because there isn't a function that looks like `is_file_in_directory(directory_name, file_name)` -- I've only provided a way to list the files in a directory with `list_local_files(directory_name)`.  So we'll start from a place acknowledging that this isn't exactly easy.  

But instead of leaving this to the LLM model or API, we're handling here within _Give Up The Func_ by changing the prompt itself to perform the function extraction.  This makes it more straightforward, too, for us to tweak the prompt language to best match what we want.  And -- in running this on local LLMs -- we can indulge in many more hits against the LLM without worrying about cost, perhaps with more exacting (or even redundant) questions.


#### Additional Thoughts/References

 * The folks at [Gorilla](https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html) have done all the hard work, it's worth checking them out.
 * (May 2024) Mistral7b is getting there.  Mistral's addition of function calling in version 0.3 requires using the `RAW` param in Ollama ([here's a simple CURL based on the examples in the docs](https://gist.githubusercontent.com/gravitymonkey/04393648c7f8f6a116a2e4d331e6d60b/raw/f3df20c6fd0527756aeb4a0845a0d3156436f91d/gistfile1.txt)).  I considered building an adapter from the OpenAI API to using Ollama's RAW instead, but found the approach here worked better and more reliably for now.
 * So in trying to solve this problem I found this example (shoutout [@Jamb9876 on Reddit](https://www.reddit.com/user/Jamb9876/)) with a prompt that was very close to what I wanted to achieve [https://github.com/namuan/llm-playground/blob/main/local-llm-tools-simple.py](https://github.com/namuan/llm-playground/blob/main/local-llm-tools-simple.py), with the flexibility of being able to tweak the prompt and impact results.
 * [Functionary](https://github.com/MeetKai/functionary) is very interesting - basically taking the approach of building focused improvement on function calling directly into a model.  
 * What's next?  Testing, additional examples.  Perhaps looking into making it work with Autogen?  
 * And of course, this library is named after [the 1975 song by P-Funk](https://www.youtube.com/watch?v=gBWH3OWfT2Y).  Ingenious reference or Dad-Joke: you decide.
  

