import pandas as pd
from rapidfuzz import fuzz, process
import streamlit as st
import requests
import json
import time
from db_manager import DatabaseManager # استيراد مدير القاعدة

def run_full_analysis(my_df, comp_df, threshold=60, progress_callback=None):
    """المحرك المطور: يجمع بين السرعة والذكاء والحفظ اللحظي"""
    db = DatabaseManager()
    session_id = db.get_session_id()
    
    # 1. تجهيز البيانات
    results = []
    total = len(my_df)
    
    # تحديد الأعمدة بذكاء
    my_name_col = next((c for c in my_df.columns if 'name' in str(c).lower() or 'اسم' in str(c)), my_df.columns[0])
    comp_names = comp_df.iloc[:, 0].tolist() # نفترض العمود الأول هو الاسم لدى المنافس

    # 2. حلقة المعالجة مع الحفظ اللحظي
    for idx, row in my_df.iterrows():
        my_name = str(row.get(my_name_col, '')).lower()
        
        # أ) مطابقة سريعة (RapidFuzz)
        match = process.extractOne(my_name, comp_names, scorer=fuzz.token_sort_ratio)
        
        best_match_data = None
        if match and match[1] >= threshold:
            best_match_data = comp_df.iloc[match[2]].to_dict()
            comp_price = best_match_data.get('price', best_match_data.get('السعر', 0))
            my_price = row.get('price', row.get('السعر', 0))
            
            # ب) التحقق بالذكاء الاصطناعي (عند الطلب أو للمطابقات المشكوك فيها)
            # إذا كان التطابق بين 60% و 85%، نستعين بالذكاء الاصطناعي فوراً
            ai_verdict = {"is_match": True, "reason": "تطابق نصي قوي"}
            if 60 <= match[1] <= 85:
                ai_res = train_and_verify_ai(my_name, match[0], my_price, comp_price)
                if ai_res:
                    ai_verdict = json.loads(ai_res)

            if ai_verdict.get("is_match"):
                res = {
                    "المنتج": row.get(my_name_col),
                    "سعرك": my_price,
                    "اسم المنافس": match[0],
                    "سعر المنافس": comp_price,
                    "الثقة": match[1],
                    "القرار": "رفع 🔴" if float(comp_price) > float(my_price) else "خفض 🟡",
                    "تفسير_AI": ai_verdict.get("reason", "")
                }
                results.append(res)
                # حفظ لحظي في Supabase لمنع ضياع التقدم
                db.save_match(res['المنتج'], res['اسم المنافس'], res)

        # تحديث الواجهة (حل مشكلة TypeError)
        if progress_callback:
            progress_callback(idx + 1, total)

    return pd.DataFrame(results)

def train_and_verify_ai(my_name, comp_name, my_price, comp_price):
    """خبير العطور المدرب عبر OpenRouter"""
    api_key = st.secrets.get("OPENROUTER_API_KEY", "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")
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    prompt = f"قارن كخبير عطور: منتجنا ({my_name}) بسعر {my_price} والمنافس ({comp_name}) بسعر {comp_price}. هل هما نفس العطر والحجم والتركيز؟ رد بـ JSON: {{'is_match': bool, 'reason': str}}"
    
    try:
        res = requests.post(url, headers={"Authorization": f"Bearer {api_key}"}, json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [{"role": "user", "content": prompt}]
        }, timeout=5)
        return res.json()['choices'][0]['message']['content']
    except:
        return None
