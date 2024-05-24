from give_up_the_func import toolbox, use_tools
from openai import OpenAI
import os

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
]
for t in tests:
    client = OpenAI(
        base_url = 'http://localhost:11434/v1',
        api_key='ollama', # required, but unused        
    )
    print("------------")
    print(f"prompt: {t}")
    answer = use_tools(client, "mistral", t)
    print(f"tool result: {answer}")    
print("------------")    