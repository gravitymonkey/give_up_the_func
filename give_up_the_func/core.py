import inspect
import json
from typing import get_type_hints
from openai import OpenAI
import os
import logging

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
                      - 'tool': The name of the tool (a string).
                      - 'tool_input': The input parameters for the tool (a dictionary).

    Returns:
        list: A list of dictionaries representing the responses of the executed tools. Each dictionary has two keys:
              - 'tool_name': The name of the tool (a string).
              - 'response': The response of the tool (a string or a JSON-formatted string).

    Raises:
        Exception: If an error occurs while executing a tool, an exception is raised and printed to the console.
    
    """
    if tools is None or len(tools) == 0:
        return None
    func_list = get_toolbox()
    responses = []
    # confirm the tool is in the toolbox - in case the LLM is making up tools
    for tool in tools:
        if type(tool) is dict:
            tool_name = tool["tool"]
            tool_input = tool["tool_input"]
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

def _make_admin_functions_prompt():

    admin_functions_prompt = f"""
    You have access to the following tools:
    {_make_functions()}

    You must follow these instructions:
    Always select one or more of the above tools based on the user query
    If a tool is found, you must respond in the JSON format matching the following schema:
    {{
    "tools": {{
            "tool": "<name of the selected tool>",
            "tool_input": <parameters for the selected tool as explicitly stated in the user's query, matching the tool's JSON schema>
    }}
    }}
    Do not make up any tools or use any tools that are not listed above.
    Only specify paramaters for tool_input that are clearly defined in the user's prompt that follows.
    If there are missing required parameters to call a tool, do not return the tool.
    If there are multiple tools required, make sure a list of tools are returned in a JSON array.
    If there is no tool that match the user request, you MUST respond with empty json.
    DO NOT add any additional Notes or Explanations.
    """
    return admin_functions_prompt

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

def list_tools(client: object, model: str, prompt: str) -> dict[str, str]:
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
                    return response, tools_dict["tools"]
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

def reconcile_response(tools, tool_responses, client, model, original_prompt):
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

def use_tools(client, model, prompt):
    """
    A conveinience method to use the specified tools to generate a response to the user's question.

    Args:
        client (Client): The client object used to interact with the chat API.
        model (str): The model to use for generating the response.
        prompt (str): The user's question or prompt.

    Returns:
        str: The generated response to the user's question.
        None: If the tool_responses is None.
    """
    response, xx = list_tools(client, model, prompt)
    tool_responses = exec_tools(xx)
    full_response, answer = reconcile_response(xx, tool_responses, client, model, prompt)
    return answer
