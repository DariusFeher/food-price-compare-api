from bs4 import BeautifulSoup
import requests, lxml
import time
import csv
import xlsxwriter

short_names = [] # List to store name of the product, e.g. Salted Block Butter
full_names = [] # List to store the full name of the product, e.g. Tesco British Salted Block Butter 250G ++
links = [] # List to store the link to the product
prices=[] # List to store price of the product
currencies = [] # List to store the currency - at the moment, all of them will be in pounds, but may be useful in the future or for different supermarkets
ids = []

headers = {
    'User-agent':
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
  }

params = {
	'page' : 1
}

BASE_URL = 'https://www.tesco.com'

category_urls = {
	'fresh-food' : 'https://www.tesco.com/groceries/en-GB/shop/fresh-food/all?include-children=true',
	'bakery' : 'https://www.tesco.com/groceries/en-GB/shop/bakery/all',
	'frozen-food' : 'https://www.tesco.com/groceries/en-GB/shop/frozen-food/all',
	'food-cupboard' : 'https://www.tesco.com/groceries/en-GB/shop/food-cupboard/all',
	'drinks' : 'https://www.tesco.com/groceries/en-GB/shop/drinks/all',
	'easter' : 'https://www.tesco.com/groceries/en-GB/shop/easter/all',
	'pet-food' : 'https://www.tesco.com/groceries/en-GB/shop/pets/all',
}

csv_columns = ['Short_name','Price','Currency', 'Full_name', 'Link']

workbook = xlsxwriter.Workbook('/Users/dariusmarianfeher/Documents/ThirdYearProject/TescoProducts.xlsx')

# Specify the name of the sheet
worksheet = workbook.add_worksheet("TescoProducts")

# Start from the first cell. Rows and
# columns are zero indexed.
row = 0
col = 0
for col_name in csv_columns:
    worksheet.write(row, col, col_name)
    col += 1

prodList = []
for category in category_urls:
	params['page'] = 1 # Restart page nr
	while True:
		html = requests.get(category_urls[category], headers=headers, params=params).text
		time.sleep(0.5)
		# print(html)
		if "the page you are looking for has not been found" in html:
			break
		soup = BeautifulSoup(html, 'html.parser')
		try:
			prodList = soup.find('div', {'class':'product-lists'}).find('ul').findAll('li', {'class': 'product-list--list-item'})
		except:
			break
		print("PAGE", params['page'])
		no_prod = 0
		for product in prodList:
			prod = None
			price = None
			currency = None

			try:
				short_name = product.find('span', {'class' : "visually-hidden"}).text
				price = product.find('span', {'class' : "value"}).text
				currency = product.find('span', {'class' : "currency"}).text
				link = BASE_URL + product.find('a', {'class' : 'eYySMn'})['href']
				full_name = product.find('a', {'class' : 'eYySMn'}).text
				id = str(product.find('input', {'name' : "id"})['value'])
			except:
				continue
			
			no_prod += 1
			short_names.append(short_name)
			full_names.append(full_name)
			links.append(link)
			prices.append(price)
			currencies.append(currency)
			ids.append(id)

			col = 0
			row += 1
			data = [short_name, price, currency,full_name, link]
			for col_data in data:
				worksheet.write(row, col, col_data)
				col += 1

		print("PRODUCTS:", no_prod)
		print('----------')
		params['page'] += 1
	
		
workbook.close()

