import streamlit as st
from log_analyzer import analyze_logs, redact_secrets, extract_error_lines

st.set_page_config(page_title="AI DevOps Log Analyzer", page_icon="🔎", layout="wide")

st.title("🔎 AI DevOps Log Analyzer")
st.caption("Analyze Linux, Docker, and Kubernetes logs using a locally running open-weight AI model.")

with st.sidebar:
    st.header("Settings")
    model = st.text_input("Ollama model", value="qwen2.5:3b")
    st.caption("Make sure this model is installed with `ollama pull qwen2.5:3b`.")
    st.markdown("---")
    st.markdown("**Privacy:** Logs are sent to your configured local Ollama service. Avoid exposing this app publicly without authentication and additional security controls.")

uploaded = st.file_uploader("Upload a log file", type=["log", "txt"])
default_text = """2026-10-13T10:15:01Z ERROR Database connection failed: connection refused
2026-10-13T10:15:02Z ERROR Connection timeout after 30 seconds
2026-10-13T10:15:03Z WARN Retrying database connection (attempt 2)
2026-10-13T10:15:04Z ERROR payment-api: readiness probe failed
"""
if uploaded is not None:
    try:
        log_text = uploaded.getvalue().decode("utf-8", errors="replace")
    except Exception as exc:
        st.error(f"Could not read uploaded file: {exc}")
        log_text = ""
else:
    log_text = default_text

log_text = st.text_area("Or paste logs here", value=log_text, height=260, help="Remove sensitive information before submitting logs.")

col1, col2 = st.columns([1, 1])
with col1:
    max_chars = st.slider("Maximum characters to analyze", min_value=2000, max_value=30000, value=12000, step=1000)
with col2:
    st.write("")
    st.write("")
    analyze_button = st.button("Analyze logs", type="primary", use_container_width=True)

if analyze_button:
    if not log_text.strip():
        st.warning("Paste or upload some logs first.")
    else:
        safe_text = redact_secrets(log_text)
        if len(safe_text) > max_chars:
            safe_text = safe_text[-max_chars:]
            st.info(f"Input trimmed to the last {max_chars:,} characters.")
        with st.expander("Preview of redacted logs"):
            st.code(safe_text, language="text")
        with st.spinner("Analyzing with your local Ollama model..."):
            result = analyze_logs(safe_text, model=model)
        if result["ok"]:
            st.subheader("Analysis report")
            st.markdown(result["analysis"])
            st.download_button(
                "Download report",
                data=result["analysis"],
                file_name="devops-log-analysis.md",
                mime="text/markdown",
            )
            with st.expander("Detected error and warning lines"):
                lines = extract_error_lines(safe_text)
                if lines:
                    st.code("\n".join(lines), language="text")
                else:
                    st.write("No obvious ERROR/WARN/FATAL lines detected.")
        else:
            st.error(result["error"])
            st.markdown("Check that Ollama is running and the selected model is installed.")
            st.code("ollama serve\nollama pull qwen2.5:3b")
else:
    st.info("A sample log is loaded. Click **Analyze logs** to try the application.")
