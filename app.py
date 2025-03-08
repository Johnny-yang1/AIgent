import streamlit as st
from ai_utils import call_qwq_api, process_qwq_response, MODEL_CONFIGS
import fitz  # PyMuPDF
import docx2txt  # 导入docx2txt库用于处理Word文档

# 页面配置 - 设置页面标题和宽屏布局
st.set_page_config(page_title="AI Chain Agent", layout="wide")

# 初始化会话状态变量
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'prompts' not in st.session_state:
    st.session_state.prompts = []
if 'results' not in st.session_state:
    st.session_state.results = []
if 'token_usage' not in st.session_state:
    st.session_state.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'chain_input' not in st.session_state:
    st.session_state.chain_input = ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "Qwen/QwQ-32B"
if 'current_api' not in st.session_state:
    st.session_state.current_api = 0
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = ""
if 'docx_text' not in st.session_state:
    st.session_state.docx_text = ""

# 定义PDF文本提取函数
def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        # 创建临时文件以供PyMuPDF处理
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # 使用PyMuPDF提取文本
        pdf_document = fitz.open("temp.pdf")
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        pdf_document.close()
        
        # 删除临时文件
        import os
        os.remove("temp.pdf")
    except Exception as e:
        st.error(f"PDF文件处理出错: {e}")
    return text

# 定义Word文档文本提取函数
def extract_text_from_docx(uploaded_file):
    text = ""
    try:
        # 创建临时文件以供docx2txt处理
        with open("temp.docx", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # 使用docx2txt提取文本
        text = docx2txt.process("temp.docx")
        
        # 删除临时文件
        import os
        os.remove("temp.docx")
    except Exception as e:
        st.error(f"Word文件处理出错: {e}")
    return text

# 侧边栏配置
with st.sidebar:
    st.title("⚙️ 配置")
    api_key = st.text_input("API Key 1", type="password")
    if api_key:
        st.session_state.api_key = api_key
    
    api_key2 = st.text_input("API Key 2", type="password")
    if api_key2:
        st.session_state.api_key2 = api_key2
    
    st.info(f"当前使用: API {st.session_state.current_api + 1}")
    
    model_options = list(MODEL_CONFIGS.keys())
    selected_model = st.selectbox(
        "选择模型",
        model_options,
        index=model_options.index(st.session_state.selected_model)
    )
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        if not st.session_state.processing_complete:
            st.session_state.current_step = 0
            st.session_state.prompts = []
            st.session_state.results = []
            st.session_state.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            st.session_state.processing_complete = False
            st.session_state.chain_input = ""
            st.session_state.docx_text = ""
            st.session_state.pdf_text = ""
            st.rerun()

# 主界面标题
st.title("🤖 怀远の超级AGENT")

# 固定的初始prompt
FIXED_INITIAL_PROMPT = "接下来，我会给你非常复杂的prompt，你需要经过深度思考，拆分成你所认为需要的步骤，每一行必须代表一个步骤，不可以在一个步骤中间换行，如果需要详细说明请在该行内完成，接下来，你需要返还你所认为的步骤的量个循序渐进的prompt，作为回答的第一行，你的回答第一行必须是总步骤的数字，不可以有任何额外文字，这些prompt必须是普通的大语言模型可以实现的，简单易懂的prompt，我会给按照顺序吧每个prompt给下一个AI，最后，经过你所认为的数量个prompt，我希望得到一个我刚开始发你的prompt所需要达到的要求和效果。你不可以使用markdown，每一个prompt需要时一段话，可以比较长，中间使用一个空行隔开。拆分的每个prompt必须超过100字。每次换行出现必须代表下一个prompt，不能随便换行。你的回答第一行是一个数字，第二行开始开始就必须是第一个prompt，不可以有额外内容。收到这些prompt的全部是AI，所以很多电脑的工具无法使用，请你确保你给出的方案都是AI可以用的。确保你最后的结果是用户想要的，比如代码，网站，结论等。不要使用：或者类似符号，直接输出1. 2. 3.作为prompt。返还的第一行必须是一个数字不能包含其他内容，这个数字必须是你给出的需要的次数。每一行必须代表一个步骤，不可以在一个步骤中间换行，如果需要详细说明请在该行内完成，如果你换行了系统会认为是下一步，而不是这一步的解释说明。请确保换行是下一步，而不是解释说明，同一步在一行内"

# 显示最终处理结果（移到顶部）
if st.session_state.processing_complete and st.session_state.results:
    st.subheader("✨ 最终结果")
    # 显示最后一个结果（总结结果）
    if len(st.session_state.results) > 0:
        with st.container():
            st.markdown("### 最终输出")
            st.write(st.session_state.results[-1])
    
    # 显示Token使用统计信息
    st.subheader("💰 Token使用情况")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("输入Token", st.session_state.token_usage["prompt_tokens"])
    with col2:
        st.metric("输出Token", st.session_state.token_usage["completion_tokens"])
    with col3:
        st.metric("总Token", st.session_state.token_usage["total_tokens"])

# 输入区域 - 使用表单收集用户输入
with st.form("input_form"):
    # 主要prompt输入框
    user_prompt = st.text_area("输入你的Prompt", height=100)
    
    # 添加文件上传组件
    col1, col2 = st.columns(2)
    with col1:
        uploaded_pdf = st.file_uploader("上传PDF文件", type=["pdf"])
    with col2:
        uploaded_docx = st.file_uploader("上传Word文件", type=["docx"])
    
    # 提交按钮
    submitted = st.form_submit_button("开始处理")

# 处理用户提交的表单
if submitted:
    # 检查是否已设置API密钥
    if not hasattr(st.session_state, 'api_key'):
        st.error("请先输入API Key")
    else:
        # 处理上传的PDF文件
        if uploaded_pdf is not None:
            with st.spinner("正在处理PDF文件..."):
                pdf_text = extract_text_from_pdf(uploaded_pdf)
                if pdf_text:
                    st.session_state.pdf_text = pdf_text
                    st.success("PDF文件处理成功！")
                else:
                    st.error("PDF文件处理失败")
        
        # 处理上传的Word文件
        if uploaded_docx is not None:
            with st.spinner("正在处理Word文件..."):
                docx_text = extract_text_from_docx(uploaded_docx)
                if docx_text:
                    st.session_state.docx_text = docx_text
                    st.success("Word文件处理成功！")
                else:
                    st.error("Word文件处理失败")
        
        # 处理用户输入的prompt
        if user_prompt:
            # 首先使用DeepSeek-R1-Distill-Qwen-32B优化用户输入的指令
            with st.spinner("正在优化用户指令..."):
                from ai_utils import optimize_user_input
                optimized_prompt = optimize_user_input(user_prompt)
                
                # 显示优化后的提示信息
                st.success("指令优化完成！")
                
            # 使用优化后的指令调用主AI处理流程
            with st.spinner(f"正在获取{st.session_state.selected_model}的响应..."):
                response = call_qwq_api(optimized_prompt, FIXED_INITIAL_PROMPT)
                if response:
                    # 获取处理步骤
                    prompts = process_qwq_response(response)
                    # 添加一个额外的总结步骤
                    prompts.append("请根据之前所有AI的输出，总结并给出最终的完整答复。你的回答应该是对整个任务的最终解决方案。如果用户叫你写小说，就不要返还框架，返还你写的小说，同理，如果用户的prompt是别的，也请回答用户想要的而非框架")
                    st.session_state.prompts = prompts
                    st.session_state.current_step = 1
                    st.session_state.results = []
                    # 将PDF或Word文本作为初始chain_input
                    if st.session_state.pdf_text:
                        st.session_state.chain_input = st.session_state.pdf_text
                    elif st.session_state.docx_text:
                        st.session_state.chain_input = st.session_state.docx_text
                else:
                    st.error("无法获取有效的API响应，请检查API密钥和网络连接后重试")

# 显示处理进度和结果
if st.session_state.prompts:
    # 显示已生成的所有prompts列表
    st.subheader("📝 步骤")
    for i, prompt in enumerate(st.session_state.prompts, 1):
        st.text(f"{i}. {prompt}")
    
    # 创建可爱的进度条
    progress_placeholder = st.empty()
    progress_text = "🌟 处理进度"
    current_progress = st.session_state.current_step / len(st.session_state.prompts) if not st.session_state.processing_complete else 1.0
    progress_bar = progress_placeholder.progress(0)
    progress_bar.progress(current_progress, text=progress_text)
    
    # 处理所有prompt，直到完成
    if not st.session_state.processing_complete and st.session_state.current_step <= len(st.session_state.prompts):
        # 显示当前处理进度
        with st.spinner(f"✨ 正在处理第 {st.session_state.current_step} 个步骤 (共{len(st.session_state.prompts)}个)..."):
            # 获取当前需要处理的prompt
            current_prompt = st.session_state.prompts[st.session_state.current_step - 1]
            
            # 准备链式输入：使用所有之前AI的输出或初始输入
            chain_input = ""
            all_previous_outputs = []
            
            if st.session_state.current_step > 1 and len(st.session_state.results) > 0:
                # 收集所有之前的AI输出
                all_previous_outputs = st.session_state.results.copy()
            elif st.session_state.current_step == 1 and st.session_state.chain_input:
                # 如果是第一个prompt且有初始输入，使用初始输入
                chain_input = st.session_state.chain_input
            
            # 调用API处理当前prompt，传递所有之前的输出
            result = call_qwq_api(current_prompt, chain_input=chain_input, all_previous_outputs=all_previous_outputs)
            if result:
                # 保存处理结果
                st.session_state.results.append(result)
                # 更新进度条
                progress_bar.progress(st.session_state.current_step / len(st.session_state.prompts))
                st.session_state.current_step += 1
                
                # 检查是否处理完所有prompt
                if st.session_state.current_step > len(st.session_state.prompts):
                    st.session_state.processing_complete = True
                    progress_bar.progress(1.0)
                    st.success("所有步骤处理完成！")
                
                # 如果还有prompt需要处理，重新运行应用继续处理
                if not st.session_state.processing_complete:
                    st.rerun()
            else:
                # API调用失败时的处理
                st.error("处理当前步骤t时出错，请检查API连接和密钥是否正确")
                # 不增加步骤，允许用户重试或重置
    
    # 显示处理结果
    if st.session_state.results:
        # 展示每个prompt的处理结果（除了最后一个）
        st.subheader("🎯 中间处理结果")
        for i, result in enumerate(st.session_state.results[:-1], 1):
            with st.expander(f"步骤 {i} : {st.session_state.prompts[i-1][:50]}..."):
                st.write(result)
        
        # 特别展示最终结果
        if len(st.session_state.results) == len(st.session_state.prompts):
            st.markdown("---")
            with st.container():
                st.markdown("### ✨ 最终输出")
                st.markdown("<div style='padding: 20px; border-radius: 10px; border: 2px solid #ff69b4; background-color: #fff5f7;'>", unsafe_allow_html=True)
                st.write(st.session_state.results[-1])
                st.markdown("</div>", unsafe_allow_html=True)
        
        # 显示Token使用统计信息
        st.subheader("💰 Token使用情况")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("输入Token", st.session_state.token_usage["prompt_tokens"])
        with col2:
            st.metric("输出Token", st.session_state.token_usage["completion_tokens"])
        with col3:
            st.metric("总Token", st.session_state.token_usage["total_tokens"])
        
        # 重置按钮：清空所有状态并重新开始
        if st.button("重置处理"):
            st.session_state.current_step = 0
            st.session_state.prompts = []
            st.session_state.results = []
            st.session_state.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            st.session_state.processing_complete = False
            st.session_state.chain_input = ""
            st.session_state.docx_text = ""
            st.rerun()