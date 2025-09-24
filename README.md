# 🤖 MultiMinds — Multi-Agent Assistant

Welcome to the **MultiMinds**! This project is a powerful and extensible framework to create and deploy collaborative, research-oriented AI agents for answering queries, automating research, and providing grounded insights. Featuring a modern Streamlit interface, web-powered answer capabilities, modular core, and containerized deployment — jumpstart your next AI agent project, research assistant, or personalized chat system!

---

## 🚀 Key Features

- **Multi-Agent Orchestration**: Combines reasoning, tool use, and web search (Tavily) — grounded, accurate, and verifiable answers
- **Interactive Frontend (Streamlit)**: Modern chat UI; configure agent mood, personality, model, and web search power on the fly
- **Solid Backend (FastAPI)**: Robust REST API for agent communication — production-ready, scalable foundation
- **Research-Driven**: Uses LangChain, LangGraph, and cloud LLMs (e.g. Llama 3 70B, 8B)
- **Easy Deployment**: Out-of-the-box Dockerfile, Jenkins pipeline and ECS-ready
- **Customizable & Modular**: Extend agents, tools, and frontend — adapt for research, education, or business tasks

---

## 🏗️ Architecture

**Simplified Flow:**
- User enters query and sets system prompt/mood in Streamlit UI
- Backend API (FastAPI) receives query, routes to multi-agent engine (LangGraph / LangChain)
- Agent(s) reason, research (Tavily web tool), and synthesize answer
- Response displayed interactively in UI

**Key Components:**
- `app/core/ai_agent.py`: Multi-agent coordination, LLM engines, web tools, and result synthesis 🔬
- `app/backend/api.py`: FastAPI backend, REST /chat endpoint 🚦
- `app/frontend/ui.py`: Streamlit chat frontend, system prompt, persona switching, query interface 💬
- `requirements.txt`, `Dockerfile`, `setup.py`: Easy install, containerization and deployment 🐋

---

## 📦 Repository Structure

```plaintext
Multi-AI-Agent-Project/
├── app/
│   ├── backend/           # FastAPI backend REST API
│   ├── common/            # Logging & error utilities
│   ├── config/            # API keys, allowed models
│   ├── core/              # Multi-agent orchestration logic
│   ├── frontend/          # Streamlit UI
│   ├── __init__.py
│   └── main.py            # Entry point: runs backend, then frontend
├── custom_jenkins/        # Jenkins automation support
├── .gitignore
├── Dockerfile             # Containerization
├── Jenkinsfile            # Pipeline: Cloning, build, SonarQube, AWS ECR/ECS deploy
├── requirements.txt
├── setup.py
```

---

## 🌟 Quick Start

### Prerequisites
- Python 3.10+
- API Keys (GROQ, TAVILY)

### Local Run
```bash
git clone https://github.com/krtanay/Multi-AI-Agent-Project.git
cd Multi-AI-Agent-Project
pip install -e .
python app/main.py
```
- Navigate to Streamlit UI at [http://localhost:8501](http://localhost:8501)

### Docker Compose
```bash
docker build -t multi-ai-agent .
docker run -p 8501:8501 -p 9999:9999 multi-ai-agent
```

### Jenkins / AWS ECS
- Use `Jenkinsfile` for CI/CD to build, scan, push Docker to AWS ECR and deploy to ECS Fargate

---

## 💡 Example Use Cases
- Custom research chatbot with evidence-based answers
- Multi-modal question answering (web + LLM)
- Internal productivity assistant for enterprises
- Academic literature review and synthesis tool
- Teaching tool with personality modes

---

## 🧩 Extending & Customization
- Add more models, tools, or agent logic in `core/`—build your custom expert agents
- Edit `frontend/ui.py` for new UI elements
- Add cloud LLMs or external tools with environment variables

---

