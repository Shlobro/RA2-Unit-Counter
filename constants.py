# constants.py

# General constants
MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff

# Offsets for units and buildings
INFOFFSET = 0x557c
AIRCRAFTOFFSET = 0x5590
TANKOFFSET = 0x5568
BUILDINGOFFSET = 0x5554

# Offsets for resources and status
CREDITSPENT_OFFSET = 0x2dc
BALANCEOFFSET = 0x30c
USERNAMEOFFSET = 0x1602a
ISWINNEROFFSET = 0x1f7
ISLOSEROFFSET = 0x1f8

# Offsets for power values
POWEROUTPUTOFFSET = 0x53a4
POWERDRAINOFFSET = 0x53a8

# Offsets for country and house type strings
HOUSETYPECLASSBASEOFFSET = 0x34
COUNTRYSTRINGOFFSET = 0x24

# Offset for color scheme
COLORSCHEMEOFFSET = 0x16054

#offset for number of war factories
NUMBEROFWFOFFSET = 0x160

# Mapping dictionaries for infantry, tanks, structures, and aircraft, Don't forget these are the offsets inside the arrays not from player base
infantry_offsets = {
    0x0: "GI", 0x4: "conscript", 0x8: "tesla trooper", 0xc: "Allied Engineer", 0x10: "Rocketeer",
    0x14: "Navy Seal", 0x18: "Yuri Clone", 0x1c: "Ivan", 0x20: "Desolator", 0x24: "Soviet Dog",
    0x3c: "Chrono Legionnaire", 0x40: "Spy", 0x50: "Yuri Prime", 0x54: "Sniper", 0x60: "Tanya",
    0x6c: "Soviet Engineer", 0x68: "Terrorist", 0x70: "Allied Dog", 0xb4: "Yuri Engineer",
    0xb8: "GGI", 0xbc: "Initiate", 0xc0: "Boris", 0xc4: "Brute", 0xc8: "Virus",
}

tank_offsets = {
    0x0: "Allied MCV", 0x4: "War Miner", 0x8: "Apoc", 0x10: "Soviet Amphibious Transport", 0xc: "Rhino Tank",
    0x24: "Grizzly", 0x34: "Aircraft Carrier", 0x38: "V3 Rocket Launcher", 0x3c: "Kirov",
    0x40: "Terror Drone", 0x44: "Flak Track", 0x48: "Destroyer", 0x4c: "Typhoon attack sub", 0x50: "Aegis Cruiser",
    0x54: "Allied Amphibious Transport", 0x58: "Dreadnought", 0x5c: "NightHawk Transport", 0x60: "Squid",
    0x64: "Dolphin", 0x68: "Soviet MCV", 0x6c: "Tank Destroyer", 0x7c: "Lasher", 0x84: "Chrono Miner",
    0x88: "Prism Tank", 0x90: "Sea Scorpion", 0x94: "Mirage Tank", 0x98: "IFV", 0xa4: "Demolition truck",
    0xdc: "Yuri Amphibious Transport", 0xe0: "Yuri MCV", 0xe4: "Slave miner undeployed", 0xf0: "Gattling Tank",
    0xf4: "Battle Fortress", 0xfc: "Chaos Drone", 0xf8: "Magnetron", 0x108: "Boomer", 0x10c: "Siege Chopper",
    0x114: "Mastermind", 0x118: "Disc", 0x120: "Robot Tank",
}

structure_offsets = {
    0x0: "Allied Power Plant", 0x4: "Allied Ore Refinery", 0x8: "Allied Con Yard", 0xc: "Allied Barracks",
    0x14: "Allied service Depot", 0x18: "Allied Battle Lab", 0x1c: "Allied War Factory", 0x24: "Tesla Reactor",
    0x28: "Sov Battle lab", 0x2c: "sov barracks", 0x34: "Sov Radar", 0x38: "Soviet War Factory",
    0x3c: "Sov Ore Ref", 0x48: "Yuri Radar", 0x50: "Sentry Gun", 0x54: "Patriot Missile",
    0x5c: "Allied Naval Yard", 0x60: "Iron Curtain", 0x64: "sov con yard", 0x68: "Sov Service Depot",
    0x6c: "ChronoSphere", 0x74: "Weather Controller", 0xd4: "Tesla Coil", 0xd8: "Nuclear Missile Launcher",
    0xf4: "Sov Naval Yard", 0xf8: "SpySat Uplink", 0xfc: "Gap Generator", 0x100: "Grand Cannon",
    0x104: "Nuclear Reactor", 0x108: "PillBox", 0x10c: "Flak Cannon", 0x11c: "Oil", 0x120: "Cloning Vats",
    0x124: "Ore Purifier", 0x1a4: "Allied AFC", 0x21c: "American AFC", 0x2dc: "Blitz oil (psychic sensor)",
    0x4b0: "Yuri Con Yard", 0x4b4: "Bio Reactor", 0x4b8: "Yuri Barracks", 0x4bc: "Yuri War Factory",
    0x4c0: "Yuri Naval Yard", 0x4c8: "Yuri Battle Lab", 0x4d0: "Gattling Cannon", 0x4d4: "Psychic Tower",
    0x4d8: "Industrial Plant", 0x4dc: "Grinder", 0x4e0: "Genetic Mutator", 0x4ec: "Psychic dominator",
    0x558: "Tank Bunker", 0x590: "Robot Control Center", 0x594: "Slave Miner Deployed", 0x59c: "Battle Bunker",
}

aircraft_offsets = {
    0x4: "Harrier",
    0x1c: "Black Eagle"
}

#Mapping of color scheme values to actual colors.
from PySide6.QtGui import QColor
COLOR_SCHEME_MAPPING = {
    3: QColor("yellow"),
    5: QColor("white"),
    7: QColor("gray"),
    11: QColor("red"),
    13: QColor("orange"),
    15: QColor("pink"),
    17: QColor("purple"),
    21: QColor("blue"),
    25: QColor("cyan"),
    29: QColor("green"),
}

# Mapping of color scheme values to friendly color names.
COLOR_NAME_MAPPING = {
    3: "yellow",
    5: "white",
    7: "gray",
    11: "red",
    13: "orange",
    15: "pink",
    17: "purple",
    21: "blue",
    25: "cyan",
    29: "green",
}


# Additional game definitions
names = {
    "Allied": {
        "Infantry": [
            "GI",
            "GGI",
            "Allied Dog",
            "Allied Engineer",
            "Chrono Legionnaire",
            "Spy",
            "Rocketeer",
            "Tanya",
            "Navy Seal"
        ],
        "Structure": [
            "Allied Power Plant",
            "SpySat",
            "Allied Naval Yard",
            "Allied Barracks",
            "ChronoSphere",
            "Allied Service Depot",
            "Gap Generator",
            "Grand Cannon",
            "Ore Purifier",
            "PillBox",
            "Allied AFC",
            "Allied Battle Lab",
            "Robot Control Center",
            "Allied Ore Refinery",
            "Weather Controller",
            "Allied War Factory",
            "Blitz oil (psychic sensor)"
        ],
        "Tank": [
            "Grizzly",
            "Chrono Miner",
            "Battle Fortress",
            "IFV",
            "Allied MCV",
            "Prism Tank",
            "Tank Destroyer",
            "Robot Tank",
            "Mirage Tank",
            "NightHawk Transport"
        ],
        "Naval": [
            "Agis Cruiser",
            "Aircraft Carrier",
            "Destroyer",
            "Dolphin",
            "Allied Amphibious Transport"
        ],
        "Aircraft": [
            "Black Eagle",
            "Harrier"
        ]
    },
    "Soviet": {
        "Infantry": [
            "conscript",
            "Desolator",
            "Boris",
            "Soviet Dog",
            "Soviet Engineer",
            "Flak Trooper",
            "Ivan",
            "Terrorist"
        ],
        "Structure": [
            "Soviet Barracks",
            "Battle Bunker",
            "Flak Cannon",
            "Industrial Plant",
            "Sentry Gun",
            "Iron Curtain",
            "Nuclear Missile Launcher",
            "Soviet War Factory",
            "Tesla Reactor",
            "Sov Radar",
            "Nuclear Reactor",
            "Sov Service Depot",
            "Sov Ore Ref",
            "Tesla Coil",
            "Sov Naval Yard",
            "Blitz oil (psychic sensor)"
        ],
        "Tank": [
            "Rhino Tank",
            "Terror Drone",
            "Flak Track",
            "War Miner",
            "V3 Rocket Launcher",
            "Apoc",
            "Siege Chopper",
            "Soviet MCV",
            "Kirov",
            "Demolition truck"
        ],
        "Naval": [
            "Dreadnought",
            "Squid",
            "Soviet Amphibious Transport",
            "Typhoon attack sub",
            "Sea Scorpion"
        ],
        "Aircraft": []
    },
    "Yuri": {
        "Infantry": [
            "Initiate",
            "Virus",
            "Yuri Clone",
            "Yuri Prime",
            "Yuri Engineer",
            "Brute"
        ],
        "Structure": [
            "Yuri War Factory",
            "Yuri Barracks",
            "Cloning Vats",
            "Grinder",
            "Gattling Cannon",
            "Tank Bunker",
            "Yuri Radar",
            "Psychic Tower",
            "Psychic dominator",
            "Slave Miner Deployed",
            "Bio Reactor",
            "Yuri Battle Lab",
            "Yuri Naval Yard",
            "Blitz oil (psychic sensor)"
        ],
        "Tank": [
            "Gattling Tank",
            "Chaos Drone",
            "Disc",
            "Lasher",
            "Mastermind",
            "Magnetron",
            "Yuri MCV"
        ],
        "Naval": [
            "Boomer",
            "Yuri Amphibious Transport"
        ],
        "Aircraft": []
    },
    "Other": {
        "Infantry": [],
        "Structure": [
            "Blitz oil (psychic sensor)"
        ],
        "Tank": [],
        "Naval": [],
        "Aircraft": [],
    }
}

factions = ['Allied', 'Soviet', 'Yuri', 'Other']
unit_types = ['Infantry', 'Structure', 'Tank', 'Naval', 'Aircraft']


def name_to_path(name):
    return 'cameos/png/' + name + '.png'

def country_name_to_faction(country_name):
    if country_name in ['Americans', 'Alliance', 'French', 'Germans', 'British']:
        return 'Allied'
    elif country_name in ['Africans', 'Arabs', 'Confederation', 'Russians']:
        return 'Soviet'
    elif country_name == 'YuriCountry':
        return 'Yuri'
    else:
        return 'Unknown'