import pandas as pd
from rapidfuzz import fuzz, process
from collections import defaultdict
import streamlit as st
# استيراد مباشر (بدون modules)
from db_manager import DatabaseManager

def preprocess_competitors(comp_df):
    index = defaultdict(list)
    for _, row in comp_df.iterrows():
        # تحديد اسم العمود بذكاء
        name_col = 'name' if 'name' in row else (row.keys()[0] if len(row) > 0 else 'name')
        val = str(row.get(name_col, '')).lower()
        key = val.split()[0] if val else 'other' # أول كلمة كـ مفتاح
        
        item = row.to_dict()
        item['search_name'] = val
        index[key].append(item)
        index['all'].append(item)
    return index

def run_super_analysis(my_df, comp_df, threshold=60):
    db = DatabaseManager()
    processed_count = db.get_progress()
    
    if processed_count > 0:
        st.success(f"⏩ تم استئناف العمل وتخطي {processed_count} منتج!")

    comp_index = preprocess_competitors(comp_df)
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(my_df)
    
    # تحديد الأعمدة في ملفك
    my_col = 'name' if 'name' in my_df.columns else my_df.columns[0]
    price_col = 'price' if 'price' in my_df.columns else (my_df.columns[1] if len(my_df.columns)>1 else None)

    for idx, row in my_df.iterrows():
        if idx < processed_count: continue

        my_name = str(row.get(my_col, '')).lower()
        key = my_name.split()[0] if my_name else 'other'
        
        # البحث في نفس المجموعة فقط (للسرعة)
        candidates = comp_index.get(key, []) or comp_index.get('all', [])
        
        best_match = None
        best_score = 0
        
        if candidates:
            choices = [c['search_name'] for c in candidates]
            match = process.extractOne(my_name, choices, scorer=fuzz.token_sort_ratio)
            if match and match[1] >= threshold:
                best_score = match[1]
                best_match = candidates[match[2]]

        # تجهيز النتيجة
        comp_price = 0
        if best_match:
            # محاولة استخراج السعر من المنافس
            for k, v in best_match.items():
                if 'price' in str(k).lower() or 'سعر' in str(k):
                    try: comp_price = float(v)
                    except: pass
                    break
        
        my_price = 0
        try: my_price = float(row.get(price_col, 0))
        except: pass

        res = {
            "my_product": row.get(my_col),
            "my_price": my_price,
            "comp_product": best_match.get('search_name') if best_match else None,
            "comp_price": comp_price,
            "confidence": best_score,
            "status": "matched" if best_match else "missing"
        }
        
        if res['status'] == 'matched':
            diff = res['comp_price'] - res['my_price']
            res['diff'] = diff
            if diff > 0: res['decision'] = "رفع السعر 🔴"
            elif diff < 0: res['decision'] = "خفض السعر 🟡"
            else: res['decision'] = "سعر ممتاز 🟢"
        else:
            res['decision'] = "مفقود 🔵"

        db.save_match(res['my_product'], res['comp_product'], res)
        results.append(res)

        if idx % 5 == 0:
            progress_bar.progress((idx + 1) / total)
            status_text.text(f"جاري العمل: {idx+1}/{total}")

    return pd.DataFrame(results)