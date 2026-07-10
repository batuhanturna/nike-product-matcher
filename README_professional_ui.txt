Nike Professional Streamlit UI

Files:
- streamlit_app.py

Install:
pip install streamlit pandas pyvis

Run:
streamlit run streamlit_app.py

Notes:
- This version loads the embedding model only when the user starts a search or adds a product.
- Product images are shown in cards and graph nodes when image_url exists in the database.
