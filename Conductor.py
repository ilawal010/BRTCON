
# ==========================================================
# GUSAU BRT – QR SCAN & VERIFY (CAMERA)
# ==========================================================
import streamlit as st
import pandas as pd
from datetime import datetime
from pyzbar import pyzbar
from PIL import Image
import os
import tempfile

DATA_DIR = "brt_data"
TICKETS_FILE = f"{DATA_DIR}/tickets.csv"
SCANS_FILE   = f"{DATA_DIR}/scan_logs.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize scan log CSV if missing
if not os.path.exists(SCANS_FILE):
    pd.DataFrame(columns=["scan_id","ticket_id","scanned_by","scan_time","valid"]).to_csv(SCANS_FILE,index=False)

# Load tickets and logs
tickets = pd.read_csv(TICKETS_FILE) if os.path.exists(TICKETS_FILE) else pd.DataFrame()
logs    = pd.read_csv(SCANS_FILE)

st.title("🚌 Gusau BRT – QR Scan Verification")
st.info("Use your camera to scan the QR code or upload an image file from device.")

scanner_id = st.text_input("Conductor / Inspector ID")

# Option 1: Camera
img_camera = st.camera_input("Scan Ticket QR with Camera")
# Option 2: Upload from device
img_upload = st.file_uploader("Or upload QR image from device", type=['png','jpg','jpeg'])

image = None
if img_camera:
    image = Image.open(img_camera)
elif img_upload:
    image = Image.open(img_upload)

if st.button("Verify Ticket"):
    if not image:
        st.warning("Please capture or upload a QR image first.")
    elif not scanner_id:
        st.warning("Please enter Conductor / Inspector ID.")
    else:
        barcodes = pyzbar.decode(image)
        if not barcodes:
            st.error("No QR code detected. Please try again.")
        else:
            qr_data = barcodes[0].data.decode("utf-8")
            if 'TicketID:' in qr_data:
                ticket_id = qr_data.split('TicketID:')[1].split('\n')[0]

                row = tickets[tickets.ticket_id == ticket_id]
                if row.empty:
                    valid = False
                else:
                    expiry = pd.to_datetime(row.expiry_time.iloc[0])
                    now = datetime.now()
                    ticket_type = row.ticket_type.iloc[0]
                    already_used = logs[(logs.ticket_id==ticket_id) & (logs.valid==True)]
                    valid = now <= expiry
                    if ticket_type.startswith("Single") and not already_used.empty:
                        valid = False

                # Log the scan
                log_row = {
                    "scan_id": ticket_id + str(len(logs)+1),
                    "ticket_id": ticket_id,
                    "scanned_by": scanner_id,
                    "scan_time": datetime.now(),
                    "valid": valid
                }
                logs = pd.concat([logs, pd.DataFrame([log_row])], ignore_index=True)
                logs.to_csv(SCANS_FILE, index=False)

                # Feedback
                if valid:
                    st.markdown("<h2 style='color:green'>✅ VALID TICKET</h2>", unsafe_allow_html=True)
                    st.audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg')
                else:
                    st.markdown("<h2 style='color:red'>❌ EXPIRED OR USED TICKET</h2>", unsafe_allow_html=True)
                    st.audio('https://actions.google.com/sounds/v1/alarms/beep_long.ogg')
            else:
                st.error("QR code format not recognized.")

