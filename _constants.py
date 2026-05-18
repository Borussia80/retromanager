import os
import sys

APP_NAME = "retromanager"

# When running from a PyInstaller bundle, resource files land in sys._MEIPASS.
_BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

VERSION_MAJOR = 2
VERSION_MINOR = 3
VERSION_REVISION = 3

RESOURCES_FILE = os.path.join(_BASE, "resources.rcc")
ICONS_DIR  = os.path.join(_BASE, "resources", "icons")
ICON_FILE  = os.path.join(ICONS_DIR, "icon_256.png")
ABOUT_LOGO = os.path.join(ICONS_DIR, "about_dialog.png")
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", APP_NAME)
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", APP_NAME)
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "ROMs")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
PLATFORMS_CACHE_FILENAME = os.path.join(CACHE_DIR, "database_cache.json")   # legacy JSON (kept for migration)
PLATFORMS_CACHE_DB       = os.path.join(CACHE_DIR, "database_cache.db")
MAME_NAMES_CACHE        = os.path.join(CACHE_DIR, "mame_names.json")

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

    # Sony PlayStation — Hearto 2024 1G1R clean sets (ZIP/BIN format, format=ZIP ✓)
    [ 'Sony - PlayStation', 'zip', [
        '2024-sony-playstation-usa-hearto-1g1r-collection',
        '2024-sony-playstation-eur-hearto-1g1r-collection',
        '2024-sony-playstation-jap-hearto-1g1r-collection',
    ]],

    # Sony PlayStation 2 — Redump CHD split by letter (format=Unknown on Archive.org;
    # _ProcessPart matches by extension only to handle this inconsistency)
    [ 'Sony - PlayStation 2', 'chd', [
        'sony-playstation-2-0-redump-collection',
        'sony-playstation-2-a-redump-collection',
        'sony-playstation-2-b-redump-collection',
        'sony-playstation-2-c-redump-collection',
        'sony-playstation-2-d0-dm-redump-collection',
        'sony-playstation-2-dn-dz-redump-collection',
        'sony-playstation-2-e-redump-collection',
        'sony-playstation-2-f-redump-collection',
        'sony-playstation-2-g-redump-collection',
        'sony-playstation-2-h-redump-collection',
        'sony-playstation-2-i-redump-collection',
        'sony-playstation-2-j-redump-collection',
        'sony-playstation-2-k-redump-collection',
        'sony-playstation-2-l-redump-collection',
        'sony-playstation-2-m0-mm-redump-collection',
        'sony-playstation-2-n-redump-collection',
        'sony-playstation-2-o0-om-redump-collection',
        'sony-playstation-2-on-oz-redump-collection',
        'sony-playstation-2-q-redump-collection',
        'sony-playstation-2-r-redump-collection',
        'sony-playstation-2-s0-sh-redump-collection',
        'sony-playstation-2-si-so-redump-collection',
        'sony-playstation-2-sp-sq-redump-collection',
        'sony-playstation-2-sr-sz-redump-collection',
        'sony-playstation-2-t-redump-collection',
        'sony-playstation-2-u-redump-collection',
        'sony-playstation-2-v-redump-collection',
        'sony-playstation-2-x-redump-collection',
        'sony-playstation-2-y-redump-collection',
        'sony-playstation-2-z-redump-collection',
    ]],

    # Sony PSP — Redump CHD in two parts (format field varies; matched by extension)
    [ 'Sony - PSP', 'chd', [
        'psp-chd-zstd-redump-part1',
        'psp-chd-zstd-redump-part2',
    ]],
]
