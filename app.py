import streamlit as st
import fitz  # PyMuPDF
import requests
import tempfile
import os
import langdetect

# 自訂 CSS：黑底白字 + ChatGPT 風格
st.markdown("""
    <style>
    body {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stApp {
        background-color: #0d1117;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #58a6ff;
    }
    .stTextArea, .stTextInput, .stSlider, .stButton button {
        background-color: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
    }
    .stButton button:hover {
        background-color: #238636;
        color: #ffffff;
    }
    .stMarkdown {
        color: #c9d1d9;
    }
    </style>
""", unsafe_allow_html=True)

# 設定 Ollama API 參數
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

# 頁面標題
st.title("📄 PDF 智能摘要 & 互動式問答 (ChatGPT 風格)")

# 上傳 PDF
uploaded_file = st.file_uploader("📤 請選擇一個 PDF 檔案", type=["pdf"])

# 使用者設定
summary_count = st.slider("✨ 設定摘要重點數量", 3, 10, 5)

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_pdf_path = tmp_file.name

    # 讀取 PDF 文字 & 頁數
    doc = fitz.open(tmp_pdf_path)
    total_pages = doc.page_count
    st.info(f"📖 PDF 頁數：{total_pages} 頁")

    all_page_texts = []
    for page in doc:
        text = page.get_text()
        all_page_texts.append(text)

    os.unlink(tmp_pdf_path)

    # 自動偵測語言
    sample_text = "".join(all_page_texts[:3])
    try:
        lang = langdetect.detect(sample_text)
    except:
        lang = "unknown"

    lang_display = "中文" if lang.startswith("zh") else "英文" if lang == "en" else "其他語言"
    st.info(f"🌐 偵測語言：{lang_display}")

    # 多頁分段摘要
    if st.button("📄 執行多頁分段摘要"):
        st.subheader("📌 分頁摘要")
        for i, page_text in enumerate(all_page_texts):
            if page_text.strip() == "":
                continue
            with st.spinner(f"第 {i+1} 頁摘要中..."):
                response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "prompt": f"請用 {summary_count} 個重點摘要以下 PDF 第 {i+1} 頁內容：\n\n{page_text}"
                    }
                )
                result = response.json()
                st.markdown(f"**第 {i+1} 頁摘要：**")
                st.write(result['response'])

    # 互動式摘要問答
    st.subheader("💬 互動式摘要問答")
    chat_question = st.text_input("📝 請輸入你想問 PDF 的問題")

    if st.button("🧠 詢問 Ollama"):
        full_text = "\n".join(all_page_texts)
        with st.spinner("Ollama 回答中..."):
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": f"這是 PDF 文件全文：\n\n{full_text}\n\n根據這份內容，回答以下問題：{chat_question}"
                }
            )
            result = response.json()
            st.markdown("**📌 回答結果：**")
            st.write(result['response'])
