import io
import sys
import yaml
from AutoHearthStone import AutoBattleGrounds

if sys.stderr is None:
    sys.stderr = io.StringIO()
if sys.stdout is None:
    sys.stdout = io.StringIO()


with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)
print(config)
AutoBattleGrounds(**config).run()