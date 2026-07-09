import streamlit as st
import requests
import time
import os

# Page configuration - Luxury Black & Gold Theme Design
st.set_page_config(
    page_title="AI Ultra-Realistic Video Generator",
    page_icon="🎥",
    layout="centered"
)

# Custom Styling for Premium Look
st.markdown("""
    <style>
    .main { background-color: #111111; color: #FFFFFF; }
    h1 { color: #D4AF37; text-align: center; font-family: 'Helvetica', sans-serif; }
    .stButton>button { background-color: #D4AF37; color: #111111; font-weight: bold; border-radius: 5px; width: 100%; }
    .stButton>button:hover { background-color: #AA7C11; color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

st.title("🎥 AI Ultra-Realistic Video Generator")
st.write("Apni picture upload karein, script likhein aur realistic AI video generate karein.")

# --- API KEYS SETUP ---
HEYGEN_API_KEY = st.sidebar.text_input("Apni HeyGen API Key Dalein", type="password")

# --- UI INPUTS ---
uploaded_file = st.file_uploader("Step 1: Apni Target Picture Upload Karein (Clear Face)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", width=250)

script_text = st.text_area("Step 2: Apni Mukammal Script Likhein", placeholder="Yahan wo sab likhein jo aap video mein bulwana chahte hain...", height=150)

# --- VIDEO GENERATION LOGIC ---
if st.button("Generate Realistic Video ✨"):
    if not HEYGEN_API_KEY:
        st.error("Bhai, pehle side-bar mein apni HeyGen API Key dalein!")
    elif not uploaded_file or not script_text:
        st.error("Bhai, picture aur script dono dena zaroori hai.")
    else:
        st.info("Video generation request bhej di gayi hai. Realistic rendering mein thoda waqt lagta hai...")
        
        try:
            # --- V2 METHOD: Get Extension ---
            file_extension = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
            if file_extension == 'jpg':
                file_extension = 'jpeg'
                
            # 1. STEP 1 OF V2: Get Presigned URL for Upload
            get_url = f"https://api.heygen.com/v2/asset/upload?filename={uploaded_file.name}"
            headers_v2 = {
                "accept": "application/json",
                "X-Api-Key": HEYGEN_API_KEY
            }
            
            get_response = requests.get(get_url, headers=headers_v2)
            
            if get_response.status_code == 200:
                upload_data = get_response.json().get("data", {})
                upload_url = upload_data.get("upload_url")
                image_id = upload_data.get("id")
                
                # 2. STEP 2 OF V2: Upload the actual file binary to the S3 Presigned URL
                content_type = f"image/{file_extension}"
                upload_headers = {"Content-Type": content_type}
                
                file_binary = uploaded_file.getvalue()
                upload_file_response = requests.put(upload_url, data=file_binary, headers=upload_headers)
                
                if upload_file_response.status_code == 200 or upload_file_response.status_code == 201:
                    st.success("Image successfully upload ho gayi! Ab video generate ho rahi hai...")
                    
                    # 3. STEP 3 OF V2: Video Generation Request
                    video_url = "https://api.heygen.com/v2/video/generate"
                    headers_video = {
                        "X-Api-Key": HEYGEN_API_KEY,
                        "Content-Type": "application/json",
                        "accept": "application/json"
                    }
                    
                    payload = {
                        "caption": False,
                        "dimension": {"width": 1080, "height": 1920},
                        "video_setting": {"subtitles": False},
                        "clips": [
                            {
                                "avatar": {
                                    "avatar_id": image_id,
                                    "avatar_type": "talking_photo",
                                    "style": "normal"
                                },
                                "voice": {
                                    "voice_id": "ur-PK-AsadNeural",
                                    "type": "text"
                                },
                                "input_text": script_text
                            }
                        ]
                    }
                    
                    response = requests.post(video_url, json=payload, headers=headers_video)
                    
                    if response.status_code == 200:
                        video_id = response.json().get("data", {}).get("video_id")
                        st.success("Rendering shuru ho chuki hai! Final status check ho raha hai...")
                        
                        # 4. Polling for Video Status (V2 checks status via v1 endpoint)
                        status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
                        
                        while True:
                            time.sleep(10)
                            status_response = requests.get(status_url, headers={"X-Api-Key": HEYGEN_API_KEY})
                            
                            if status_response.status_code == 200:
                                video_data = status_response.json().get("data", {})
                                status = video_data.get("status")
                                
                                if status == "completed":
                                    final_video_url = video_data.get("video_url")
                                    st.success("🎉 Bhai, Aapki Ultra-Realistic Video Tayyar Hai!")
                                    st.video(final_video_url)
                                    break
                                elif status == "failed":
                                    st.error("Video rendering fail ho gayi. Script ya image format check karein.")
                                    break
                            else:
                                st.error("Status check karne mein error aa raha hai.")
                                break
                    else:
                        st.error(f"Video Generation Error: {response.text}")
                else:
                    st.error(f"Binary Upload Error (Status {upload_file_response.status_code}): {upload_file_response.text}")
            else:
                st.error(f"Presigned URL Error (Status {get_response.status_code}): {get_response.text}")
                
        except Exception as e:
            st.error(f"Execution Error: {str(e)}")
