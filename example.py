from give_up_the_func import toolbox, chat_completion_with_functions_in_prompt, exec_tools, chat_serializer, chat_completion_with_oai_functions
from openai import OpenAI
import os
import json

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


@toolbox
def read_readme(
        ) -> str:
    """
    Reads README.md file from the given directory and returns a string.
    """    
    with open(f'./README.md') as f:
        return f.read()


@toolbox
def get_weather(
    location: str
) -> str:
    """
    Get the current weather for a location.

    @param location: The location to get the weather for.
    """
    return "Sunny"
    

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
    


tests = [
    "Who is the King of Oklahoma?",
    "What is my mortgage payment?",
    "What's the weather in Seattle?",
    "Is readme.txt in the files in the current directory, ./?",
    "What is the monthly payment for a $500,000 loan at 7.504% for 30 years?",
    "What's the weather right now in the city mentioned in the readme.md in the current directory?",
]
for t in tests:
    model_name = "mistral"
    client = OpenAI(
        base_url = 'http://localhost:11434/v1',
        api_key='ollama', # required, but unused        
    )

    print("------------")
    print(f"prompt: {t}")

    # chat_completion_with_functions_in_prompt will return the list of tools available

    gutfunc_response, tools = chat_completion_with_functions_in_prompt(client, model_name, t)    

    # now just print it the response (openAI compatible), and a list-of-dicts of the detected tools
    p_gutfunc_response = json.dumps(gutfunc_response, indent=4, default=chat_serializer)
    print("chat_completion_with_functions_in_prompt_response:")
    print(f"-----\n{p_gutfunc_response}\n----")
    print("the 'tools' simplified response:")
    print(tools)
    print("\n------------")

    # we can do a chat completion in OpenAI's style, with 
    # passing the functions as a separate list (not in the prompt)
    
    # we'll change some settings to call OpenAI's API
    # and compare the output to know we're compatible
    '''
    model_name = "gpt-4"
    client = OpenAI(    
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    
    full_response = chat_completion_with_oai_functions(client, model_name, t)    
    p_full_response = json.dumps(full_response, indent=4, default=chat_serializer)
    print("chat_completion_with_oai_functions_response:")
    print(f"-----\n{p_full_response}\n----")
    '''


    # here we'll call the function from the Ollama call, above,
    # to see the response.  The functions are defined in this
    # file, as well, above.
    print(f"chat_completion_with_functions_in_prompt tools: {tools}")
    tool_responses = exec_tools(tools)
    print()
    print(f"exec_tools tool_responses: {tool_responses}")
    print()


    

print("------------")    

