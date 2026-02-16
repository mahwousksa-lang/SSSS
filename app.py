import streamlit as st
import pandas as pd
from engine_v15 import run_full_analysis
from db_manager import DatabaseManager

st.set_page_config(page_title="استديو مهووس الذكي", layout="wide", page_icon="💎")

# 1. تهيئة النظام
db = DatabaseManager()
tab1, tab2, tab3 = st.tabs(["🎯 رادار المطابقة والتحقق", "💰 الإدارة المالية (ERP)", "🤖 استديو مهووس AI"])

with tab1:
    st.header("المطابقة الذكية مع Gemini")
    c1, c2 = st.columns(2)
    f1 = c1.file_uploader("ارفع منتجاتك", type='csv', key="u1")
    f2 = c2.file_uploader("ارفع ملف المنافس", type='csv', key="u2")
    
    if f1 and f2:
        if st.button("🚀 بدء التحليل العميق"):
            df1, df2 = pd.read_csv(f1), pd.read_csv(f2)
            
            # حل مشكلة TypeError بتمرير الـ progress_callback بشكل صحيح
            def progress_callback(current, total):
                st.write(f"⏳ معالجة المنتج {current} من {total}...")
            
            results = run_full_analysis(df1, df2, progress_callback=progress_callback)
            st.session_state.results = results
            st.dataframe(results)

with tab2:
    st.header("🛒 المشتريات والموردين")
    sub_t1, sub_t2, sub_t3 = st.tabs(["🛒 مشتريات", "🏪 موردين", "💰 مصروفات"])
    with sub_t1:
        st.subheader("تسجيل فاتورة مشتريات")
        # نموذج إضافة مشتريات يرسل لـ db.add_purchase
    with sub_t2:
        st.subheader("إدارة الموردين والتقييم")
        # عرض الموردين من db.get_suppliers

with tab3:
    st.header("💬 محادثة AI وكشف الأخطاء")
    # هنا تضع كود محادثة Gemini المباشرة
