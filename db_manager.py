import streamlit as st
from supabase import create_client
import uuid
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        try:
            self.supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
            self.active = True
        except:
            self.active = False

    def get_session_id(self):
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())[:8]
        return st.session_state.session_id

    def save_match(self, my_prod, comp_prod, res):
        """حفظ نتائج المطابقة فوراً"""
        if not self.active: return
        data = {
            "session_id": self.get_session_id(),
            "product_name": my_prod,
            "comp_name": comp_prod,
            "decision": res.get("القرار"),
            "created_at": datetime.now().isoformat()
        }
        self.supabase.table("analysis_results").insert(data).execute()

    # وظائف ERP (المشتريات والموردين)
    def add_purchase(self, data):
        return self.supabase.table("daily_purchases").insert(data).execute()

    def get_suppliers(self):
        return self.supabase.table("suppliers").select("*").execute()
