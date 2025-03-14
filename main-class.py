import time
import random
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import ollama
import matplotlib.pyplot as plt
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
import re
import yfinance as yf
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class CompanyScraper:
    def __init__(self):
        self.df = pd.DataFrame(columns=[
            'LinkedIn URL', 'Yahoo Finance URL', 'Official Website', 'Location',
            'Overview', 'Email', 'Product Services', 'Recent News', 'Awards'
        ])

        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        
        self.driver = uc.Chrome(options=options, version_main=133)

        # Default search sources
        self.sources = ["linkedin company profile", "yahoo finance", "official website"]
        self.google_search = "https://www.bing.com/search?q="

    def extract_email_regex(self, text):
        # Simple email pattern (you can expand it later)
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def add_labels(self, x, y):
        for i in range(len(x)):
            plt.text(x[i], y[i], f'{y[i]:,.0f}', fontsize=9, ha='center', va='bottom')

    def scrape_company(self, company_name):
        urls = []
        driver = self.driver
        sources = self.sources
        google_search = self.google_search
        df = self.df
        
        for i in range(len(sources)):
            query = f"{google_search}{company_name} {sources[i]}"
            driver.get(query)
            time.sleep(1)  # Should ideally be replaced by WebDriverWait
            
            links = driver.find_elements(By.TAG_NAME, 'a')
        
            print(links)
        
            print(f"\n==== Source: {sources[i]} ====")
            
            # Print all hrefs (for debugging)
            for link in links:
                href = link.get_attribute('href')
                # print(href)
        
            found_url = None

            if i == 0:  # LinkedIn
                for link in links:
                    href = link.get_attribute('href')
                    if href and 'linkedin.com/company/' in href:
                        found_url = href
                        # print(f"Found LinkedIn: {found_url}")
                        break

            elif i == 1:  # Yahoo Finance
                for link in links:
                    href = link.get_attribute('href')
                    if href and 'finance.yahoo.com/quote/' in href:
                        found_url = href
                        # print(f"Found Yahoo Finance: {found_url}")
                        break
        
            else:  # Official website
                for link in links:
                    href = link.get_attribute('href')
                    if href and 'bing.com' not in href and href.startswith('http'):
                        found_url = href
                        # print(f"Found Official Site: {found_url}")
                        break
        
            urls.append(found_url if found_url else 'Not Found')

        texts = []

        tags_to_find = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        urls.append('https://www.bing.com/search?q=' + company_name + '+headquarter+address')
        urls.append('https://www.bing.com/search?q=' + company_name + '+awards')
        urls.append('https://www.bing.com/search?q=' + company_name + '+recent+news')
        urls.append('https://www.bing.com/search?q=' + company_name + '+support+email+address')
        contexts = ['LinkedIn: \n', 'Yahoo Finance: \n', 'Official Website: \n', 'Location: \n', 'Awards: \n', 'Recent News: \n', 'Email: \n']
        
        for i in range(len(urls)):
        
            if urls[i] != 'Not Found':
                driver.get(urls[i])
            
                time.sleep(1)
                
                page_text = ""
                
                for tag in tags_to_find:
                    elements = driver.find_elements(By.TAG_NAME, tag)
        
                    if elements:
                        for element in elements:
                            text = element.text.strip()
                            if text:  # only append if text is not empty
                                page_text += text + "\n"
            
                texts.append(contexts[i])
                texts.append(page_text)
            else:
                page_text = ""
                texts.append(contexts[i])
                texts.append(page_text)

        # Assuming texts contains all the text from the page
        full_text = "\n".join(texts)
        
        # Craft a specific instruction for the model
        prompts = [
            f"""
            Here is the information you need to answer the question:
            {full_text}
        
            Explain a bit about the {company_name}!
            """,
        
            f"""
            Here is the information you need to answer the question:
            {full_text}
        
            What are the product & services of the {company_name}? If not found, then just explain what the company do.
            """,
        
            f"""
            Here is the information you need to answer the question:
            {texts[12]+texts[13]}
        
            What are the emails found above? Mention as much emails as possible found in the text.
            """,
        
            f"""
            Here is the information you need to answer the question:
            {texts[8] + texts[9]}
        
            List the awards based on the information above!
            """,
        
            f"""
            Here is the latest news of a company:
            {texts[10] + texts[11]}
        
            Please restructure the news text!
            """,
        
            f"""
            Here is the details of {company_name} location:
            {texts[6] + texts[7]}
        
            Where is the address/location of {company_name} headquarter based on the information?
            """,
        ]
        
        answer = []
        
        for i in range(len(prompts)):
            response = ollama.chat(
                model='phi',  # or 'phi' depending on your model name
                messages=[
                    {'role': 'user', 'content': prompts[i]}
                ]
            )
        
            answer.append(response['message']['content'])
        
        df.loc[len(df)] = [urls[0], urls[1], urls[2], answer[5], answer[0], answer[2], answer[1], answer[4], answer[3]]
        df = df.applymap(lambda x: x.replace('\n', '') if isinstance(x, str) else x)

        df['Email'] = df['Email'].apply(self.extract_email_regex)

        # Initialize ticker
        ticker = yf.Ticker(urls[1].split('/')[-2])
        
        # Get financial data
        income_statement = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow_statement = ticker.cashflow
        info = ticker.info

        income_statement = income_statement.reset_index()
        balance_sheet = balance_sheet.reset_index()
        cashflow_statement = cashflow_statement.reset_index()

        columns = income_statement.columns.tolist()

        for i in range(1, len(columns)):
            columns[i] = columns[i].year
        
        income_statement.columns = columns
        
        columns = balance_sheet.columns.tolist()
        
        for i in range(1, len(columns)):
            columns[i] = columns[i].year
        
        balance_sheet.columns = columns
        
        columns = cashflow_statement.columns.tolist()
        
        for i in range(1, len(columns)):
            columns[i] = columns[i].year
        
        cashflow_statement.columns = columns
        
        financial_model = pd.concat([income_statement, balance_sheet], axis=0)
        financial_model = pd.concat([financial_model, cashflow_statement], axis=0)

        needed_features = ['Net Income', 'Operating Revenue', 'Gross Profit', 'EBIT', 'Free Cash Flow']
        financial_model = financial_model[financial_model['index'].isin(needed_features)].reset_index(drop=True)

        # Years (raw, from your table headers)
        years = [2023, 2022, 2021, 2020]
        
        # Raw data values (no conversion)
        operating_revenue = financial_model.iloc[3].tolist()[1:]
        gross_profit = financial_model.iloc[2].tolist()[1:]
        ebit = financial_model.iloc[0].tolist()[1:]
        net_income = financial_model.iloc[1].tolist()[1:]
        free_cash_flow = financial_model.iloc[4].tolist()[1:]
        
        # Plotting
        plt.figure(figsize=(12, 7))
        
        # Plot each line
        plt.plot(years, operating_revenue, marker='o', label='Operating Revenue')
        plt.plot(years, gross_profit, marker='o', label='Gross Profit')
        plt.plot(years, ebit, marker='o', label='EBIT')
        plt.plot(years, net_income, marker='o', label='Net Income')
        plt.plot(years, free_cash_flow, marker='o', label='Free Cash Flow')
        
        # Call add_labels() for each line
        self.add_labels(years, operating_revenue)
        self.add_labels(years, gross_profit)
        self.add_labels(years, ebit)
        self.add_labels(years, net_income)
        self.add_labels(years, free_cash_flow)
        
        # Styling
        plt.title('GOTO Financial Model (2020 - 2023)', fontsize=16)
        plt.xlabel('Year')
        plt.ylabel('Amount ($)')
        plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
        plt.grid(True, linestyle='--', linewidth=0.5)
        plt.legend()
        plt.xticks(years)
        plt.tight_layout()
        plt.savefig(company_name + "_finance.png")
        financial_model.to_csv(company_name + "_finance.csv")

        return df

    def save(self, df):
        if 'data.csv' in os.listdir():
            data = pd.read_excel('data.xlsx', engine='openpyxl')
            data = pd.concat([data, df], axis = 0).reset_index(drop=True)
            data.to_csv('data.csv')
            data.to_excel('data.xlsx')
        else:
            df.to_csv('data.csv')
            df.to_excel('data.xlsx')
    
