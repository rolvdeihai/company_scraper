import streamlit as st
from CompanyScraperClass import CompanyScraper  # Assuming you move your scraper to scraper_module.py
import pandas as pd
import matplotlib.pyplot as plt
import base64
import os

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Company Scraper", layout="wide")

# ------------------ TITLE ------------------
st.title("🔍 Company Data Scraper & Analyzer")

# ------------------ INIT SESSION STATE ------------------
if "company_name" not in st.session_state:
    st.session_state.company_name = ""

if "df_result" not in st.session_state:
    st.session_state.df_result = None

if "error_message" not in st.session_state:
    st.session_state.error_message = None

# ------------------ SCRAPER INSTANCE ------------------
scraper = CompanyScraper()

# ------------------ FUNCTIONS ------------------
def scrape_callback():
    company = st.session_state.input_company.strip()
    if not company:
        st.warning("Please enter a company name.")
        return

    with st.spinner("Scraping in progress... this may take a few minutes ⏳"):
        try:
            df_result, error_message = scraper.scrape_company(company)

            st.session_state.company_name = company
            st.session_state.df_result = df_result
            st.session_state.error_message = error_message

            if error_message != 'N/A':
                st.error(f"⚠️ An error occurred: {error_message}")
            else:
                st.success(f"✅ Scraping complete for '{company}'!")

        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

def update_data_callback():
    if st.session_state.df_result is None:
        st.warning("No data to update. Please scrape a company first.")
        return

    try:
        scraper.save(st.session_state.df_result)
        st.success("✅ Data updated and saved successfully!")
    except Exception as e:
        st.error(f"❌ Failed to update data: {e}")

def download_link(data, filename, link_text, mime):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:{mime};base64,{b64}" download="{filename}">{link_text}</a>'
    st.markdown(href, unsafe_allow_html=True)

# ------------------ INPUT SECTION ------------------
st.text_input("Enter the company name you want to scrape:",
              key="input_company")

# Scrape Button
st.button("🚀 Scrape Company Data", on_click=scrape_callback)

# ------------------ RESULTS DISPLAY ------------------
if st.session_state.df_result is not None:
    company_name = st.session_state.company_name
    df_result = st.session_state.df_result

    st.markdown("---")
    st.subheader(f"📄 Scraped Info for **{company_name}**")

    st.dataframe(df_result)

    # CSV Download
    csv = df_result.to_csv(index=False).encode()
    download_link(csv, f"{company_name}_data.csv", "📥 Download CSV", "text/csv")

    # Update Data Button
    st.button("💾 Update Data", on_click=update_data_callback)

    # Show Plot
    st.subheader("📊 Financial Model Plot")
    results_folder = "results"
    image_filename = f"{company_name}_finance.png"
    image_path = os.path.join(results_folder, image_filename)

    if os.path.exists(image_path):
        st.image(image_path, caption="📊 Financial Model Plot")

        # Download Plot Button
        with open(image_path, "rb") as img_file:
            download_link(img_file.read(), f"{company_name}_finance.png", "📥 Download Financial Chart", "image/png")
    else:
        st.warning(f"No plot found at {image_path}. Did the scraper generate it?")

# ------------------ DEFAULT INFO ------------------
else:
    st.info("Enter a company name and press **Scrape Company Data** to start scraping.")

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("🚀 Made with Streamlit, Selenium & Ollama | Jethro Elijah Lim")
