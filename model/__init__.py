import toml
import logging
import os

logging.basicConfig(filename='error.log', level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if not os.path.exists('config.toml'):
    logging.error('config.toml not found')
    raise FileNotFoundError('config.toml not found')

with open('config.toml', 'r') as f:
    config = toml.load(f)

    config["export_color"] = tuple(config["export_color"])
    for dictionary in ['text_colors', 'power_coord']:
        for key in config[dictionary]:
            config[dictionary][key] = tuple(config[dictionary][key])

    if not os.path.exists(config["cards_file_path"]):
        logging.error('Cards file not found.')
        raise FileNotFoundError(config["cards_file_path"])
    if not os.path.exists(config["sigils_file_path"]):
        logging.error('Sigils file not found.')
        raise FileNotFoundError(config["sigils_file_path"])
    if not os.path.exists(config["traits_file_path"]):
        logging.error('Traits file not found.')
        raise FileNotFoundError(config["traits_file_path"])
    if not os.path.exists("data/fonts/" + config["font"] + ".ttf"):
        logging.error('Font file not found.')
        raise FileNotFoundError(config["font"])
