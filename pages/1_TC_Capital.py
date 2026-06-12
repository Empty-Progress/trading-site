import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib

lib.render_bot_page("tc", "TC Capital", lib.TC_GOLD, "The Base System")
