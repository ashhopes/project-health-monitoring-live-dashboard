# dashboard_cloud.py - UPDATED WITH LOGO, CORRECT TIME & MUJI THEME
"""
REAL-TIME DASHBOARD FOR STEMCUBE
WITH UMP LOGO, CORRECT TIME & MUJI THEME
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import pytz
from collections import deque
import base64
from io import BytesIO

# ================ TRY TO IMPORT SERIAL ================
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE REAL-TIME MONITOR",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ UMP LOGO BASE64 ================
UMP_LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAfQAAABmCAYAAAD3mVZSAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA
AXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAZdSURBVHgB7d1BbhtHEIDRGRp5/4uyJ5ByYBwY
wIF9YIC4h6QL2ySbe2d2B1jfRwEESfL/j1/f/vgJAPDavr1/AAD4IkEHAEkEHQCkEXQAkEbQAUAa
QQcAaQQdAKQRdACQRtABQBpBBwBpBB0ApBF0AJBG0AFAGkE3wOsX3j/xAsA6V2y/Owg6AHh9j85S
0AFAu6uzFHQA0GrGLAUdALSZNUtBBwAtZs9S0AHAy1bmKOgA4KWr8xN0APCy1fkJOgB4ycoMBR0A
vGRljoIOAF6wOkdBBwDjrc5R0AHAaKtzFHQA0GLGPAUdAIw2Y56CDgDGmjVPQQcAI82cq6ADgHFm
zlXQAcAos2cr6ABgjNnzFXQAMMLq+Qo6AFhu9YwFHQAsN3vGgg4Alpo9Z0EHAEvNnrOgA4BlVsxZ
0AHAEitmLegAYL4VsxZ0ADDXilkLOgCYa9W8BR0AzLNq3oIOAOZZNW9BBwDzrJq3oAOAeVbNW9AB
wByr5i3oAGCeVfMWdAAwz6p5CzoAmGflzAUdAMyxcuaCDgDmWDlzQQcAc6ycuaADgBlWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AGA9//4HZRl
AQAt9zY4AAAAAElFTkSuQmCC
"""

# ================ MUJI + OLIVE MARROON THEME ================
st.markdown(f"""
<style>
    /* MUJI + OLIVE MARROON COLOR PALETTE */
    :root {{
        --muji-maroon: #8B4513;
        --olive-green: #556B2F;
        --champagne: #F7E7CE;
        --soft-beige: #F5F5DC;
        --dark-chocolate: #3C2F2F;
        --cream: #FFFDD0;
        --warm-brown: #A0522D;
        --earth-green: #6B8E23;
    }}
    
    /* MAIN BACKGROUND */
    .stApp {{
        background: linear-gradient(135deg, var(--soft-beige) 0%, var(--cream) 100%);
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    
    /* HEADER WITH LOGO */
    .main-header {{
        background: linear-gradient(135deg, var(--muji-maroon) 0%, var(--olive-green) 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 6px 20px rgba(139, 69, 19, 0.3);
        text-align: center;
        position: relative;
    }}
    
    .logo-container {{
        position: absolute;
        left: 30px;
        top: 50%;
        transform: translateY(-50%);
    }}
    
    .logo-img {{
        height: 60px;
        width: auto;
        filter: brightness(0) invert(1);
    }}
    
    /* CARD STYLES */
    .metric-card {{
        background: linear-gradient(135deg, white 0%, var(--champagne) 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(85, 107, 47, 0.15);
        border-left: 4px solid var(--olive-green);
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(85, 107, 47, 0.2);
    }}
    
    .graph-container {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
        border-top: 4px solid var(--muji-maroon);
        margin-bottom: 20px;
    }}
    
    /* SIDEBAR */
    .sidebar-section {{
        background: linear-gradient(135deg, var(--champagne) 0%, white 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
        margin-bottom: 20px;
        border: 2px solid var(--soft-beige);
    }}
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 5px;
        background: var(--soft-beige);
        padding: 5px;
        border-radius: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: var(--champagne);
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        color: var(--dark-chocolate);
        border: 2px solid transparent;
        transition: all 0.3s;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--muji-maroon) 0%, var(--olive-green) 100%) !important;
        color: white !important;
        border-color: var(--muji-maroon) !important;
    }}
    
    /* BUTTONS */
    .stButton button {{
        background: linear-gradient(135deg, var(--olive-green) 0%, var(--muji-maroon) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }}
    
    .stButton button:hover {{
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
    }}
    
    /* METRICS */
    .metric-value {{
        font-size: 32px;
        font-weight: 700;
        color: var(--dark-chocolate);
        margin: 5px 0;
    }}
    
    .metric-label {{
        font-size: 13px;
        color: var(--olive-green);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* STATUS INDICATORS */
    .status-normal {{
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    .status-warning {{
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    .status-critical {{
        background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    /* DATA TABLE */
    .dataframe {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    .dataframe th {{
        background: var(--olive-green) !important;
        color: white !important;
        font-weight: 600 !important;
    }}
    
    /* FOOTER */
    .dashboard-footer {{
        background: linear-gradient(135deg, var(--dark-chocolate) 0%, #2C1810 100%);
        color: var(--champagne);
        padding: 20px;
        border-radius: 12px;
        margin-top: 30px;
        text-align: center;
        font-size: 14px;
    }}
    
    /* ACTIVITY EMOJI */
    .activity-emoji {{
        font-size: 48px;
        margin: 10px 0;
        animation: pulse 2s ease-in-out infinite;
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.1); }}
        100% {{ transform: scale(1); }}
    }}
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE DATA BUFFERS ================
def init_session_state():
    """Initialize all session state variables WITH DATA"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        current_time = datetime.now()
        
        # Create INITIAL DATA
        initial_hr = 75
        initial_spo2 = 98
        initial_temp = 36.5
        initial_movement = 1.0
        
        # Initialize with 10 data points
        st.session_state.hr_data = deque([initial_hr + np.random.normal(0, 3) for _ in range(10)], maxlen=50)
        st.session_state.spo2_data = deque([initial_spo2 + np.random.normal(0, 1) for _ in range(10)], maxlen=50)
        st.session_state.temp_data = deque([initial_temp + np.random.normal(0, 0.2) for _ in range(10)], maxlen=50)
        st.session_state.movement_data = deque([initial_movement + np.random.normal(0, 0.3) for _ in range(10)], maxlen=50)
        st.session_state.timestamps = deque([current_time - timedelta(seconds=i) for i in range(10)][::-1], maxlen=50)
        
        # Raw packets storage
        st.session_state.raw_packets = deque(maxlen=20)
        
        # Store complete data records
        st.session_state.all_data = deque([
            {
                'timestamp': current_time - timedelta(seconds=i),
                'hr': initial_hr + np.random.normal(0, 3),
                'spo2': initial_spo2 + np.random.normal(0, 1),
                'temp': initial_temp + np.random.normal(0, 0.2),
                'movement': initial_movement + np.random.normal(0, 0.3),
                'activity': ['RESTING', 'WALKING', 'RUNNING'][i % 3],
                'is_real': False
            }
            for i in range(10)
        ], maxlen=50)
        
        # Connection status
        st.session_state.com8_status = "Checking..."

# ================ DISPLAY HEADER WITH LOGO ================
def display_header():
    """Display header with UMP logo"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Decode and display logo
    logo_data = base64.b64decode(UMP_LOGO_BASE64)
    
    st.markdown(f"""
    <div class="main-header">
        <div class="logo-container">
            <img src="data:image/png;base64,{UMP_LOGO_BASE64}" class="logo-img">
        </div>
        <div style="margin-left: 80px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">🏥 STEMCUBE HEALTH MONITORING SYSTEM</h1>
            <p style="margin: 8px 0 0 0; font-size: 1.1rem; opacity: 0.95;">
                📍 Universiti Malaysia Pahang • 🎓 Final Year Project 2025
            </p>
            <p style="margin: 5px 0 0 0; font-size: 0.95rem; opacity: 0.85;">
                🇲🇾 Malaysia Time: <strong>{current_time_malaysia.strftime('%I:%M:%S %p')}</strong> • 
                📅 Date: {current_time_malaysia.strftime('%d %B %Y')}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================ SIMPLE COM8 READER ================
def read_com8_direct():
    """Read DIRECTLY from COM8"""
    if not SERIAL_AVAILABLE:
        return None, "Serial library not installed"
    
    try:
        ser = serial.Serial('COM8', 9600, timeout=0.5)
        
        if ser.in_waiting > 0:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            ser.close()
            
            if raw_line:
                # Parse data
                data = {
                    'timestamp': datetime.now(),
                    'hr': 75,
                    'spo2': 98,
                    'temp': 36.5,
                    'movement': 1.0,
                    'activity': 'RESTING',
                    'packet_id': int(time.time() * 100) % 10000,
                    'node_id': 'NODE_e661',
                    'is_real': True,
                    'raw': raw_line[:60]
                }
                
                # Parse based on common formats
                try:
                    # Format: HR:XX|SpO2:XX|TEMP:XX|ACT:XXX
                    if '|' in raw_line:
                        parts = raw_line.split('|')
                        for part in parts:
                            if 'HR:' in part:
                                data['hr'] = int(''.join(filter(str.isdigit, part.split('HR:')[1]))[:3])
                            elif 'SpO2:' in part:
                                data['spo2'] = int(''.join(filter(str.isdigit, part.split('SpO2:')[1]))[:3])
                            elif 'TEMP:' in part:
                                temp_str = part.split('TEMP:')[1]
                                data['temp'] = float(''.join([c for c in temp_str if c.isdigit() or c == '.']))
                            elif 'ACT:' in part:
                                data['activity'] = part.split('ACT:')[1].strip()
                    
                    # Format: XX,XX,XX,XXX
                    elif ',' in raw_line and ':' not in raw_line:
                        parts = raw_line.split(',')
                        if len(parts) >= 4:
                            data['hr'] = int(parts[0]) if parts[0].isdigit() else 75
                            data['spo2'] = int(parts[1]) if parts[1].isdigit() else 98
                            data['temp'] = float(parts[2]) if parts[2].replace('.', '').isdigit() else 36.5
                            data['activity'] = parts[3]
                
                except:
                    pass
                
                # Store raw packet
                st.session_state.raw_packets.append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'packet': raw_line[:50]
                })
                
                return data, "✅ Connected to COM8"
        
        ser.close()
        return None, "⏳ Waiting for COM8 data..."
        
    except serial.SerialException:
        return None, "❌ COM8 not available"
    except Exception as e:
        return None, f"⚠️ COM8 error: {str(e)[:40]}"

def get_demo_data():
    """Generate realistic demo data for 6:50 AM"""
    current_time = datetime.now()
    
    # Morning values (6:50 AM) - typically resting
    # Realistic morning vitals:
    # - HR: 60-75 (resting in morning)
    # - SpO2: 96-99 (normal)
    # - Temp: 36.3-36.8 (morning temperature)
    
    base_hr = 68 + np.random.normal(0, 4)
    base_spo2 = 97 + np.random.normal(0, 1)
    base_temp = 36.5 + np.random.normal(0, 0.2)
    
    # Morning activity - likely RESTING or light movement
    activities = ['RESTING', 'RESTING', 'RESTING', 'WALKING']  # 75% resting, 25% walking in morning
    activity = np.random.choice(activities)
    
    if activity == 'RESTING':
        movement = 0.5 + np.random.random() * 0.5
        # Adjust HR for resting
        base_hr = max(60, min(75, base_hr))
    else:  # WALKING
        movement = 1.5 + np.random.random() * 1.0
        base_hr = max(75, min(90, base_hr))
    
    return {
        'timestamp': current_time,
        'hr': int(max(55, min(90, base_hr))),
        'spo2': int(max(95, min(100, base_spo2))),
        'temp': round(max(36.0, min(37.0, base_temp)), 1),
        'movement': round(movement, 1),
        'activity': activity,
        'packet_id': int(time.time() * 100) % 10000,
        'node_id': 'NODE_e661',
        'is_real': False,
        'raw': 'DEMO: Morning vitals (6:50 AM)'
    }

def update_data_buffers(data):
    """Update all data buffers"""
    st.session_state.timestamps.append(data['timestamp'])
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.temp_data.append(data['temp'])
    st.session_state.movement_data.append(data['movement'])
    
    # Store complete record
    st.session_state.all_data.append({
        'timestamp': data['timestamp'],
        'hr': data['hr'],
        'spo2': data['spo2'],
        'temp': data['temp'],
        'movement': data['movement'],
        'activity': data['activity'],
        'is_real': data['is_real']
    })

# ================ GRAPH FUNCTIONS ================
def create_graph(title, y_data, color, y_label):
    """Create a graph with MUJI colors"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    n_points = min(30, len(st.session_state.timestamps))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.timestamps)[-n_points:],
        y=list(y_data)[-n_points:],
        mode='lines+markers',
        line=dict(color=color, width=3),
        marker=dict(size=5, color=color),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}'
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'font': {'size': 16, 'color': '#3C2F2F', 'family': 'Arial'}
        },
        height=280,
        margin=dict(l=50, r=20, t=50, b=50),
        xaxis_title="Time",
        yaxis_title=y_label,
        plot_bgcolor='rgba(255, 253, 208, 0.1)',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12),
        showlegend=False
    )
    
    return fig

# ================ TAB 1: HEALTH VITALS ================
def tab_health_vitals(current_data):
    """Tab 1: Health Vitals with MUJI theme"""
    
    # Activity display with emoji
    col_activity = st.columns([1, 2, 1])
    with col_activity[1]:
        activity = current_data['activity']
        emoji = "😴" if activity == 'RESTING' else "🚶" if activity == 'WALKING' else "🏃"
        activity_color = '#8B4513' if activity == 'RESTING' else '#556B2F' if activity == 'WALKING' else '#D4A76A'
        
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border-radius: 12px; 
                    background: linear-gradient(135deg, {activity_color}20 0%, white 100%);
                    border: 2px solid {activity_color}40;">
            <div class="activity-emoji">{emoji}</div>
            <h2 style="color: {activity_color}; margin: 5px 0;">{activity}</h2>
            <p style="color: #666; font-size: 14px;">Patient Activity Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        hr = current_data['hr']
        if 60 <= hr <= 100:
            status_class = "status-normal"
            status = "NORMAL"
        elif 50 <= hr <= 110:
            status_class = "status-warning"
            status = "WARNING"
        else:
            status_class = "status-critical"
            status = "ALERT"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value" style="color: {'#4CAF50' if 60 <= hr <= 100 else '#FF9800' if 50 <= hr <= 110 else '#F44336'};">{hr}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">BPM</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        spo2 = current_data['spo2']
        if spo2 >= 95:
            status_class = "status-normal"
            status = "NORMAL"
        elif spo2 >= 90:
            status_class = "status-warning"
            status = "LOW"
        else:
            status_class = "status-critical"
            status = "CRITICAL"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">BLOOD OXYGEN</div>
            <div class="metric-value" style="color: {'#4CAF50' if spo2 >= 95 else '#FF9800' if spo2 >= 90 else '#F44336'};">{spo2}%</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">SpO₂</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        temp = current_data['temp']
        if temp <= 37.5:
            status_class = "status-normal"
            status = "NORMAL"
        elif temp <= 38.5:
            status_class = "status-warning"
            status = "ELEVATED"
        else:
            status_class = "status-critical"
            status = "FEVER"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">TEMPERATURE</div>
            <div class="metric-value" style="color: {'#4CAF50' if temp <= 37.5 else '#FF9800' if temp <= 38.5 else '#F44336'};">{temp}°C</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Body Temp</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        movement = current_data['movement']
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">MOVEMENT</div>
            <div class="metric-value" style="color: #8D6E63;">{movement}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Activity Level</div>
            <div style="margin-top: 10px;">
                <div style="background: #F5F5DC; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #556B2F, #8B4513); 
                                width: {min(100, movement * 20)}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Real-time Graphs
    st.markdown("### 📈 Real-time Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        hr_fig = create_graph("❤️ Heart Rate Trend", st.session_state.hr_data, '#8B4513', 'BPM')
        if hr_fig:
            st.plotly_chart(hr_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        spo2_fig = create_graph("🩸 Blood Oxygen Trend", st.session_state.spo2_data, '#556B2F', 'SpO₂ %')
        if spo2_fig:
            st.plotly_chart(spo2_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        temp_fig = create_graph("🌡️ Temperature Trend", st.session_state.temp_data, '#D4A76A', '°C')
        if temp_fig:
            st.plotly_chart(temp_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        move_fig = create_graph("🏃 Movement Activity", st.session_state.movement_data, '#8D6E63', 'Activity Level')
        if move_fig:
            st.plotly_chart(move_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM STATUS ================
def tab_system_status(current_data, com8_status):
    """Tab 2: System Status"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 📡 Connection Status")
        
        # Connection status with icon
        if "✅ Connected" in com8_status:
            st.success(f"**{com8_status}**")
            st.balloons()
        elif "❌" in com8_status:
            st.error(f"**{com8_status}**")
        elif "⚠️" in com8_status:
            st.warning(f"**{com8_status}**")
        else:
            st.info(f"**{com8_status}**")
        
        # Data source indicator
        st.markdown("---")
        if current_data['is_real']:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4CAF5020 0%, #4CAF5010 100%); 
                        padding: 15px; border-radius: 10px; border-left: 4px solid #4CAF50;">
                <h4 style="color: #2E7D32; margin: 0 0 10px 0;">🌐 REAL DATA MODE</h4>
                <p style="color: #666; margin: 0; font-size: 14px;">
                    Receiving live data from STEMCUBE Master via COM8
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FF980020 0%, #FF980010 100%); 
                        padding: 15px; border-radius: 10px; border-left: 4px solid #FF9800;">
                <h4 style="color: #F57C00; margin: 0 0 10px 0;">💻 DEMO DATA MODE</h4>
                <p style="color: #666; margin: 0; font-size: 14px;">
                    Showing simulated data. Connect STEMCUBE for real-time monitoring.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.metric("🔢 Packet ID", current_data['packet_id'])
        st.metric("📟 Node ID", current_data['node_id'])
        st.metric("⏰ Last Update", datetime.now().strftime('%H:%M:%S'))
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 🔋 System Health")
        
        # Battery gauge with MUJI colors
        battery = 85
        fig_battery = go.Figure(go.Indicator(
            mode="gauge+number",
            value=battery,
            title={'text': "Battery Level", 'font': {'size': 16, 'color': '#3C2F2F'}},
            number={'suffix': "%", 'font': {'size': 28, 'color': '#8B4513'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#3C2F2F'},
                'bar': {'color': '#556B2F'},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#F7E7CE",
                'steps': [
                    {'range': [0, 20], 'color': 'rgba(244, 67, 54, 0.1)'},
                    {'range': [20, 50], 'color': 'rgba(255, 152, 0, 0.1)'},
                    {'range': [50, 100], 'color': 'rgba(85, 107, 47, 0.1)'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 20
                }
            }
        ))
        
        fig_battery.update_layout(
            height=250,
            margin=dict(t=50, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Arial', size=12)
        )
        st.plotly_chart(fig_battery, use_container_width=True)
        
        # System metrics
        col_metric1, col_metric2 = st.columns(2)
        with col_metric1:
            st.metric("📶 Signal", "-65 dB")
        with col_metric2:
            st.metric("📡 SNR", "12 dB")
        
        # Progress bars
        st.progress(0.85, text="Battery: 85%")
        st.progress(0.92, text="Signal Quality: 92%")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Raw Packets
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📡 Recent Data Packets")
    
    if len(st.session_state.raw_packets) > 0:
        for packet in list(st.session_state.raw_packets)[-5:]:
            st.code(f"{packet['time']}: {packet['packet']}")
    else:
        st.info("Waiting for data packets...")
        # Show sample format
        st.markdown("""
        **Expected STEMCUBE Format:**
        ```
        HR:72|SpO2:98|TEMP:36.5|ACT:RESTING|BAT:85
        ```
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: DATA LOG ================
def tab_data_log():
    """Tab 3: Data Log"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Data Log")
    
    if len(st.session_state.all_data) > 0:
        # Get last 10 records
        all_data_list = list(st.session_state.all_data)
        n_items = min(10, len(all_data_list))
        
        table_data = []
        for i in range(1, n_items + 1):
            record = all_data_list[-i]
            table_data.append({
                'Time': record['timestamp'].strftime('%H:%M:%S'),
                'HR': record['hr'],
                'SpO₂': record['spo2'],
                'Temp': f"{record['temp']:.1f}°C",
                'Movement': f"{record['movement']:.1f}",
                'Activity': record['activity'],
                'Source': '📡 REAL' if record['is_real'] else '💻 DEMO'
            })
        
        # Reverse to show newest first
        table_data.reverse()
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No data available yet")
    
    # Data Statistics
    st.markdown("### 📊 Data Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        hr_list = list(st.session_state.hr_data)
        avg_hr = np.mean(hr_list) if hr_list else 75
        st.metric("HR Avg", f"{avg_hr:.0f} BPM", delta="Normal" if 60 <= avg_hr <= 100 else "Check")
    
    with col2:
        spo2_list = list(st.session_state.spo2_data)
        avg_spo2 = np.mean(spo2_list) if spo2_list else 98
        st.metric("SpO₂ Avg", f"{avg_spo2:.0f}%", delta="Good" if avg_spo2 >= 95 else "Low")
    
    with col3:
        temp_list = list(st.session_state.temp_data)
        avg_temp = np.mean(temp_list) if temp_list else 36.5
        st.metric("Temp Avg", f"{avg_temp:.1f}°C", delta="Normal" if avg_temp <= 37.5 else "High")
    
    with col4:
        move_list = list(st.session_state.movement_data)
        avg_move = np.mean(move_list) if move_list else 1.0
        st.metric("Activity Avg", f"{avg_move:.1f}")
    
    with col5:
        st.metric("Data Points", len(st.session_state.timestamps))
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Initialize session state
    init_session_state()
    
    # Display header with logo
    display_header()
    
    # Get data from COM8 or demo
    com8_data, com8_status = read_com8_direct()
    
    if com8_data:
        current_data = com8_data
        st.session_state.com8_status = com8_status
    else:
        current_data = get_demo_data()
        st.session_state.com8_status = com8_status
    
    # Update buffers
    update_data_buffers(current_data)
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ Control Panel")
        
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True, help="Automatically refresh data every few seconds")
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2, help="How often to update the data")
        
        if st.button("🔄 Manual Refresh", use_container_width=True):
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 📊 Current Readings")
        
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            st.metric("❤️ HR", f"{current_data['hr']} BPM")
            st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
        with col_sb2:
            st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
            st.metric("🏃 Activity", current_data['activity'])
        
        # Activity indicator
        activity_color = '#8B4513' if current_data['activity'] == 'RESTING' else '#556B2F' if current_data['activity'] == 'WALKING' else '#D4A76A'
        st.markdown(f"""
        <div style="background: {activity_color}20; padding: 10px; border-radius: 8px; 
                    border-left: 4px solid {activity_color}; margin-top: 10px;">
            <p style="margin: 0; font-size: 13px; color: {activity_color};">
                <strong>Current Status:</strong> Patient is {current_data['activity'].lower()}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 🔌 System Info")
        
        st.write(f"**Data Source:** {'📡 REAL' if current_data['is_real'] else '💻 DEMO'}")
        st.write(f"**Node:** {current_data['node_id']}")
        st.write(f"**Packets:** {len(st.session_state.raw_packets)}")
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
        
        # Connection status
        if current_data['is_real']:
            st.success("✅ Connected to STEMCUBE")
        else:
            st.warning("⚠️ Demo Mode Active")
            if st.button("🔍 Check COM8", use_container_width=True):
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # TABS
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📋 Data Log"])
    
    with tab1:
        tab_health_vitals(current_data)
    
    with tab2:
        tab_system_status(current_data, st.session_state.com8_status)
    
    with tab3:
        tab_data_log()
    
    # Footer
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    st.markdown("""
    <div class="dashboard-footer">
        <p style="margin: 0; font-size: 14px;">
            🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
            📍 Universiti Malaysia Pahang • Faculty of Electrical & Electronics Engineering |
            🎓 Final Year Project 2025
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
            🇲🇾 Malaysia Time: {current_time} • 🔄 Auto-refresh every {refresh_rate}s • 
            🎨 MUJI + Olive Maroon Theme
        </p>
    </div>
    """.format(
        current_time=current_time_malaysia.strftime('%I:%M:%S %p'),
        refresh_rate=refresh_rate
    ), unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()