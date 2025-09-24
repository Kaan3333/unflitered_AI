import streamlit as st
import time
from datetime import datetime
import requests

from config import USERS, EC2_INSTANCE_ID, AWS_REGION, SERVER_PORT
from aws_manager import AWSInstanceManager
from llm_client import LLMClient, get_server_url
from database import DatabaseManager

# Page config
st.set_page_config(
    page_title="🚀 AI Multi-Assistant Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_user_theme(username):
    """Apply user-specific theme"""
    user_config = USERS[username]
    
    theme_css = f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {user_config['background']} 0%, #ffffff 100%);
    }}
    
    .user-header {{
        background: {user_config['color']};
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }}
    
    .stButton > button {{
        background-color: {user_config['color']};
        color: white;
        border: none;
        border-radius: 20px;
        transition: all 0.3s;
    }}
    
    .stButton > button:hover {{
        background-color: {user_config['color']}dd;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    .use-case-card {{
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid {user_config['color']};
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .metric-card {{
        background: {user_config['color']}22;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }}
    
    .search-result {{
        background: #f8f9fa;
        border: 1px solid {user_config['color']}44;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    .shopping-link {{
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white !important;
        padding: 10px 20px;
        border-radius: 25px;
        text-decoration: none;
        display: inline-block;
        margin: 5px;
        transition: transform 0.3s;
    }}
    
    .shopping-link:hover {{
        transform: scale(1.05);
        text-decoration: none;
        color: white !important;
    }}
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

def show_login():
    """Enhanced login with use cases preview"""
    st.title("🚀 AI Multi-Assistant Platform")
    
    st.markdown("""
    ### 🌟 Choose Your AI Assistant
    
    Each assistant is specialized for different tasks and has unique capabilities:
    """)
    
    # Create 2x2 grid for 4 users
    col1, col2 = st.columns(2)
    
    users_list = list(USERS.items())
    
    # First row
    with col1:
        show_user_card(users_list[0])
    with col2:
        show_user_card(users_list[1])
    
    # Second row
    col3, col4 = st.columns(2)
    with col3:
        show_user_card(users_list[2])
    with col4:
        show_user_card(users_list[3])

def show_user_card(user_data):
    """Show enhanced user card with use cases"""
    username, user_info = user_data
    
    with st.container():
        st.markdown(f"""
        <div style="
            border: 2px solid {user_info['color']}; 
            border-radius: 15px; 
            padding: 20px; 
            margin: 10px 0;
            background: {user_info['background']};
            text-align: center;
        ">
            <div style="font-size: 64px; margin-bottom: 10px;">{user_info['icon']}</div>
            <h3 style="color: {user_info['color']}; margin-bottom: 5px;">{user_info['name']}</h3>
            <p style="color: #666; font-style: italic; margin-bottom: 15px;">{user_info['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Use Cases Preview
        with st.expander(f"💡 See what {user_info['name']} can do"):
            for use_case in user_info['use_cases'][:3]:  # Show first 3
                st.markdown(f"• {use_case}")
            st.markdown(f"*...and {len(user_info['use_cases'])-3} more capabilities!*")
        
        if st.button(f"🚀 Start with {user_info['name']}", 
                    key=username, 
                    use_container_width=True):
            login_user(username, user_info)

def login_user(username, user_info):
    """Handle user login"""
    # Set session state
    st.session_state.logged_in = True
    st.session_state.username = username
    
    # Create/get user in database
    st.session_state.user_id = st.session_state.db_manager.create_or_get_user(
        username=username,
        display_name=user_info['name'],
        icon=user_info['icon'],
        description=user_info['description']
    )
    
    # Get/create conversation
    st.session_state.conversation_id = st.session_state.db_manager.get_or_create_conversation(
        st.session_state.user_id
    )
    
    # Load existing messages
    st.session_state.messages = st.session_state.db_manager.get_conversation_messages(
        st.session_state.conversation_id
    )
    
    st.rerun()

def show_sidebar():
    """Enhanced sidebar with user-specific tools"""
    with st.sidebar:
        user_data = USERS[st.session_state.username]
        
        # User Header with Theme
        st.markdown(f"""
        <div class="user-header">
            <div style="font-size: 48px;">{user_data['icon']}</div>
            <h3>{user_data['name']}</h3>
            <p style="margin: 0; opacity: 0.9;">{user_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Switch Assistant", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        
        # User-Specific Use Cases
        show_use_cases()
        
        st.divider()
        
        # User-Specific Tools
        show_user_tools()
        
        st.divider()
        
        # AWS Instance Control
        show_instance_control()
        
        st.divider()
        
        # User Statistics
        show_user_stats()

def show_use_cases():
    """Show user-specific use cases"""
    user_data = USERS[st.session_state.username]
    
    st.markdown("### 💡 What I can help you with:")
    
    for use_case in user_data['use_cases']:
        st.markdown(f"""
        <div class="use-case-card">
            {use_case}
        </div>
        """, unsafe_allow_html=True)

def show_user_tools():
    """Show user-specific tools"""
    user = st.session_state.username
    
    st.markdown("### 🛠️ My Special Tools")
    
    if user == "researcher":
        if st.button("📚 Generate Citation", use_container_width=True):
            st.info("📖 Citation generator activated! Ask me to cite any source.")
            
        if st.button("✅ Fact-Check Mode", use_container_width=True):
            st.session_state.fact_check_mode = True
            st.success("🔍 Fact-checking mode enabled!")
            
        if st.button("🔬 Academic Search", use_container_width=True):
            st.info("🎓 Academic search prioritized! I'll focus on scholarly sources.")
    
    elif user == "student":
        difficulty = st.select_slider(
            "🎯 Explanation Level:",
            options=["Beginner", "Intermediate", "Advanced"],
            value="Intermediate"
        )
        st.session_state.explanation_level = difficulty
        
        if st.button("🧠 Create Quiz", use_container_width=True):
            st.info("📝 Quiz mode activated! I'll create questions about our topics.")
            
        if st.button("📋 Study Notes", use_container_width=True):
            st.info("📖 Study notes mode! I'll summarize key points for studying.")
    
    elif user == "business":
        if st.button("📊 Market Analysis", use_container_width=True):
            st.info("📈 Market analysis mode! I'll focus on trends and data.")
            
        if st.button("🏢 Competitor Research", use_container_width=True):
            st.session_state.competitor_mode = True
            st.success("🔍 Competitor research mode enabled!")
            
        if st.button("📋 Executive Summary", use_container_width=True):
            st.info("💼 Executive summary mode! I'll provide structured insights.")
    
    elif user == "shopping":
        price_range = st.select_slider(
            "💰 Budget Range:",
            options=["Budget", "Mid-Range", "Premium", "No Limit"],
            value="Mid-Range"
        )
        st.session_state.price_range = price_range
        
        if st.button("🔍 Product Finder", use_container_width=True):
            st.info("🛒 Product finder activated! Tell me what you want to buy.")
            
        if st.button("💰 Deal Hunter", use_container_width=True):
            st.session_state.deal_mode = True
            st.success("🏷️ Deal hunting mode! I'll find the best prices.")
            
        if st.button("⭐ Review Analyzer", use_container_width=True):
            st.info("📊 Review analyzer ready! I'll summarize product reviews.")

def show_main_chat():
    """Enhanced main chat with user-specific features"""
    user_data = USERS[st.session_state.username]
    
    # Apply user theme
    apply_user_theme(st.session_state.username)
    
    # Title with user branding
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>{user_data['icon']} {user_data['name']} Assistant</h1>
        <p style="font-size: 1.2em; color: {user_data['color']};">
            {user_data['description']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check instance status
    status = st.session_state.aws_manager.get_status()
    public_ip = st.session_state.aws_manager.get_public_ip()
    
    if status != "running":
        st.warning("""
        🚨 **GPU Instance is not running!**
        
        Please start the instance using the sidebar controls to begin our conversation.
        """)
        return
    
    if not public_ip:
        st.error("Cannot get instance IP address. Please check AWS connection.")
        return
    
    # Check server health
    server_url = get_server_url(public_ip, SERVER_PORT)
    llm_client = LLMClient(server_url)
    
    if not llm_client.is_server_healthy():
        st.warning(f"""
        🟡 **{user_data['name']} is waking up...**
        
        The AI model is loading. This takes 3-5 minutes after instance start.
        """)
        
        if st.button("🔄 Check Status"):
            st.rerun()
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message("user" if message["is_user"] else "assistant"):
            st.markdown(message["content"])
            
            # Enhanced search results display for shopping
            if not message["is_user"] and message["search_results"]:
                show_enhanced_search_results(message["search_results"])
    
    # Enhanced chat input with user-specific placeholder
    chat_placeholder = get_chat_placeholder(st.session_state.username)
    
    if prompt := st.chat_input(chat_placeholder):
        handle_user_input(prompt, llm_client)

def get_chat_placeholder(username):
    """Get user-specific chat placeholder"""
    placeholders = {
        "researcher": "Ask me about research, studies, or academic topics...",
        "student": "What would you like to learn about today?",
        "business": "Ask me about market trends, business strategy, or analysis...",
        "shopping": "Tell me what you want to buy, and I'll find it for you!"
    }
    return placeholders.get(username, "How can I help you today?")

def show_enhanced_search_results(search_results):
    """Enhanced search results display with shopping links"""
    if not search_results:
        return
    
    # Separate shopping results from general results
    shopping_results = [r for r in search_results if r.get('type') == 'product_link']
    general_results = [r for r in search_results if r.get('type') != 'product_link']
    
    if shopping_results:
        st.markdown("### 🛒 Shopping Links")
        
        # Display shopping results as attractive buttons
        cols = st.columns(len(shopping_results))
        for i, result in enumerate(shopping_results):
            with cols[i]:
                site_name = result.get('site', 'Shop')
                st.markdown(f"""
                <a href="{result['url']}" target="_blank" class="shopping-link">
                    🛍️ {site_name}<br>
                    <small>{result['title'][:30]}...</small>
                </a>
                """, unsafe_allow_html=True)
    
    if general_results:
        with st.expander(f"🔍 Additional Sources ({len(general_results)} found)", expanded=False):
            for i, result in enumerate(general_results, 1):
                st.markdown(f"""
                <div class="search-result">
                    <strong>{i}. {result['title']}</strong> ({result['source']})
                    <br><br>
                    {result['snippet']}
                    <br><br>
                    🔗 <a href="{result['url']}" target="_blank">View Source</a>
                </div>
                """, unsafe_allow_html=True)

def handle_user_input(prompt: str, llm_client: LLMClient):
    """Enhanced user input handling with user-specific processing"""
    user_config = USERS[st.session_state.username]
    
    # Add user message to chat
    st.session_state.messages.append({
        "is_user": True,
        "content": prompt,
        "search_results": [],
        "search_used": False
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate AI response with user-specific processing
    with st.chat_message("assistant"):
        spinner_text = get_spinner_text(st.session_state.username, prompt)
        
        with st.spinner(spinner_text):
            try:
                # Enhanced prompt with user-specific context
                enhanced_prompt = build_enhanced_prompt(prompt, st.session_state.username)
                
                # Call LLM API
                response_data = llm_client.generate_text(
                    prompt=enhanced_prompt,
                    user_type=st.session_state.username, # <--- DIESE ZEILE HINZUFÜGEN
                    max_length=user_config["max_length"],
                    temperature=user_config["temperature"],
                    search_enabled=True
                )
                
                response = response_data["response"]
                search_results = response_data.get("search_results", [])
                search_used = response_data.get("search_used", False)
                
                # Post-process response for shopping user
                if st.session_state.username == "shopping" and search_results:
                    response = enhance_shopping_response(response, search_results)
                
                # Display response
                st.markdown(response)
                
                # Show enhanced search results
                if search_results:
                    show_enhanced_search_results(search_results)
                
                # Save to database
                save_conversation(prompt, response, search_results, search_used)
                
            except Exception as e:
                show_error_message(str(e), st.session_state.username)

def get_spinner_text(username, prompt):
    """Get user-specific spinner text"""
    spinner_texts = {
        "researcher": "🔬 Researching academic sources and analyzing data...",
        "student": "📚 Finding the best way to explain this concept...",
        "business": "📊 Analyzing market trends and business insights...",
        "shopping": "🛍️ Searching for the best products and deals..."
    }
    
    # Special cases for shopping
    if username == "shopping":
        buy_keywords = ['kaufen', 'bestellen', 'buy', 'purchase']
        if any(keyword in prompt.lower() for keyword in buy_keywords):
            return "🛒 Finding the best shopping links for you..."
    
    return spinner_texts.get(username, "🤖 Thinking and searching...")

def build_enhanced_prompt(prompt, username):
    """Build user-specific enhanced prompt"""
    user_config = USERS[username]
    system_prompt = user_config["system_prompt"]
    
    # Add special context for shopping
    if username == "shopping":
        shopping_context = """
        IMPORTANT: When users want to buy something, always provide exactly 3 specific product links in your response.
        Format shopping recommendations like this:
        
        "Here are 3 great options for [product]:
        
        1. [Product name] - [Brief description]
        2. [Product name] - [Brief description]  
        3. [Product name] - [Brief description]
        
        You'll find the direct shopping links below my response!"
        """
        system_prompt += f"\n\n{shopping_context}"
    
    # Add context from session state
    context_additions = []
    
    if hasattr(st.session_state, 'explanation_level'):
        context_additions.append(f"Explanation level: {st.session_state.explanation_level}")
    
    if hasattr(st.session_state, 'price_range'):
        context_additions.append(f"Budget preference: {st.session_state.price_range}")
    
    if hasattr(st.session_state, 'fact_check_mode') and st.session_state.fact_check_mode:
        context_additions.append("FACT-CHECK MODE: Extra focus on source verification")
    
    if hasattr(st.session_state, 'deal_mode') and st.session_state.deal_mode:
        context_additions.append("DEAL MODE: Focus on finding best prices and discounts")
    
    context = "\n".join(context_additions)
    if context:
        system_prompt += f"\n\nCurrent context: {context}"
    
    return f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

def enhance_shopping_response(response, search_results):
    """Enhance shopping response with product count"""
    shopping_results = [r for r in search_results if r.get('type') == 'product_link']
    
    if shopping_results:
        count = len(shopping_results)
        enhancement = f"\n\n✅ **Found {count} shopping option{'s' if count != 1 else ''} for you!** Check the shopping links below."
        return response + enhancement
    
    return response

def save_conversation(prompt, response, search_results, search_used):
    """Save conversation to database"""
    # Save user message
    st.session_state.db_manager.save_message(
        st.session_state.conversation_id,
        is_user=True,
        content=prompt
    )
    
    # Save assistant message
    st.session_state.db_manager.save_message(
        st.session_state.conversation_id,
        is_user=False,
        content=response,
        search_results=search_results,
        search_used=search_used
    )
    
    # Add to session messages
    st.session_state.messages.extend([
        {
            "is_user": False,
            "content": response,
            "search_results": search_results,
            "search_used": search_used
        }
    ])

def show_error_message(error_str, username):
    """Show user-specific error message"""
    user_data = USERS[username]
    
    st.error(f"""
    ❌ **{user_data['name']} encountered an issue:** {error_str}
    
    **Troubleshooting:**
    - Make sure the GPU instance is running
    - Wait for the server to fully initialize (3-5 minutes)
    - Check your internet connection
    """)

def show_instance_control():
    """Instance control (same as before but with enhanced styling)"""
    st.markdown("### 🖥️ GPU Instance Control")
    
    aws_manager = st.session_state.aws_manager
    
    try:
        with st.spinner("Checking instance status..."):
            status = aws_manager.get_status()
            public_ip = aws_manager.get_public_ip()
        
        # Status display with better styling
        status_colors = {
            "running": "🟢",
            "stopped": "🔴", 
            "stopping": "🟡",
            "starting": "🟡",
            "pending": "🟡"
        }
        
        status_color = status_colors.get(status, "⚪")
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>{status_color} Status: {status.upper()}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if public_ip and status == "running":
            st.success(f"🌐 **Server IP:** {public_ip}")
            
            # Check server health
            server_url = get_server_url(public_ip, SERVER_PORT)
            llm_client = LLMClient(server_url)
            
            if llm_client.is_server_healthy():
                st.success("✅ AI Assistant Ready!")
            else:
                st.warning("⏳ AI Assistant Loading...")
        
        # Control buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 START", 
                        disabled=(status in ["running", "starting", "pending"]), 
                        use_container_width=True):
                try:
                    new_ip = aws_manager.start_instance()
                    st.success(f"Instance started! IP: {new_ip}")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Start failed: {e}")
        
        with col2:
            if st.button("⏹️ STOP", 
                        disabled=(status in ["stopped", "stopping"]),
                        use_container_width=True):
                try:
                    aws_manager.stop_instance()
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Stop failed: {e}")
        
        # Auto-shutdown info with better styling
        if status == "running" and public_ip:
            show_auto_shutdown_info(public_ip)
    
    except Exception as e:
        st.error(f"Cannot connect to AWS: {e}")

def show_auto_shutdown_info(public_ip):
    """Show auto-shutdown information"""
    server_url = get_server_url(public_ip, SERVER_PORT)
    llm_client = LLMClient(server_url)
    server_status = llm_client.get_server_status()
    
    if server_status:
        shutdown_in = max(0, server_status.get("shutdown_in_seconds", 0))
        
        if shutdown_in > 0:
            minutes = int(shutdown_in // 60)
            seconds = int(shutdown_in % 60)
            st.info(f"⏰ Auto-shutdown: {minutes}m {seconds}s")
        else:
            st.warning("⚠️ May shutdown soon!")
            
        if st.button("🔄 Reset Timer", use_container_width=True):
            llm_client.is_server_healthy()
            st.success("Timer reset!")
            time.sleep(1)
            st.rerun()

def show_user_stats():
    """Enhanced user statistics"""
    st.markdown("### 📊 Your Statistics")
    
    try:
        stats = st.session_state.db_manager.get_user_stats(st.session_state.user_id)
        user_data = USERS[st.session_state.username]
        
        # Enhanced metrics display
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['message_count']}</h3>
                <p>Messages</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['search_count']}</h3>
                <p>Searches</p>
            </div>
            """, unsafe_allow_html=True)
        
        if stats["last_activity"]:
            last_activity = datetime.fromisoformat(stats["last_activity"].replace('Z', '+00:00'))
            st.markdown(f"**Last Active:** {last_activity.strftime('%Y-%m-%d %H:%M')}")
        
        # User-specific stats
        if st.session_state.username == "shopping":
            # Could add shopping-specific metrics here
            st.markdown("🛒 **Shopping Assistant Stats**")
        
    except Exception as e:
        st.error(f"Cannot load stats: {e}")

# Initialize session state
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'aws_manager' not in st.session_state:
        st.session_state.aws_manager = AWSInstanceManager(EC2_INSTANCE_ID, AWS_REGION)
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()

def main():
    """Main application with enhanced 4-user system"""
    init_session_state()
    
    if not st.session_state.logged_in:
        show_login()
    else:
        show_sidebar()
        show_main_chat()

if __name__ == "__main__":
    main()