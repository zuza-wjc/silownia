import os

templates: dict[str, str] = {}
directory = "./templates/"

for file in os.listdir(directory):
	with open(directory + file, encoding="utf-8")  as f:
		templates[os.path.splitext(file)[0]] = f.read()