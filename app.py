import streamlit as st
import joblib
import os

# Set page configuration
st.set_page_config(page_title="Spam Detection System", page_icon="📧", layout="centered")

# Load the model and vectorizer
MODEL_PATH = 'model.pkl'
VECTORIZER_PATH = 'vectorizer.pkl'

@st.cache_resource
def load_models():
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        return model, vectorizer
    else:
        return None, None

model, vectorizer = load_models()

# App UI
st.title("📧 Spam Email/SMS Detection System")
st.markdown("""
Welcome to the Spam Detection System! 
Enter your email or SMS message below to check if it's **Spam** or **Not Spam (Ham)**.
""")

st.write("---")

user_input = st.text_area("Enter your message here:", height=150, placeholder="e.g., Congratulations! You've won a $1000 Walmart gift card. Click here to claim now.")

if st.button("Check Message", type="primary"):
    if not user_input.strip():
        st.warning("Please enter a message to classify.")
    else:
        if model is None or vectorizer is None:
            st.error("Model or Vectorizer not found! Please run the `spam_detection.ipynb` notebook first to train and save the model.")
        else:
            with st.spinner("Analyzing message..."):
                # Preprocess and predict
                transformed_input = vectorizer.transform([user_input])
                prediction = model.predict(transformed_input)[0]
                
                if prediction == 1:
                    st.error("🚨 **Spam Detected!** This message looks suspicious.")
                else:
                    st.success("✅ **Not Spam!** This message appears to be safe.")

st.write("---")
st.caption("Built with Streamlit • Machine Learning Pipeline powered by Scikit-Learn")
