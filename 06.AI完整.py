import streamlit as st
import os
import json
import time
from openai import OpenAI
from datetime import datetime
from pathlib import Path  # 改进点：使用 pathlib 处理路径更安全

from streamlit.commands import logo

# ==========================================
# 1. 页面配置与初始化
# ==========================================
icon_path="😚"
# Logo_Path="resources  资源/logo2.png"
st.set_page_config(
    page_title="波特版AI伴侣",
    page_icon=icon_path,
    layout="wide",
    initial_sidebar_state="expanded"
)
with st.sidebar:
    # st.logo(Logo_Path)
    st.write("嗨嗨嗨，来了")
st.title("波特AI智能伴侣")
# 改进点：使用 pathlib 定义路径，避免硬编码字符串拼接
SESSION_DIR = Path("session")
SESSION_DIR.mkdir(exist_ok=True)  # 如果目录不存在则自动创建

# ==========================================
# 2. 工具函数 (Utils)
# ==========================================
def generate_session_id():
    """生成基于时间戳的唯一会话ID"""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def safe_filename(name):
    """将文件名中的非法字符替换，Windows下主要处理冒号"""
    return str(name).replace(":", "-")

# ==========================================
# 3. 会话管理函数 (CRUD)
# ==========================================
def save_session(session_id):
    """保存当前会话状态到 JSON 文件"""
    if not session_id:
        return

    # 提取需要保存的数据
    session_data = {
        "nick_name": st.session_state.get("nick_name", "用户"),
        "nature": st.session_state.get("nature", "温柔"),
        "messages": st.session_state.get("messages", []),
        "timestamp": time.time()  # 用于排序
    }

    file_path = SESSION_DIR / f"{safe_filename(session_id)}.json"

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.toast(f"保存失败: {e}", icon="❌")

def load_all_sessions():
    """加载所有会话列表，按时间倒序排列"""
    if not SESSION_DIR.exists():
        return []

    sessions = []
    # 遍历目录下所有json文件
    for json_file in SESSION_DIR.glob("*.json"):
        try:
            # 从文件名恢复 session_id (去掉 .json 后缀)
            session_id = json_file.stem
            # 读取文件获取时间戳用于排序
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                timestamp = data.get("timestamp", 0)
                # 尝试获取昵称作为显示名
                display_name = data.get("nick_name", "未知用户")
                sessions.append({
                    "id": session_id,
                    "name": f"{session_id} ({display_name})",
                    "timestamp": timestamp
                })
        except Exception:
            continue
   # 按时间戳倒序排序 (最新的在前面)
    sessions.sort(key=lambda x: x["timestamp"], reverse=True)
    return sessions

def load_session(session_id):
    """加载指定会话的数据到 st.session_state"""
    file_path = SESSION_DIR / f"{safe_filename(session_id)}.json"

    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            st.session_state.messages = data.get("messages", [])
            st.session_state.nick_name = data.get("nick_name", "用户")
            st.session_state.nature = data.get("nature", "温柔")
            st.session_state.current_session = session_id
        except Exception as e:
            st.error(f"加载失败: {e}")

def delete_session(session_id):
    """删除指定会话文件"""
    file_path = SESSION_DIR / f"{safe_filename(session_id)}.json"

    if file_path.exists():
        try:
            file_path.unlink()  # 删除文件

            # 如果删除的是当前正在聊天的会话，重置状态
            if st.session_state.current_session == session_id:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_id()
                st.rerun()
        except Exception as e:
            st.error(f"删除失败: {e}")

# ==========================================
# 4. 状态初始化
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "nick_name" not in st.session_state:
    st.session_state.nick_name = "用户"

if "nature" not in st.session_state:
    st.session_state.nature = "温柔"

if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_id()

# ==========================================
# 5. 侧边栏逻辑
# ==========================================
with st.sidebar:
    st.header("🎛️ 控制面板")
   # 新建会话
    if st.button("✨ 新建会话", use_container_width=True, type="primary"):
        # 先保存当前会话
        save_session(st.session_state.current_session)
        # 重置状态
        st.session_state.messages = []
        st.session_state.current_session = generate_session_id()
        st.rerun()

    st.divider()

    # 会话历史列表
    st.subheader("📜 历史记录")
    session_list = load_all_sessions()

    if not session_list:
        st.info("暂无历史记录")

    for session in session_list:
        # 使用 columns 布局来实现“加载”和“删除”按钮并排或紧凑排列
        col_load, col_del = st.columns([4, 1])
        with col_load:
            # 判断是否为当前会话，如果是则高亮
            is_current = session["id"] == st.session_state.current_session
            btn_type = "primary" if is_current else "secondary"

            if st.button(
                session["name"],
                key=f"load_{session['id']}",
                use_container_width=True,
                type=btn_type
            ):
                if not is_current:
                    load_session(session["id"])
                    st.rerun()

        with col_del:
            if st.button("🗑️", key=f"del_{session['id']}"):
                delete_session(session["id"])

    st.divider()

    # 人设设置
    st.subheader("⚙️ 人设调整")
    new_nick = st.text_input("你的称呼", value=st.session_state.nick_name)
    new_nature = st.text_area("我的性格", value=st.session_state.nature, height=100)

    if new_nick != st.session_state.nick_name or new_nature != st.session_state.nature:
        st.session_state.nick_name = new_nick
        st.session_state.nature = new_nature
        # 实时更新保存（可选，也可以在发消息时保存）
        save_session(st.session_state.current_session)
# 6. 主界面与 AI 交互逻辑
# ==========================================
st.title(f"💬 和 {st.session_state.nick_name} 的聊天")

# 定义系统提示词
system_prompt = f"""
你是用户的AI伴侣。
你们的对话设定如下：
用户昵称：{st.session_state.nick_name}
你的性格：{st.session_state.nature}

请保持你的性格设定，与用户进行自然、流畅的对话。
"""

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if prompt := st.chat_input("请输入你想说的话..."):
    # 1. 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 将用户消息加入历史
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. 调用 DeepSeek API
    # 改进点：确保 API KEY 存在
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        st.error("未找到 DeepSeek API Key，请检查环境变量设置。")
        st.stop()

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # 改进点：修正了 API 调用参数，移除了错误的 write 参数
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
                stream=False,
            )

            # 4. 处理流式响应
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content_piece = chunk.choices[0].delta.content
                    full_response += content_piece
                    # 实时刷新显示
                    message_placeholder.markdown(full_response + "▌")

                    # 5. 最终显示（去掉光标）
                message_placeholder.markdown(full_response)

                # 6. 保存 AI 回复到历史
                st.session_state.messages.append({"role": "assistant", "content": full_response})

                # 7. 异步保存会话（避免阻塞UI，但在简单脚本中直接调用也可以）
                save_session(st.session_state.current_session)

        except Exception as e:
            st.error(f"API 调用出错: {e}")