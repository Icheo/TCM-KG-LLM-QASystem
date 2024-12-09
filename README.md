# TCM-KG-LLM-QASystem
This is the official codebase for TCM-KG-LLM-QASystem.
# Introduction
TCM-KG-LLM-QASystem is an advanced question-answering system that leverages a knowledge graph and large language models to efficiently retrieve and analyze Traditional Chinese Medicine case records. The principle of the Q&A process is as follows:
![QA process](https://github.com/Icheo/TCM-KG-LLM-QASystem/blob/main/Figure/QA%20process.png)
# Getting Started
## Step 1 Installation
Set up conda environment and clone the github repo.
```
# create a new environment
$ conda create --name qa
$ conda activate qa
# install requirements
$ pip install -r requirements.txt
```
##  Step 2 Running
```
$ cd notebook
$ jupyter notebook
```
### 1. Extract entities
Modify the following parameters to your own path and API key.
After running, the file will be generated at the output file location.
```
file_path = "..\data\wzq-medical-cases.xlsx"
output_file = "..\data\output.xlsx
client = ZhipuAI(api_key="zhipu_api_key")
```
### 2. Entity standardization
The parameters that need to be modified are the same with Extract entities process.
### 3. Create knowledge graph
Modify the following parameters to your own path and neo4j parameters.
```
df = pd.read_csv("csv_path") # Path to CSV file for creating knowledge graph
g = Graph('neo4j_url', auth=('neo4j', 'password'), name='neo4j')
```
### 4. Question answering
Modify the following parameters to your own API key and neo4j parameters.
```
os.environ["OPENAI_API_KEY"] = "openai_api_key"
openai.api_base = "base_url"
os.environ["NEO4J_URI"] = "neo4j_url"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
```
