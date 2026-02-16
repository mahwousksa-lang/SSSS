import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = None
        self.enabled = False
        try:
            # محاولة الاتصال (تدعم الطريقتين)
            url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
            key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
            if url and key:
                self.supabase = create_client(url, key)
                self.enabled = True
        except:
            pass

    def get_session_id(self):
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())[:8]
        return st.session_state.session_id

    def save_match(self, my_prod, comp_prod, result):
        if not self.enabled: return
        data = {
            "session_id": self.get_session_id(),
            "my_product": my_prod,
            "comp_product": comp_prod,
            "status": result.get('status', 'pending'),
            "confidence": result.get('confidence', 0),
            "price_diff": result.get('diff', 0),
            "created_at": datetime.now().isoformat()
        }
        try:
            self.supabase.table("matches").insert(data).execute()
        except:
            pass

    def get_progress(self):
        if not self.enabled: return 0
        try:
            res = self.supabase.table("matches").select("id", count="exact").eq("session_id", self.get_session_id()).execute()
            return res.count
        except:
            return 0