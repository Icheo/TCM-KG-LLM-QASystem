import os
import gradio as gr
from typing import List, Tuple
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

# 设置Neo4j环境变量
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = ""

# 连接Neo4j
graph = Neo4jGraph()

# 定义查询
description_query = """
MATCH (m:病名|症状|用药|治则|病机)
WHERE m.name CONTAINS $candidate
MATCH (m)-[r:治疗|属于|运用|推荐用药|遵循|导致]-(t)
WITH m, type(r) as type, collect(coalesce(t.name)) as names
WITH m, type+": "+reduce(s="", n IN names | s + n + ", ") as types
WITH m, collect(types) as contexts
WITH m, "type:" + labels(m)[0] + "\ntitle: "+ coalesce(m.name)  +"\n" +
       reduce(s="", c in contexts | s + substring(c, 0, size(c)-2) +"\n") as context
RETURN context LIMIT 1
"""

def get_information(entity: str) -> str:
    try:
        data = graph.query(description_query, params={"candidate": entity})
        return data[0]["context"]
    except IndexError:
        return "No information was found"

# 定义工具
class InformationInput(BaseModel):
    entity: str = Field(description="something about traditional Chinese medicine mentioned in the question")

class InformationTool(BaseTool):
    name: str = "Information"
    description: str = "useful for when you need to answer questions about traditional Chinese medicine"
    args_schema: type[BaseModel] = InformationInput

    def _run(self, entity: str) -> str:
        return get_information(entity)

    async def _arun(self, entity: str) -> str:
        return get_information(entity)

# 初始化LLM和工具
llm = ChatOpenAI(
    model="gpt-3.5-turbo", 
    temperature=0, 
    openai_api_key="openai_api_key",
    openai_api_base="base_url"
)
tools = [InformationTool()]

llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in tools])

# 设置提示模板
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant that finds information about traditional Chinese medicine "
        " and recommends them." 
        "Do only the things the user specifically requested. "
        "Start with '根据王仲奇医案' when answering, end with '查询结果存在个体现象，医疗情况因人而异，请结合自身状况并始终咨询专业医生的建议以获得最佳护理。'",
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

def _format_chat_history(chat_history: List[Tuple[str, str]]):
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer

# 设置Agent
agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: _format_chat_history(x["chat_history"])
        if x.get("chat_history")
        else [],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 定义聊天历史
chat_history = []

def respond(message, history):
    # 将历史记录转换为所需格式
    formatted_history = [(h[0], h[1]) for h in history]
    
    # 调用agent_executor
    response = agent_executor.invoke({
        "input": message,
        "chat_history": formatted_history
    })
    
    return response["output"]

# 创建Gradio界面
iface = gr.ChatInterface(
    respond,
    title="王仲奇医案中医问答助手",
    description="请输入您的问题，我会根据王仲奇医案为您解答。",
    theme="soft",
    examples=[
        "自汗可以用什么中药治疗？",
        "外感湿邪可能导致什么症状？",
        "黄芪可以用来治疗什么？",
        "如何治疗腹痛？",
        "失眠可以吃什么中药？"
    ]
)

if __name__ == "__main__":
    iface.launch(share=True) 