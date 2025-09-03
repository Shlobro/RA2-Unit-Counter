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

# offset for number of war factories
NUMBEROFWFOFFSET = 0x160

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

# Mapping of color scheme values to actual colors.
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
            "Desolator",
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
            "Yuri Ore Refinery",  # added based on top dict
            "Yuri Puppet Master"
            # Removed "Psychic dominator" (now "Yuri Puppet Master") and "Slave Miner Deployed"
        ],
        "Tank": [
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
