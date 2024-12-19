import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import os

# Path to the chromedriver executable
executable_path = 'chromedriver.exe'

# Create a service object
service = Service(executable_path)

# Function to initialize the driver and navigate to the webpage
def initialize_driver():
    driver = webdriver.Chrome(service=service)
    driver.get("https://tradestat.commerce.gov.in/meidb/cntcomq.asp?ie=e")    #export
    # driver.get("https://tradestat.commerce.gov.in/meidb/cntcomq.asp?ie=i")    #import
    time.sleep(2)
    return driver

# Initialize the driver
driver = initialize_driver()

# Locate the select elements
select_element_month = driver.find_element(By.ID, 'select1')
select_element_year = driver.find_element(By.ID, 'select2')
select_element_country = driver.find_element(By.ID, 'select3')
select_element_hscode = driver.find_element(By.NAME, 'hslevel')

# Create Select objects
select_month = Select(select_element_month)
select_year = Select(select_element_year)
select_country = Select(select_element_country)
select_hscode = Select(select_element_hscode)

# List of months and years to iterate through
years = list(range(2024, 2025))                         # Adjust the years as needed
months = ['MAY']                                        # Adjust the months as needed

# Iterate through each country
for country_index in range(len(select_country.options)):
    select_country = Select(driver.find_element(By.ID, 'select3'))
    select_country.select_by_index(country_index)
    country = select_country.options[country_index].text
    time.sleep(1)

    # Select HS code level 
    # select_hscode.select_by_value('2')     #hs2
    select_hscode.select_by_value('4')     #hs4
    # select_hscode.select_by_value('8')     #hs8
    time.sleep(3)

    # Select the radio button with the id 'radioDALL'
    radio_button_all = driver.find_element(By.ID, 'radioDAll')
    radio_button_all.click()
    time.sleep(3)

    # Select quantity
    quantity_button_all = driver.find_element(By.ID, 'radioval')       #value
    # quantity_button_all = driver.find_element(By.ID, 'radioqty')        #qty
    quantity_button_all.click()
    time.sleep(3)

    # Dictionary to store DataFrames for each month and year combination
    month_year_data = {}

    # Iterate through each year
    for year in years:
        select_year.select_by_visible_text(str(year))
        time.sleep(1)

        # Iterate through each month
        for month in months:
            select_month.select_by_visible_text(month)
            time.sleep(1)

            # Perform the action required after selecting each combination
            input_element = driver.find_element(By.CLASS_NAME, 'frm-btn')
            input_element.send_keys(Keys.ENTER)
            time.sleep(3)  # Wait for the page to reload or update

            # Check if the table is present
            try:
                table = driver.find_element(By.XPATH, '//table[@border="1"]')
                header_row = table.find_elements(By.TAG_NAME, 'tr')[0]
                headers = [header.text for header in header_row.find_elements(By.TAG_NAME, 'th')]

                # Extract the table data
                rows = table.find_elements(By.TAG_NAME, 'tr')[1:]  # Skip the header row

                data = []
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    row_data = [cells[i].text for i in [0, 1, 2, 4]]  #monthly value update
                    # row_data = [cells[i].text for i in [0, 1, 2, 5]]  #monthly qty update 
                    # row_data = [cells[i].text for i in [0, 1, 2, 7]]  #annually value update
                    # row_data = [cells[i].text for i in [0, 1, 2, 8]]  #annually qty update
                    data.append(row_data)

                # Create the DataFrame for the current combination
                columns = [headers[i] for i in [0, 1, 2, 4]]    #monthly value update
                # columns = [headers[i] for i in [0, 1, 2, 5]]    #monthly qty update
                # columns = [headers[i] for i in [0, 1, 2, 7]]    #annually value update
                # columns = [headers[i] for i in [0, 1, 2, 8]]    #annually qty update
                df = pd.DataFrame(data, columns=columns)

                # Store the DataFrame in the dictionary
                key = f'{year}_{month}'
                month_year_data[key] = df

                print(f"Data for {country} {month} {year} processed successfully.")

            except NoSuchElementException:
                print(f"No data found for {country} {month} {year}.")

            driver.back()
            time.sleep(3)

    # Concatenate all DataFrames for the current country
    if month_year_data:
        result = pd.DataFrame()

        for key, df in month_year_data.items():
            df.drop(columns=['S.No.', 'Commodity'], inplace=True)           #value
            # df.drop(columns=['S.No.', 'Commodity','Unit'], inplace=True)    #qty
            df.rename(columns={'HSCode': 'HS CODE'}, inplace=True)
            df.set_index('HS CODE', inplace=True)

            if result.empty:
                result = df.copy()
            else:
                result = result.join(df, how='outer', rsuffix=f'_{key}')

        # Join result with hscode_df to include DESCRIPTION
        hscode_csv_path = "C:/Users/parth/Desktop/MoC Scrapping/chromedriver-win64/Database/database_2024_Sep_HS4_export_value.csv"  #change hscode path accordingly - value/qty/2/4/8/export/import - change path \ -> to /
        hscode_df = pd.read_csv(hscode_csv_path)
        # hscode_df['HS CODE'] = hscode_df['HS CODE'].apply(lambda x: '0' + str(x) if len(str(x)) == 1 else str(x))    #2hs
        hscode_df['HS CODE'] = hscode_df['HS CODE'].apply(lambda x: '0' + str(x) if len(str(x)) == 3 else str(x))    #4hs
        # hscode_df['HS CODE'] = hscode_df['HS CODE'].apply(lambda x: '0' + str(x) if len(str(x)) == 7 else str(x))    #8hs
        hscode_df.set_index('HS CODE', inplace=True)
        result = pd.merge(result, hscode_df, left_index=True, right_index=True, how='left')

        # Ensure the Country column is included once
        result['Country']=country
        # Reorder columns to place DESCRIPTION as the first column
        columns = ['Country','DESCRIPTION']+[col for col in result.columns if col not in ['Country','DESCRIPTION']]
        result = result[columns]

        # Save the merged DataFrame to CSV
        country_filename = f'trade_data_{country.replace(" ", "_")}.csv'
        
        if os.path.exists(country_filename):
            existing_df = pd.read_csv(country_filename)
            
            # Merge existing_df and result on 'HS CODE' to update existing data
            # existing_df['HS CODE'] = existing_df['HS CODE'].apply(lambda x: '0' + str(x) if len(str(x)) == 1 else str(x))     #2hs
            existing_df['HS CODE'] = existing_df['HS CODE'].apply(lambda x: '0' + str(x) if len(str(x)) == 3 else str(x))     #4hs
            # existing_df['HS CODE'] = existing_df['HS CODE'].apply(lambda x: '0' + str(x) if len(str(x)) == 7 else str(x))     #8hs
            existing_df.set_index('HS CODE', inplace=True)
            updated_df = existing_df.join(result, how='outer')
            updated_df.to_csv(country_filename, index=True)
        else:
            result.to_csv(country_filename, index=True)

# Close the driver
driver.quit()
