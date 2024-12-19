import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, UnexpectedAlertPresentException

# Path to the chromedriver executable
executable_path = '/Users/narasimha/Downloads/Everything/Vayuman/Projects/Scraping/chromedriver-mac-arm64 3/chromedriver'  # Ensure this is the correct path

# Create a service object
service = Service(executable_path)

# Function to initialize the driver and navigate to the webpage without incognito mode
def initialize_driver():
    options = webdriver.ChromeOptions() 
    options.add_argument('--incognito') 

    # Use the path to Chrome Dev on macOS
    options.binary_location = '/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev'
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes")
        time.sleep(2)
        return driver
    except WebDriverException as e:
        print(f"Error initializing WebDriver: {e}")
        return None


# Function to extract data from the first seven tables
# Function to extract data from the first seven tables
def extract_data_from_page(driver):
    all_data = []
    try:
        # Wait for the tables to be present
        tables = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'statistics-table'))
        )
        # Extract data from the first seven tables
        for index, table in enumerate(tables[:9]):
            data = []
            rows = table.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                if index == 5:  # Sixth table (0-based index is 5)
                    cols = row.find_elements(By.TAG_NAME, 'th')
                    if not cols:
                        cols = row.find_elements(By.TAG_NAME, 'td')
                else:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                cols = [col.text for col in cols]
                data.append(cols)
            all_data.append(data)
    except Exception as e:
        print(f"Error extracting data from page: {e}")
    return all_data

# Function to handle unexpected alerts
def handle_unexpected_alert(driver):
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"Alert detected: {alert.text}")
        alert.accept()
    except TimeoutException:
        pass

# Retry function to handle retries with delay
def retry_function(func, max_retries=3, delay=2, *args, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except (WebDriverException, TimeoutException, UnexpectedAlertPresentException) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            handle_unexpected_alert(kwargs['driver'])
            time.sleep(delay)
    raise Exception(f"Failed after {max_retries} attempts.")

# Initialize the driver
driver = initialize_driver()
if driver is None:
    print("Failed to initialize the WebDriver.")
    exit(1)

# Function to get the number of portfolio managers
def get_number_of_managers(driver):
    try:
        select_element_portfolio_manager = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'pmrId'))
        )
        options = select_element_portfolio_manager.find_elements(By.TAG_NAME, 'option')
        return len(options)
    except Exception as e:
        print(f"Error getting number of portfolio managers: {e}")
        return 0

# Get the number of portfolio managers
number_of_managers = get_number_of_managers(driver)
print(f"Number of portfolio managers: {number_of_managers}")

# List of months
months = ['August']

# Iterate through each portfolio manager, year, and month
for manager_index in range(1, number_of_managers):  # Update to use the dynamic number of managers
    for year in range(2024, 2025):  # Update to include the years you want
        for month in months:
            try:
                # Define a function to interact with the page and extract data
                def interact_with_page_and_extract_data(driver, manager_index, month, year):
                    try:
                        select_element_month = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.NAME, 'month'))
                        )
                        select_element_year = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.NAME, 'year'))
                        )
                        select_element_portfolio_manager = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.NAME, 'pmrId'))
                        )
                        input_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'go-search'))  # Ensure this class name is correct
                        )
                        
                        # Select the portfolio manager
                        Select(select_element_portfolio_manager).select_by_index(manager_index)

                        # Select the month
                        Select(select_element_month).select_by_visible_text(month)
                        
                        # Select the year
                        Select(select_element_year).select_by_visible_text(str(year))
                        
                        # Click the search button
                        input_element.click()
                        time.sleep(5)  # Wait for the page to load
                        
                        # Extract data from the page
                        return extract_data_from_page(driver)
                    except Exception as e:
                        print(f"Error interacting with page: {e}")
                        return []

                # Retry interacting with the page and extracting data
                data = retry_function(interact_with_page_and_extract_data, max_retries=3, delay=2, 
                                    driver=driver, manager_index=manager_index, month=month, year=year)
                
                if data:  # If data is not empty
                    # Store each table's data into separate DataFrames and save to CSV
                    for idx, table_data in enumerate(data):
                        df = pd.DataFrame(table_data)
                        csv_filename = f'data_manager_{manager_index}_year_{year}_month_{month}_table_{idx+1}.csv'
                        df.to_csv(csv_filename, index=False)
                        print(f"Data for Manager {manager_index}, Year {year}, Month {month}, Table {idx+1} saved to {csv_filename}")
                else:
                    print(f"No data extracted for Manager {manager_index}, {year} {month}")
            except Exception as e:
                print(f"Error processing Manager {manager_index}, {year} {month}: {e}")

# Close the driver
driver.quit()
