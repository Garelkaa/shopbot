import configparser
from dataclasses import dataclass


@dataclass
class Telegram:
    token: str
    admin_id: int

@dataclass
class Links:
    forward_channel_id: int
    zalets_channel_id: int
    reviews_channel_url: str
    support_username: str
    admin_username: str


@dataclass
class Config:
    tg: Telegram
    links: Links


def load_config(path: str):
    config = configparser.ConfigParser()
    config.read(path)

    tg_bot = config["Telegram"]
    links = config["Links"]

    return Config(
        tg=Telegram(
            token=tg_bot["token"],
            admin_id=int(tg_bot["admin_id"]),
        ),
        links=Links(
            forward_channel_id=int(links['forward_channel_id']),
            zalets_channel_id=int(links['zalets_channel_id']),
            reviews_channel_url=links['reviews_channel_url'],
            support_username=links['support_username'],
            admin_username=links['admin_username']
        )
    )

def write_config(config: Config):
    parser = configparser.ConfigParser()
    parser['Telegram'] = {'token': config.tg.token,
                          'admin_id': config.tg.admin_id}
    parser['Links'] = {'admin_username': config.links.admin_username,
                       'forward_channel_id': config.links.forward_channel_id,
                       'zalets_channel_id': config.links.zalets_channel_id,
                       'reviews_channel_url': config.links.reviews_channel_url,
                       'support_username': config.links.support_username}
    with open('config.ini', 'w') as fp:
        parser.write(fp)

config = load_config("config.ini")
