import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import zipfile
import io
import tempfile
import shutil
from pathlib import Path
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="CraftiQ",
    page_icon="images/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configure Google AI
@st.cache_resource
def setup_ai():
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    return genai.GenerativeModel(
        "gemini-2.5-flash", 
        generation_config={"response_mime_type": "application/json"}
    )

def create_file_structure(files_data):
    """Create files and return as zip buffer"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        for file_info in files_data:
            file_path = Path(temp_dir) / file_info['path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info['content'])
        
        # Create zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        return zip_buffer
    
    finally:
        shutil.rmtree(temp_dir)

def generate_website_files(query: str, model):
    """Generate website files based on user query"""
    
    GENERATION_PROMPT = f"""
    Based on the user query: "{query}", generate a complete, professional website with all necessary files.
    
    Create a modern, responsive website with:
    - HTML files (semantic, accessible)
    - CSS files (modern styling, responsive design)
    - JavaScript files (if needed for functionality)
    - Include meta tags, proper structure
    
    Make the website:
    - Fully functional and interactive
    - Mobile responsive
    - Modern design with good UX
    - Fast loading
    - Accessible (proper ARIA labels, alt texts)
    - SEO friendly
    
    Return the response in this exact JSON format:
    {{
        "project_name": "descriptive_project_name",
        "description": "Brief description of the website",
        "features": ["list", "of", "key", "features"],
        "files": [
            {{
                "path": "index.html",
                "content": "complete HTML content with proper structure"
            }},
            {{
                "path": "css/style.css", 
                "content": "complete CSS with modern styling and responsive design"
            }},
            {{
                "path": "js/script.js",
                "content": "complete JavaScript for functionality"
            }}
        ]
    }}
    
    Ensure all files are complete, functional, and production-ready.
    """
    
    try:
        with st.spinner('AI is generating your website...'):
            response = model.generate_content(GENERATION_PROMPT)
            return json.loads(response.text)
    except Exception as e:
        st.error(f"Generation failed: {str(e)}")
        return {"error": str(e)}

def main():
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #ff4b4b 0%, #e63946 50%, #dc2626 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }

    .feature-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
    }
    
    .generated-info {
       border-left: none;
    }
    
    .success-message {
        background: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        color: #155724;
        margin: 1rem 0;
    }
    
    .scroll-message {
        color: #666;
        text-align: center;
        margin: 1rem 0;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">CraftiQ</h1>', unsafe_allow_html=True)
    st.markdown("### AI magic that turns ideas into websites✨")
    
    # Initialize session state
    if 'generated_data' not in st.session_state:
        st.session_state.generated_data = None
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'show_scroll_message' not in st.session_state:
        st.session_state.show_scroll_message = False
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("## 🚀 Features")
        st.markdown("""
        - **AI-Powered Generation**: Creates complete websites from descriptions
        - **Modern Design**: Responsive, mobile-friendly layouts
        - **Full Stack**: HTML, CSS, JavaScript files
        - **Download Ready**: Get all files as ZIP
        - **No Coding Required**: Just describe what you want!
        """)
        
        st.markdown("## 💡 Example Queries")
        example_queries = [
            "Create a portfolio website for a web developer",
            "Build a restaurant menu with online ordering",
            "Make a todo app with dark theme",
            "Design a blog website for travel stories",
            "Create a landing page for a tech startup"
        ]
        
        for query in example_queries:
            if st.button(f"📝 {query}", key=f"example_{hash(query)}"):
                st.session_state.current_query = query
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📝 Describe Your Website")
        
        # Text area for user input
        user_query = st.text_area(
            "What kind of website do you want to create?",
            value=st.session_state.current_query,
            height=150,
            placeholder="e.g., Create a modern portfolio website for a photographer with gallery, about page, and contact form. Use dark theme with elegant animations.",
            help="Be as detailed as possible. Mention colors, features, pages, functionality, etc.",
            key="user_query_input"
        )
        
        # Update session state when user types
        if user_query != st.session_state.current_query:
            st.session_state.current_query = user_query
        
        # Generate button
        if st.button("🚀 Generate Website", type="primary", use_container_width=True):
            if not user_query.strip():
                st.error("⚠️ Please describe what kind of website you want to create!")
                return
            
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("⚠️ Google API key not found! Please set GOOGLE_API_KEY in your .env file.")
                return
            
            # Setup AI model
            try:
                model = setup_ai()
            except Exception as e:
                st.error(f"❌ Failed to setup AI model: {str(e)}")
                return
            
            # Generate website
            start_time = time.time()
            result = generate_website_files(user_query, model)
            generation_time = time.time() - start_time
            
            if 'error' in result:
                st.error(f"❌ Generation failed: {result['error']}")
                return
            
            # Store result in session state
            st.session_state.generated_data = result
            st.session_state.generation_time = generation_time
            st.session_state.show_scroll_message = True  # Show scroll message after successful generation
            st.success(f"✅ Website generated successfully in {generation_time:.2f} seconds!")
            st.rerun()
        
        # Show scroll down message if website was just generated
        if st.session_state.show_scroll_message and st.session_state.generated_data:
            st.markdown("""
            <div class="scroll-message">
                <strong>Scroll down to see your generated website!</strong>
                <div class="scroll-arrow">👇</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("## 📊 Quick Stats")
        
        if st.session_state.generated_data:
            data = st.session_state.generated_data
            
            # Display project info
            st.metric("📁 Project Name", data.get('project_name', 'Unknown'))
            st.metric("📄 Files Generated", len(data.get('files', [])))
            st.metric("⚡ Generation Time", f"{st.session_state.generation_time:.2f}s")
        else:
            st.info("Generate a website to see stats here!")
    
    # Display generated website information
    if st.session_state.generated_data:
        data = st.session_state.generated_data
        
        st.markdown("---")
        st.markdown("## 🎉 Website Generated Successfully!")
        
        # Project details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f'<div class="generated-info">', unsafe_allow_html=True)
            st.markdown(f"**📁 Project:** {data.get('project_name', 'Unknown')}")
            st.markdown(f"**📝 Description:** {data.get('description', 'No description')}")
            
            if 'features' in data:
                st.markdown("**✨ Features:**")
                for feature in data['features']:
                    st.markdown(f"- {feature}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Create download button
            try:
                zip_buffer = create_file_structure(data['files'])
                
                st.download_button(
                    label="📥 Download Website Files",
                    data=zip_buffer.getvalue(),
                    file_name=f"{data.get('project_name', 'website')}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
                
                st.success("✅ Ready for download!")
                
            except Exception as e:
                st.error(f"❌ Failed to create download: {str(e)}")
        
        # File preview
        st.markdown("## 👀 File Preview")
        
        tabs = st.tabs([f"📄 {file_info['path']}" for file_info in data['files']])
        
        for i, (tab, file_info) in enumerate(zip(tabs, data['files'])):
            with tab:
                file_extension = Path(file_info['path']).suffix.lower()
                
                # Determine syntax highlighting
                if file_extension == '.html':
                    language = 'html'
                elif file_extension == '.css':
                    language = 'css'
                elif file_extension == '.js':
                    language = 'javascript'
                else:
                    language = 'text'
                
                st.code(file_info['content'], language=language)
                
                # Copy button for each file
                st.download_button(
                    f"💾 Download {file_info['path']}",
                    data=file_info['content'],
                    file_name=file_info['path'],
                    mime='text/plain',
                    key=f"download_{i}"
                )
        
        # Clear button
        if st.button("🗑️ Clear Generated Website", type="secondary"):
            st.session_state.generated_data = None
            st.session_state.current_query = ""
            st.session_state.show_scroll_message = False  # Hide scroll message when clearing
            st.rerun()

if __name__ == "__main__":
    main()