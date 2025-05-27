import streamlit as st
from pathlib import Path
import google.generativeai as genai
import dotenv
import os
import tempfile
import uuid
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import pytz
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib

# Backend setup

dotenv.load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Configure the model with appropriate settings for medical analysis
generation_config = {
    "temperature": 0.2,  # Lower temperature for more reliable medical information
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
def search_health_centers(location, facility_type):
    """
    Dynamically search for health centers based on location and facility type
    This function simulates API calls to health databases
    """
    try:
        # Simulate API call delay
        import time
        time.sleep(1)
            
        # Generate dynamic results based on location and facility type
        centers = []
            
        # Base coordinates for different regions (this would normally come from geocoding API)
        location_coords = get_location_coordinates(location)
            
        if location_coords:
            # Generate facilities around the location
            for i in range(3, 8):  # Generate 3-7 facilities
                lat_offset = (i * 0.01) - 0.03
                lon_offset = (i * 0.008) - 0.02
                    
                center = {
                    "name": generate_facility_name(facility_type, i),
                    "lat": location_coords["lat"] + lat_offset,
                    "lon": location_coords["lon"] + lon_offset,
                    "address": f"{generate_address(location, i)}",
                    "phone": generate_phone_number(),
                    "distance": round(abs(lat_offset + lon_offset) * 100, 1)
                }
                centers.append(center)
            
        return centers
        
    except Exception as e:
        st.error(f"खोज में त्रुटि: {str(e)}")
        return []

def get_location_coordinates(location):
    """Get coordinates for a location (simulated geocoding)"""
    # This would normally use a geocoding API like Google Maps, OpenStreetMap, etc.
    location_map = {
        # Major cities
        "दिल्ली": {"lat": 28.6139, "lon": 77.2090},
        "मुंबई": {"lat": 19.0760, "lon": 72.8777},
        "बैंगलोर": {"lat": 12.9716, "lon": 77.5946},
        "कोलकाता": {"lat": 22.5726, "lon": 88.3639},
        "चेन्नई": {"lat": 13.0827, "lon": 80.2707},
        "हैदराबाद": {"lat": 17.3850, "lon": 78.4867},
        "पुणे": {"lat": 18.5204, "lon": 73.8567},
        "अहमदाबाद": {"lat": 23.0225, "lon": 72.5714},
            
        # PIN codes (major ones)
        "110001": {"lat": 28.6139, "lon": 77.2090},
        "400001": {"lat": 19.0760, "lon": 72.8777},
        "560001": {"lat": 12.9716, "lon": 77.5946},
        "700001": {"lat": 22.5726, "lon": 88.3639},
        "600001": {"lat": 13.0827, "lon": 80.2707},
        "500001": {"lat": 17.3850, "lon": 78.4867},
        "411001": {"lat": 18.5204, "lon": 73.8567},
        "380001": {"lat": 23.0225, "lon": 72.5714},
    }
        
        # Check exact match first
    for key, coords in location_map.items():
        if location.lower() in key.lower() or key.lower() in location.lower():
            return coords
        
        # If PIN code, try to match first 3 digits
    if location.isdigit() and len(location) >= 3:
        pin_prefix = location[:3]
        pin_regions = {
            "110": {"lat": 28.6139, "lon": 77.2090},  # Delhi
            "400": {"lat": 19.0760, "lon": 72.8777},  # Mumbai
            "560": {"lat": 12.9716, "lon": 77.5946},  # Bangalore
            "700": {"lat": 22.5726, "lon": 88.3639},  # Kolkata
            "600": {"lat": 13.0827, "lon": 80.2707},  # Chennai
            "500": {"lat": 17.3850, "lon": 78.4867},  # Hyderabad
        }
        if pin_prefix in pin_regions:
            return pin_regions[pin_prefix]
        
    # Default to Delhi if no match found
    return {"lat": 28.6139, "lon": 77.2090}

def generate_facility_name(facility_type, index):
    """Generate realistic facility names based on type"""
    names = {
        "अस्पताल": [
            "सरकारी जिला अस्पताल", "सामुदायिक स्वास्थ्य केंद्र", "मेडिकल कॉलेज अस्पताल", 
            "जनरल अस्पताल", "सिविल अस्पताल", "रेलवे अस्पताल", "ESI अस्पताल"
        ],
        "क्लिनिक": [
            "प्राथमिक स्वास्थ्य केंद्र", "उप स्वास्थ्य केंद्र", "मातृत्व क्लिनिक", 
            "परिवार कल्याण क्लिनिक", "आयुष्मान क्लिनिक", "जन औषधि क्लिनिक"
        ],
        "स्त्री रोग विशेषज्ञ": [
            "डॉ. प्रिया शर्मा क्लिनिक", "डॉ. सुनीता गुप्ता", "डॉ. अनीता वर्मा", 
            "डॉ. मीरा सिंह", "डॉ. रीता अग्रवाल", "डॉ. कविता शुक्ला"
        ],
        "स्वास्थ्य केंद्र": [
            "आंगनवाड़ी केंद्र", "सामुदायिक स्वास्थ्य केंद्र", "प्राथमिक स्वास्थ्य केंद्र",
            "शहरी स्वास्थ्य केंद्र", "मातृ शिशु स्वास्थ्य केंद्र", "ग्रामीण स्वास्थ्य केंद्र"
        ],
        "परिवार नियोजन केंद्र": [
            "परिवार कल्याण केंद्र", "जनसंख्या नियंत्रण केंद्र", "प्रजनन स्वास्थ्य केंद्र",
            "मातृत्व परामर्श केंद्र", "परिवार नियोजन क्लिनिक", "महिला स्वास्थ्य केंद्र"
        ]
    }
    
    facility_names = names.get(facility_type, ["स्वास्थ्य केंद्र"])
    return f"{facility_names[index % len(facility_names)]} - {index}"

def generate_address(location, index):
    """Generate realistic addresses"""
    areas = ["मुख्य बाजार", "रेलवे स्टेशन रोड", "बस स्टैंड", "सिविल लाइन्स", "पुराना शहर", "नया क्षेत्र"]
    return f"{areas[index % len(areas)]}, {location}"

def generate_phone_number():
    """Generate realistic phone numbers"""
    import random
    return f"{random.choice(['011', '022', '033', '044', '080'])}-{random.randint(20000000, 99999999)}"
# Enhanced system prompt for better medical analysis (Hindi)
system_prompt = """
आप YSHY (Your Smart Healthcare Yardstick) हैं, एक AI सहायक जो महिलाओं के अंतरंग स्वास्थ्य की स्थितियों के चित्रों का विश्लेषण करने में विशेषज्ञता रखते हैं। आपका उद्देश्य पूर्ण गोपनीयता और सम्मान बनाए रखते हुए प्रारंभिक जानकारी और मार्गदर्शन प्रदान करना है।

विश्लेषण निर्देश:
1. अंतरंग क्षेत्र के चित्र का सावधानीपूर्वक परीक्षण करें, निम्न सामान्य स्थितियों के संकेतों के लिए:
- यीस्ट संक्रमण (सफेद स्राव, लालिमा, सूजन)
- बैक्टीरियल वेजिनोसिस (पतला धूसर स्राव, गंध)
- जेनिटल हरपीज (छाले, घाव, घाव)
- HPV मस्से (मांस के रंग के विकास)
- डर्मेटाइटिस या जलन (लालिमा, सूजन, दाने)
- लिकेन स्क्लेरोसस (सफेद धब्बे, पतली त्वचा)
- वल्वोडिनिया (कोई दृश्यमान लक्षण नहीं लेकिन दर्द की शिकायत)
- बार्थोलिन सिस्ट (योनि के उद्घाटन के पास सूजन)
- फोलिकुलिटिस (सूजे हुए बाल रोम)
- संपर्क डर्मेटाइटिस (जलनकारी पदार्थों के संपर्क के बाद दाने)

2. हमेशा अपनी प्रतिक्रिया को इस सटीक प्रारूप में संरचित करें:

## प्रारंभिक मूल्यांकन
[चित्र में आप जो देखते हैं उसका एक संक्षिप्त, संवेदनशील विवरण प्रदान करें]

## संभावित स्थितियां
[संभावित 1-3 स्थितियां जो दृश्य लक्षणों से मेल खाती हैं, संभाव्यता के क्रम में]

## स्थिति विवरण
[उल्लिखित प्रत्येक स्थिति के लिए, यह क्या है, सामान्य कारण और विशिष्ट प्रगति का संक्षिप्त विवरण प्रदान करें]

## अनुशंसित कदम
[स्व-देखभाल और चिकित्सा सहायता कब लेनी चाहिए, इसके लिए 3-5 विशिष्ट सिफारिशें प्रदान करें]

## उपचार विकल्प
[संभावित उपचारों की सूची जो स्वास्थ्य देखभाल प्रदाता द्वारा निर्धारित किए जा सकते हैं]

## रोकथाम के टिप्स
[पहचानी गई स्थितियों के लिए विशिष्ट 2-3 रोकथाम युक्तियां प्रदान करें]

## महत्वपूर्ण नोट
यह चिकित्सकीय निदान नहीं है। कई महिला अंतरंग स्थितियों के समान दृश्य लक्षण होते हैं। एक स्वास्थ्य देखभाल प्रदाता सटीक कारण और उचित उपचार निर्धारित करने के लिए परीक्षण कर सकता है। आपकी गोपनीयता और स्वास्थ्य महत्वपूर्ण हैं - कृपया उचित निदान और उपचार के लिए स्वास्थ्य पेशेवर से परामर्श करें।

3. अत्यंत महत्वपूर्ण दिशानिर्देश:
- अपनी भाषा में स्पष्ट, सटीक और सहानुभूतिपूर्ण रहें
- कभी भी निश्चित निदान प्रदान करने का दावा न करें
- पेशेवर चिकित्सा सलाह के महत्व पर जोर दें
- सामान्य स्थितियों के बारे में शैक्षिक जानकारी पर ध्यान केंद्रित करें
- सम्मानजनक रहें और उचित चिकित्सा शब्दावली का उपयोग करें
- यदि छवि की गुणवत्ता खराब या अपर्याप्त है, तो स्पष्ट रूप से इस सीमा को बताएं
- दृश्यमान लक्षणों के आधार पर 1-5 (1=हल्का, 5=गंभीर) के बीच गंभीरता रेटिंग शामिल करें, लेकिन इस बात पर जोर दें कि यह प्रारंभिक है
- चिकित्सा ध्यान देने के लिए समयसीमा के लिए सिफारिश जोड़ें (जैसे, "24 घंटे के भीतर", "सप्ताह के भीतर", "अपनी सुविधा पर")

4. गोपनीयता आवश्यकताएं:
- किसी भी व्यक्तिगत पहचान जानकारी का अनुरोध न करें
- पिछले विश्लेषणों से विशिष्ट विवरण संग्रहीत या संदर्भित न करें
- प्रत्येक विश्लेषण को एक नया, स्वतंत्र मूल्यांकन मानें

याद रखें: आपकी भूमिका प्रारंभिक मार्गदर्शन और शिक्षा प्रदान करना है ताकि उपयोगकर्ताओं को संभावित स्थितियों और उचित अगले कदमों को समझने में मदद मिल सके, पेशेवर चिकित्सा देखभाल को प्रतिस्थापित करना नहीं।
"""

# Configure the symptom checker model (Hindi)
symptom_checker_prompt = """
आप महिलाओं के स्वास्थ्य लक्षण विश्लेषक हैं। प्रदान की गई लक्षण जानकारी के आधार पर, संभावित स्थितियों और उचित अगले कदमों का सुझाव दें। केवल स्त्री रोग संबंधी और अंतरंग स्वास्थ्य स्थितियों पर ध्यान केंद्रित करें।

प्रदान किए गए लक्षणों का विश्लेषण करें और इस सटीक प्रारूप में प्रतिक्रिया दें:

## संभावित स्थितियां
[वर्णित लक्षणों से मेल खाने वाली 3-5 संभावित स्थितियों की सूची, संभाव्यता के क्रम में]

## स्थिति विवरण
[प्रत्येक स्थिति के लिए, एक संक्षिप्त स्पष्टीकरण प्रदान करें]

## अनुशंसित कदम
[स्व-देखभाल और चिकित्सा ध्यान के लिए विशिष्ट सिफारिशें प्रदान करें]

## महत्वपूर्ण नोट
यह चिकित्सा निदान नहीं है। समान लक्षण विभिन्न स्थितियों को इंगित कर सकते हैं। एक स्वास्थ्य देखभाल प्रदाता सटीक कारण और उचित उपचार निर्धारित करने के लिए परीक्षण कर सकता है।

सटीक, सहानुभूतिपूर्ण रहें, और पेशेवर चिकित्सा सलाह के महत्व पर जोर दें।
"""

# Initialize Gemini models
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

symptom_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

# User session management
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'history' not in st.session_state:
    st.session_state.history = []
if 'history_file' not in st.session_state:
    st.session_state.history_file = None
if 'user_timezone' not in st.session_state:
    st.session_state.user_timezone = "UTC"
if 'language' not in st.session_state:
    st.session_state.language = "Hindi"
if 'symptom_tracker' not in st.session_state:
    st.session_state.symptom_tracker = []
if 'reminder_days' not in st.session_state:
    st.session_state.reminder_days = 7

# Data Handling Functions
def generate_anonymous_id():
    """Generate a unique anonymous ID based on session and timestamp"""
    unique_string = f"{st.session_state.session_id}-{datetime.now().isoformat()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:12]

def save_history_to_file():
    """Save analysis history to an encrypted file for user download"""
    if st.session_state.history:
        history_data = json.dumps({
            "session_id": st.session_state.session_id,
            "history": st.session_state.history,
            "symptom_tracker": st.session_state.symptom_tracker,
            "exported_date": datetime.now().isoformat()
        })
        # Simple encryption by encoding to base64 (not truly secure but adds a layer of privacy)
        encoded_data = base64.b64encode(history_data.encode()).decode()
        st.session_state.history_file = encoded_data
        return encoded_data
    return None

def load_history_from_file(file_content):
    """Load analysis history from an uploaded file"""
    try:
        # Decode the base64 encrypted data
        decoded_data = base64.b64decode(file_content).decode()
        data = json.loads(decoded_data)
        
        # Validate the data structure
        if "history" in data and "session_id" in data and "symptom_tracker" in data:
            st.session_state.history = data["history"]
            st.session_state.symptom_tracker = data["symptom_tracker"]
            return True
        return False
    except Exception as e:
        st.error(f"इतिहास फ़ाइल लोड नहीं कर सका: {str(e)}")
        return False

def add_to_symptom_tracker(condition, severity, date=None):
    """Add a symptom entry to the tracker"""
    if date is None:
        date = datetime.now()
    
    st.session_state.symptom_tracker.append({
        "date": date.isoformat(),
        "condition": condition,
        "severity": severity
    })

def get_condition_trend_data():
    """Get data for condition trend visualization"""
    if not st.session_state.symptom_tracker:
        return None
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(st.session_state.symptom_tracker)
    if df.empty:
        return None
    
    # Convert date strings to datetime with flexible format
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    
    # Sort by date
    df = df.sort_values('date')
    
    return df

# Image Processing Functions
def anonymize_image(image_bytes):
    """Apply a subtle watermark to indicate the image is being processed privately"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(img)
        
        # Add subtle "PRIVATE ANALYSIS" text in corner
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
        
        # Add semi-transparent text in corner
        draw.text((10, 10), "YSHY निजी", fill=(255, 255, 255, 128), font=font)
        
        # Convert back to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()
    except Exception as e:
        # If any error occurs, return original image
        return image_bytes

# UI Configuration
st.set_page_config(
    page_title="YSHY | निजी स्वास्थ्य सहायक",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for improved styling
st.markdown("""
<style>
    .reportview-container {
        background-color: #f0f8ff;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton button {
        border-radius: 20px;
    }
    .big-font {
        font-size: 20px !important;
    }
    .stAlert {
        border-radius: 10px;
    }
    .reminder-box {
        background-color: #f0f4f8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4e89ae;
    }
    .privacy-banner {
        background-color: #172A42;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    .result-box {
        border-left: 5px solid #6c5ce7;
        padding-left: 15px;
    }
    .condition-high {
        color: #e74c3c;
        font-weight: bold;
    }
    .condition-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .condition-low {
        color: #2ecc71;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for settings and tools
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/caduceus.png", width=50)
    st.title("YSHY: आपका स्मार्ट हेल्थकेयर यार्डस्टिक")

    # User Settings
    st.header("सेटिंग्स")
    
    # Language selection
    if st.button("अंग्रेज़ी में बदलें"):
        st.switch_page("pages/english.py")

    # QR code for sharing app (placeholder - in real app would generate actual QR)
    st.header("गुमनाम रूप से साझा करें")
    st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://yshy-health-app.streamlit.app", width=150)
    st.caption("किसी ऐसे व्यक्ति के साथ इस ऐप को साझा करने के लिए स्कैन करें जिसे इसकी आवश्यकता है")

# Main App Interface
st.title("YSHY: आपका स्मार्ट हेल्थकेयर यार्डस्टिक")
st.markdown("""
<div class="privacy-banner">
    🔒 <b>गोपनीयता सुनिश्चित:</b> छवियां निजी तौर पर संसाधित की जाती हैं और तुरंत हटा दी जाती हैं। सर्वरों पर कोई डेटा संग्रहीत नहीं किया जाता है।
</div>
""", unsafe_allow_html=True)

st.markdown("""
### निजी, गोपनीय स्वास्थ्य मार्गदर्शन
पूरी तरह से निजी वातावरण में अंतरंग स्वास्थ्य चिंताओं के बारे में प्रारंभिक जानकारी प्राप्त करें।
""")

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs(["दृश्य विश्लेषण", "लक्षण जांचकर्ता", "इतिहास और रुझान", "संसाधन", "शिक्षा"])

with tab1:
    st.header("दृश्य विश्लेषण")
    st.markdown("AI-सहायता प्राप्त विश्लेषण के लिए एक या अधिक छवियां अपलोड करें। छवियों को निजी तौर पर संसाधित किया जाता है और तुरंत हटा दिया जाता है।")
    
    # File uploader with multiple file support
    uploaded_files = st.file_uploader("छवियां चुनें...", type=["png", "jpg", "jpeg"], 
                                    accept_multiple_files=True,
                                    help="प्रभावित क्षेत्र(ओं) की स्पष्ट, अच्छी तरह से प्रकाशित छवियां चुनें")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if uploaded_files:
            # Display uploaded images count
            st.info(f"📁 {len(uploaded_files)} छवि(यां) अपलोड की गई")
            
            # Display all uploaded images with enhanced privacy
            with st.expander("अपलोड की गई छवियों की समीक्षा करें", expanded=False):
                for i, uploaded_file in enumerate(uploaded_files):
                    st.image(anonymize_image(uploaded_file.getvalue()), caption=f"छवि {i+1}", use_container_width=True)
            
            # Analysis button
            analyze_button = st.button("विश्लेषण शुरू करें", key="analyze_button", help="AI द्वारा छवियों का विश्लेषण करने के लिए क्लिक करें")
            
            if analyze_button:
                with st.spinner("छवियों का विश्लेषण किया जा रहा है... कृपया प्रतीक्षा करें (इसमें कुछ समय लग सकता है)"):
                    analysis_results = []
                    
                    # Process each image
                    for i, uploaded_file in enumerate(uploaded_files):
                        try:
                            # For privacy protection - add basic anonymization to images
                            processed_image = anonymize_image(uploaded_file.getvalue())
                            
                            # This would be the actual API call to Google's Gemini Vision
                            image_parts = [
                                {
                                    "mime_type": uploaded_file.type,
                                    "data": base64.b64encode(processed_image).decode('utf-8')
                                }
                            ]
                            
                            prompt_parts = [system_prompt, image_parts[0]]
                            
                            # Generate analysis from Gemini
                            response = model.generate_content(prompt_parts)
                            result = response.text
                            
                            # Extract possible conditions, recommended steps, etc.
                            analysis_results.append({
                                "image_number": i + 1,
                                "result": result,
                                "timestamp": datetime.now().isoformat(),
                                "id": generate_anonymous_id()
                            })
                            
                            # Save to history
                            st.session_state.history.append({
                                "type": "image_analysis",
                                "timestamp": datetime.now().isoformat(),
                                "result": result,
                                "id": generate_anonymous_id()
                            })
                            
                        except Exception as e:
                            st.error(f"छवि {i+1} का विश्लेषण करते समय त्रुटि: {str(e)}")
                    
                    # Display results placeholder (in real app these would be the actual results)
                    st.success(f"{len(analysis_results)} छवि(यों) का विश्लेषण पूरा हुआ")
                    
                    # Display each analysis result
                    for analysis in analysis_results:
                        with st.expander(f"छवि {analysis['image_number']} का विश्लेषण परिणाम", expanded=True):
                            st.markdown(f"<div class='result-box'>{analysis['result']}</div>", unsafe_allow_html=True)
                            
                            # Automatically extract likely conditions from the analysis result
                            try:
                                # Look for the section with conditions in the analysis result
                                result_text = analysis['result']
                                conditions = []
                                
                                # Try to find the Possible Conditions section (संभावित स्थितियां)
                                if "## संभावित स्थितियां" in result_text:
                                    # Split by sections
                                    sections = result_text.split("##")
                                    for i, section in enumerate(sections):
                                        if "संभावित स्थितियां" in section:
                                            # Extract lines after heading
                                            lines = section.strip().split("\n")[1:]
                                            for line in lines:
                                                line = line.strip()
                                                if line and not line.startswith("##"):
                                                    # Clean up the text (remove markers, numbers, etc.)
                                                    condition = line.lstrip("0123456789.-* ")
                                                    if condition:
                                                        conditions.append(condition)
                                            break
                                
                                # Automatically add conditions to tracker and display them
                                if conditions:
                                    # Add all conditions automatically with default severity 3
                                    for condition in conditions:
                                        add_to_symptom_tracker(condition, 3)
                                    
                                    # Simply show confirmation message
                                    st.success("सभी पहचानी गई स्थितियां ट्रैकर में जोड़ी गईं")
                                    
                                    # Show list of added conditions
                                    st.markdown("### स्वचालित रूप से ट्रैक की गई स्थितियां:")
                                    for i, condition in enumerate(conditions):
                                        st.markdown(f"**{i+1}. {condition}** (गंभीरता: 3)")
                                        

                            except Exception as e:
                                st.info("स्वचालित स्थिति ट्रैकिंग में समस्या आई है। विश्लेषण अभी भी उपलब्ध है।")
    
    with col2:
        st.subheader("मार्गदर्शन और निर्देश")
        st.markdown("""
        #### छवियों के साथ सर्वोत्तम परिणाम प्राप्त करने के लिए सुझाव:
        
        1. **अच्छी रोशनी**: एक अच्छी तरह से प्रकाशित क्षेत्र में चित्र लें
        2. **स्पष्टता**: सुनिश्चित करें कि छवि फोकस में है और धुंधली नहीं है
        3. **कई कोण**: यदि संभव हो तो विभिन्न कोणों से अतिरिक्त छवियां प्रदान करें
        4. **माप**: परिप्रेक्ष्य के लिए विषय के निकट कोई कॉइन या मापने वाली वस्तु रखें
        5. **संदर्भ**: यदि संदर्भ उपयोगी हो तो प्रभावित और सामान्य क्षेत्रों दोनों को शामिल करें
        
        #### महत्वपूर्ण:
        - YSHY निजी है और आपकी गोपनीयता का सम्मान करता है
        - छवियां केवल विश्लेषण के लिए उपयोग की जाती हैं और हमारे सर्वर पर संग्रहीत नहीं की जाती हैं
        - किसी भी निष्कर्ष को अंतिम निदान के रूप में नहीं माना जाना चाहिए
        - गंभीर लक्षणों के लिए हमेशा स्वास्थ्य पेशेवर से परामर्श करें
        """)
        
        # Add reminder about medical advice
        st.warning("याद रखें: YSHY कभी भी पेशेवर चिकित्सा देखभाल का विकल्प नहीं है। हमेशा स्वास्थ्य पेशेवर से परामर्श करें।")

with tab2:
    st.header("लक्षण जांचकर्ता")
    st.markdown("अपने लक्षणों का वर्णन करें और संभावित स्थितियों और अगले कदमों के बारे में AI-सहायता प्राप्त प्रतिक्रिया प्राप्त करें।")
    
    # Text area for symptom description
    symptom_description = st.text_area("अपने लक्षणों का विस्तार से वर्णन करें...", height=150, 
                                    help="जितना अधिक विवरण आप प्रदान करेंगे, उतना बेहतर विश्लेषण होगा")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Add checkboxes for common symptoms
        st.subheader("सामान्य लक्षण")
        symptom_options = {
            "दर्द": st.checkbox("दर्द या परेशानी"),
            "खुजली": st.checkbox("खुजली या जलन"),
            "स्राव": st.checkbox("असामान्य स्राव"),
            "गंध": st.checkbox("असामान्य गंध"),
            "लालिमा": st.checkbox("लालिमा या सूजन"),
            "घाव": st.checkbox("घाव या छाले"),
            "अनियमित_मासिक_धर्म": st.checkbox("अनियमित मासिक धर्म"),
            "दर्द_मासिक_धर्म": st.checkbox("दर्दनाक मासिक धर्म"),
            "यौन_दर्द": st.checkbox("यौन संबंध के दौरान दर्द"),
            "बुखार": st.checkbox("बुखार"),
        }
        
        # Selected symptoms
        selected_symptoms = [symptom for symptom, selected in symptom_options.items() if selected]
        
        if selected_symptoms:
            symptom_description += "\n\nचुने गए लक्षण: " + ", ".join(selected_symptoms)
        
        # Duration selector
        st.subheader("लक्षणों की अवधि")
        duration = st.radio("", ["24 घंटे से कम", "कुछ दिन", "एक सप्ताह", "कई सप्ताह", "महीनों"])
        
        # Add to description
        if duration:
            symptom_description += f"\n\nअवधि: {duration}"
        
        # Severity slider
        symptom_severity = st.slider("गंभीरता (1-5, जहां 5 सबसे गंभीर है)", 1, 5, 3)
        symptom_description += f"\n\nगंभीरता (1-5): {symptom_severity}"
        
        # Check symptoms button
        if st.button("लक्षणों का विश्लेषण करें", 
                help="अपने लक्षणों का AI-आधारित विश्लेषण प्राप्त करने के लिए क्लिक करें"):
            if symptom_description.strip():
                with st.spinner("लक्षणों का विश्लेषण किया जा रहा है... कृपया प्रतीक्षा करें"):
                    try:
                        # API call with symptom description
                        prompt_parts = [symptom_checker_prompt, symptom_description]
                        response = symptom_model.generate_content(prompt_parts)
                        result = response.text
                        
                        # Save to history
                        analysis_id = generate_anonymous_id()
                        st.session_state.history.append({
                            "type": "symptom_analysis",
                            "timestamp": datetime.now().isoformat(),
                            "symptoms": symptom_description,
                            "result": result,
                            "id": analysis_id
                        })
                        
                        # Display result
                        st.success("विश्लेषण पूरा हुआ")
                        st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)
                        
                        # Automatically extract conditions from the result text
                        try:
                            # Look for the section with conditions in the analysis result
                            conditions = []
                            
                            # Try to find the Possible Conditions section (संभावित स्थितियां)
                            if "## संभावित स्थितियां" in result:
                                # Split by sections
                                sections = result.split("##")
                                for i, section in enumerate(sections):
                                    if "संभावित स्थितियां" in section:
                                        # Extract lines after heading
                                        lines = section.strip().split("\n")[1:]
                                        for line in lines:
                                            line = line.strip()
                                            if line and not line.startswith("##"):
                                                # Clean up the text (remove markers, numbers, etc.)
                                                condition = line.lstrip("0123456789.-* ")
                                                if condition:
                                                    conditions.append(condition)
                                        break
                            
                            # Automatically add conditions to tracker and display them
                            if conditions:
                                # Add all conditions automatically with default severity 3
                                for condition in conditions:
                                    add_to_symptom_tracker(condition, 3)
                                
                                # Simply show confirmation message
                                st.success("सभी पहचानी गई स्थितियां ट्रैकर में जोड़ी गईं")
                                
                                # Show list of added conditions
                                st.markdown("### स्वचालित रूप से ट्रैक की गई स्थितियां:")
                                for i, condition in enumerate(conditions):
                                    st.markdown(f"**{i+1}. {condition}** (गंभीरता: 3)")
                            

                        except Exception as e:
                            st.info("स्वचालित स्थिति ट्रैकिंग में समस्या आई है। विश्लेषण अभी भी उपलब्ध है।")
                        
                    except Exception as e:
                        st.error(f"लक्षणों का विश्लेषण करते समय त्रुटि: {str(e)}")
            else:
                st.warning("कृपया विश्लेषण से पहले अपने लक्षणों का वर्णन करें")
    
    with col2:
        st.subheader("अंतरंग स्वास्थ्य टिप्स")
        st.markdown("""
        #### महिला अंतरंग स्वास्थ्य के लिए सामान्य टिप्स:
        
        1. **नियमित स्वच्छता**: हल्के, सुगंध-मुक्त साबुन से धोएं और अच्छी तरह से सुखाएं
        2. **सूती अंडरवियर**: सांस लेने योग्य कपड़े पहनें जो नमी को दूर रखें
        3. **सही पीएच संतुलन**: आपका अंतरंग क्षेत्र प्राकृतिक रूप से थोड़ा अम्लीय होता है, डूश या कठोर उत्पादों से इसे अव्यवस्थित न करें
        4. **सुरक्षित यौन अभ्यास**: योनि संक्रमण और यौन संचारित संक्रमणों से बचने के लिए अवरोधक का उपयोग करें
        5. **समय पर जांच**: नियमित पैप स्मीयर और स्त्री रोग परीक्षा के लिए अपने डॉक्टर के पास जाएं
        
        #### कब चिकित्सा सहायता लें:
        - अचानक या तीव्र दर्द
        - भारी या असामान्य स्राव
        - गंध में महत्वपूर्ण बदलाव
        - अचानक खुजली, जलन या सूजन
        - बुखार या सामान्य अस्वस्थता के साथ लक्षण
        - मूत्र त्यागने या यौन संबंध के दौरान दर्द
        """)
        
        # Add disclaimer box
        st.info("अस्वीकरण: इस लक्षण विश्लेषक का उद्देश्य शैक्षिक है और पेशेवर चिकित्सा सलाह का विकल्प नहीं है। यदि आप चिंतित हैं, कृपया स्वास्थ्य पेशेवर से परामर्श करें।")

with tab3:
    st.header("इतिहास और रुझान")
    
    # Tabs for history, tracker, and export
    hist_tab1, hist_tab2, hist_tab3 = st.tabs(["पिछले विश्लेषण", "लक्षण ट्रैकर", "डेटा निर्यात"])
    
    with hist_tab1:
        st.subheader("पिछले विश्लेषण")
        
        if st.session_state.history:
            # Reverse to show newest first
            for entry in reversed(st.session_state.history):
                entry_time = datetime.fromisoformat(entry["timestamp"])
                formatted_time = entry_time.strftime("%Y-%m-%d %H:%M")
                
                # Different display for image analysis vs symptom analysis
                if entry["type"] == "image_analysis":
                    with st.expander(f"छवि विश्लेषण - {formatted_time}"):
                        st.markdown(entry["result"])
                elif entry["type"] == "symptom_analysis":
                    with st.expander(f"लक्षण विश्लेषण - {formatted_time}"):
                        st.markdown("### वर्णित लक्षण:")
                        st.text(entry["symptoms"])
                        st.markdown("### विश्लेषण परिणाम:")
                        st.markdown(entry["result"])
        else:
            st.info("कोई पिछला विश्लेषण नहीं मिला। छवियों का विश्लेषण करने या लक्षणों की जांच करने के बाद, आप उन्हें यहां देख पाएंगे।")
    
    with hist_tab2:
        st.subheader("लक्षण ट्रैकर")
        
        if st.session_state.symptom_tracker:
            # Show current tracked symptoms
            df = get_condition_trend_data()
            if df is not None:
                # Create summary
                st.markdown("### ट्रैक किए गए स्थितियां")
                
                # List unique conditions and their most recent severity
                unique_conditions = df.groupby('condition')['severity'].last().reset_index()
                for _, row in unique_conditions.iterrows():
                    condition_class = "condition-low"
                    if row['severity'] >= 4:
                        condition_class = "condition-high"
                    elif row['severity'] >= 2:
                        condition_class = "condition-medium"
                    
                    st.markdown(f"- <span class='{condition_class}'>{row['condition']} (गंभीरता: {row['severity']})</span>", unsafe_allow_html=True)
                
                # Create trend chart
                st.markdown("### गंभीरता के रुझान")
                
                # Plot data
                fig = px.line(df, x='date', y='severity', color='condition',
                            labels={'date': 'दिनांक', 'severity': 'गंभीरता', 'condition': 'स्थिति'},
                            title="समय के साथ लक्षणों की गंभीरता")
                
                fig.update_layout(
                    xaxis_title="दिनांक",
                    yaxis_title="गंभीरता (1-5)",
                    legend_title="स्थिति"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Option to add new entry manually
                st.subheader("नया ट्रैकर एंट्री जोड़ें")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # If we have existing conditions, show them in a dropdown
                    conditions_list = df['condition'].unique().tolist()
                    if conditions_list:
                        condition_input = st.selectbox("स्थिति", options=conditions_list)
                    else:
                        condition_input = st.text_input("स्थिति", "")
                
                with col2:
                    severity_input = st.slider("गंभीरता", 1, 5, 3)
                
                with col3:
                    date_input = st.date_input("दिनांक", datetime.now())
                
                if st.button("ट्रैकर में जोड़ें"):
                    if condition_input:
                        # Convert date to datetime
                        date_time = datetime.combine(date_input, datetime.min.time())
                        add_to_symptom_tracker(condition_input, severity_input, date_time)
                        st.success(f"'{condition_input}' को ट्रैकर में जोड़ा गया")
                        st.rerun()
                    else:
                        st.warning("स्थिति का नाम दर्ज करें")
                
                # Option to delete entries
                st.subheader("ट्रैकर एंट्री मिटाएं")
                if st.button("सभी ट्रैकर एंट्री मिटाएं", key="delete_tracker"):
                    st.session_state.symptom_tracker = []
                    st.success("सभी ट्रैकर एंट्री मिटा दी गई हैं")
                    st.rerun()
            else:
                st.info("लक्षण ट्रैकर डेटा उपलब्ध नहीं है")
        else:
            st.info("कोई ट्रैक किए गए लक्षण नहीं मिले। जब आप लक्षणों या परिस्थितियों को अपने ट्रैकर में जोड़ेंगे, तो आप यहां उनके रुझान देखेंगे।")
            
            # Sample tracker entry
            st.subheader("अपना पहला ट्रैकर एंट्री जोड़ें")
            condition_input = st.text_input("स्थिति का नाम", "")
            severity_input = st.slider("गंभीरता (1-5)", 1, 5, 3)
            
            if st.button("ट्रैकर में जोड़ें"):
                if condition_input:
                    add_to_symptom_tracker(condition_input, severity_input)
                    st.success(f"'{condition_input}' को ट्रैकर में जोड़ा गया")
                    st.rerun()
                else:
                    st.warning("स्थिति का नाम दर्ज करें")
    
    with hist_tab3:
        st.subheader("डेटा निर्यात ")
        st.markdown("अपने इतिहास और ट्रैकर डेटा को निर्यात करें । आपका डेटा गोपनीय रूप से संग्रहीत किया जाता है और केवल आपके पास उपलब्ध है।")
        
        col1, col2 = st.columns(2)
        
        with col1:
            
            if st.button("इतिहास और ट्रैकर डेटा सहेजें"):
                encoded_data = save_history_to_file()
                if encoded_data:
                    st.success("डेटा सफलतापूर्वक तैयार किया गया")
                    st.download_button(
                        label="डेटा फ़ाइल डाउनलोड करें",
                        data=encoded_data,
                        file_name=f"yshy_health_data_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                else:
                    st.warning("निर्यात करने के लिए कोई डेटा नहीं मिला")
        
    

import streamlit as st
import pandas as pd

# Function to retrieve health centers dynamically
def get_health_centers():
    """
    Returns a dictionary of health centers by PIN code with realistic names.
    TODO: Replace this sample data with an API call or database query for real data.
    """
    return {
        "201014": {  # Example: Ghaziabad, Uttar Pradesh
            "अस्पताल": [
                {"name": "अपोलो अस्पताल", "lat": 28.6129, "lon": 77.2295},
                {"name": "फोर्टिस अस्पताल", "lat": 28.6139, "lon": 77.2395},
                {"name": "मैक्स अस्पताल", "lat": 28.6149, "lon": 77.2405}
            ],
            "क्लिनिक": [
                {"name": "मैक्स क्लिनिक", "lat": 28.6229, "lon": 77.2495},
                {"name": "अपोलो क्लिनिक", "lat": 28.6239, "lon": 77.2505}
            ]
        },
        "110001": {  # Example: Central Delhi
            "अस्पताल": [
                {"name": "AIIMS दिल्ली", "lat": 28.6139, "lon": 77.2090},
                {"name": "सफदरजंग अस्पताल", "lat": 28.6239, "lon": 77.2190},
                {"name": "राम मनोहर लोहिया अस्पताल", "lat": 28.6249, "lon": 77.2200}
            ],
            "क्लिनिक": [
                {"name": "अपोलो क्लिनिक", "lat": 28.6339, "lon": 77.2290},
                {"name": "फोर्टिस क्लिनिक", "lat": 28.6349, "lon": 77.2300}
            ]
        },
        "560001": {  # Example: Bangalore, Karnataka
            "अस्पताल": [
                {"name": "बैंगलोर मेडिकल कॉलेज", "lat": 12.9716, "lon": 77.5946},
                {"name": "निमहंस अस्पताल", "lat": 12.9726, "lon": 77.5956}
            ],
            "क्लिनिक": [
                {"name": "अपोलो क्लिनिक बैंगलोर", "lat": 12.9736, "lon": 77.5966}
            ]
        }
    }

# Main app section for finding health centers
with tab4:
    st.header("संसाधन")
    st.markdown("### निकटतम स्वास्थ्य केंद्र ढूंढें")
    
    # Input columns
    col1, col2 = st.columns(2)
    
    with col1:
        city_pin = st.text_input("अपना शहर या पिन कोड दर्ज करें")
        facility_type = st.selectbox("स्वास्थ्य सुविधा प्रकार",
                                ["अस्पताल", "क्लिनिक", "स्त्री रोग विशेषज्ञ",
                                    "स्वास्थ्य केंद्र", "परिवार नियोजन केंद्र"])
        search_button = st.button("खोजें")
    
    with col2:
        if search_button:
            if not city_pin:
                st.warning("कृपया अपना शहर या पिन कोड दर्ज करें।")
            else:
                with st.spinner("निकटतम स्वास्थ्य केंद्रों की खोज की जा रही है..."):
                    centers = search_health_centers(city_pin, facility_type)
                    
                
# Add this at the top of your app after imports
                    if 'user_location' not in st.session_state:
                        st.session_state.user_location = None

                    # Your existing code...
                    if centers:
                        # Display map with health centers
                        df = pd.DataFrame(centers)
                        st.map(df[['lat', 'lon']])
                        
                        # Display detailed list of health centers
                        st.markdown("### निकटतम स्वास्थ्य केंद्र")
                        st.write(f"**{facility_type}** के लिए {len(centers)} परिणाम मिले:")
                        
                        for i, center in enumerate(centers, 1):
                            with st.expander(f"{i}. {center['name']} - {center['distance']} किमी"):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**पता:** {center['address']}")
                                    st.write(f"**दूरी:** {center['distance']} किमी")
                                with col_b:
                                    st.write(f"**फोन:** {center['phone']}")
                                    
                                    # Create maps URL based on available location data
                                    if st.session_state.user_location:
                                        # If user location is available, show directions
                                        lat, lon = st.session_state.user_location
                                        maps_url = f"https://www.google.com/maps/dir/{lat},{lon}/{center['lat']},{center['lon']}"
                                        button_text = "🗺️ दिशा प्राप्त करें"
                                    else:
                                        # If no user location, just show the center location
                                        maps_url = f"https://www.google.com/maps/place/{center['lat']},{center['lon']}"
                                        button_text = "🗺️ मानचित्र पर देखें"
                                    
                                    # Remove the key parameter - st.link_button doesn't support it
                                    st.link_button(button_text, maps_url)
                    else:
                        st.info(f"'{city_pin}' में '{facility_type}' के लिए कोई परिणाम नहीं मिला। कृपया अलग स्थान या सुविधा प्रकार का प्रयास करें।")

        else:
            st.info("निकटतम स्थानों को खोजने के लिए अपना स्थान दर्ज करें और 'खोजें' पर क्लिक करें।")
    
    # Additional resources
    st.markdown("---")
    st.subheader("अतिरिक्त संसाधन")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **आपातकालीन नंबर**
        - एम्बुलेंस: 108
        - पुलिस: 100
        - अग्निशमन: 101
        """)
    
    with col2:
        st.markdown("""
        **महत्वपूर्ण टेस्ट**
        - हीमोग्लोबिन जांच
        - ब्लड शुगर टेस्ट
        - यूरिन टेस्ट
        - अल्ट्रासाउंड
        """)
    
    with col3:
        st.markdown("""
        **सरकारी योजनाएं**
        - जननी सुरक्षा योजना
        - आयुष्मान भारत
        - प्रधानमंत्री मातृ वंदना योजना
        """)
with tab5:
    st.header("शिक्षा")
    
    # Education section tabs
    edu_tab1, edu_tab2, edu_tab3 = st.tabs(["सामान्य स्थितियां", "स्वास्थ्य टिप्स", "अक्सर पूछे जाने वाले प्रश्न"])
    
    with edu_tab1:
        st.subheader("सामान्य अंतरंग स्वास्थ्य स्थितियां")
        
        conditions = {
            "यीस्ट संक्रमण": {
                "description": "यीस्ट संक्रमण कैंडिडा नामक एक प्रकार के फंगस के कारण होता है। यह योनि में खमीर की अधिक वृद्धि का परिणाम है।",
                "symptoms": "खुजली, जलन, लालिमा, दही जैसा सफेद स्राव, यौन संबंध के दौरान दर्द या परेशानी, मूत्र त्यागने पर जलन",
                "treatment": "एंटीफंगल क्रीम, मौखिक गोलियां, योनि सपोजिटरी। डॉक्टर आपकी स्थिति के आधार पर सबसे उपयुक्त उपचार सुझाएंगे।",
                "prevention": "सूखा रहें, ढीले कपड़े पहनें, संक्रमित होने पर जल्द इलाज कराएं, प्रोबायोटिक्स पर विचार करें।"
            },
            "बैक्टीरियल वेजिनोसिस": {
                "description": "बैक्टीरियल वेजिनोसिस योनि में बैक्टीरिया के असंतुलन के कारण होता है, जिससे प्राकृतिक बैक्टीरिया का संतुलन बिगड़ जाता है।",
                "symptoms": "पानी जैसा ग्रे/सफेद स्राव, मछली जैसी गंध, योनि में खुजली या जलन, मूत्र त्यागने पर जलन",
                "treatment": "एंटीबायोटिक्स (मौखिक या क्रीम/जेल), योनि के प्राकृतिक पीएच संतुलन को बहाल करना।",
                "prevention": "योनि धोने से बचें, सुरक्षित यौन अभ्यास करें, योनि की प्राकृतिक सफाई प्रक्रिया में हस्तक्षेप न करें।"
            },
            "ट्राइकोमोनिएसिस": {
                "description": "ट्राइकोमोनिएसिस एक यौन संचारित संक्रमण है जो ट्राइकोमोनास वजिनालिस परजीवी के कारण होता है।",
                "symptoms": "पीला/हरा मुलायम स्राव, बुरी गंध, योनि में जलन और खुजली, मूत्र त्यागने में दर्द, योनि क्षेत्र में सूजन",
                "treatment": "मेट्रोनिडाजोल या टिनिडाजोल जैसी एंटीप्रोटोजोअल दवाएं। दोनों साथियों का इलाज आवश्यक है।",
                "prevention": "कंडोम का उपयोग करें, एक निष्ठावान यौन साझेदार रखें, योनि क्षेत्र को साफ और सूखा रखें।"
            },
            "जेनिटल हरपीज": {
                "description": "जेनिटल हरपीज हरपीस सिम्प्लेक्स वायरस (HSV) के कारण होता है और प्रभावित क्षेत्रों के प्रत्यक्ष संपर्क से फैलता है।",
                "symptoms": "छोटे लाल उभार, छाले, घाव, खुजली, जलन, पीड़ा, प्रभावित क्षेत्र में कोमलता, सूजन",
                "treatment": "एंटीवायरल दवाएं लक्षणों को कम कर सकती हैं और प्रकोपों की अवधि को कम कर सकती हैं, लेकिन कोई इलाज नहीं है।",
                "prevention": "कंडोम का उपयोग करें, सक्रिय हरपीज घावों वाले किसी भी व्यक्ति के साथ त्वचा-से-त्वचा संपर्क से बचें।"
            },
            "चलैमिडिया": {
                "description": "चलैमिडिया ट्रैकोमैटिस बैक्टीरिया के कारण होने वाला एक आम यौन संचारित संक्रमण है।",
                "symptoms": "अक्सर कोई लक्षण नहीं, लेकिन इसमें असामान्य योनि स्राव, मूत्र त्यागने पर जलन, यौन संबंध के दौरान दर्द शामिल हो सकते हैं",
                "treatment": "एंटीबायोटिक्स, आमतौर पर एक एकल खुराक या एक सप्ताह के उपचार के रूप में। सभी यौन साझेदारों का भी इलाज किया जाना चाहिए।",
                "prevention": "कंडोम का उपयोग करें, नियमित STI परीक्षण कराएं, यौन साझेदारों की संख्या सीमित करें।"
            }
        }
        
        selected_condition = st.selectbox("एक स्थिति चुनें", list(conditions.keys()))
        
        if selected_condition:
            condition = conditions[selected_condition]
            st.markdown(f"### {selected_condition}")
            st.markdown(f"**विवरण**: {condition['description']}")
            st.markdown(f"**लक्षण**: {condition['symptoms']}")
            st.markdown(f"**उपचार**: {condition['treatment']}")
            st.markdown(f"**रोकथाम**: {condition['prevention']}")
            
            st.warning("यह जानकारी केवल शैक्षिक उद्देश्यों के लिए है। सटीक निदान और उपचार के लिए हमेशा स्वास्थ्य देखभाल पेशेवर से परामर्श करें।")
    
    with edu_tab2:
        st.subheader("अंतरंग स्वास्थ्य के लिए जरूरी स्वास्थ्य टिप्स")
        
        st.markdown("""
        ### दैनिक अंतरंग स्वास्थ्य देखभाल
        
        #### 1. उचित स्वच्छता
        - हल्के, सुगंध रहित, हाइपोएलर्जेनिक साबुन से केवल बाहरी क्षेत्र धोएं
        - कभी भी योनि के अंदर साबुन न लगाएं
        - आगे से पीछे की ओर पोंछें
        - अच्छी तरह से सूखा लें
        
        #### 2. सही कपड़े
        - ढीले, सूती अंडरवियर पहनें
        - सोते समय अंडरवियर को बदलें या बिना अंडरवियर सोएं
        - तंग सिंथेटिक कपड़ों से बचें
        - गीले स्विमसूट या कसरत के कपड़ों में लंबे समय तक न रहें
        
        #### 3. मासिक धर्म स्वच्छता
        - टैंपोन या सैनिटरी पैड को हर 4-6 घंटे में बदलें
        - रात में टैंपोन का उपयोग करने से बचें
        - मेन्स्ट्रुअल कप्स को 12 घंटे में एक बार खाली करें और साफ करें
        - सुरक्षित, गुणवत्तापूर्ण मासिक धर्म उत्पादों का उपयोग करें
        
        #### 4. सुरक्षित यौन अभ्यास
        - गर्भनिरोधक के लिए कंडोम का उपयोग करें और एसटीआई से बचें
        - यौन संपर्क के बाद पेशाब करें
        - यौन उपकरणों को हर उपयोग के बाद साफ करें
        - यदि परेशानी हो तो यौन गतिविधि को रोकें
        
        #### 5. आहार और हाइड्रेशन
        - प्रति दिन 8-10 गिलास पानी पिएं
        - संतुलित आहार लें जिसमें प्रचुर मात्रा में फल और सब्जियां हों
        - प्रोबायोटिक खाद्य पदार्थों को शामिल करें जैसे दही और किन्वा
        - अत्यधिक चीनी, कैफीन और अल्कोहल से बचें
        """)
        
        st.markdown("""
        ### गलत धारणाएं और तथ्य
        
        | गलत धारणा | तथ्य |
        |------------|------|
        | योनि को नियमित रूप से डूश करना चाहिए | डूशिंग अंतरंग क्षेत्र के प्राकृतिक संतुलन को बाधित करती है और संक्रमण का खतरा बढ़ा सकती है |
        | अंतरंग क्षेत्र को सुगंधित या विशेष उत्पादों से साफ करने की आवश्यकता है | केवल गुनगुने पानी और हल्के साबुन की आवश्यकता होती है; विशेष उत्पाद अक्सर अधिक नुकसान पहुंचाते हैं |
        | सभी योनि स्राव असामान्य होते हैं | स्वस्थ योनि में प्राकृतिक स्राव होता है जो मासिक चक्र के दौरान बदलता रहता है |
        | अंतरंग स्वास्थ्य समस्याएं हमेशा लक्षण दिखाती हैं | कई गंभीर स्थितियों में भी कोई लक्षण नहीं हो सकते हैं - नियमित जांच महत्वपूर्ण है |
        | मासिक धर्म के दौरान स्नान करना हानिकारक है | स्नान सुरक्षित है और वास्तव में साफ-सफाई बनाए रखने में सहायता कर सकता है |
        """)
        
        st.info("स्वस्थ वार्तालाप: अपने चिकित्सक से अंतरंग स्वास्थ्य के बारे में बात करने से न डरें। आपकी चिंताएं वैध हैं और पेशेवर देखभाल के लायक हैं।")
    
    with edu_tab3:
        st.subheader("अक्सर पूछे जाने वाले प्रश्न")
        
        faqs = {
            "मुझे स्त्री रोग विशेषज्ञ के पास कब जाना चाहिए?": """
            निम्नलिखित स्थितियों में स्त्री रोग विशेषज्ञ के पास जाएं:
            - वार्षिक नियमित जांच के लिए
            - असामान्य योनि स्राव या गंध
            - योनि में असामान्य रक्तस्राव
            - अंतरंग क्षेत्र में दर्द, सूजन या असुविधा
            - यौन संबंध के दौरान दर्द
            - अनियमित, भारी या दर्दनाक मासिक धर्म
            - गर्भधारण की योजना बनाते समय
            - गर्भनिरोधक या एचआरटी पर चर्चा के लिए
            """,
            
            "क्या लेधर तेल और वैसलीन जैसे घरेलू उत्पादों का उपयोग अंतरंग क्षेत्र में लुब्रिकेशन के लिए किया जा सकता है?": """
            नहीं, घरेलू तेलों या पेट्रोलियम-आधारित उत्पादों (जैसे वैसलीन) का उपयोग अंतरंग क्षेत्र में नहीं किया जाना चाहिए।
            
            कारण:
            - ये उत्पाद कंडोम और अन्य बैरियर के साथ उपयोग करने पर क्षतिग्रस्त हो सकते हैं
            - संक्रमण और बैक्टीरियल वेजिनोसिस का खतरा बढ़ सकता है
            - त्वचा जलन या एलर्जी प्रतिक्रिया हो सकती है
            
            केवल पानी या सिलिकॉन आधारित चिकित्सकीय लुब्रिकेंट का उपयोग करें जो अंतरंग उपयोग के लिए विशेष रूप से बनाए गए हैं।
            """,
            
            "क्या बार-बार होने वाले यीस्ट संक्रमण सामान्य हैं?": """
            यीस्ट संक्रमण आम हैं, और कई महिलाओं को जीवन में कभी न कभी कम से कम एक होता है। हालांकि, एक वर्ष में 4 या अधिक संक्रमण होना ("आवर्ती यीस्ट संक्रमण") आमतौर पर निम्न के कारण हो सकता है:
            
            - गर्भनिरोधक का प्रकार
            - हार्मोनल परिवर्तन
            - एंटीबायोटिक का उपयोग
            - अनियंत्रित मधुमेह
            - कमजोर प्रतिरक्षा प्रणाली
            - कुछ साबुन या अन्य उत्पादों के प्रति प्रतिक्रिया
            
            यदि आप बार-बार यीस्ट संक्रमण का अनुभव करते हैं, तो अंतर्निहित कारणों का पता लगाने और अधिक प्रभावी प्रबंधन योजना विकसित करने के लिए डॉक्टर से परामर्श करें।
            """,
            
            "क्या मासिक धर्म के दौरान यौन गतिविधि सुरक्षित है?": """
            हां, मासिक धर्म के दौरान यौन संबंध बनाना पूरी तरह से सुरक्षित है अगर दोनों पार्टनर सहज हों। कुछ बातें ध्यान में रखें:
            
            - कंडोम का उपयोग अभी भी एसटीआई से सुरक्षा प्रदान करता है और गड़बड़ी को कम करता है
            - तौलिया बिछाकर या शॉवर में संबंध बनाकर सफाई को आसान बनाएं
            - मासिक कप या स्पंज उपयोग करने पर विचार करें
            - अगर आपको एंडोमेट्रियोसिस या अन्य स्थितियां हैं, तो आपको इस दौरान अधिक दर्द हो सकता है
            
            याद रखें, आप अभी भी मासिक धर्म के दौरान गर्भवती हो सकती हैं, इसलिए अगर आप गर्भधारण नहीं चाहती हैं तो गर्भनिरोधक का उपयोग करें।
            """,
            
            "मैं अपने अंतरंग क्षेत्र में बाल कैसे प्रबंधित करूं?": """
            अंतरंग क्षेत्र के बालों का प्रबंधन एक व्यक्तिगत पसंद है। यदि आप इसे प्रबंधित करना चाहते हैं:
            
            सुरक्षित विकल्प:
            - ट्रिमिंग - सबसे कम जोखिम वाला विकल्प
            - शेविंग - सावधानी से करें, नए ब्लेड का उपयोग करें, और स्वच्छ रखें
            - डिपिलेटरी क्रीम - पहले पैच टेस्ट करें और संवेदनशील त्वचा फॉर्मूले का उपयोग करें
            - वैक्सिंग - पेशेवर से करवाएं या घर पर सावधानी से करें
            - लेजर - लंबे समय के समाधान के लिए पेशेवर से परामर्श करें
            
            याद रखें:
            - जनन अंगों के बाल प्राकृतिक हैं और उनकी अंतरंग क्षेत्र को सुरक्षित रखने में भूमिका है
            - हमेशा स्वच्छता का पालन करें
            - जलन या जख्म होने पर तुरंत बंद कर दें
            """,
            
            "क्या pH असंतुलन वास्तव में अंतरंग स्वास्थ्य समस्याओं का कारण बनता है?": """
            हां, योनि का pH स्तर महत्वपूर्ण है। स्वस्थ योनि थोड़ी अम्लीय होती है (pH लगभग 3.8 से 4.5), जो अवांछित बैक्टीरिया और यीस्ट को पनपने से रोकने में मदद करती है।
            
            pH असंतुलन से निम्नलिखित हो सकते हैं:
            - बैक्टीरियल वेजिनोसिस
            - यीस्ट संक्रमण
            - योनि की जलन या परेशानी
            - अन्य प्रकार के संक्रमण के लिए अधिक संवेदनशीलता
            
            निम्नलिखित कारणों से pH असंतुलित हो सकता है:
            - साबुन, डूश, स्प्रे या परफ्यूम का उपयोग
            - मासिक धर्म (रक्त अधिक क्षारीय है)
            - वीर्य (अधिक क्षारीय है)
            - कुछ दवाओं का उपयोग
            - हार्मोनल परिवर्तन
            
            अपने योनि के प्राकृतिक संतुलन को बनाए रखें:
            - अंतरंग क्षेत्र के धोने के लिए केवल पानी या हल्के, सुगंध रहित साबुन का उपयोग करें
            - डूश से बचें
            - सूती अंडरवियर पहनें
            - प्रोबायोटिक खाद्य पदार्थ खाएं
            """,
        }
        
        for question, answer in faqs.items():
            with st.expander(question):
                st.markdown(answer)

# Footer
st.markdown("---")
st.markdown("© 2023 YSHY - आपका स्मार्ट हेल्थकेयर यार्डस्टिक | **यह एप्लिकेशन चिकित्सकीय देखभाल का विकल्प नहीं है**")

