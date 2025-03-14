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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import platform
import subprocess

class CompanyScraper:
    def __init__(self):
        self.df = pd.DataFrame(columns=[
            'LinkedIn URL', 'Yahoo Finance URL', 'Official Website', 'Location',
            'Overview', 'Email', 'Product Services', 'Recent News', 'Awards'
        ])

        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        
        chrome_major_version = self.get_chrome_major_version()
        if chrome_major_version:
            print(f"Detected Chrome major version: {chrome_major_version}")
            self.driver = uc.Chrome(options=options, version_main=chrome_major_version)
        else:
            for version in range(60, 200):
                try:
                    print(f"Trying fallback version: {version}")
                    self.driver = uc.Chrome(options=options, version_main=version)
                    print(f"Successfully started driver with fallback version: {version}")
                    break
                except Exception as e:
                    print(f"Failed with fallback version {version}: {e}")
            else:
                raise Exception("Unable to start Chrome driver with any version.")
                
        self.sources = ["linkedin company profile", "yahoo finance", "official website"]
        self.google_search = "https://www.bing.com/search?q="

    def get_chrome_major_version(self):
        system = platform.system()
        version = ""
    
        try:
            if system == "Windows":
                process = subprocess.run(
                    [r'reg', 'query', r'HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon', '/v', 'version'],
                    capture_output=True, text=True, check=True
                )
                # Extract version number from the output
                version_line = process.stdout.strip().split('\n')[-1]
                version = version_line.split()[-1]

            elif system == "Darwin":  # macOS
                process = subprocess.run(
                    ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                    capture_output=True, text=True, check=True
                )
                version = process.stdout.strip().replace("Google Chrome ", "")
    
            elif system == "Linux":
                process = subprocess.run(
                    ["google-chrome", "--version"], capture_output=True, text=True, check=True
                )
                version = process.stdout.strip().replace("Google Chrome ", "")
    
            else:
                print("Unsupported OS")
                return None
    
            # Extract the major version (before the first dot)
            major_version = int(re.match(r"(\d+)", version).group(1))
            return major_version
    
        except Exception as e:
            print(f"Error detecting Chrome version: {e}")
            return None

    def extract_email_regex(self, text):
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(pattern, text)
        return emails if emails else None

    def add_labels(self, x, y):
        for i in range(len(x)):
            plt.text(x[i], y[i], f'{y[i]:,.0f}', fontsize=9, ha='center', va='bottom')

    def scrape_company(self, company_name):
        MAX_RETRIES = 1  # Same retry limit for consistency
        urls = []
        driver = self.driver
        sources = self.sources
        google_search = self.google_search
        df = self.df
        
        for i in range(len(sources)):
            query = f"{google_search}{company_name} {sources[i]}"
            driver.get(query)
        
            time.sleep(1)
        
            links = driver.find_elements(By.TAG_NAME, 'a')
            print(f"\n==== Source: {sources[i]} ====")
        
            found_url = None
        
            if i == 0:  # LinkedIn
                for link in links:
                    retries = 0
                    href = None
                    while retries < MAX_RETRIES:
                        try:
                            href = link.get_attribute('href')
                            break  # Success!
                        except StaleElementReferenceException:
                            retries += 1
                            print(f"Retrying href ({retries}/{MAX_RETRIES}) for LinkedIn source")
                            time.sleep(0.5)
                    else:
                        print("Skipped link after retries (LinkedIn)")
                        continue
        
                    if href and 'linkedin.com/company/' in href:
                        found_url = href
                        break
        
            elif i == 1:  # Yahoo Finance
                for link in links:
                    retries = 0
                    href = None
                    while retries < MAX_RETRIES:
                        try:
                            href = link.get_attribute('href')
                            break  # Success!
                        except StaleElementReferenceException:
                            retries += 1
                            print(f"Retrying href ({retries}/{MAX_RETRIES}) for Yahoo Finance source")
                            time.sleep(0.5)
                    else:
                        print("Skipped link after retries (Yahoo Finance)")
                        continue
        
                    if href and 'finance.yahoo.com/quote/' in href:
                        found_url = href
                        break
        
            else:  # Official website
                for link in links:
                    retries = 0
                    href = None
                    while retries < MAX_RETRIES:
                        try:
                            href = link.get_attribute('href')
                            break  # Success!
                        except StaleElementReferenceException:
                            retries += 1
                            print(f"Retrying href ({retries}/{MAX_RETRIES}) for Official Website source")
                            time.sleep(0.5)
                    else:
                        print("Skipped link after retries (Official Website)")
                        continue
        
                    if href and 'bing.com' not in href and href.startswith('http'):
                        found_url = href
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
        
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
        
                page_text = ""
        
                MAX_RETRIES = 1
        
                for tag in tags_to_find:
                    elements = driver.find_elements(By.TAG_NAME, tag)
        
                    if elements:
                        for element in elements:
                            retries = 0
                            while retries < MAX_RETRIES:
                                try:
                                    text = element.text.strip()
                                    if text:
                                        page_text += text + "\n"
                                    break  # Success! break out of the retry loop
                                except StaleElementReferenceException:
                                    retries += 1
                                    print(f"Retrying {retries}/{MAX_RETRIES} for tag: {tag}")
                                    time.sleep(0.5)  # optional: small delay before retrying
                            else:
                                print(f"Skipped element after {MAX_RETRIES} retries for tag: {tag}")
                                continue

                texts.append(contexts[i])
                texts.append(page_text)
        
            else:
                page_text = ""
                texts.append(contexts[i])
                texts.append(page_text)

        # Assuming texts contains all the text from the page
        full_text = "\n".join(texts[0:6])
        
        # Craft a specific instruction for the model
        prompts = [
            f"""
            Here is the information you need to answer the question:
            {full_text}
        
            Explain a bit about the {company_name}! Answer confidently!
            """,
        
            f"""
            Here is the information you need to answer the question:
            {full_text}
        
            What are the product & services of the {company_name}? If not found, then just explain what the company do.
            """,
        
            # f"""
            # Here is the information you need to answer the question:
            # {texts[12]+texts[13]}
        
            # What are the emails found above? Mention as much emails as possible found in the text.
            # """,
        
            f"""
            Here is the information you need to answer the question:
            {texts[8] + texts[9]}
        
            List the awards based on the information above! Answer confidently!
            """,
        
            f"""
            Here is the latest news of a company:
            {texts[10] + texts[11]}
        
            Just explain whats on the text! Answer confidently!
            """,
        
            f"""
            Here is the details of {company_name} company headquarters address or location:
            {texts[6] + texts[7]}
        
            Where is the address or location of {company_name} headquarters based on the given information?
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
        
        df.loc[len(df)] = [urls[0], urls[1], urls[2], answer[4], answer[0], texts[13], answer[1], answer[3], answer[2]]
        # df = df.applymap(lambda x: x.replace('\n', '') if isinstance(x, str) else x)

        df['Email'] = df['Email'].apply(self.extract_email_regex)

        error_message = "N/A"

        # Initialize ticker
        if (urls[1] != 'Not Found'):
            try:
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
                financial_model = financial_model.dropna(axis=1, how='all')
                print(financial_model)
        
                # Years (raw, from your table headers)
                years = list(financial_model.columns)[1:]
                
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
                plt.title(company_name + ' Financial Model (' + str(years[len(years)-1]) + ' - ' + str(years[1]) + ')', fontsize=16)
                plt.xlabel('Year')
                plt.ylabel('Amount ($)')
                plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
                plt.grid(True, linestyle='--', linewidth=0.5)
                plt.legend()
                plt.xticks(years)
                plt.tight_layout()
                results_folder = 'results'
    
                if not os.path.exists(results_folder):
                    os.makedirs(results_folder)
                    print(f"Created folder: {results_folder}")
                
                # Define file paths inside the results folder
                plot_path = os.path.join(results_folder, f"{company_name}_finance.png")
                csv_path = os.path.join(results_folder, f"{company_name}_finance.csv")
                
                # Save plot and CSV to the results folder
                plt.savefig(plot_path)
                financial_model.to_csv(csv_path)
                
            except IndexError:
                error_message = "Financial information not found (IndexError). Data is saved. You may try again later."
            
            except KeyError:
                error_message = "Financial information not found (KeyError). Data is saved. You may try again later."
        
            except Exception:
                error_message = "Financial information not found (Unexpected Error). Data is saved. You may try again later."

            driver.close()

        return df, error_message

    def save(self, df, folder='results'):
        # Make sure the folder exists
        os.makedirs(folder, exist_ok=True)
    
        # Set file paths
        csv_path = os.path.join(folder, 'data.csv')
        excel_path = os.path.join(folder, 'data.xlsx')
    
        if os.path.exists(csv_path):
            data = pd.read_csv(csv_path)
            data = pd.concat([data, df], axis=0).reset_index(drop=True)
            data.to_csv(csv_path, index=False)
            data.to_excel(excel_path, index=False)
        else:
            df.to_csv(csv_path, index=False)
            df.to_excel(excel_path, index=False)
    
