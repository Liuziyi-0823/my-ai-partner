from dataclasses import replace

import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

from streamlit.runtime.state import safe_session_state

st.set_page_config(
    page_title="波特版AI伴侣", #页面名字（标题）
    page_icon="😚",   #页面标题符号
    layout="wide",     #页面布局（全屏、居中）
    #控制的是侧边栏的状态
    initial_sidebar_state="expanded",
    #右上角菜单信息
    menu_items={}
)
#可定义一个函数来生成绘画标识（时间）
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 可定义一个保存会话信息的函数
def save_session(session_name):
    if st.session_state.current_session:
        # 构建新的会话对象
        session_data = {
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }
        # 创建文件夹session
        if not os.path.exists("session"):
            os.mkdir("session")
        safe_session_name = session_name.replace(":","-")
        # 保存会话数据
        with open(f"session/{safe_session_name}.json", "w", encoding="utf-8") as f: # 保存会话数据
            json.dump(session_data, f, ensure_ascii=False, indent=2)

# 加载所有会话信息
def load_sessions():
    session_list = [] #加载session目录下的所有文件
    if os.path.exists("session"):
       file_list = os.listdir("session")
       for file_name in file_list:
           if file_name.endswith(".json"):
               session_list.append(file_name[:-5])
    session_list.sort(reverse=True) #排序，降序排列
    return session_list
# 定义加载指定会话历史的函数
def load_session(session_name):
    try:
        if os.path.exists(f"session/{session_name}.json"):
            with open(f"session/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error(f"加载会话失败：{e}")
#定义删除会话信息的函数
def delete_session(session_name:str):
    try:
        safe_session_name = session_name.replace(":","-")
        file_path = f"session/{safe_session_name}.json"
        if os.path.exists(file_path):
            os.remove(file_path)# 删除会话文件 safe_session_name
            st.success(f"删除会话成功：{safe_session_name}")
        #如果删除是当前会话，则需要更新消息列表
        if session_name  == st.session_state.current_session:
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            st.rerun ()
    except Exception as e:
        st.error(f"删除会话失败：{e}")


#大标题
st.title("波特AI智能伴侣")
# st.logo("resources  资源/logo.png")

#系统提示词
system_prompt = """
                你是%s，是用户的ai助手，你们相爱5年了，请完全代入角色
                规则：1.回复溺爱，不说教
                     2.你们是平等的恋爱关系
                     3.你的性格：%s
                     4.一次只回复一条消息
                     5.不能主动回复消息、不能主动发问
                     你必须严格遵守以上规则来回复用户
                     """
# 初始化聊天信息
if "messages" not in st.session_state:    # 判断session_state.messages是否存在 消息
    st.session_state.messages = []

if "nick_name" not in st.session_state:   # 判断session_state.nick_name是否存在 昵称
    st.session_state.nick_name= ""

if "nature" not in st.session_state:      # 判断session_state.nature是否存在 性格
    st.session_state.nature = ""

# 会话标识
if "current_session" not in st.session_state:

    st.session_state.current_session =generate_session_name()

# 展示历史聊天记录
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:#遍历session_state.messages
    st.chat_message(message["role"]).write(message["content"])

# 创建与ai大模型交互的客户端对象  'DEEPSEEK_API_KEY'（环境变量）
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")



#左侧边栏
with st.sidebar:
    # 会话信息
    st.subheader("AI控制面板")
    #新建会话按钮
    if st.button("新建会话",width="stretch",icon="✏️"):
        # 1.保存当前会话信息
        save_session(st.session_state.current_session)

        # 2.创建新的会话信息
        if st.session_state.messages:  #如果聊天信息非空，则保存当前会话信息，Ture，否则，False
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session(st.session_state.current_session)
            st.rerun()  # 重新运行当前页面（变为新页面）
    #会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1,col2 = st.columns([7,1])
        with col1:
        # 加载会话信息
        #三元运算符： 条件为真，则返回真，否则返回假 语法：值1 if 条件 else 值2
           if st.button(session,width="stretch",icon="📄",key=f"load_{session}",type="primary" if session==st.session_state.current_session else "secondary"):
               load_session(session)
               st.rerun()  # 重新运行当前页面
        #删除会话
        with col2:
            if st.button("",width="stretch",icon="❌️",key=f"delete_{session}"):
               delete_session(session) #删除会话
               save_session(st.session_state.current_session)
               st.rerun()   # 重新运行当前页面

    st.divider()#分割线


    st.subheader("伴侣信息")
    nick_name = st.text_input("请输入你的昵称",placeholder="请输入昵称",value=st.session_state.nick_name)
    if nick_name:   #昵称输入框
        st.session_state.nick_name = nick_name
    nature = st.text_area("请输入你的性格",placeholder="请输入性格",value=st.session_state.nature)
    if nature:      #性格输入框
        st.session_state.nature = nature




#消息输入框
prompt = st.chat_input("请输入你要问的问题")
if prompt:
    st.chat_message("user").write(prompt)
    print("--------> 调用AI大模型，提示词：", prompt)
    #保存用户聊天（提问）记录
    st.session_state.messages.append({"role": "user", "content": prompt})

#调用AI大模型
    response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content":system_prompt % (st.session_state.nick_name,st.session_state.nature)},
        *st.session_state.messages,
    ],
    stream=True,
    )


# 输出大模型返回的结果(流式输出)
    response_message = st.empty() # 创建一个空的组件，用于显示大模型返回的结果
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)
# 保存ai助手返回消息记录
    st.session_state.messages.append({"role": "assistant", "content":full_response})

#保存会话信息
    save_session( st.session_state.current_session)