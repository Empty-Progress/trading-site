import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib

lib.render_bot_page("martan", "Martan Trading", lib.MARTAN_BLUE, "The Upgraded System")
