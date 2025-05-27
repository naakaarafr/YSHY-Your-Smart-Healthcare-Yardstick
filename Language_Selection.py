import streamlit as st

# Page configuration
st.set_page_config(
    page_title="YSHY | Private Healthcare Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Fixed CSS with proper dark theme contrast
st.markdown("""
<style>
    /* Base styling for dark theme */
    .stApp {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    
    /* Main container styling */
    .main-container {
        padding: 2rem 0;
        max-width: 1000px;
        margin: 0 auto;
    }
    

    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #ffffff !important;
        text-align: center;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        color: #ffffff !important; /* Fallback for browsers that don't support gradient text */
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #cccccc !important;
        margin-top: 1rem;
        text-align: center;
        font-weight: 500;
    }
    
    /* Language selection card with dark theme */
    .language-selection-card {
        background: rgba(40, 40, 40, 0.8);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(60, 60, 60, 0.5);
        margin: 2rem 0;
        backdrop-filter: blur(10px);
    }
    
    /* Enhanced button styling with better visibility */
    .stButton button {
        border-radius: 20px !important;
        width: 100% !important;
        padding: 1.5rem 2rem !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        border: none !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
        margin: 1rem 0 !important;
        height: 80px !important;
        color: white !important;
    }
    
    /* English button styling */
    .english-button button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 20px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        white-space: pre-line !important;
        line-height: 1.4 !important;
        text-align: center !important;
    }
         
    .english-button button:hover {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 35px rgba(79, 172, 254, 0.6) !important;
    }
         
    /* Hindi button styling */
    .hindi-button button {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 20px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        white-space: pre-line !important;
        line-height: 1.4 !important;
        text-align: center !important;
    }
         
    .hindi-button button:hover {
        background: linear-gradient(135deg, #fee140 0%, #fa709a 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 35px rgba(250, 112, 154, 0.6) !important;
    }

    /* Remove default streamlit button styling */
    .stButton > button {
        height: auto !important;
        min-height: 80px !important;
    }
    
    /* Privacy banner with dark theme */
    .privacy-banner {
        background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid rgba(60, 60, 60, 0.5);
        color: #ffffff !important;
        font-weight: 500;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    
    /* About section with dark theme */
    .about-section {
        background: rgba(40, 40, 40, 0.7);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #666666;
        margin: 2rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(60, 60, 60, 0.4);
        color: #ffffff !important;
    }
    
    .big-font {
        font-size: 20px !important;
        line-height: 1.6;
        color: #ffffff !important;
    }
    
    .big-font strong {
        color: #cccccc !important;
    }
    
    /* Welcome message box with dark theme */
    .welcome-box {
        background: linear-gradient(135deg, rgba(40, 40, 40, 0.8) 0%, rgba(30, 30, 30, 0.9) 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #666666;
        margin: 1.5rem 0;
        text-align: center;
        border: 1px solid rgba(60, 60, 60, 0.5);
        backdrop-filter: blur(5px);
        color: #ffffff !important;
    }
    
    .welcome-box .big-font {
        color: #ffffff !important;
    }
    
    .welcome-box strong {
        color: #cccccc !important;
    }
    
    /* Enhanced expander styling with dark theme */
    .streamlit-expanderHeader {
        background: rgba(40, 40, 40, 0.8) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(60, 60, 60, 0.5) !important;
        color: #ffffff !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(35, 35, 35, 0.8) !important;
        border: 1px solid rgba(60, 60, 60, 0.4) !important;
        color: #ffffff !important;
    }
    
    /* Footer with dark theme */
    .footer {
        margin-top: 4rem;
        text-align: center;
        color: #cccccc !important;
        font-size: 1rem;
        font-weight: 500;
        padding: 1rem;
        background: rgba(40, 40, 40, 0.7);
        border-radius: 15px;
        border-top: 3px solid #666666;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(60, 60, 60, 0.4);
    }
    
    .footer strong {
        color: #ffffff !important;
    }
    
    /* Override any Streamlit default text colors */
    .stMarkdown, .stMarkdown p, .stMarkdown div {
        color: inherit !important;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ensure all text elements have proper contrast */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: inherit;
    }
    
    /* Force dark background for all Streamlit elements */
    .stApp > div {
        background-color: #1a1a1a !important;
    }
    
    /* Expander content styling */
    .stExpander .streamlit-expanderContent div {
        color: #ffffff !important;
    }
    
    /* Remove the light theme media query completely to ensure dark theme always applies */
</style>
""", unsafe_allow_html=True)

# Privacy banner
st.markdown("""
<div class="privacy-banner">
    🔒 Your privacy is protected. Language selection is stored locally for better experience.
</div>
""", unsafe_allow_html=True)

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Title section with enhanced styling

st.markdown('<h1 class="main-title">🩺<span class="gradient-text">Welcome to YSHY</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Please select your preferred language<br>कृपया अपनी पसंदीदा भाषा चुनें</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Welcome message box
st.markdown("""
<div class="welcome-box">
    <div class="big-font">
        🎯 <strong>Choose your language to get started</strong><br>
        <span style="color: #cccccc;">Experience YSHY in the language you're most comfortable with</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Language selection buttons with enhanced styling
col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    # Create two sub-columns for the buttons
    btn_col1, btn_col2 = st.columns([1, 1], gap="large")

    with btn_col1:
        st.markdown('<div class="english-button">', unsafe_allow_html=True)
        if st.button("Continue in English", key="English_btn", use_container_width=True):
            st.switch_page("pages/English.py")
        st.markdown('</div>', unsafe_allow_html=True)

    with btn_col2:
        st.markdown('<div class="hindi-button">', unsafe_allow_html=True)
        if st.button("हिंदी में जारी रखें", key="Hindi_btn", use_container_width=True):
            st.switch_page("pages/हिन्दी.py")
        st.markdown('</div>', unsafe_allow_html=True)

# Enhanced About section - FIXED VERSION
with st.expander("ℹ️ About YSHY - Learn More"):
    st.markdown("**🚀 About YSHY Platform**")
    st.write("")
    st.write("YSHY is designed to provide you with the best experience in your preferred language. Our platform supports multiple languages to ensure accessibility for all users.")
    st.write("")
    
    st.markdown("**🌐 Supported Languages:**")
    st.write("• English - Full feature support")
    st.write("• हिंदी - पूर्ण सुविधा समर्थन")
    st.write("")
    
    st.markdown("**✨ Key Features:**")
    st.write("• Bilingual interface support")
    st.write("• Localized content and interactions")
    st.write("• Seamless language switching")
    st.write("• Enhanced user experience")

# Additional info section
st.markdown("""
<div class="about-section">
    <div class="big-font">
        🎨 <strong>Enhanced User Experience</strong><br>
        Select your language above to access all features in your preferred language.
        The interface will adapt to provide you with the most comfortable experience.
    </div>
</div>
""", unsafe_allow_html=True)

# Footer with enhanced styling
st.markdown("""
<div class="footer">
    <strong>🔧 Powered by Streamlit</strong><br>
    Built with ❤️ for multilingual accessibility
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Enhanced JavaScript for better interactions
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Add enhanced button interactions
    const buttons = document.querySelectorAll('[data-testid="baseButton-secondary"]');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.02)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
        button.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(-1px) scale(0.98)';
        });
        button.addEventListener('mouseup', function() {
            this.style.transform = 'translateY(-3px) scale(1.02)';
        });
    });
    
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
});
</script>
""", unsafe_allow_html=True)