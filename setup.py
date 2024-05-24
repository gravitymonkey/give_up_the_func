from setuptools import setup, find_packages

setup(
    name='give_up_the_func', 
    version='0.0.1',  
    author='gravitymonkey',  
    author_email='jason@gravitymonkey.com',  
    description='A helper library for using function calling on local LLMs.',  
    long_description=open('README.md').read(),  # Long description read from the README.md
    long_description_content_type='text/markdown',  # Type of the long description
    url='https://github.com/gravitymonkey/give_up_the_func',  # URL of your project
    packages=find_packages(),  # Packages to include
    install_requires=[
        'openai',  # Dependencies, you can add more as required
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',  
        'Intended Audience :: Developers',  # Target audience
        'License :: OSI Approved :: MIT License',  # License
        'Programming Language :: Python :: 3',  # Programming language
        'Programming Language :: Python :: 3.7',  # Specify which python versions are supported
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.7',  # Minimum version requirement of the package
    keywords='chatbot, functions, LLM, AI',  
    include_package_data=True, 
)