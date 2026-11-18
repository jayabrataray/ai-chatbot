# Deployment Guide (Streamlit Cloud)

1. Push your repository to GitHub (`main` branch).
2. Sign in to [share.streamlit.io](https://share.streamlit.io/) and select `jayabrataray/ai-chatbot`.
3. Set **Main file path** to `app.py`.
4. Open **Advanced settings -> Secrets** and add:
   ```toml
   OPENROUTER_API_KEY = "sk-or-v1-your-api-key-here"
   ```
5. Click **Deploy**.
