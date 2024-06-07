import inspect
import json
from typing import get_type_hints
from openai import OpenAI
import os
import logging


ADMIN_FUNCTIONS_PROMPT = f"""
    You must follow these instructions:
    Always select one or more of the above tools based on the user query
    If a tool is found, you must respond in the JSON format matching the following schema:
    {{
    "tools": {{
            "name": "<name of the selected tool>",
            "arguments": <parameters for the selected tool as explicitly stated in the user's query, matching the tool's JSON schema>
    }}
    }}
    Do not make up any tools or use any tools that are not listed above.
    Only specify paramaters for tool_input that are clearly defined in the user's prompt that follows.
    If there are missing required parameters to call a tool, do not return the tool.
    If there are multiple tools required, make sure a list of tools are returned in a JSON array.
    If there is no tool that match the user request, you MUST respond with empty json.
    DO NOT add any additional Notes or Explanations.
    """

# Create a logger for the library
logger = logging.getLogger('give_up_the_func')

_collected_toolbox = []

def toolbox(func):
    """
    Decorator that collects the decorated function into a list.
    """
    _collected_toolbox.append(func)
    return func

def get_toolbox():
    """
    Return the list of functions decorated with @toolbox.
    """
    return _collected_toolbox

class FunctionCaller:
    """
    A class that wraps a function and its arguments, allowing it to be called later.

    Args:
        func: The function to be called.
        *args: Positional arguments to be passed to the function.
        **kwargs: Keyword arguments to be passed to the function.
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        """
        Calls the wrapped function with the provided arguments.

        Returns:
            The result of calling the function.
        """
        return self.func(*self.args, **self.kwargs)

def exec_tools(tools):
    """
    Executes a list of tools and returns their responses.

    Args:
        tools (list): A list of tools to execute. Each tool is represented as a dictionary with two keys:
                      - 'name': The name of the tool (a string).
                      - 'arguments': The input parameters for the tool (a dictionary).

    Returns:
        list: A list of dictionaries representing the responses of the executed tools. Each dictionary has two keys:
              - 'tool_name': The name of the tool (a string).
              - 'response': The response of the tool (a string or a JSON-formatted string).

    Raises:
        Exception: If an error occurs while executing a tool, an exception is raised and printed to the console.
    
    """
    if tools is None or len(tools) == 0:
        return None
    if type(tools) is str:
        tools = json.loads(tools)
    if tools[0].get("error"):
        return None
    func_list = get_toolbox()
    responses = []
    # confirm the tool is in the toolbox - in case the LLM is making up toolnames!
    for tool in tools:
        if type(tool) is dict:
            tool_name = tool["name"]
            tool_input = tool["arguments"]
            if type(tool_input) is str:
                tool_input = json.loads(tool_input)
            for func in func_list:
                if func.__name__ == tool_name:
                    try:
                        fc = FunctionCaller(func, **tool_input)                    
                        output = fc()
                        tool_output = None
                        if type(output) is str or type(output) is int or type(output) is float:
                            tool_output = {"tool_name": tool_name, "response": output}
                        else:
                            tool_output = {"tool_name": tool_name, "response": json.dumps(output, indent=4)}
                        responses.append(tool_output)
                    
                    except Exception as e:
                        logger.warning(f"Error executing tool {tool_name}: {str(e)}")
    return responses


def _get_type_name(t):
    if hasattr(t, '__name__'):
        return t.__name__
    return str(t)

def _get_param_descriptions(doc):
    descriptions = {}
    if doc is not None:
        lines = inspect.cleandoc(doc).split('\n')
        for line in lines:
            parts = line.split(':')
            if len(parts) == 2 and parts[0].strip().startswith('@param'):
                pname = parts[0].strip().split(' ')[1]
                descriptions[pname] = parts[1].strip()
    return descriptions

def _clean_description(description):
    desc = ""
    lines = description.split("\n")
    for line in lines:
        line = line.strip()
        if line != "":
            if not line.startswith("@param"):
               desc += line.strip() + " "
    return desc.strip()

def _function_to_json(func):
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    param_descriptions = _get_param_descriptions(func.__doc__)

    function_info = {
        "name": func.__name__,
        "description": _clean_description(func.__doc__),
        "parameters": {"type": "object", "properties": {}, "required": []},
        "returns": type_hints.get("return", "void").__name__,
    }

    for name, param in signature.parameters.items():
        param_type = _get_type_name(type_hints.get(name, type(None)))
        
        if param_type == "str":
            param_type = "string"
        elif param_type == "int":
            param_type = "number"
        elif param_type == "float":
            param_type = "number"

        is_required = param.default == inspect.Parameter.empty
        function_info["parameters"]["properties"][name] = {
            "type": param_type,
            "description": param_descriptions.get(name, "")
            }
        if is_required:
            function_info["parameters"]["required"].append(name)


    return json.dumps(function_info, indent=2)

def _make_functions(as_json=True):
    functions = []
    for func in get_toolbox():
        s = _function_to_json(func) 
        sf = json.loads(s)
        fx = {"type": "function", "function":sf }
        functions.append(fx)
    if as_json:
        functions_json = json.dumps(functions, indent=2)
        return functions_json
    else:
        return functions


def get_admin_functions_prompt():
    """
    Returns the current prompt use to describe how to extract functions.

    Returns:
        str: The prompt.
    """
    return ADMIN_FUNCTIONS_PROMPT

def set_admin_functions_prompt(prompt: str):
    """
    Set the prompt which describes how to handle functions.

    Args:
        prompt (str): The prompt to use to describe how to handle functions.

    Returns:
        None
    """
    global ADMIN_FUNCTIONS_PROMPT
    ADMIN_FUNCTIONS_PROMPT = prompt

def _make_admin_functions_prompt():
    prompt = f"""You have access to the following tools:
    {_make_functions()}
    {ADMIN_FUNCTIONS_PROMPT}
    """
    return prompt

def _parse_tools(response: dict):
    try:
        content = response.choices[0].message.content
        content = content.replace("\_", "_") # fixes escape char in mistral
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]   
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(content)
        logger.error(f"Exception parsing JSON - JSONDecodeError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Exception parsing response: {str(e)}")
        return None
    
def chat_completion_with_oai_functions(client: object, model: str, prompt: str) -> dict[str, str]:
    messages = [{"role": "user", "content": prompt}]
    funcs = _make_functions(as_json=False)
    func_list = []
    for f in funcs:
        func_list.append(f["function"])
    return client.chat.completions.create(
            model=model,
            messages=messages,
            functions=func_list,
            stream=False,
        )        


def chat_completion_with_functions_in_prompt(client: object, model: str, prompt: str) -> dict[str, str]:
    """
    Retrieve a list of tools based on the given model and prompt.

    Args:
        client (object): The client object used to make API requests.
        model (str): The name of the model to use for generating completions.
        prompt (str): The user prompt to provide as input.

    Returns:
        tuple: A tuple containing the API response and a list of tools.
            - The API response is a dictionary containing the response from the API call.
            - The list of tools is a list of dictionaries representing the tools extracted from the API response.

    Raises:
        Exception: If there is an error during the API call or parsing the response.
    """
    messages = [{"role": "system", "content": _make_admin_functions_prompt()}, {"role": "user", "content": prompt}]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
        )        
        try:
            tools_dict = _parse_tools(response)
            if tools_dict:
                if "tools" in tools_dict:
                    # make the full response as compatible with OpenAI's response as possible
                    message = response.choices[0].message
                    first_tool = tools_dict["tools"][0]
                    first_tool["arguments"] = json.dumps(first_tool["arguments"])
                    message.function_call = first_tool                    
                    message.content = None
                    response.choices[0].finish_reason = "function_call"
                    return response, tools_dict["tools"]
                else:
                    response.choices[0].message.function_call = None
                    return response, []
            else:
                return response, []
        except Exception as e:
            return response, [{"error": f"JSON call error: {str(e)}"}]
        return response, []
    except Exception as e:
        exception_name = type(e).__name__
        if exception_name == "NotFoundError":
            return response, [{"error": f"wrong model name? {str(e)}"}]
        return response, [{"error": f"{str(e)}"}]

def generate_reconciled_response(tools, tool_responses, client, model, original_prompt):
    """
    Generate a reconciled response using the given tools and tool responses.

    Args:
        tools: The tools found for generate the responses.
        tool_responses: The responses generated by the tools.
        client: The client object used for making API requests.
        model: The model used for generating the response.
        original_prompt (str): The original user prompt.

    Returns:
        tuple: A tuple containing the full response object and the content of the first choice.

    """
    if tool_responses is not None:
        # answer the original question with the results and form a response
        messages = [
            {"role": "system", "content": f"Using the data retrieved from the following functions, generate an appropriate response to the user's question(s). \n **** \n The result of using {tools} is {tool_responses}."},
            {"role": "user", "content": original_prompt},
        ]
        full_response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
        )
        return full_response, full_response.choices[0].message.content
    return None, None

