import pandas as pd
from rapidfuzz import fuzz, process
import streamlit as st
import requests
import json

def run_full_analysis(my_df, comp_dfs, threshold=60):
    """المحرك الرئيسي الذي يبحث عنه ملف app.py"""
    # تحويل قائمة ملفات المنافسين إلى DataFrame واحد كبير
    all_comp = []
    for df in comp_dfs:
        all_comp.append(df)
    comp_df = pd.concat(all_comp, ignore_index=True)
    
    results = []
    # منطق المطابقة السريع باستخدام RapidFuzz
    for idx, row in my_df.iterrows():
        my_name = str(row.get('name', row.get('الاسم', ''))).lower()
        comp_names = comp_df['name'].tolist() if 'name' in comp_df.columns else comp_df.iloc[:,0].tolist()
        
        match = process.extractOne(my_name, comp_names, scorer=fuzz.token_sort_ratio)
        
        if match and match[1] >= threshold:
            res = {
                "المنتج": row.get('name', ''),
                "سعرك": row.get('price', 0),
                "اسم المنافس": match[0],
                "سعر المنافس": comp_df.iloc[match[2]].get('price', 0),
                "التشابه": match[1],
                "القرار": "ارفع" if comp_df.iloc[match[2]].get('price', 0) > row.get('price', 0) else "خفض"
            }
            results.append(res)
    return pd.DataFrame(results)

def train_and_verify_ai(my_name, comp_name, my_price, comp_price):
    """وظيفة التحقق الذكي (التي طلبتها عند كل منتج)"""
    api_key = "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"
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    prompt = f"""أنت خبير تقني في متجر 'مهووس العطور'. 
    قارن بين:
    منتجنا: {my_name} بسعر {my_price}
    المنافس: {comp_name} بسعر {comp_price}
    
    هل هما نفس المنتج تماماً (الماركة، التركيز EDP/EDT، الحجم)؟
    أجب بصيغة JSON فقط:
    {{"is_match": true/false, "confidence": 0-100, "reason": "السبب باختصار"}}"""

    try:
        res = requests.post(url, 
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "google/gemini-2.0-flash-exp:free", "messages": [{"role": "user", "content": prompt}]}
        )
        return res.json()['choices'][0]['message']['content']
    except:
        return None