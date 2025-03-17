import yaml

from AutoHearthStone import AutoHearthStone

with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

AutoHearthStone(**config).run()