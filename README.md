# Jarvus Agent Platform – Your AI Co-Founder

> An intelligent AI agent system that serves as your third co-founder, capable of complex task execution, memory management, and seamless integration with your digital workspace.

## 🎯 What It Does

Jarvus is an advanced AI agent platform that transforms how you interact with your digital environment. It combines powerful language models with sophisticated memory systems, browser automation, and workflow orchestration to create a truly intelligent assistant that learns from your interactions and adapts to your needs.

**Real-world problems it solves:**
- **Task Automation**: Automatically handles complex multi-step workflows across web applications
- **Memory & Context**: Remembers your preferences, past interactions, and work patterns
- **Browser Intelligence**: Seamlessly controls web browsers to perform tasks on your behalf
- **Workflow Orchestration**: Plans and executes complex sequences of actions with error handling
- **Integration Hub**: Connects with Google Workspace, calendars, email, and other productivity tools

**Who it's for:**
- **Knowledge Workers**: Researchers, writers, analysts who need intelligent assistance
- **Developers**: Engineers who want to automate repetitive development tasks
- **Business Professionals**: Executives and managers who need workflow automation
- **Content Creators**: Writers, designers, marketers who work across multiple platforms

**Why it matters:**
Jarvus represents the next evolution of AI assistants - moving beyond simple chat interfaces to become a true digital co-founder that understands your context, learns your patterns, and executes complex tasks autonomously.

## ⚙️ Features

### 🤖 **Multi-Agent Architecture**
- **Planning Agent**: Breaks down complex tasks into executable steps
- **Execution Agent**: Handles tool calls and task execution with error recovery
- **Validation Agent**: Ensures results meet success criteria and quality standards
- **Memory Agent**: Manages context, learning, and knowledge retention

### 🧠 **Advanced Memory System**
- **Episodic Memory**: Stores specific interactions and experiences
- **Semantic Memory**: Captures facts, preferences, and learned knowledge
- **Procedural Memory**: Remembers workflows and "how-to" procedures
- **Hierarchical Memory**: Contextual decision-making and influence management
- **Vector Search**: Semantic similarity search across all memory types

### 🌐 **Browser Automation**
- **Chrome Integration**: Full browser control via Electron desktop app
- **Web Scraping**: Intelligent content extraction and form filling
- **Tab Management**: Multi-tab workflows and navigation
- **JavaScript Execution**: Dynamic page interaction and automation
- **Screenshot Capture**: Visual feedback and documentation

### 🔧 **Tool Integration**
- **Google Workspace**: Docs, Sheets, Slides, Drive, Gmail, Calendar
- **OAuth Integration**: Secure authentication with multiple services
- **Pipedream MCP**: Model Context Protocol for tool discovery
- **Custom Tools**: Extensible tool registry for specialized workflows

### 📊 **Workflow Orchestration**
- **Multi-step Execution**: Complex task planning and execution
- **Error Handling**: Automatic retry and fallback mechanisms
- **Progress Tracking**: Real-time status updates and monitoring
- **Result Validation**: Quality assurance and success criteria checking

### 🔐 **Security & Privacy**
- **Local Processing**: Desktop app for sensitive browser operations
- **OAuth Security**: Secure token management and refresh
- **Memory Encryption**: Encrypted storage of user data and preferences
- **Access Control**: User-based tool permissions and data isolation


### **Data Flow**
1. **User Input** → Web app or desktop interface
2. **Agent Planning** → LLM analyzes task and creates execution plan
3. **Memory Context** → Retrieves relevant past interactions and knowledge
4. **Tool Selection** → Chooses appropriate tools for task execution
5. **Execution** → Orchestrates multi-step workflow with error handling
6. **Validation** → Ensures results meet quality standards
7. **Memory Storage** → Updates memory with new learnings and experiences

## 🛠️ Tech Stack

### **Backend**
- **Framework**: Flask 3.1.0 with SQLAlchemy 2.0
- **Database**: SQL Server (Azure) + ChromaDB (Vector Search)
- **Authentication**: Flask-Login with OAuth2 integration
- **API**: RESTful endpoints with JSON-RPC for MCP

### **AI & LLM**
- **Primary**: Azure AI Inference (OpenAI-compatible)
- **Memory**: Sentence Transformers for semantic embeddings
- **Vector Search**: ChromaDB with scikit-learn similarity

### **Frontend & Desktop**
- **Web UI**: Flask templates with Bootstrap
- **Desktop App**: Electron with Express.js API server
- **Browser Control**: Playwright for automation
- **Real-time**: WebSocket for live updates

### **Infrastructure**
- **Cloud**: Azure App Service with SQL Database
- **Deployment**: GitHub Actions CI/CD pipeline
- **Monitoring**: Azure Application Insights
- **Security**: Azure Key Vault for secrets management

### **Development Tools**
- **Database Migrations**: Alembic
- **Testing**: pytest with comprehensive test suite
- **Code Quality**: flake8 linting
- **Documentation**: MkDocs with technical specs

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- Node.js 18+ (for desktop app)
- Azure SQL Database
- Azure AI Service

### **1. Clone & Setup**
```bash
git clone https://github.com/marismith79/Jarvus2 jarvus
cd jarvus
make virtualenv
source .venv/bin/activate
make install
```

### **2. Environment Configuration**
Create a `.env` file:
```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key
FLASK_SECRET_KEY=your-flask-secret

# Azure SQL Database
AZURE_SQL_CONNECTION_STRING="mssql+pyodbc://user:pass@server.database.windows.net:1433/db?driver=ODBC+Driver+18+for+SQL+Server&encrypt=yes&TrustServerCertificate=yes"

# Azure AI Service
AZURE_AI_FOUNDRY_KEY=your-openai-key
AZURE_AI_FOUNDRY_ENDPOINT=https://your-resource.openai.azure.com
AZURE_AI_FOUNDRY_API_VERSION=2024-02-15-preview
AZURE_AI_FOUNDRY_DEPLOYMENT_NAME=your-model-name

# OAuth Configuration
PIPEDREAM_REDIRECT_URI=http://localhost:5001/pipedream/callback
PIPEDREAM_DOCS_OAUTH_APP_ID=your-pipedream-app-id
# ... additional OAuth app IDs
```

### **3. Database Setup**
```bash
# Initialize database
jarvus create-db

# Apply migrations
make migrations

# Add admin user
jarvus add-user -u admin -p your-password
```

### **4. Start the Application**
```bash
# Development mode with auto-reload
python run_dev.py

# Or production mode
jarvus run
```

### **5. Desktop App (Optional)**
```bash
cd jarvus_desktop
npm install
npm start
```

### **6. Access the Platform**
- **Web Interface**: http://localhost:5001
- **Admin Panel**: http://localhost:5001/admin/
- **API Endpoints**: http://localhost:5001/api/v1/

## 📖 Usage Examples

### **Basic Chat Interaction**
```python
# Send a message to your agent
POST /chatbot/send
{
  "message": "Create a Google Doc summarizing today's meeting notes",
  "agent_id": 1
}
```

### **Workflow Execution**
```python
# Execute a complex workflow
POST /workflows/execute
{
  "workflow": {
    "steps": [
      {"action": "search_web", "query": "latest AI research papers"},
      {"action": "create_document", "template": "research_summary"},
      {"action": "schedule_meeting", "topic": "AI research review"}
    ]
  }
}
```

### **Memory Management**
```python
# Store important information
POST /memory/store
{
  "memory_type": "fact",
  "content": "User prefers dark mode interfaces",
  "importance": 0.8
}

# Retrieve contextual memories
GET /memory/search?query=user preferences&context=interface
```

## 🚀 Deployment

### **Azure Deployment**
The project includes automated deployment via GitHub Actions:

1. **Push to main branch** triggers automatic deployment
2. **Azure App Service** hosts the Flask application
3. **Azure SQL Database** provides persistent storage
4. **Azure Key Vault** manages secrets and configuration

### **Local Production Setup**
```bash
# Set production environment
export FLASK_ENV=production
export AZURE_SQL_CONNECTION_STRING="your_production_connection"

# Apply migrations
make migrations

# Start production server
gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
```

## 📚 Documentation

- **[Memory System](documentation/memory/MEMORY_SYSTEM.md)**: Detailed memory architecture
- **[Browser API](BROWSER_API_ARCHITECTURE.md)**: Browser automation architecture
- **[Desktop App](jarvus_desktop/README.md)**: Electron app documentation
- **[Development Plan](documentation/general/MVP_DEV_PLAN.md)**: Project roadmap

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Azure AI Services** for powerful language model capabilities
- **Pipedream** for seamless tool integration via MCP
- **Playwright** for robust browser automation
- **ChromaDB** for efficient vector search and storage

---

**Jarvus** - Your AI co-founder that never sleeps, never forgets, and always learns. 🚀