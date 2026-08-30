"""
QoderPilot account provisioning components.
No Google OAuth, no Qoder Desktop needed.
Flow: tempik (temp mail) â†’ signup â†’ captcha â†’ OTP â†’ PAT created.
"""
from .config import *
from .utils import *
from .tempmail import TempikClient
from .proxy import ProxyPool
from .captcha import solve_slider_local
from .signup import SignupManager, create_accounts
from .pat import PATManager
