import requests
import json
import time
import random
import streamlit as st

# API配置 - 定义了与AI模型通信的服务器地址
# 这是发送AI请求的目标网址，所有的AI对话都会发送到这个地址
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# 模型配置 - 定义了可用的AI模型及其参数设置
# 每个模型都有一个最大令牌数限制，这决定了AI回答的最大长度
# 令牌(token)是AI处理文本的基本单位，大约相当于1-2个汉字或0.75个英文单词
MODEL_CONFIGS = {
    "Qwen/QwQ-32B": {"max_tokens": 8192},  # 通义千问QwQ模型，可输出最多8192个令牌
    "Pro/deepseek-ai/DeepSeek-R1": {"max_tokens": 8192},  # DeepSeek-R1模型，可输出最多8192个令牌
    "Qwen/Qwen2.5-72B-Instruct-128K": {"max_tokens": 4096},  # 通义千问2.5大模型，可输出最多4096个令牌
    "Pro/deepseek-ai/DeepSeek-V3": {"max_tokens": 4096}  # DeepSeek-V3模型，可输出最多4096个令牌
}

# 指令优化模型 - 用于优化用户输入的指令的专用模型
# 这个模型会分析用户的原始指令，并将其改写为更加详细、明确的形式
INPUT_OPTIMIZER_MODEL = "Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

def call_qwq_api(prompt, initial_prompt="", chain_input="", all_previous_outputs=None):
    # 构建API请求消息列表
    messages = []
    # 如果提供了初始提示，将其作为系统消息添加到列表中
    # 系统消息用于设定AI的行为规则、角色和限制
    if initial_prompt:
        messages.append({"role": "system", "content": initial_prompt})
    
    # 处理链式输入：如果存在前一个AI的输出，将其与当前prompt组合
    # 这允许多个AI模型协作完成复杂任务，前一个AI的输出可以作为下一个AI的输入
    if all_previous_outputs and len(all_previous_outputs) > 0:
        # 如果提供了所有之前的输出，将它们全部包含在提示中
        # 这种方式可以让AI看到整个处理过程中的所有中间结果
        previous_outputs_text = "\n\n".join([f"第{i+1}个AI的输出：\n{output}" for i, output in enumerate(all_previous_outputs)])
        prompt = f"之前所有AI的输出：\n{previous_outputs_text}\n\n你的任务：\n{prompt}"
    elif chain_input:
        # 向后兼容：如果只提供了单个chain_input
        # 这是一种简化的链式调用方式，只考虑前一个AI的输出
        prompt = f"前一个AI的输出：\n{chain_input}\n\n你的任务：\n{prompt}"
    
    # 添加用户消息到列表中
    # 用户消息包含实际的问题或指令，是AI需要回答或执行的内容
    messages.append({"role": "user", "content": prompt})
    
    # 获取当前选择的模型配置
    # 不同的模型有不同的参数设置，如最大输出长度
    model_config = MODEL_CONFIGS[st.session_state.selected_model]
    
    # 构建API请求参数
    # 这些参数控制AI生成回答的方式，如温度（创造性）、最大长度等
    payload = {
        "model": st.session_state.selected_model,  # 使用用户选择的AI模型
        "messages": messages,  # 包含系统提示和用户问题的消息列表
        "stream": False,  # 不使用流式输出（即等待完整回答后一次性返回）
        "max_tokens": model_config["max_tokens"],  # 设置回答的最大长度
        "stop": None,  # 不设置特定的停止词
        "temperature": 0.7,  # 温度参数，控制回答的随机性/创造性，0.7是适中的值
        "top_p": 0.7,  # 控制词汇选择的多样性，与temperature配合使用
        "top_k": 50,  # 每一步只考虑概率最高的前50个词
        "frequency_penalty": 0.5,  # 降低重复词汇的概率，避免AI重复自己
        "n": 1,  # 只生成一个回答
        "response_format": {"type": "text"}  # 指定回答格式为纯文本
    }
    
    # 获取当前应该使用的API密钥
    # 系统支持两个API密钥，随机选择一个使用，增加可靠性
    st.session_state.current_api = random.randint(0, 1)
    current_api_key = st.session_state.api_key if st.session_state.current_api == 0 else st.session_state.api_key2
    
    # 设置HTTP请求头，包含认证信息和内容类型
    headers = {
        "Authorization": f"Bearer {current_api_key}",  # 使用Bearer令牌认证方式
        "Content-Type": "application/json"  # 指定请求内容为JSON格式
    }
    
    # 设置重试参数
    # 如果请求失败，系统会自动重试，提高成功率
    max_retries = 5  # 最大重试次数
    base_retry_delay = 2  # 基础重试延迟（秒）
    timeout = 180  # 请求超时时间（秒）
    
    # 开始尝试发送请求，支持多次重试
    for retry in range(max_retries + 1):
        try:
            # 显示当前尝试信息
            retry_msg = "" if retry == 0 else f"（第{retry}次重试）"
            st.info(f"正在使用API {st.session_state.current_api + 1} 发送请求...{retry_msg}")
            
            # 计算当前重试的延迟时间（指数退避策略）
            # 每次重试的等待时间会翻倍，避免对服务器造成过大压力
            current_retry_delay = base_retry_delay * (2 ** retry) if retry > 0 else 0
            
            # 发送HTTP POST请求到API服务器
            response = requests.post(API_URL, json=payload, headers=headers, timeout=timeout)
            
            # 显示API响应状态码
            st.write(f"API响应状态码: {response.status_code}")
            
            # 处理非成功状态码
            if response.status_code != 200:
                # 显示错误信息
                error_msg = f"API {st.session_state.current_api + 1} 请求失败: HTTP {response.status_code}"
                st.error(error_msg)
                
                # 切换到另一个API密钥
                # 如果一个API密钥失败，尝试使用另一个，增加成功率
                st.session_state.current_api = 1 - st.session_state.current_api
                current_api_key = st.session_state.api_key if st.session_state.current_api == 0 else st.session_state.api_key2
                headers["Authorization"] = f"Bearer {current_api_key}"
                
                # 对于服务器错误，尝试重试
                # 504是网关超时，500以上是服务器内部错误，这些情况下重试可能会成功
                if (response.status_code == 504 or response.status_code >= 500) and retry < max_retries:
                    st.warning(f"检测到服务器错误，将使用API {st.session_state.current_api + 1} 在{current_retry_delay}秒后重试...")
                    time.sleep(current_retry_delay)  # 等待一段时间后重试
                    timeout += 30  # 每次重试增加超时时间，给服务器更多处理时间
                    continue
                    
                # 尝试解析错误响应为JSON并显示
                try:
                    error_json = response.json() if response.content else {"error": "无响应内容"}
                    st.json(error_json)
                except json.JSONDecodeError:
                    # 如果无法解析为JSON，显示原始响应
                    st.error("API返回了非JSON格式的响应:")
                    st.code(response.text if response.content else "无响应内容")
                return None  # 请求失败，返回None
            
            # 确保响应状态码正常
            # 这会在状态码不是2xx时抛出异常
            response.raise_for_status()
            
            # 尝试将响应解析为JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                # 解析失败时显示错误信息
                st.error(f"无法解析API响应为JSON: {str(e)}")
                st.error("原始响应内容:")
                st.code(response.text if response.content else "无响应内容")
                return None  # 解析失败，返回None
            
            # 显示API响应详情（可展开查看）
            with st.expander("查看API响应详情"):
                st.json(response_data)
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    st.write(f"Finish Reason: {response_data['choices'][0].get('finish_reason', 'unknown')}")
                
            # 更新令牌使用统计
            # 跟踪输入、输出和总令牌数，用于计费和监控
            if "usage" in response_data:
                usage = response_data["usage"]
                st.session_state.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                st.session_state.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                st.session_state.token_usage["total_tokens"] += usage.get("total_tokens", 0)
            
            # 返回AI的回答内容
            return response_data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            # 处理请求异常（如网络错误、超时等）
            st.error(f"API请求异常: {str(e)}")
            if retry < max_retries:
                # 如果还有重试次数，等待后重试
                st.warning(f"网络请求异常，将在{current_retry_delay}秒后重试...")
                time.sleep(current_retry_delay)
                timeout += 30  # 增加超时时间
                continue
            return None  # 所有重试都失败，返回None
        except (KeyError, json.JSONDecodeError) as e:
            # 处理响应解析错误
            st.error(f"API响应解析错误: {str(e)}")
            if response and response.content:
                st.error("原始响应内容:")
                st.code(response.text)
            return None  # 解析错误，返回None
        except Exception as e:
            # 处理其他未知错误
            st.error(f"未知错误: {str(e)}")
            return None  # 未知错误，返回None

def optimize_user_input(user_prompt):
    """
    使用DeepSeek-R1-Distill-Qwen-32B模型优化用户输入的指令
    
    Args:
        user_prompt (str): 用户原始输入的指令或问题文本
        
    Returns:
        str: 优化后的指令文本，如果优化失败则返回原始输入
    """
    # 构建优化指令的系统提示
    # 这个系统提示详细说明了指令优化助手的角色和任务要求
    system_prompt = """你是一个专业的指令优化助手。你的任务是分析用户的原始指令，并将其扩展为更加详细、明确和结构化的指令。
请确保优化后的指令：
1. 保留原始指令的核心意图和目标
2. 添加必要的上下文和背景信息
3. 明确任务的具体步骤和预期输出
4. 消除歧义和模糊表述
5. 使用清晰的结构和格式
6. 必须确保是LLM可以制作的任务
7. 此AI无法上网，请确保你的指令准确无误
8. 理解用户想要真是的表达信息

请直接输出优化后的指令，不要添加解释或其他内容。"""
    
    # 构建API请求消息列表
    # 包含系统提示和用户原始指令
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt+system_prompt}
    ]
    
    # 构建API请求参数
    # 设置模型和各种生成参数
    payload = {
        "model": "Pro/deepseek-ai/DeepSeek-R1",  # 使用DeepSeek-R1模型进行指令优化
        "messages": messages,  # 包含系统提示和用户指令的消息列表
        "stream": False,  # 不使用流式输出
        "max_tokens": 4096,  # 设置回答的最大长度
        "stop": None,  # 不设置特定的停止词
        "temperature": 0.7,  # 温度参数，控制回答的随机性
        "top_p": 0.7,  # 控制词汇选择的多样性
        "top_k": 50,  # 每一步只考虑概率最高的前50个词
        "frequency_penalty": 0.5,  # 降低重复词汇的概率
        "n": 1  # 只生成一个回答
    }
    
    # 获取当前应该使用的API密钥
    # 随机选择一个API密钥，增加系统可靠性
    st.session_state.current_api = random.randint(0, 1)
    current_api_key = st.session_state.api_key if st.session_state.current_api == 0 else st.session_state.api_key2
    
    # 设置HTTP请求头
    headers = {
        "Authorization": f"Bearer {current_api_key}",  # 使用Bearer令牌认证
        "Content-Type": "application/json"  # 指定请求内容为JSON格式
    }
    
    # 设置重试参数
    # 如果请求失败，系统会自动重试
    max_retries = 3  # 最大重试次数
    base_retry_delay = 5  # 基础重试延迟（秒）
    timeout = 300  # 请求超时时间（秒）
    
    # 开始尝试发送请求，支持多次重试
    for retry in range(max_retries + 1):
        try:
            # 显示当前尝试信息
            retry_msg = "" if retry == 0 else f"（第{retry}次重试）"
            st.info(f"正在使用API {st.session_state.current_api + 1} 优化用户指令...{retry_msg}")
            
            # 计算当前重试的延迟时间（指数退避策略）
            current_retry_delay = base_retry_delay * (2 ** retry) if retry > 0 else 0
            
            # 发送HTTP POST请求到API服务器
            response = requests.post(API_URL, json=payload, headers=headers, timeout=timeout)
            
            # 处理非成功状态码
            if response.status_code != 200:
                # 显示错误信息
                error_msg = f"指令优化API请求失败: HTTP {response.status_code}"
                st.error(error_msg)
                
                # 切换到另一个API密钥
                st.session_state.current_api = 1 - st.session_state.current_api
                current_api_key = st.session_state.api_key if st.session_state.current_api == 0 else st.session_state.api_key2
                headers["Authorization"] = f"Bearer {current_api_key}"
                
                # 对于服务器错误，尝试重试
                if (response.status_code == 504 or response.status_code >= 500) and retry < max_retries:
                    st.warning(f"检测到服务器错误，将使用API {st.session_state.current_api + 1} 在{current_retry_delay}秒后重试...")
                    time.sleep(current_retry_delay)  # 等待一段时间后重试
                    timeout += 30  # 每次重试增加超时时间
                    continue
                    
                # 如果优化失败，返回原始输入
                # 确保即使优化失败，用户的请求仍然能够被处理
                st.warning("指令优化失败，将使用原始指令继续处理")
                return user_prompt
            
            # 确保响应状态码正常
            response.raise_for_status()
            
            # 尝试将响应解析为JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                # 解析失败时显示错误信息
                st.error(f"无法解析指令优化API响应为JSON: {str(e)}")
                # 如果解析失败，返回原始输入
                # 确保即使解析失败，用户的请求仍然能够被处理
                return user_prompt
            
            # 显示API响应详情（可展开查看）
            with st.expander("查看指令优化响应详情"):
                st.json(response_data)
                
            # 更新令牌使用统计
            # 跟踪输入、输出和总令牌数，用于计费和监控
            if "usage" in response_data:
                usage = response_data["usage"]
                st.session_state.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                st.session_state.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                st.session_state.token_usage["total_tokens"] += usage.get("total_tokens", 0)
            
            # 获取优化后的指令文本
            optimized_prompt = response_data["choices"][0]["message"]["content"]
            
            # 显示优化前后的对比
            # 帮助用户了解指令是如何被优化的
            with st.expander("查看指令优化前后对比"):
                st.subheader("原始指令")
                st.write(user_prompt)
                st.subheader("优化后的指令")
                st.write(optimized_prompt)
            
            # 返回优化后的指令
            return optimized_prompt
        except requests.exceptions.RequestException as e:
            # 处理请求异常（如网络错误、超时等）
            st.error(f"指令优化API请求异常: {str(e)}")
            if retry < max_retries:
                # 如果还有重试次数，等待后重试
                st.warning(f"网络请求异常，将在{current_retry_delay}秒后重试...")
                time.sleep(current_retry_delay)
                timeout += 30  # 增加超时时间
                continue
            # 如果所有重试都失败，返回原始输入
            # 确保即使所有重试都失败，用户的请求仍然能够被处理
            st.warning("指令优化失败，将使用原始指令继续处理")
            return user_prompt
        except Exception as e:
            # 处理其他未知错误
            st.error(f"指令优化过程中发生未知错误: {str(e)}")
            # 发生任何其他错误，返回原始输入
            # 确保即使发生未知错误，用户的请求仍然能够被处理
            return user_prompt

def process_qwq_response(response):
    if response:
        # 显示原始响应内容（可展开查看）
        st.expander("原始响应内容").code(response)
        
        # 处理带有思考标记的响应
        # 某些AI模型会使用</think>标记来分隔思考过程和实际回答
        if "</think>" in response:
            # 分割响应，获取实际内容部分（思考标记之后的内容）
            actual_content = response.split("</think>", 1)[1].strip()
            # 将内容按行分割，并移除空行
            lines = [p.strip() for p in actual_content.split('\n') if p.strip()]
            try:
                # 尝试从第一行获取循环次数（步骤数量）
                # 这是基于特定的响应格式，第一行应该是一个数字，表示总步骤数
                num_steps = int(lines[0])
                # 返回指定数量的步骤，跳过第一行（循环次数）
                # 这些步骤将用于后续的处理
                return lines[1:num_steps+1]
            except (ValueError, IndexError):
                # 如果无法从第一行获取有效的循环次数，显示警告并使用默认处理方式
                st.warning("无法从第一行获取有效的循环次数，将使用默认的处理方式")
                # 默认返回前10个非空行作为步骤
                return lines[:10]
        else:
            # 如果响应中没有思考标记，显示警告
            st.warning("未找到</think>标记，可能响应不完整")
            # 将内容按行分割，并移除空行
            lines = [p.strip() for p in response.strip().split('\n') if p.strip()]
            try:
                # 尝试从第一行获取循环次数
                num_steps = int(lines[0])
                # 返回指定数量的步骤，跳过第一行
                return lines[1:num_steps+1]
            except (ValueError, IndexError):
                # 如果无法获取有效的循环次数，返回前10个非空行作为步骤
                return lines[:10]
    # 如果响应为空或None，返回空列表
    return []