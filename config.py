import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = "eu-central-1"
EC2_INSTANCE_ID = "i-0c18ec623d1063fb9"  # DEINE Instance ID

# Server Configuration  
SERVER_PORT = 8000

# 4 Users mit spezifischen Configs
USERS = {
    "researcher": {
        "name": "Dr. Researcher", 
        "icon": "🔬",
        "description": "Academic research and analysis",
        "color": "#1f4e79",
        "background": "#f8f9fa",
        "temperature": 0.3,
        "max_length": 500,
        "search_priority": "academic",
        "system_prompt": """You are Dr. Researcher, a precise academic researcher. 
        Always cite sources, provide detailed explanations, and focus on factual accuracy. 
        Prefer academic and scientific sources.""",
        "use_cases": [
            "📚 Research academic papers and studies",
            "🧪 Analyze scientific data and findings", 
            "📖 Fact-check information with citations",
            "📊 Compare research methodologies",
            "🎓 Explain complex academic concepts",
            "📝 Help with literature reviews"
        ],
        "tools": ["citation_generator", "fact_checker", "academic_search"]
    },
    "student": {
        "name": "Student Sam", 
        "icon": "📚",
        "description": "Learning and education support",
        "color": "#28a745",
        "background": "#f1f8e9",
        "temperature": 0.7,
        "max_length": 300,
        "search_priority": "educational",
        "system_prompt": """You are Student Sam, a patient and encouraging tutor. 
        Explain concepts clearly with simple examples. Break down complex topics into digestible parts. 
        Always encourage learning and curiosity.""",
        "use_cases": [
            "🎓 Learn new subjects step-by-step",
            "📝 Get homework help and explanations",
            "🧠 Create study guides and summaries", 
            "❓ Ask 'explain like I'm 5' questions",
            "📊 Understand difficult concepts with examples",
            "🎯 Practice with custom quiz questions"
        ],
        "tools": ["quiz_generator", "study_notes", "difficulty_adjuster"]
    },
    "business": {
        "name": "Business Pro", 
        "icon": "💼",
        "description": "Business intelligence and strategy",
        "color": "#dc3545",
        "background": "#fff3e0",
        "temperature": 0.5,
        "max_length": 400,
        "search_priority": "business",
        "system_prompt": """You are Business Pro, a strategic business consultant. 
        Focus on actionable insights, market trends, and ROI. Provide structured, 
        data-driven advice for business decisions.""",
        "use_cases": [
            "📈 Analyze market trends and opportunities",
            "🏢 Research competitors and industry analysis",
            "💰 Evaluate business strategies and ROI",
            "📊 Create executive summaries and reports",
            "🎯 Develop marketing strategies",
            "⚖️ Assess business risks and compliance"
        ],
        "tools": ["market_analyzer", "competitor_intel", "executive_summary"]
    },
    "shopping": {
        "name": "Shopping Scout", 
        "icon": "🛍️",
        "description": "Personal shopping assistant and deal finder",
        "color": "#6f42c1",
        "background": "#f8f0ff",
        "temperature": 0.6,
        "max_length": 350,
        "search_priority": "shopping",
        "system_prompt": """You are Shopping Scout, a helpful personal shopping assistant. 
        Help users find the best products and deals. Always provide 3 specific product links 
        when users want to buy something. Focus on value, quality, and user needs.""",
        "use_cases": [
            "🛒 Find specific products with direct links",
            "💰 Compare prices across different stores",
            "⭐ Get product reviews and recommendations", 
            "🔍 Discover alternatives and similar products",
            "💳 Find current deals and discounts",
            "📱 Get shopping advice and buying guides"
        ],
        "tools": ["product_finder", "price_comparator", "deal_hunter"]
    }
}

# Database Configuration
DATABASE_NAME = "chat_history.db"

# Auto-shutdown settings
IDLE_TIMEOUT_MINUTES = 10
WARNING_TIMEOUT_MINUTES = 2