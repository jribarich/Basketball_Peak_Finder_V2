"""
Creates a dictionary of all NBA players
Run this to update the NBA dictionary each year

To update:
1.  source venv/bin/activate
2. python3 players.py

By Jack Ribarich
Date: August 1, 2020

"""

import requests
import ast
from bs4 import BeautifulSoup
from unidecode import unidecode  # for converting non-English letters

def test():
	response = requests.get('https://www.basketball-reference.com/players/a/')
	soup = BeautifulSoup(response.text, 'html.parser')
	players = soup.find_all('th', class_='left')

	for x in players:
		print(x.find('a').text)
		print(x.get('data-append-csv'))
		print()


def find():
	player = input("What player's html do you want? ")
	with open('player_database.txt') as f:
		player_dict = ast.literal_eval(f.read())

	print(player_dict[player])


def main():
	url = "https://www.basketball-reference.com/players/"
	end = "/"

	player_dict = {}

	i = ord('a')  # start with 'a' last names

	# iterate over alphabet and store url into dictionary
	while i <= ord('z'):
		response = requests.get(url + chr(i) + end)
		soup = BeautifulSoup(response.text, 'html.parser')
		players = soup.find_all('th', class_='left')

		for x in players:
			player_dict[unidecode(x.find('a').text.lower())] = x.get('data-append-csv')
		
		i += 1

	# write dictionary a file
	f = open('player_database.txt', 'w')
	f.write(str(player_dict))
	f.close()


if __name__ == "__main__":
	main()  # creates/updates player database
	#find()  # finds a specific player
	#test()  # tests how to find certain html elements