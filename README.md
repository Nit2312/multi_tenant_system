# Multi-tenant Financial Advisor AI System

A sophisticated RAG-based financial advisory system that provides conversational guidance from classic finance and marketing literature. Built with Flask, LangChain, and powered by Groq's advanced language models.

## 🎯 Project Overview

This system transforms classic financial literature into an interactive, conversational AI mentor that provides strategic financial guidance. It processes PDF documents from renowned authors like Warren Buffett, Benjamin Graham, Robert Kiyosaki, and others to deliver personalized, context-aware financial advice.

## 🚀 Key Features

### 🤖 Conversational AI Interface
- **Natural Dialogue**: Senior financial mentor speaking to disciples
- **Anti-Reasoning Protection**: Prevents AI thinking process leakage
- **Context-Aware Responses**: Grounded in retrieved document sources
- **Session Management**: Chat history tracking for continuity

### 📚 Document Processing
- **Multi-Format Support**: PDF document ingestion and processing
- **Vector Storage**: ChromaDB for efficient similarity search
- **Reranking System**: Advanced document relevance scoring
- **Metadata Extraction**: Book names, authors, and content categorization

### 🎨 User Experience
- **Modern Web Interface**: Clean, responsive design
- **Real-time Metrics**: Precision@k and recall@k tracking
- **Query Classification**: Finance vs. marketing categorization
- **Book-Specific Queries**: Targeted search within specific books

## 🏗️ Architecture

### Backend Components
- **Flask API**: RESTful endpoints for chat and system management
- **LangChain Integration**: Document processing and RAG chains
- **Groq LLM**: Advanced language model for response generation
- **ChromaDB**: Vector database for document storage and retrieval

### Frontend Components
- **Modern UI**: Clean, intuitive interface
- **Real-time Chat**: WebSocket-like interaction
- **Metrics Dashboard**: Performance tracking and analytics
- **Responsive Design**: Mobile-friendly interface

## 📁 Project Structure

```
Multi_tenant_system/
├── api/
│   ├── app.py                 # Main Flask application
│   ├── answer_evaluator.py    # Response evaluation system
│   ├── query_classifier.py    # Query categorization logic
│   └── vectorstore_manager.py # Vector database operations
├── data/
│   ├── finance_documents/     # Financial literature PDFs
│   └── marketing_documents/   # Marketing literature PDFs
├── static/
│   ├── css/style.css          # Styling
│   ├── js/app.js              # Frontend JavaScript
│   └── favicon.ico            # Site icon
├── templates/
│   └── index.html             # Main web interface
├── .venv/                     # Python virtual environment
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js (for frontend development)
- Groq API key
- Astra DB credentials (optional)

### Installation Steps

1. **Clone the Repository**
```bash
git clone <repository-url>
cd Multi_tenant_system
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file with:
```env
GROQ_API_KEY=your_groq_api_key
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_NAMESPACE=your_namespace
```

5. **Document Preparation**
Place PDF documents in:
- `data/finance_documents/` - Financial literature
- `data/marketing_documents/` - Marketing literature

6. **Run the Application**
```bash
python api/app.py
```

The system will be available at `http://127.0.0.1:5000`

## 🎯 Usage Guide

### Basic Chat Interface
1. Open the web interface in your browser
2. Type your financial or marketing question
3. Receive conversational guidance from classic literature
4. View source attribution and confidence scores

### Advanced Features
- **Book-Specific Queries**: "What does Rich Dad Poor Dad teach about taxes?"
- **General Financial Advice**: "How should I start investing?"
- **Marketing Strategy**: "How to win and influence people?"

### API Endpoints
- `POST /api/chat` - Main chat endpoint
- `GET /api/status` - System status check
- `POST /api/initialize` - Initialize RAG system

## 📊 System Metrics

The system tracks comprehensive metrics:
- **Precision@k**: Relevance of retrieved documents
- **Recall@k**: Coverage of relevant documents
- **Response Grounding**: Source attribution verification
- **Processing Time**: Query response latency
- **Source Citations**: Document reference tracking

## 🧠 AI Model Configuration

### Language Model
- **Model**: OpenAI GPT-OSS-120B via Groq
- **Temperature**: 0.3 (balanced consistency and creativity)
- **Max Tokens**: 1536 (comprehensive responses)
- **Anti-Reasoning**: Built-in thinking process filtering

### Prompt Engineering
The system uses specialized prompts for:
- **Natural Conversation**: Mentor-disciple relationship
- **Source Integration**: Seamless document knowledge blending
- **Response Formatting**: Clean, structured output without lists
- **Safety Protocols**: Prevents reasoning leakage

## 🔧 Technical Implementation

### RAG Pipeline
1. **Query Classification**: Finance vs. marketing categorization
2. **Document Retrieval**: Vector similarity search with reranking
3. **Context Formatting**: Structured document preparation
4. **Response Generation**: LLM-powered answer creation
5. **Quality Assurance**: Grounding verification and metrics tracking

### Document Processing
- **PDF Parsing**: Text extraction and metadata capture
- **Chunking Strategy**: Optimal segment sizing for retrieval
- **Vectorization**: Embedding generation for similarity search
- **Indexing**: Efficient storage and retrieval system

## 🎨 Design Philosophy

### Conversational Approach
- **Natural Dialogue**: Avoids mechanical formatting
- **Mentor Tone**: Senior financial advisor perspective
- **Practical Focus**: Actionable guidance over theory
- **Context Integration**: Seamless knowledge blending

### User Experience
- **Simplicity**: Clean, intuitive interface
- **Performance**: Fast response times
- **Reliability**: Consistent, accurate responses
- **Transparency**: Source attribution and confidence scoring

## 🔒 Security & Safety

### Input Validation
- **Query Sanitization**: Prevents injection attacks
- **Response Filtering**: Removes inappropriate content
- **Rate Limiting**: Prevents system abuse
- **Error Handling**: Graceful failure management

### Data Protection
- **Session Management**: Secure user sessions
- **API Key Protection**: Environment variable storage
- **Logging**: Comprehensive audit trails
- **Privacy**: No personal data storage

## 📈 Performance Optimization

### Retrieval Efficiency
- **Vector Indexing**: Fast similarity search
- **Reranking**: Improved relevance scoring
- **Caching**: Reduced processing time
- **Batch Processing**: Optimized document handling

### Response Quality
- **Grounding Verification**: Source-based accuracy
- **Metrics Tracking**: Continuous improvement
- **Prompt Optimization**: Enhanced response generation
- **Model Tuning**: Balanced parameters

## 🔄 Development Workflow

### Adding New Documents
1. Place PDFs in appropriate data directory
2. Restart the application
3. Documents automatically processed and indexed
4. Available for immediate querying

### System Updates
- **Model Updates**: Change LLM parameters in `app.py`
- **Prompt Improvements**: Modify templates in `load_and_process_data()`
- **Metric Adjustments**: Update evaluation criteria
- **UI Changes**: Modify frontend files in `static/` and `templates/`

## 🐛 Troubleshooting

### Common Issues
- **Port Conflicts**: Change port or stop conflicting services
- **API Errors**: Verify Groq API key and network connectivity
- **Document Processing**: Check PDF file formats and permissions
- **Memory Issues**: Monitor system resources and adjust chunk sizes

### Debug Mode
Enable debug logging by setting:
```python
app.run(debug=True)
```

## 📝 Contributing

### Development Guidelines
- Follow existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for API changes
- Maintain backward compatibility

### Feature Requests
- Submit issues with detailed descriptions
- Provide use cases and expected outcomes
- Include relevant documentation or examples

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For technical support or questions:
- Review the troubleshooting section
- Check system logs for error details
- Verify environment configuration
- Contact development team for assistance

---

**Built with ❤️ for financial education and empowerment**
