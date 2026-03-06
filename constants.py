# constants.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

# offset for number of war factories
NUMBEROFWFOFFSET = 0x160

# Infiltration flags
BARRACKS_INFILTRATED_OFFSET = 0x2bf
WAR_FACTORY_INFILTRATED_OFFSET = 0x2c0

#---------------------------------------------
#all the new factory offsets here:

# Offsets inside FactoryClass
PERCENTAGECOMPLETEOFFSET = 0x24    # Percentage complete of the unit being built
QUEUEDUNITSAMOUNT = 0x50           # Number of queued units (not used for Buildings)
QUEUEDUNITSPTROFFSET = 0x44        # Pointer to queued units array (not used for Buildings)

# Offsets inside technoTypeClass
UNITNAMEOFFSET = 0x64             # Offset to read 20 bytes string for unit name

# Offsets in technoClass to get to technoType pointer.
TECHNOCLASS_TO_TECHNOTYPE_INFANTRY_OFFSET = 0x6c0  # For Infantry factories
TECHNOCLASS_TO_TECHNOTYPE_BUILDINGS_OFFSET = 0x520 # For Buildings factories
TECHNOCLASS_TO_TECHNOTYPE_UNIT_OFFSET = 0x6c4        # For Tanks, Aircraft, Ships, and Defenses


# Global list of factory types (name, offset)
QUEUED_FACTORIES_OFFSETS = {
    "Aircraft": 0x53ac,
    "Infantry": 0x53b0,
    "Vehicles": 0x53b4,
    "Ships": 0x53b8
}

BUILDING_FACTORIES_OFFSETS = {
    "Buildings": 0x53bc,
    "Defenses": 0x53CC
}

# Mapping dictionaries for infantry, tanks, structures, and aircraft, Don't forget these are the offsets inside the arrays not from player base
infantry_offsets = {
    0x0: "GI",  # [E1] -> GI
    0x4: "Conscript",  # [E2] -> Conscript
    0x8: "Shock Trooper",  # [SHK] -> Shock Trooper
    0xc: "Engineer",  # [ENGINEER] -> Engineer
    0x10: "Rocketeer",  # [JUMPJET] -> Rocketeer
    0x14: "SEAL",  # [GHOST] -> SEAL
    0x18: "Yuri Clone",  # (InfantryTypes: YURI – using “Yuri Clone” as in the original dict)
    0x1c: "Crazy Ivan",  # [IVAN] -> Crazy Ivan
    0x20: "Desolater",  # [DESO] -> Desolater
    0x24: "Attack Dog",  # [DOG] -> Attack Dog
    0x3c: "Chrono Legionnaire",  # [CLEG] -> Chrono Legionnaire
    0x40: "Spy",  # [SPY] -> Spy
    0x44: "Chrono Commando",
    0x48: "Psi-Corp Trooper",
    0x4c: "Chrono Ivan",
    0x50: "Yuri Prime",  # [YURIPR] -> Yuri Prime
    0x54: "Sniper",  # [SNIPE] -> Sniper
    0x60: "Tanya",  # [TANY] -> Tanya
    0x64: "Flak Trooper",
    0x68: "Terrorist",  # [TERROR] -> Terrorist
    0x6c: "Soviet Engineer",  # [SENGINEER] -> Soviet Engineer
    0x70: "Allied Attack Dog",  # [ADOG] -> Allied Attack Dog
    0xb4: "Yuri Engineer",  # [YENGINEER] -> Yuri Engineer
    0xb8: "Guardian GI",  # [GGI] -> Guardian GI
    0xbc: "Yuri Initiate",  # [INIT] -> Yuri Initiate
    0xc0: "Boris",  # [BORIS] -> Boris
    0xc4: "Yuri Brute",  # [BRUTE] -> Yuri Brute
    0xc8: "Yuri Virus",  # [VIRUS] -> Yuri Virus
}

tank_offsets = {
    0x0: "Allied Construction Vehicle",  # [AMCV] → Allied Construction Vehicle
    0x4: "War Miner",  # [HORV] or [HARV] → War Miner
    0x8: "Apocalypse",  # [APOC] → Apocalypse
    0x10: "Armored Transport",  # [SAPC]
    0xc: "Rhino Heavy Tank",  # [HTNK] → Rhino Heavy Tank
    0x24: "Grizzly Battle Tank",  # [MTNK] → Grizzly Battle Tank
    0x34: "Aircraft Carrier",  # [CARRIER] → Aircraft Carrier
    0x38: "V3 Launcher",  # [V3] → V3 Launcher
    0x3c: "Kirov Airship",  # [ZEP] → Kirov Airship
    0x40: "Terror Drone",  # [DRON] → Terror Drone
    0x44: "Flak Track",  # [HTK] → Flak Track
    0x48: "Destroyer",  # [DEST] → Destroyer
    0x4c: "Typhoon Attack Sub",  # [SUB] → Typhoon Attack Sub
    0x50: "Aegis Cruiser",  # [AEGIS] → Aegis Cruiser
    0x54: "Landing Craft",  # [SAPC] → Armored Transport
    0x58: "Dreadnought",  # [DRED] → Dreadnought
    0x5c: "BlackHawk Transport",  # [SHAD]
    0x60: "Giant Squid",  # [SQD] → Giant Squid
    0x64: "Dolphin",  # [DLPH] → Dolphin
    0x68: "Soviet Construction Vehicle",  # [SMCV] → Soviet Construction Vehicle
    0x6c: "Tank Destroyer",  # [TNKD] → Tank Destroyer
    0x7c: "Lasher Light Tank",  # [LTNK] → Lasher Light Tank
    0x84: "Chrono Miner",  # [CMIN] → Chrono Miner
    0x88: "Prism Tank",  # [SREF] → Prism Tank
    0x90: "Sea Scorpion",  # [HYD] → Sea Scorpion
    0x94: "Mirage Tank",  # [MGTK] → Mirage Tank
    0x98: "IFV",  # [FV] → IFV
    0xa4: "Demolitions Truck",  # [DTRUCK] → Demolitions Truck
    0xdc: "Hover Transport Yuri",  # [YHVR]
    0xe0: "Yuri Construction Vehicle",  # [PCV] → Yuri Construction Vehicle
    0xe4: "Slave miner",  # [SMIN]
    0xf0: "Gattling Tank",  # [YTNK] → Gattling Tank
    0xf4: "Battle Fortress",  # [BFRT] → Battle Fortress
    0xfc: "Chaos Drone",  # [CAOS] → Chaos Drone
    0xf8: "Magnetron",  # [TELE] → Magnetron
    0x108: "Yuri Boomer",  # [BSUB] → Yuri Boomer
    0x10c: "Soviet Siege Chopper",  # [SCHP] → Soviet Siege Chopper
    0x114: "Master Mind",  # [MIND] → Master Mind
    0x118: "Floating Disk",  # [DISK]
    0x120: "Robot Tank",  # [ROBO] → Robot Tank
}

structure_offsets = {
    0x0: "Allied Power Plant",  # [GAPOWR]
    0x4: "Allied Ore Refinery",  # [GAREFN]
    0x8: "Allied Construction Yard",  # [GACNST]
    0xc: "Allied Barracks",  # [GAPILE]
    0x14: "Allied Service Depot",  # [GADEPT]
    0x18: "Allied Battle Lab",  # [GATECH]
    0x1c: "Allied War Factory",  # [GAWEAP]
    0x24: "Soviet Tesla Reactor",  # [NAPOWR]
    0x28: "Soviet Battle Lab",  # [NATECH]
    0x2c: "Soviet Barracks",  # [NAHAND]
    0x34: "Soviet Radar Tower",  # [NARADR]
    0x38: "Soviet War Factory",  # [NAWEAP]
    0x3c: "Soviet Ore Refinery",  # [NAREFN]
    0x48: "Yuri Psychic Sensor",  # [NAPSIS]
    0x50: "Soviet Sentry Gun",  # [NALASR]
    0x54: "Allied Patriot Missile",  # [NASAM]
    0x5c: "Allied Shipyard",  # [GAYARD]
    0x60: "Soviet Iron Curtain Device",  # [NAIRON]
    0x64: "Soviet Construction Yard",  # [NACNST]
    0x68: "Soviet Service Depot",  # [NADEPT]
    0x6c: "Allied Chrono Sphere",  # [GACSPH]
    0x74: "Allied Weather Controller",  # [GAWEAT]
    0xd4: "Soviet Tesla Coil",  # [TESLA]
    0xd8: "Soviet Nuclear Missile Silo",  # [NAMISL]
    0xdc: "Allied Prism Cannon",
    0xf4: "Soviet Shipyard",  # [NAYARD]
    0xf8: "Allied SpySat Uplink",  # [GASPYSAT]
    0xfc: "Allied Gap Generator",  # [GAGAP]
    0x100: "Allied Grand Cannon",  # [GTGCAN]
    0x104: "Soviet Nuclear Reactor",  # [NANRCT]
    0x108: "Allied Pill Box",  # [GAPILL]
    0x10c: "Soviet Flak Cannon",  # [NAFLAK]
    0x11c: "Tech Oil Derrick",  # [CAOILD]
    0x120: "Yuri Cloning Vats",  # [NACLON]
    0x124: "Allied Ore Processor",  # [GAOREP]
    0x1a4: "Allied American Airforce Command Headquarters",  # [AMRADR]
    0x21c: "Allied Airforce Command Headquarters",  # [GAAIRC]
    0x2dc: "Psychic Beacon",  # (updated from “Blitz oil (psychic sensor)”)
    0x4b0: "Yuri Construction Yard",  # [YACNST]
    0x4b4: "Yuri Bio Reactor",  # [YAPOWR]
    0x4b8: "Yuri Barracks",  # [YABRCK]
    0x4bc: "Yuri War Factory",  # [YAWEAP]
    0x4c0: "Yuri Submarine Pen",  # [YAYARD]
    0x4c8: "Yuri Battle Lab",  # [YATECH]
    0x4d0: "Yuri Gattling Cannon",  # [YAGGUN]
    0x4d4: "Yuri Psychic Tower",  # [YAPSYT]
    0x4d8: "Soviet Industrial Plant",  # [NAINDP]
    0x4dc: "Yuri Grinder",  # [YAGRND]
    0x4e0: "Yuri Genetic Mutator Device",  # [YAGNTC]
    0x4ec: "Yuri Puppet Master",  # [YAPPET]
    0x558: "Yuri Tank Bunker",  # [NATBNK]
    0x590: "Allied Robot Control Center",  # [GAROBO]
    0x594: "Yuri Ore Refinery",  # [YAREFN]
    0x59c: "Soviet Battle Bunker",  # [NABNKR]
}

aircraft_offsets = {
    0x4: "Intruder",
    0x1c: "Black Eagle"
}

# Cumulative post-game score offsets from offsets.py.
BUILT_AIRCRAFT_TOTAL_OFFSETS = {
    0x32c: "Intruder",
    0x344: "Black Eagle",
}

BUILT_INFANTRY_TOTAL_OFFSETS = {
    0xb30: "GI",
    0xb34: "Conscript",
    0xb38: "Shock Trooper",
    0xb3c: "Engineer",
    0xb40: "Rocketeer",
    0xb44: "SEAL",
    0xb48: "Yuri Clone",
    0xb4c: "Crazy Ivan",
    0xb50: "Desolater",
    0xb54: "Attack Dog",
    0xb6c: "Chrono Legionnaire",
    0xb70: "Spy",
    0xb80: "Yuri Prime",
    0xb84: "Sniper",
    0xb90: "Tanya",
    0xb94: "Flak Trooper",
    0xb98: "Terrorist",
    0xb9c: "Soviet Engineer",
    0xba0: "Allied Attack Dog",
    0xbe4: "Yuri Engineer",
    0xbe8: "Guardian GI",
    0xbec: "Yuri Initiate",
    0xbf0: "Boris",
    0xbf4: "Yuri Brute",
    0xbf8: "Yuri Virus",
}

BUILT_UNIT_TOTAL_OFFSETS = {
    0x1338: "Allied Construction Vehicle",
    0x133c: "War Miner",
    0x1340: "Apocalypse",
    0x1344: "Rhino Heavy Tank",
    0x1348: "Armored Transport",
    0x135c: "Grizzly Battle Tank",
    0x136c: "Aircraft Carrier",
    0x1370: "V3 Launcher",
    0x1374: "Kirov Airship",
    0x1378: "Terror Drone",
    0x137c: "Flak Track",
    0x1380: "Destroyer",
    0x1384: "Typhoon Attack Sub",
    0x1388: "Aegis Cruiser",
    0x138c: "Landing Craft",
    0x1390: "Dreadnought",
    0x1394: "BlackHawk Transport",
    0x1398: "Giant Squid",
    0x139c: "Dolphin",
    0x13a0: "Soviet Construction Vehicle",
    0x13a4: "Tank Destroyer",
    0x13b4: "Lasher Light Tank",
    0x13bc: "Chrono Miner",
    0x13c0: "Prism Tank",
    0x13c8: "Sea Scorpion",
    0x13cc: "Mirage Tank",
    0x13d0: "IFV",
    0x13dc: "Demolitions Truck",
    0x1414: "Hover Transport Yuri",
    0x1418: "Yuri Construction Vehicle",
    0x141c: "Slave miner",
    0x1428: "Gattling Tank",
    0x142c: "Battle Fortress",
    0x1430: "Chaos Drone",
    0x1434: "Magnetron",
    0x1440: "Yuri Boomer",
    0x1444: "Soviet Siege Chopper",
    0x144c: "Master Mind",
    0x1450: "Floating Disk",
    0x1458: "Robot Tank",
}

BUILT_BUILDING_TOTAL_OFFSETS = {
    0x1b40: "Allied Power Plant",
    0x1b44: "Allied Ore Refinery",
    0x1b48: "Allied Construction Yard",
    0x1b4c: "Allied Barracks",
    0x1b54: "Allied Service Depot",
    0x1b58: "Allied Battle Lab",
    0x1b5c: "Allied War Factory",
    0x1b64: "Soviet Tesla Reactor",
    0x1b68: "Soviet Battle Lab",
    0x1b6c: "Soviet Barracks",
    0x1b74: "Soviet Radar Tower",
    0x1b78: "Soviet War Factory",
    0x1b7c: "Soviet Ore Refinery",
    0x1b88: "Yuri Psychic Sensor",
    0x1b90: "Soviet Sentry Gun",
    0x1b94: "Allied Patriot Missile",
    0x1b9c: "Allied Shipyard",
    0x1ba0: "Soviet Iron Curtain Device",
    0x1ba4: "Soviet Construction Yard",
    0x1ba8: "Soviet Service Depot",
    0x1bac: "Allied Chrono Sphere",
    0x1bb4: "Allied Weather Controller",
    0x1c14: "Soviet Tesla Coil",
    0x1c18: "Soviet Nuclear Missile Silo",
    0x1c34: "Soviet Shipyard",
    0x1c38: "Allied SpySat Uplink",
    0x1c3c: "Allied Gap Generator",
    0x1c44: "Soviet Nuclear Reactor",
    0x1c48: "Allied Pill Box",
    0x1c4c: "Soviet Flak Cannon",
    0x1c5c: "Tech Oil Derrick",
    0x1c60: "Yuri Cloning Vats",
    0x1c64: "Allied Ore Processor",
    0x1ce4: "Allied Airforce Command Headquarters",
    0x1d5c: "Allied American Airforce Command Headquarters",
    0x1ff0: "Yuri Construction Yard",
    0x1ff4: "Yuri Bio Reactor",
    0x1ff8: "Yuri Barracks",
    0x1ffc: "Yuri War Factory",
    0x2000: "Yuri Submarine Pen",
    0x2008: "Yuri Battle Lab",
    0x2010: "Yuri Gattling Cannon",
    0x2014: "Yuri Psychic Tower",
    0x2018: "Soviet Industrial Plant",
    0x201c: "Yuri Grinder",
    0x2020: "Yuri Genetic Mutator Device",
    0x202c: "Yuri Puppet Master",
    0x2098: "Yuri Tank Bunker",
    0x20d0: "Allied Robot Control Center",
    0x20dc: "Soviet Battle Bunker",
}

LOST_AIRCRAFT_TOTAL_OFFSETS = {}

LOST_INFANTRY_TOTAL_OFFSETS = {
    0x2b50: "GI",
    0x2b54: "Conscript",
    0x2b58: "Shock Trooper",
    0x2b5c: "Engineer",
    0x2b60: "Rocketeer",
    0x2b64: "SEAL",
    0x2b68: "Yuri Clone",
    0x2b6c: "Crazy Ivan",
    0x2b70: "Desolater",
    0x2b74: "Attack Dog",
    0x2b8c: "Chrono Legionnaire",
    0x2b90: "Spy",
    0x2ba0: "Yuri Prime",
    0x2ba4: "Sniper",
    0x2bb0: "Tanya",
    0x2bb4: "Flak Trooper",
    0x2bb8: "Terrorist",
    0x2bbc: "Soviet Engineer",
    0x2bc0: "Allied Attack Dog",
    0x2c04: "Yuri Engineer",
    0x2c08: "Guardian GI",
    0x2c0c: "Yuri Initiate",
    0x2c10: "Boris",
    0x2c14: "Yuri Brute",
    0x2c18: "Yuri Virus",
}

LOST_UNIT_TOTAL_OFFSETS = {
    0x3358: "Allied Construction Vehicle",
    0x335c: "War Miner",
    0x3360: "Apocalypse",
    0x3364: "Rhino Heavy Tank",
    0x3368: "Armored Transport",
    0x337c: "Grizzly Battle Tank",
    0x338c: "Aircraft Carrier",
    0x3390: "V3 Launcher",
    0x3394: "Kirov Airship",
    0x3398: "Terror Drone",
    0x339c: "Flak Track",
    0x33a0: "Destroyer",
    0x33a4: "Typhoon Attack Sub",
    0x33a8: "Aegis Cruiser",
    0x33ac: "Landing Craft",
    0x33b0: "Dreadnought",
    0x33b4: "BlackHawk Transport",
    0x33b8: "Giant Squid",
    0x33bc: "Dolphin",
    0x33c0: "Soviet Construction Vehicle",
    0x33c4: "Tank Destroyer",
    0x33d4: "Lasher Light Tank",
    0x33dc: "Chrono Miner",
    0x33e0: "Prism Tank",
    0x33e8: "Sea Scorpion",
    0x33ec: "Mirage Tank",
    0x33f0: "IFV",
    0x33fc: "Demolitions Truck",
    0x3434: "Hover Transport Yuri",
    0x3438: "Yuri Construction Vehicle",
    0x343c: "Slave miner",
    0x3448: "Gattling Tank",
    0x344c: "Battle Fortress",
    0x3450: "Chaos Drone",
    0x3454: "Magnetron",
    0x3460: "Yuri Boomer",
    0x3464: "Soviet Siege Chopper",
    0x346c: "Master Mind",
    0x3470: "Floating Disk",
    0x3478: "Robot Tank",
}

LOST_BUILDING_TOTAL_OFFSETS = {
    0x3b60: "Allied Power Plant",
    0x3b64: "Allied Ore Refinery",
    0x3b68: "Allied Construction Yard",
    0x3b6c: "Allied Barracks",
    0x3b74: "Allied Service Depot",
    0x3b78: "Allied Battle Lab",
    0x3b7c: "Allied War Factory",
    0x3b84: "Soviet Tesla Reactor",
    0x3b88: "Soviet Battle Lab",
    0x3b8c: "Soviet Barracks",
    0x3b94: "Soviet Radar Tower",
    0x3b98: "Soviet War Factory",
    0x3b9c: "Soviet Ore Refinery",
    0x3ba8: "Yuri Psychic Sensor",
    0x3bb0: "Soviet Sentry Gun",
    0x3bb4: "Allied Patriot Missile",
    0x3bbc: "Allied Shipyard",
    0x3bc0: "Soviet Iron Curtain Device",
    0x3bc4: "Soviet Construction Yard",
    0x3bc8: "Soviet Service Depot",
    0x3bcc: "Allied Chrono Sphere",
    0x3bd4: "Allied Weather Controller",
    0x3c34: "Soviet Tesla Coil",
    0x3c38: "Soviet Nuclear Missile Silo",
    0x3c4c: "Soviet Shipyard",
    0x3c50: "Allied SpySat Uplink",
    0x3c54: "Allied Gap Generator",
    0x3c5c: "Soviet Nuclear Reactor",
    0x3c60: "Allied Pill Box",
    0x3c64: "Soviet Flak Cannon",
    0x3c74: "Tech Oil Derrick",
    0x3c78: "Yuri Cloning Vats",
    0x3c7c: "Allied Ore Processor",
    0x3d04: "Allied Airforce Command Headquarters",
    0x3d7c: "Allied American Airforce Command Headquarters",
    0x4010: "Yuri Construction Yard",
    0x4014: "Yuri Bio Reactor",
    0x4018: "Yuri Barracks",
    0x401c: "Yuri War Factory",
    0x4020: "Yuri Submarine Pen",
    0x4028: "Yuri Battle Lab",
    0x4030: "Yuri Gattling Cannon",
    0x4034: "Yuri Psychic Tower",
    0x4038: "Soviet Industrial Plant",
    0x403c: "Yuri Grinder",
    0x4040: "Yuri Genetic Mutator Device",
    0x404c: "Yuri Puppet Master",
    0x40b8: "Yuri Tank Bunker",
    0x40f0: "Allied Robot Control Center",
    0x40f4: "Slave miner",
    0x40fc: "Soviet Battle Bunker",
}

# Mapping of color scheme values to actual colors.
from PySide6.QtGui import QColor

# Single source of truth for player color schemes.
# Qt does not recognize "pistachio" or "mint" as named colors, so explicit hex values are used.
COLOR_SCHEMES = {
    3: ("yellow", QColor("yellow")),
    5: ("white", QColor("white")),
    7: ("gray", QColor("gray")),
    11: ("red", QColor("red")),
    13: ("orange", QColor("orange")),
    15: ("pink", QColor("pink")),
    17: ("purple", QColor("purple")),
    21: ("blue", QColor("blue")),
    25: ("cyan", QColor("cyan")),
    29: ("green", QColor("green")),
    39: ("khaki", QColor("khaki")),
    41: ("crimson", QColor("crimson")),
    43: ("teal", QColor("teal")),
    45: ("pistachio", QColor("#93C572")),
    47: ("brown", QColor("brown")),
    49: ("mint", QColor("#98FF98")),
    51: ("magenta", QColor("magenta")),
    53: ("lavender", QColor("lavender")),
}

COLOR_SCHEME_MAPPING = {
    scheme_id: color for scheme_id, (_, color) in COLOR_SCHEMES.items()
}

# Mapping of color scheme values to friendly color names.
COLOR_NAME_MAPPING = {
    scheme_id: friendly_name for scheme_id, (friendly_name, _) in COLOR_SCHEMES.items()
}

# Additional game definitions
names = {
    "Allied": {
        "Infantry": [
            "GI",
            "Guardian GI",  # was "GGI"
            "Allied Attack Dog",  # was "Allied Dog"
            "Engineer",  # was "Allied Engineer"
            "Chrono Legionnaire",
            "Spy",
            "Rocketeer",
            "Tanya",
            "SEAL",  # was "Navy Seal"
            "Chrono Commando",
            "Chrono Ivan",
            "Psi-Corp Trooper",
            "Sniper"
        ],
        "Structure": [
            "Allied Power Plant",
            "Allied Ore Refinery",
            "Allied Barracks",
            "Allied Service Depot",
            "Allied Battle Lab",
            "Allied War Factory",
            "Allied Chrono Sphere",  # added space for clarity
            "Allied Shipyard",  # was "Allied Naval Yard"
            "Allied SpySat Uplink",  # was "SpySat"
            "Allied Gap Generator",  # was "Gap Generator"
            "Allied Grand Cannon",  # was "Grand Cannon"
            "Allied Pill Box",  # was "PillBox"
            "Allied Airforce Command Headquarters",  # was "Allied AFC"
            "Allied Robot Control Center",  # was "Robot Control Center"
            "Allied Ore Processor",  # was "Ore Purifier"
            "Allied Weather Controller",  # was "Weather Controller"
            "Allied Prism Cannon",
            "Allied Patriot Missile"
        ],
        "Tank": [
            "Grizzly Battle Tank",  # was "Grizzly"
            "Chrono Miner",
            "Battle Fortress",
            "IFV",
            "Allied Construction Vehicle",  # was "Allied MCV"
            "Prism Tank",
            "Tank Destroyer",
            "Robot Tank",
            "Mirage Tank",
            "BlackHawk Transport"  # was "NightHawk Transport"
        ],
        "Naval": [
            "Aegis Cruiser",  # was "Agis Cruiser"
            "Aircraft Carrier",
            "Destroyer",
            "Dolphin",
            "Landing Craft"
        ],
        "Aircraft": [
            "Black Eagle",
            "Intruder"
        ]
    },
    "Soviet": {
        "Infantry": [
            "Conscript",
            "Desolater",
            "Boris",
            "Attack Dog",  # was "Soviet Dog"
            "Soviet Engineer",
            "Crazy Ivan",  # was "Ivan"
            "Terrorist",
            "Flak Trooper",
            "Shock Trooper"
        ],
        "Structure": [
            "Soviet Barracks",
            "Soviet Battle Bunker",  # updated from "Battle Bunker"
            "Soviet Flak Cannon",  # was "Flak Cannon"
            "Soviet Industrial Plant",  # was "Industrial Plant"
            "Soviet Sentry Gun",  # was "Sentry Gun"
            "Soviet Iron Curtain Device",  # was "Iron Curtain"
            "Soviet Nuclear Missile Silo",  # was "Nuclear Missile Launcher"
            "Soviet War Factory",
            "Soviet Tesla Reactor",  # was "Tesla Reactor"
            "Soviet Radar Tower",  # was "Sov Radar"
            "Soviet Nuclear Reactor",  # was "Nuclear Reactor"
            "Soviet Service Depot",  # was "Sov Service Depot"
            "Soviet Ore Refinery",  # was "Sov Ore Ref"
            "Soviet Tesla Coil",  # was "Tesla Coil"
            "Soviet Shipyard",  # was "Sov Naval Yard"
            "Soviet Battle Lab"
        ],
        "Tank": [
            "Rhino Heavy Tank",  # was "Rhino Tank"
            "Terror Drone",
            "Flak Track",
            "War Miner",
            "V3 Launcher",  # was "V3 Rocket Launcher"
            "Apocalypse",  # was "Apoc"
            "Soviet Siege Chopper",  # was "Siege Chopper"
            "Soviet Construction Vehicle",  # was "Soviet MCV"
            "Kirov Airship",  # was "Kirov"
            "Demolitions Truck"  # was "Demolition truck"
        ],
        "Naval": [
            "Dreadnought",
            "Giant Squid",  # was "Squid"
            "Typhoon Attack Sub",  # was "Typhoon attack sub"
            "Sea Scorpion",
            "Armored Transport"
        ],
        "Aircraft": []
    },
    "Yuri": {
        "Infantry": [
            "Yuri Initiate",  # was "Initiate"
            "Yuri Virus",  # was "Virus"
            "Yuri Clone",
            "Yuri Prime",
            "Yuri Engineer",
            "Yuri Brute"  # was "Brute"
        ],
        "Structure": [
            "Yuri War Factory",
            "Yuri Barracks",
            "Yuri Cloning Vats",  # was "Cloning Vats"
            "Yuri Bio Reactor",  # was "Bio Reactor"
            "Yuri Submarine Pen",  # was "Yuri Naval Yard"
            "Yuri Battle Lab",
            "Yuri Gattling Cannon",  # was "Gattling Cannon"
            "Yuri Psychic Tower",  # was "Psychic Tower"
            "Yuri Psychic Sensor",  # was "Yuri Radar"
            "Yuri Grinder",  # was "Grinder"
            "Yuri Genetic Mutator Device",  # was "Genetic Mutator"
            "Yuri Tank Bunker",  # was "Tank Bunker"
            "Yuri Puppet Master"
            # Removed "Psychic dominator" (now "Yuri Puppet Master"), "Slave Miner Deployed",
            # and "Yuri Ore Refinery" from unit selection because Slave Miner is a single counter exception.
        ],
        "Tank": [
            "Slave miner",
            "Gattling Tank",
            "Chaos Drone",
            "Floating Disk",  # was "Disc"
            "Lasher Light Tank",  # was "Lasher"
            "Master Mind",  # was "Mastermind"
            "Magnetron",
            "Yuri Construction Vehicle"  # was "Yuri MCV"
        ],
        "Naval": [
            "Yuri Boomer",  # was "Boomer"
            "Hover Transport Yuri"
        ],
        "Aircraft": []
    },
    "Other": {
        "Infantry": [],
        "Structure": [
            "Psychic Beacon"  # Blitz oil
        ],
        "Tank": [],
        "Naval": [],
        "Aircraft": []
    }
}

factions = ['Allied', 'Soviet', 'Yuri', 'Other']
unit_types = ['Infantry', 'Structure', 'Tank', 'Naval', 'Aircraft']

SLAVE_MINER_CANONICAL_NAME = "Slave miner"
SLAVE_MINER_ALIASES = {
    "Slave miner",
    "Slave miner undeployed",
    "Slave Miner Deployed",
}

DISPLAY_IMAGE_ALIASES = {
    "Armored Transport": "Landing Craft",
    "GGI": "Guardian GI",
    "Allied Engineer": "Engineer",
    "Navy Seal": "SEAL",
    "SpySat": "Allied SpySat Uplink",
    "Allied Naval Yard": "Allied Shipyard",
    "Chronoshpere": "Allied Chrono Sphere",
    "Gap Generator": "Allied Gap Generator",
    "Grand Cannon": "Allied Grand Cannon",
    "Ore Purifier": "Allied Ore Processor",
    "Allied AFC": "Allied Airforce Command Headquarters",
    "PillBox": "Allied Pill Box",
    "Robot Control Center": "Allied Robot Control Center",
    "Weather Controller": "Allied Weather Controller",
    "Grizzly": "Grizzly Battle Tank",
    "Allied MCV": "Allied Construction Vehicle",
    "Allied Amphibious Transport": "Landing Craft",
    "NightHawk Transport": "BlackHawk Transport",
    "Agis Cruiser": "Aegis Cruiser",
    "Harrier": "Intruder",
    "Soviet Dog": "Attack Dog",
    "Ivan": "Crazy Ivan",
    "Battle Bunker": "Soviet Battle Bunker",
    "Flak Cannon": "Soviet Flak Cannon",
    "Iron Curtain": "Soviet Iron Curtain Device",
    "Sentry Gun": "Soviet Sentry Gun",
    "Industrial Plant": "Soviet Industrial Plant",
    "Nuclear Missile Launcher": "Soviet Nuclear Missile Silo",
    "Sov Radar": "Soviet Radar Tower",
    "Nuclear Reactor": "Soviet Nuclear Reactor",
    "Tesla Reactor": "Soviet Tesla Reactor",
    "Sov Service Depot": "Soviet Service Depot",
    "Sov Naval Yard": "Soviet Shipyard",
    "Rhino Tank": "Rhino Heavy Tank",
    "Apoc": "Apocalypse",
    "Siege Chopper": "Soviet Siege Chopper",
    "Kirov": "Kirov Airship",
    "V3 Rocket Launcher": "V3 Launcher",
    "Soviet MCV": "Soviet Construction Vehicle",
    "Demolition truck": "Demolitions Truck",
    "Squid": "Giant Squid",
    "Initiate": "Yuri Initiate",
    "Virus": "Yuri Virus",
    "Brute": "Yuri Brute",
    "Cloning Vats": "Yuri Cloning Vats",
    "Tank Bunker": "Yuri Tank Bunker",
    "Gattling Cannon": "Yuri Gattling Cannon",
    "Grinder": "Yuri Grinder",
    "Yuri Radar": "Yuri Psychic Sensor",
    "Psychic Tower": "Yuri Psychic Tower",
    "Psychic dominator": "Yuri Puppet Master",
    "Bio Reactor": "Yuri Bio Reactor",
    "Yuri Naval Yard": "Yuri Submarine Pen",
    "Disc": "Floating Disk",
    "Mastermind": "Master Mind",
    "Lasher": "Lasher Light Tank",
    "Yuri Amphibious Transport": "Hover Transport Yuri",
    "Yuri MCV": "Yuri Construction Vehicle",
    "Boomer Sub": "Yuri Boomer",
}


def canonicalize_unit_name(unit_name):
    if unit_name in SLAVE_MINER_ALIASES:
        return SLAVE_MINER_CANONICAL_NAME
    return unit_name


def get_display_image_name(unit_name):
    canonical_name = canonicalize_unit_name(unit_name)
    return DISPLAY_IMAGE_ALIASES.get(canonical_name, canonical_name)


def name_to_path(name):
    candidates = [
        os.path.join(BASE_DIR, 'cameos', 'png', f'{name}.png'),
        os.path.join(BASE_DIR, 'dist', 'cameos', 'png', f'{name}.png'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def find_vet_image_path(name):
    candidates = [
        os.path.join(BASE_DIR, 'cameos', 'png', f'{name} Vet.png'),
        os.path.join(BASE_DIR, 'cameos', 'png', f'{name} vet.png'),
        os.path.join(BASE_DIR, 'cameos', 'png', f'{name}_vet.png'),
        os.path.join(BASE_DIR, 'cameos', 'png', f'{name.lower()}_vet.png'),
        os.path.join(BASE_DIR, 'dist', 'cameos', 'png', f'{name} Vet.png'),
        os.path.join(BASE_DIR, 'dist', 'cameos', 'png', f'{name} vet.png'),
        os.path.join(BASE_DIR, 'dist', 'cameos', 'png', f'{name}_vet.png'),
        os.path.join(BASE_DIR, 'dist', 'cameos', 'png', f'{name.lower()}_vet.png'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def resolve_factory_image_path(unit_name, prefer_vet=False):
    image_name = get_display_image_name(unit_name)
    if prefer_vet:
        vet_path = find_vet_image_path(image_name)
        if vet_path:
            return vet_path
    return name_to_path(image_name)


def country_name_to_faction(country_name):
    if country_name in ['Americans', 'Alliance', 'French', 'Germans', 'British']:
        return 'Allied'
    elif country_name in ['Africans', 'Arabs', 'Confederation', 'Russians']:
        return 'Soviet'
    elif country_name == 'YuriCountry':
        return 'Yuri'
    else:
        return 'Unknown'
