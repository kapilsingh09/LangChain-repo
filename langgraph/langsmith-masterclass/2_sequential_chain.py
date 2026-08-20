from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from free_model.free_model_hf import free_model
import os
os.environ['LANGCHAIN_PROJECT'] = 'Sequential LLM App'

load_dotenv()

prompt1 = PromptTemplate(
    template='Generate a detailed report on {topic}',
    input_variables=['topic']
)

prompt2 = PromptTemplate(
    template='Generate a 5 pointer summary from the following text \n {text}',
    input_variables=['text']
)

model = free_model()

parser = StrOutputParser()

chain = prompt1 | model | parser | prompt2 | model | parser

config={
    'run_name':'sequential chain',
    'tags':{"llm app","report generation","summarization"},
    'metadata':{'model1':'free model','model_temp': '0','parser':'stroutputparser'}
}

result = chain.invoke({'topic': 'rain density in India'},config=config)

print(result)
