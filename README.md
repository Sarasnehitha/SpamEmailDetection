# Spam Email Detection System 📧

A complete Machine Learning project to classify emails and SMS messages as Spam or Not Spam (Ham).
This project includes an interactive Jupyter Notebook for training the model and a clean Streamlit UI for inference.

## Project Structure
- `spam_detection.ipynb`: Jupyter notebook for data downloading, preprocessing, training, evaluating, and exporting the ML model.
- `app.py`: Streamlit web application that serves the trained model for interactive user testing.
- `requirements.txt`: Python dependencies.

## Setup Instructions

1. **Install dependencies**:
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Train the Model**:
   Open the Jupyter Notebook and run all cells to download the dataset, train the Naive Bayes model, and generate `model.pkl` and `vectorizer.pkl`.
   ```bash
   jupyter notebook spam_detection.ipynb
   ```
   *(Alternatively, run the cells in VS Code's notebook interface)*

3. **Run the Web App**:
   Once the model is trained and saved, launch the Streamlit UI:
   ```bash
   streamlit run app.py
   ```
