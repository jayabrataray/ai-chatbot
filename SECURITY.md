# Security Policy

- Never commit `.env` files or hardcoded API keys to this repository.
- Local keys are loaded via `python-dotenv` from `.env` (excluded in `.gitignore`).
- Production keys on Streamlit Cloud are stored inside encrypted `st.secrets`.
