import os

APP_NAME = "retromanager"

VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_REVISION = "0 RC1"

RESOURCES_FILE = os.path.join(os.path.split(__file__)[0], "resources.rcc")
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", APP_NAME)
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", APP_NAME)
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "ROMs")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
PLATFORMS_CACHE_FILENAME = os.path.join(CACHE_DIR, "database_cache.json")

ARCHIVE_PLATFORMS_DATA = [
    # Nintendo — original nointro.* IDs went private; using public mirrors (ZIP format)
    [ 'Nintendo - NES', 'zip', [
        '100-in-1-real-game-china-en-ja-pirate',       # titles 0-9
        'no-intro-nes-roms-from-myrient-a-e',
        'no-intro-nes-roms-from-myrient-f-l',
        'no-intro-nes-roms-from-myrient-m-r',
        'no-intro-nes-roms-from-myrient-s-z',
    ]],
    [ 'Nintendo - SNES',             'zip', 'ef_nintendo_snes_no-intro_2024-04-20' ],
    [ 'Nintendo - 64',               'zip', 'ef_nintendo_64_no-intro_2024-02-10'   ],
    [ 'Nintendo - Famicom Disk',     'zip', 'ef_nintendo_fds_no-intro_2024-03-02'  ],
    [ 'Nintendo - GameBoy',          'zip', 'theentiregameboycollection'            ],
    [ 'Nintendo - GameBoy Color',    'zip', 'theentireGAMEBOYCOLORcollection'      ],
    [ 'Nintendo - GameBoy Advance',  'zip', 'theentiregameboyadvancecollection'     ],
    # Nintendo VirtualBoy — all known sources are private, omitted
    # Nintendo 64DD  — only available as a single bundle archive, not individual files

    # Sega — original IDs still public (7z)
    [ 'Sega - Master System / Mark III', '7z', 'nointro.ms-mkiii'    ],
    [ 'Sega - Megadrive / Genesis',      '7z', 'nointro.md'          ],
    [ 'Sega - 32X',                      '7z', 'nointro.32x'         ],
    [ 'Sega - Game Gear',                '7z', 'nointro.gg'          ],

    # Atari — original IDs still public (7z)
    [ 'Atari 2600', '7z', 'nointro.atari-2600' ],
    [ 'Atari 5200', '7z', 'nointro.atari-5200' ],
    [ 'Atari 7800', '7z', 'nointro.atari-7800' ],

    # NEC — original ID still public (7z)
    [ 'NEC - PC Engine / TurboGrafx-16', '7z', 'nointro.tg-16' ],

    # SNK — No-Intro style MVS romset (individual ZIPs, no subdirectory)
    [ 'SNK - Neo Geo MVS', 'zip', 'neo-geo-mvs-romset' ],

    # Arcade — full MAME merged set (individual ZIPs inside mame-merged/ subdirectory)
    [ 'Arcade - MAME', 'zip', 'mame-merged' ],
]
