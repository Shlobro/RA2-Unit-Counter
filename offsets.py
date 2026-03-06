KNOWN_OFFSETS = {
    0x24: "ArrayIndex (COUNTRYSTRINGOFFSET)",
    0x34: "Type - HouseTypeClass* (HOUSETYPECLASSBASEOFFSET)",
    # RelatedTags DynamicVectorClass<TagClass*>
    # ConYards DynamicVectorClass<BuildingClass*>
    0x60: "ConYards.Count (Construction Yard count)",
    # Buildings DynamicVectorClass<BuildingClass*>
    0x70: "Buildings related (when i made second tank bunker 10 -> 20)",
    0x78: "Buildings.Count (goes up slowly when i make structure. like +4 for afc. +1 for allied service depot etc and goes down when you lose stuff)",
    # UnitRepairStations DynamicVectorClass<BuildingClass*>
    0x84: "UnitRepairStations.Items (something to do with service depot?)",
    0x88: "UnitRepairStations.Count (something to do with service depot)",
    0x8c: "UnitRepairStations.Capacity (something to do with service depot)",
    0x90: "UnitRepairStations.Count (amount of service depot - allied and soviet and civ captured)",
    # Grinders DynamicVectorClass<BuildingClass*>
    0x9c: "Grinders.Items (when i made a grinder 0 -> 259953408)",
    0xa0: "Grinders.Count (when i made a grinder 0 -> 10)",
    0xa4: "Grinders.Capacity (when i made a grinder 1734934529 -> 1734934785)",
    0xa8: "Grinders.Count (number of grinders)",
    # Absorbers DynamicVectorClass<BuildingClass*>
    0xc0: "Absorbers.Count (number of bio reactors)",
    # Bunkers DynamicVectorClass<BuildingClass*>
    0xcc: "Bunkers.Items (when i made tank bunker 0 -> 279128848)",
    0xd0: "Bunkers.Count (when i made tank bunker 0 -> 10)",
    0xd4: "Bunkers.Capacity (when i made tank bunker 1702035457 -> 1702035713)",
    0xd8: "Bunkers.Count (number of tank bunkers)",
    # Occupiables DynamicVectorClass<BuildingClass*>
    0xe4: "Occupiables.Items (something to do with battle bunker - only first time made)",
    0xe8: "Occupiables.Count (something to do with battle bunker - only first time made)",
    0xec: "Occupiables.Capacity (something to do with battle bunker - only first time made)",
    0xf0: "Occupiables.Count (Battle bunker count)",
    # CloningVats DynamicVectorClass<BuildingClass*>
    0xfc: "CloningVats.Items (when I made bio reactor 0 -> 279125536)",
    0x100: "CloningVats.Count (when I made bio reactor 0 -> 10)",
    0x104: "CloningVats.Capacity (when I made bio reactor 774766593 -> 774766849)",
    0x108: "CloningVats.Count (when I made bio reactor 0 -> 1)",
    # SecretLabs DynamicVectorClass<BuildingClass*> - secret lab buildings
    0x10c: "SecretLabs.Items (pointer to secret lab building array)",
    0x110: "SecretLabs.Count",
    0x114: "SecretLabs.Capacity",
    0x118: "SecretLabs.IsAllocated",
    # PsychicDetectionBuildings DynamicVectorClass<BuildingClass*>
    0x12c: "PsychicDetectionBuildings.Items (went up as soon as i put yuri radar 0 -> 260024688)",
    0x130: "PsychicDetectionBuildings.Count (went up as soon as i put yuri radar 0 -> 10)",
    0x134: "PsychicDetectionBuildings.Capacity (went up as soon as i put yuri radar 1851850753 -> 1851851009)",
    0x138: "PsychicDetectionBuildings.Count (number of yuri radar)",
    # FactoryPlants DynamicVectorClass<BuildingClass*>
    0x144: "FactoryPlants.Items (somthing to do with industrial plant)",
    0x148: "FactoryPlants.Count (somthing to do with industrial plant)",
    0x14c: "FactoryPlants.Capacity (somthing to do with industrial plant)",
    0x150: "FactoryPlants.Count (industrial plant bonus - 1 = active, 0 = not active)",
    0x158: "CountResourceGatherers (Miners)",
    0x15c: "CountResourceDestinations (Ore refinery's)",
    0x160: "CountWarfactories (War Factory's)",

    0x164: "InfantrySelfHeal",  # int - hospital/armory bonus counter
    0x168: "UnitsSelfHeal",  # int - service depot bonus counter
    # StartingUnits DynamicVectorClass follows
    # AIDifficulty - NOTE: reversed! Hard=0, Easy=2
    0x17c: "AIDifficulty (Hard=0, Medium=1, Easy=2 - reversed!)",
    # Multipliers (doubles = 8 bytes each)
    0x180: "FirepowerMultiplier (double)",
    0x188: "GroundspeedMultiplier (double - unused)",
    0x190: "AirspeedMultiplier (double - unused)",
    0x198: "ArmorMultiplier (double)",
    0x1a0: "ROFMultiplier (double)",
    0x1a8: "CostMultiplier (double)",
    0x1b0: "BuildTimeMultiplier (double - unused)",
    0x1b8: "RepairDelay (double)",
    0x1c0: "BuildDelay (double)",
    0x1c8: "IQLevel",
    0x1cc: "TechLevel",
    # AltAllies DWORD
    0x1d4: "StartingCredits (actual credits = this * 100)",
    0x1d8: "StartingEdge",
    0x1e0: "SideIndex",
    0x1e4: "CurrentPlayer (bool - is controlled by player at this computer)",
    0x1e5: "PlayerControl (bool - a human controls this House)",
    0x1e6: "Production (bool - AI production has begun)",
    0x1e7: "AutocreateAllowed (bool)",
    # 2 unknown bytes
    0x1ea: "AITriggersActive (bool)",
    0x1eb: "AutoBaseBuilding (bool)",
    0x1ec: "DiscoveredByPlayer (bool)",
    0x1ed: "Defeated (bool)",
    0x1f2: "IsGameOver",  # bool - from header line 722
    0x1f3: "IsWinner",  # bool - from header line 723
    0x1f4: "IsLoser",  # bool - from header line 724
    0x1f5: "CiviliansEvacuated",  # bool
    0x1f6: "FirestormActive",  # bool (was IsGameOver - offset may vary)
    0x1f7: "HasThreatNode (ISWINNEROFFSET - check offset)",
    0x1f8: "RecheckTechTree (ISLOSEROFFSET - check offset)",

    # PlanningPaths WaypointPathClass*[12] and other fields
    0x1fc: "SelectedPathIndex related (changed when made allied engi but only for the first one)",
    0x23d: "Visionary (char)",
    0x23e: "MapIsClear (bool)",
    0x240: "HasBeenThieved (bool - something entered by Thief/VehicleThief)",
    0x241: "Repairing (bool - BuildingClass::Repair for AI)",
    0x245: "AllToHunt (bool)",
    0x248: "IQLevel2 (int - duplicate of IQLevel, unknown why)",
    0x24c: "AIMode",

    # Supers DynamicVectorClass<SuperClass*> - superweapons owned by this house
    0x26c: "LastBuiltBuildingType (Structure just placed - 9=tesla reactor, 10=sov battle lab, 11=soviet barracks, 13=soviet radar, 14=sov WF, 15=soviet Ore ref, 16=sov wall, 20=sentry gun, 24=iron curtain, 26=sov service depot, 25=soviet construction vehicle, 53=tesla coil, 54=Nuke, 65=nuke power plant, 67=flak track, 310=industrial plant, 359=battle bunker)",
    0x270: "LastBuiltInfantryType (Infantry just made - 1=conscript, 2=Tesla Trooper, 7=Crazy Ivan, 8=deso, 9=soviet dog, 25=flak trooper, 27=soviet Engi, 48=Boris)",
    0x274: "LastBuiltAircraftType (header has Aircraft here, but observed as vehicle - 1=sov war miner, 2=apoc, 3=rhino tank, 14=v3 rocket launcher, 15=kirov, 16=Terror drone, 17=flak track, 26=Sov mcv, 67=siege chopper)",
    0x278: "LastBuiltVehicleType (header has Vehicle here, but observed as aircraft - swapped with 0x274?)",

    # TimerStruct RepairTimer (12 bytes each timer)
    0x27c: "AllowWinBlocks",
    0x280: "RepairTimer",  # CDTimerClass for AI
    0x28c: "AlertTimer (unknown_timer_28C)",
    0x298: "SavourTimer",
    # PowerBlackoutTimer
    0x2a4: "PowerBlackoutTimer (something to do with force shield)",
    0x2a8: "PowerBlackoutTimer+4 (something to do with force shield)",
    0x2ac: "PowerBlackoutTimer+8 (something to do with force shield)",
    # RadarBlackoutTimer follows




    # Infiltration flags (bools) - header lines 757-761
    0x2bc: "Side2TechInfiltrated (Yuri battle lab infiltrated - 1=yes 0=no)",
    0x2bd: "Side1TechInfiltrated (Soviet battle lab infiltrated - 1=yes 0=no)",
    0x2be: "Side0TechInfiltrated (Allied battle lab infiltrated - 1=yes 0=no)",
    0x2bf: "BarracksInfiltrated (0 if not)",
    0x2c0: "WarFactoryInfiltrated (0 if not)",

    # AltOwner DWORDs (0x2C1-0x2D0) - unused in game
    # 0x2c1: InfantryAltOwner, 0x2c5: UnitAltOwner, 0x2c9: AircraftAltOwner, 0x2cd: BuildingAltOwner

    0x2d4: "AirportDocks (number of aircrafts that can be built)",
    0x2d8: "PoweredUnitCenters (Robot tanks online=1, offline=0 - Robot Control Centers)",
    0x2dc: "unknown_2DC (Credits spent)",
    0x2e0: "unknown_2E0 (HarvestedCredits)",
    0x2e4: "unknown_2E4 (StolenBuildingsCredits)",

    # Owned counts - header lines 784-788
    0x2e8: "OwnedUnits (number of vehicles)",
    0x2ec: "OwnedNavy (number of Naval units)",
    0x2f0: "OwnedBuildings (Number of structures - even ones in queue, goes down if cancelled)",
    0x2f4: "OwnedInfantry (Amount of infantry)",
    0x2f8: "OwnedAircraft (aircraft count)",

    # OwnedTiberium struct (stores ore amounts), then Balance
    0x30c: "Balance",  # int - current credits
    0x310: "TotalStorage",  # int - capacity of all building Storage (silos + refineries)
    # OwnedWeed struct follows

    # TotalStorage, OwnedWeed follow Balance
    # Then ScoreStruct arrays - each ScoreStruct is 0x808 bytes: int Counts[0x200], NumCounts, ByteOrder
    # BuiltAircraftTypes ScoreStruct (aircraft built counts by type index)
    0x32c: "BuiltAircraftTypes.Counts[0] (Total amount of Harriers made)",
    0x340: "BuiltAircraftTypes.Counts[5] (paradrop plane - keeps going up every paradrop)",
    0x344: "BuiltAircraftTypes.Counts[6] (Total amount of Black eagles made)",
    0x350: "BuiltAircraftTypes.Counts[9] (amount of spy planes made)",

    # BuiltInfantryTypes ScoreStruct (infantry built counts by type index)
    0xb30: "BuiltInfantryTypes.Counts[0] (Total amount of GI made)",
    0xb34: "Total amount of Conscript made",
    0xb38: "Total amount of Tesla Trooper made",
    0xb3c: "Total amount of Allied Engineer made",
    0xb40: "Total amount of Rocketeer made",
    0xb44: "Total amount of Navy SEAL made",
    0xb48: "Total amount of Yuri Clone made",
    0xb4c: "Total amount of Crazy Ivan made",
    0xb50: "Total amount of Desolator made",
    0xb54: "Total amount of Soviet Dog made",
    0xb6c: "Total amount of Chrono Legionnaire made",
    0xb70: "Total amount of Spy made",
    0xb80: "Total amount of Yuri Prime made",
    0xb84: "Total amount of Sniper made",
    0xb90: "Total amount of Tanya made",
    0xb94: "Total amount of Flak Trooper made",
    0xb98: "Total amount of Terrorist made",
    0xb9c: "Total amount of Soviet Engineer made",
    0xba0: "Total amount of Allied Dog made",
    0xbe4: "Total amount of Yuri Engineer made",
    0xbe8: "Total amount of Guardian GI (GGI) made",
    0xbec: "Total amount of Initiate made",
    0xbf0: "Total amount of Boris made",
    0xbf4: "Total amount of Brute made",
    0xbf8: "Total amount of Virus made",

    # BuiltUnitTypes ScoreStruct (vehicle/unit built counts by type index)
    0x1338: "BuiltUnitTypes.Counts[0] (Total amount of Allied MCV made)",
    0x133c: "Total amount of War Miners made",
    0x1340: "Total amount of Apocalypse Tanks made",
    0x1344: "Total amount of Rhino Tanks made",
    0x1348: "Total amount of Soviet Amphibious Transports made",
    0x135c: "Total amount of Grizzly Tanks made",
    0x136c: "Total amount of Aircraft Carriers made",
    0x1370: "Total amount of V3 Rocket Launchers made",
    0x1374: "Total amount of Kirov Airships made",
    0x1378: "Total amount of Terror Drones made",
    0x137c: "Total amount of Flak Tracks made",
    0x1380: "Total amount of Destroyers made",
    0x1384: "Total amount of Typhoon Attack Subs made",
    0x1388: "Total amount of Aegis Cruisers made",
    0x138c: "Total amount of Allied Amphibious Transports made",
    0x1390: "Total amount of Dreadnoughts made",
    0x1394: "Total amount of NightHawk Transports made",
    0x1398: "Total amount of Giant Squids made",
    0x139c: "Total amount of Dolphins made",
    0x13a0: "Total amount of Soviet MCVs made",
    0x13a4: "Total amount of Tank Destroyers made",
    0x13b4: "Total amount of Lasher Tanks made",
    0x13bc: "Total amount of Chrono Miners made",
    0x13c0: "Total amount of Prism Tanks made",
    0x13c8: "Total amount of Sea Scorpions made",
    0x13cc: "Total amount of Mirage Tanks made",
    0x13d0: "Total amount of IFVs made",
    0x13dc: "Total amount of Demolition Trucks made",
    0x1414: "Total amount of Yuri Amphibious Transports made",
    0x1418: "Total amount of Yuri MCVs made",
    0x141c: "Total amount of Slave Miners Undeployed made",
    0x1428: "Total amount of Gattling Tanks made",
    0x142c: "Total amount of Battle Fortresses made",
    0x1430: "Total amount of Chaos Drones made",
    0x1434: "Total amount of Magnetrons made",
    0x1440: "Total amount of Boomers made",
    0x1444: "Total amount of Siege Choppers made",
    0x144c: "Total amount of Masterminds made",
    0x1450: "Total amount of Flying Discs made",
    0x1458: "Total amount of Robot Tanks made",

    # BuiltBuildingTypes ScoreStruct (building built counts by type index)
    0x1b40: "BuiltBuildingTypes.Counts[0] (Total amount of Allied Power Plant ever built)",
    0x1b44: "Total amount of Allied Ore Refinery ever built",
    0x1b48: "Total amount of Allied Con Yard ever built",
    0x1b4c: "Total amount of Allied Barracks ever built",
    0x1b54: "Total amount of Allied Service Depot ever built",
    0x1b58: "Total amount of Allied Battle Lab ever built",
    0x1b5c: "Total amount of Allied War Factory ever built",
    0x1b64: "Total amount of Tesla Reactor ever built",
    0x1b68: "Total amount of Soviet Battle Lab ever built",
    0x1b6c: "Total amount of Soviet Barracks ever built",
    0x1b74: "Total amount of Soviet Radar ever built",
    0x1b78: "Total amount of Soviet War Factory ever built",
    0x1b7c: "Total amount of Soviet Ore Refinery ever built",
    0x1b88: "Total amount of Yuri Radar ever built",
    0x1b90: "Total amount of Sentry Gun ever built",
    0x1b94: "Total amount of Patriot Missile ever built",
    0x1b9c: "Total amount of Allied Naval Yard ever built",
    0x1ba0: "Total amount of Iron Curtain ever built",
    0x1ba4: "Total amount of Soviet Con Yard ever built",
    0x1ba8: "Total amount of Soviet Service Depot ever built",
    0x1bac: "Total amount of Chrono Sphere ever built",
    0x1bb4: "Total amount of Weather Controller ever built",
    0x1c14: "Total amount of Tesla Coil ever built",
    0x1c18: "Total amount of Nuclear Missile Launcher ever built",
    0x1c34: "Total amount of Soviet Naval Yard ever built",
    0x1c38: "Total amount of SpySat Uplink ever built",
    0x1c3c: "Total amount of Gap Generator ever built",
    0x1c44: "Total amount of Nuclear Reactor ever built",
    0x1c48: "Total amount of PillBox ever built",
    0x1c4c: "Total amount of Flak Cannon ever built",
    0x1c5c: "Total amount of Oil Derrick ever built",
    0x1c60: "Total amount of Cloning Vats ever built",
    0x1c64: "Total amount of Ore Purifier ever built",
    0x1ce4: "Total amount of Allied AFC ever built",
    0x1d5c: "Total amount of American AFC ever built",
    0x1ff0: "Total amount of Yuri Con Yard ever built",
    0x1ff4: "Total amount of Bio Reactor ever built",
    0x1ff8: "Total amount of Yuri Barracks ever built",
    0x1ffc: "Total amount of Yuri War Factory ever built",
    0x2000: "Total amount of Yuri Naval Yard ever built",
    0x2008: "Total amount of Yuri Battle Lab ever built",
    0x2010: "Total amount of Gattling Cannon ever built",
    0x2014: "Total amount of Psychic Tower ever built",
    0x2018: "Total amount of Industrial Plant ever built",
    0x201c: "Total amount of Grinder ever built",
    0x2020: "Total amount of Genetic Mutator ever built",
    0x202c: "Total amount of Psychic Dominator ever built",
    0x2098: "Total amount of Tank Bunker ever built",
    0x20d0: "Total amount of Robot Control Center ever built",
    0x20d4: "Total amount of Slave Miner Deployed ever built",
    0x20dc: "Total amount of Battle Bunker ever built",

    # KilledAircraftTypes ScoreStruct would be around 0x2348 - TODO missing the aircraft lost here

    # KilledInfantryTypes ScoreStruct (infantry killed/lost counts by type index)
    0x2b50: "KilledInfantryTypes.Counts[0] (GI lost)",
    0x2b54: "Conscripts lost",
    0x2b58: "Tesla Troopers lost",
    0x2b5c: "Allied Engineer lost",
    0x2b60: "Rocketeer lost",
    0x2b64: "Navy SEAL lost",
    0x2b68: "Yuri Clone lost",
    0x2b6c: "Crazy Ivan lost",
    0x2b70: "Desolator lost",
    0x2b74: "Soviet Dog lost",
    0x2b8c: "Chrono Legionnaire lost",
    0x2b90: "Spy lost",
    0x2ba0: "Yuri Prime lost",
    0x2ba4: "Sniper lost",
    0x2bb0: "Tanya lost",
    0x2bb4: "Flak Trooper lost",
    0x2bb8: "Terrorist lost",
    0x2bbc: "Soviet Engineer lost",
    0x2bc0: "Allied Dog lost",
    0x2c04: "Yuri Engineer lost",
    0x2c08: "Guardian GI (GGI) lost",
    0x2c0c: "Initiate lost",
    0x2c10: "Boris lost",
    0x2c14: "Brute lost",
    0x2c18: "Virus lost",

    # KilledUnitTypes ScoreStruct (vehicle/unit killed/lost counts by type index)
    0x3358: "KilledUnitTypes.Counts[0] (Allied MCV lost)",
    0x335c: "War Miner lost",
    0x3360: "Apocalypse Tank lost",
    0x3364: "Rhino Tank lost",
    0x3368: "Soviet Amphibious Transport lost",
    0x337c: "Grizzly Tank lost",
    0x338c: "Aircraft Carrier lost",
    0x3390: "V3 Rocket Launcher lost",
    0x3394: "Kirov Airship lost",
    0x3398: "Terror Drone lost",
    0x339c: "Flak Track lost",
    0x33a0: "Destroyer lost",
    0x33a4: "Typhoon Attack Sub lost",
    0x33a8: "Aegis Cruiser lost",
    0x33ac: "Allied Amphibious Transport lost",
    0x33b0: "Dreadnought lost",
    0x33b4: "NightHawk Transport lost",
    0x33b8: "Giant Squid lost",
    0x33bc: "Dolphin lost",
    0x33c0: "Soviet MCV lost",
    0x33c4: "Tank Destroyer lost",
    0x33d4: "Lasher Tank lost",
    0x33dc: "Chrono Miner lost",
    0x33e0: "Prism Tank lost",
    0x33e8: "Sea Scorpion lost",
    0x33ec: "Mirage Tank lost",
    0x33f0: "IFV lost",
    0x33fc: "Demolition Truck lost",
    0x3434: "Yuri Amphibious Transport lost",
    0x3438: "Yuri MCV lost",
    0x343c: "Slave Miner Undeployed lost",
    0x3448: "Gattling Tank lost",
    0x344c: "Battle Fortress lost",
    0x3450: "Chaos Drone lost",
    0x3454: "Magnetron lost",
    0x3460: "Boomer lost",
    0x3464: "Siege Chopper lost",
    0x346c: "Mastermind lost",
    0x3470: "Flying Disc lost",
    0x3478: "Robot Tank lost",

    # KilledBuildingTypes ScoreStruct (building killed/lost counts by type index)
    0x3b60: "KilledBuildingTypes.Counts[0] (Allied Power Plant lost)",
    0x3b64: "Allied Ore Refinery lost",
    0x3b68: "Allied Con Yard lost",
    0x3b6c: "Allied Barracks lost",
    0x3b74: "Allied Service Depot lost",
    0x3b78: "Allied Battle Lab lost",
    0x3b7c: "Allied War Factory lost",
    0x3b84: "Tesla Reactor lost",
    0x3b88: "Soviet Battle Lab lost",
    0x3b8c: "Soviet Barracks lost",
    0x3b94: "Soviet Radar lost",
    0x3b98: "Soviet War Factory lost",
    0x3b9c: "Soviet Ore Refinery lost",
    0x3ba8: "Yuri Radar lost",
    0x3bb0: "Sentry Gun lost",
    0x3bb4: "Patriot Missile lost",
    0x3bbc: "Allied Naval Yard lost",
    0x3bc0: "Iron Curtain lost",
    0x3bc4: "Soviet Construction Yard lost",
    0x3bc8: "Soviet Service Depot lost",
    0x3bcc: "Chrono Sphere lost",
    0x3bd4: "Weather Controller lost",
    0x3c34: "Tesla Coil lost",
    0x3c38: "Nuclear Missile Launcher lost",
    0x3c4c: "Soviet Naval Yard lost",
    0x3c50: "SpySat Uplink lost",
    0x3c54: "Gap Generator lost",
    0x3c5c: "Nuclear Reactor lost",
    0x3c60: "PillBox lost",
    0x3c64: "Flak Cannon lost",
    0x3c74: "Oil Derrick lost",
    0x3c78: "Cloning Vats lost",
    0x3c7c: "Ore Purifier lost",
    0x3d04: "Allied AFC lost",
    0x3d7c: "American AFC lost",
    0x4010: "Yuri Construction Yard lost",
    0x4014: "Bio Reactor lost",
    0x4018: "Yuri Barracks lost",
    0x401c: "Yuri War Factory lost",
    0x4020: "Yuri Naval Yard lost",
    0x4028: "Yuri Battle Lab lost",
    0x4030: "Gattling Cannon lost",
    0x4034: "Psychic Tower lost",
    0x4038: "Industrial Plant lost",
    0x403c: "Grinder lost",
    0x4040: "Genetic Mutator lost",
    0x404c: "Psychic Dominator lost",
    0x40b8: "Tank Bunker lost",
    0x40f0: "Robot Control Center lost",
    0x40f4: "Slave Miner Deployed lost",
    0x40fc: "Battle Bunker lost",

    # NumAirpads, NumBarracks, NumWarFactories, NumConYards, NumShipyards, NumOrePurifiers - header lines 803-809
    # Then CostXMult floats, then PowerOutput/PowerDrain
    0x5378: "NumAirpads",
    0x537c: "NumBarracks (Barracks count)",
    0x5380: "NumWarFactories (war factorys)",
    0x5384: "NumConYards (Construction Yard count)",
    0x5388: "NumShipyards",
    0x538c: "NumOrePurifiers",
    # CostXMult floats (4 bytes each) - header lines 810-814
    0x5390: "CostInfantryMult (float)",
    0x5394: "CostUnitsMult (float)",
    0x5398: "CostAircraftMult (float)",
    0x539c: "CostBuildingsMult (float)",
    0x53a0: "CostDefensesMult (float)",

    0x53a4: "PowerOutput",  # int - header line 815
    0x53a8: "PowerDrain",  # int - header line 816

    # Primary factory pointers - header lines 817-825
    0x53ac: "Primary_ForAircraft (FactoryClass* - aircraft factory pointer)",
    0x53b0: "Primary_ForInfantry (FactoryClass* - infantry factory pointer)",
    0x53b4: "Primary_ForVehicles (FactoryClass* - tank being built? 0 when none)",
    0x53b8: "Primary_ForShips (FactoryClass* - ship factory pointer)",
    0x53bc: "Primary_ForBuildings (FactoryClass* - structure being built, BLOCKED)",
    0x53c0: "Primary_Unused1 (FactoryClass*)",
    0x53c4: "Primary_Unused2 (FactoryClass*)",
    0x53c8: "Primary_Unused3 (FactoryClass*)",
    0x53cc: "Primary_ForDefenses (FactoryClass* - defense structure factory)",
    # 12 unknown bytes (0x53D0-0x53DB)
    0x53dc: "OurFlagCarrier (UnitClass* - unit carrying flag in CTF)",
    0x53e0: "OurFlagCoords (CellStruct - X,Y coords of flag)",
    # OurFlagCarrier (UnitClass*), OurFlagCoords (CellStruct)
    # KilledUnitsOfHouses[0x14], TotalKilledUnits, KilledBuildingsOfHouses[0x14], TotalKilledBuildings
    0x53e4: "KilledUnitsOfHouses or TotalKilledUnits (infantry lost)",
    0x5434: "KilledBuildingsOfHouses related (infantry lost)",
    0x5438: "TotalKilledBuildings (number of buildings lost)",
    0x5488: "BaseSpawnCell or BaseCenter related (number of buildings lost)",
    0x5490: "BaseCenter/unknown (changes to huge number when undeployed and 0 when deployed - BLOCKED)",
    # SiloMoney, PreferredTargetType, PreferredTargetCell, etc.
    0x54d8: "PreferredDefensiveCellStartTime or nearby (keeps going up destroying own buildings 176669 -> 176696)",
    0x54e8: "SiloMoney related (goes up by 200 every miner dump - Ignored)",
    0x5510: "OwnedBuildingTypes related (Number of structures in queue - goes down if cancelled)",
    0x5524: "OwnedUnitTypes related (vehicle count?)",
    0x552c: "CounterClass.Items pointer (went 0 -> 285645296 when sold tesla reactor - Blocked)",
    0x5530: "CounterClass.Count (went 0 -> 11 when sold tesla reactor)",
    0x5534: "CounterClass.Capacity (went 1 -> 257 when sold tesla reactor)",
    0x5538: "OwnedInfantryTypes related (infantry count)",
    0x5560: "OwnedBuildingTypes1 related (Number of structures currently has)",
    0x5574: "OwnedUnitTypes1 related (number of vehicles)",

    # CounterClass arrays - header lines 877-901
    # OwnedXTypes = currently owned (BuildLimit > 0 check)
    # OwnedXTypes1 = owned and present on map (prereq checks)
    # OwnedXTypes2 = total produced from factory (BuildLimit < 0 check)
    0x5554: "OwnedBuildingTypes (BUILDINGOFFSET - CounterClass for buildings currently owned)",
    0x5568: "OwnedUnitTypes (TANKOFFSET - CounterClass for units currently owned)",
    0x557c: "OwnedInfantryTypes (INFOFFSET - CounterClass for infantry currently owned)",
    0x5590: "OwnedAircraftTypes (AIRCRAFTOFFSET - CounterClass for aircraft currently owned)",

    # OwnedXTypes1 - present on map
    0x55A4: "OwnedBuildingTypes1 (Total made Buildings Offset - present on map)",
    0x55B8: "OwnedUnitTypes1 (Total made Tanks Offset - present on map)",
    0x55CC: "OwnedInfantryTypes1 (Total made Inf Offset - present on map)",
    0x55E0: "OwnedAircraftTypes1 (Total made Aircraft Offset - present on map)",

    # OwnedXTypes2 - total produced from factory (follows after OwnedXTypes1)






    0x5588: "OwnedInfantryTypes1 related (infantry count)",
    0x55a4: "OwnedBuildingTypes2.Items (went from 0 to super high when i placed tesla reactor - BLOCKED)",
    0x55a8: "OwnedBuildingTypes2.Count (goes up the more structures you have? not linear)",
    0x55ac: "OwnedBuildingTypes2.Capacity (went from 1 to 257 when i placed tesla reactor)",
    0x55b0: "OwnedBuildingTypes2.Items or Count (total amount of structures placed)",
    0x55d8: "OwnedInfantryTypes2 related (Infantry count???? when i killed sov barracks 79020 -> 144567)",

    # OwnedXTypes2 (CounterClass) continues...
    0x55f8: "AttackDelayA (int - unused)",
    0x55fc: "AttackDelayB (int - unused)",
    0x5600: "EnemyHouseIndex (int - index of enemy house for AI)",
    # AngerNodes DynamicVectorClass<AngerStruct>, ScoutNodes DynamicVectorClass<ScoutStruct>
    0x5724: "AngerNodes or ScoutNodes related (went 49918736 -> 259478592 when placed tesla reactor - BLOCKED)",
    0x5728: "AngerNodes/ScoutNodes (went 20 -> 30 when placed tesla reactor - BLOCKED)",
    0x5730: "unkTimer3/unkTimer4 (deploying soviet mcv makes this 20, undeploying=0 - BLOCKED)",
    # ProducingXTypeIndex fields - what is currently being produced
    0x5748: "ProducingBuildingTypeIndex (int - building type index being produced)",
    0x574c: "ProducingUnitTypeIndex (int - unit type index being produced)",
    0x5750: "ProducingInfantryTypeIndex (int - infantry type index being produced)",
    0x5754: "ProducingAircraftTypeIndex (int - aircraft type index being produced)",
    0x5758: "RatioAITriggerTeam (went 25 -> 21 when placed second tesla reactor - BLOCKED)",
    0x575c: "RatioTeamAircraft (went 9 -> 11 when placed tesla reactor - BLOCKED)",
    0x5760: "RatioTeamInfantry (went 6 -> 10 when placed tesla reactor - BLOCKED)",
    0x5764: "RatioTeamBuildings",
    0x5768: "BaseDefenseTeamCount",
    # DropshipStruct DropshipData[3] - for paradrop/reinforcement planes
    0x5778: "DropshipData or CurrentDropshipIndex (when soviet barracks got destroyed: 257 -> 0)",
    # HasCloakingRanges, Color (RGB), LaserColor (RGB)
    0x5790: "Color (ColorStruct RGB - player color)",
    0x5794: "LaserColor (ColorStruct RGB)",
    # BaseClass Base follows - contains AI base building info
    0x57a4: "Base or Timer related (Adds around 360 every second - Game time?)",
    0x57a8: "Base.PercentBuilt or related (scrolling around the map???)",
    # RecheckPower, RecheckRadar, SpySatActive, IsBeingDrained (bools)
    0x57b4: "RecheckPower (bool)",
    0x57b5: "RecheckRadar (bool)",
    0x57b6: "SpySatActive (bool - spy satellite active)",
    0x57b7: "IsBeingDrained (bool - being drained by spy)",
    0x57b8: "Edge (spawn edge)",
    0x57bc: "EMPTarget or NukeTarget (CellStruct - keeps going up when low power 395159 -> 395726)",
    # Allies DWORD - bitmask of allied houses
    0x57c4: "Allies (DWORD bitmask - one bit per allied HouseClass)",
    # DamageDelayTimer, TeamDelayTimer, and other timers follow
    # PlainName char[0x15], UINameString char[0x20], UIName wchar_t[0x15] - header lines 948-950
    0x1602a: "PlainName (player name - defaults to country name in SP or <human player><computer player> in MP)",
    0x16054: "ColorSchemeIndex (color scheme)",
    0x16058: "StartingCell (CellStruct - spawn location X)",
    0x1605a: "StartingCell+2 (CellStruct - spawn location Y)",
    0x1605c: "StartingAllies (DWORD)",
    # WaypointPath DynamicVectorClass follows
    # PredictionEnemyX floats - AI threat estimation
    0x1609c: "PredictionEnemyArmor (float - defaults to 0.33)",
    0x160a0: "PredictionEnemyAir (float)",
    0x160a4: "PredictionEnemyInfantry (float)",
    # TotalOwnedXCost (ints) - header lines 965-968
    0x160a8: "TotalOwnedInfantryCost (money spent on infantry)",
    0x160ac: "TotalOwnedVehicleCost (money spent on tanks)",
    0x160b0: "TotalOwnedAircraftCost",
    #0x160b4: "unknown_160B4",
    # End of HouseClass at 0x160B8 - this is the last address no point in going beyond this
}