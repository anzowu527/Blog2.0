# page_components/Service_Info.py
from __future__ import annotations
import streamlit as st

# ---------------- Constants ----------------
DOG = "dog"
CAT = "cat"
ZH  = "zh"
EN  = "en"

# ---------------- State ----------------
def _init_state():
    if "svc_view" not in st.session_state:
        st.session_state.svc_view = DOG
    if "lang" not in st.session_state:
        st.session_state.lang = ZH  # 默认中文
        st.session_state.lang = ZH       # default language: Chinese

def _switch_to(tab: str):
    st.session_state.svc_view = tab

def _toggle_lang():
    st.session_state.lang = EN if st.session_state.lang == ZH else ZH

# ---------------- i18n ----------------
def T(key: str) -> str:
    lang = st.session_state.lang
    return _STRINGS[key][lang]

_STRINGS = {
    "title":            {ZH:"🛎️ 服务与信息",              EN:"🛎️ Service & Info"},
    "dog_btn":          {ZH:"🐶 狗狗服务",                EN:"🐶 Dog Services"},
    "cat_btn":          {ZH:"🐱 猫猫服务",                EN:"🐱 Cat Services"},

    # shared
    "hours_area_h3":    {ZH:"营业时间 & 区域",            EN:"Hours & Area"},
    "hours_area_body":  {ZH:"• 一般 8:00–20:00（可协商弹性）  \n• 大洛杉矶周边",
                         EN:"• Typically 8:00–20:00 (flexible by arrangement)  \n• Greater Los Angeles area"},
    "pricing_h3":       {ZH:"价格区间（参考）",           EN:"Pricing (Reference)"},
    "pricing_note":     {ZH:"*价格会基于体型/年龄/性格/健康/日程与照护强度评估。*",
                         EN:"*Pricing depends on size/age/temperament/health/schedule and care intensity.*"},
    "cancel_h3":        {ZH:"取消/改期（简要）",           EN:"Cancellation / Reschedule (Brief)"},
    "cancel_body":      {ZH:"• 48小时以上：全额退  \n• 24–48小时：收取部分费用  \n• 24小时内：按当天规则计费\n*节假日或热门时段可能有不同规则。*",
                         EN:"• >48 hrs: full refund  \n• 24–48 hrs: partial fee  \n• <24 hrs: same-day policy applies\n*Holidays/peak periods may differ.*"},
    "faq_h3":           {ZH:"常见问题（FAQ）",             EN:"Frequently Asked Questions (FAQ)"},

    # dog page
    "dog_intro":        {ZH:'欢迎来到 **Pawpaw Homestay**（🐶 狗狗服务）— 以下为服务、流程与小贴士。',
                         EN:'Welcome to **Pawpaw Homestay** (🐶 Dog Services) — details on services, process, and tips below.'},
    "dog_services_h3":  {ZH:"我们提供的服务（狗狗）",      EN:"Services We Provide (Dogs)"},
    "dog_services_ul":  {ZH:"- 🏡 **过夜寄养 Boarding**：家庭环境，规律作息与互动  \n- 🌞 **日托 Daycare**：白天寄托，固定散步与后院放风  \n- 🚶 **遛狗 Walks**：能量释放与嗅闻散步  \n- 🍽️ **投喂/加餐**：按既定食谱与时间  \n- 💊 **喂药**：按医嘱口服（需提前说明）",
                         EN:"- 🏡 **Boarding**: home setting with routine & interaction  \n- 🌞 **Daycare**: daytime care with walks & backyard time  \n- 🚶 **Walks**: sniffy walks for exercise  \n- 🍽️ **Feeding**: per your schedule/recipe  \n- 💊 **Medication**: oral per instruction (please inform in advance)"},
    "dog_skills_label": {ZH:"**擅长照护**：",              EN:"**Areas of Expertise**:"},
    "dog_skills_pills": {ZH:"<span class='pill'>幼犬社交与如厕节律</span><span class='pill'>分离焦虑舒缓</span><span class='pill'>基础礼仪巩固</span><span class='pill'>老年犬关怀</span>",
                         EN:"<span class='pill'>Puppy socialization & potty rhythm</span><span class='pill'>Separation-anxiety easing</span><span class='pill'>Basic manners reinforcement</span><span class='pill'>Senior care</span>"},
    "dog_flow_h3":      {ZH:"预定流程",                    EN:"Booking Flow"},
    "dog_flow_ol":      {ZH:"1) 在左侧 **Members / Dogtopia** 了解真实记录  \n2) 通过微信或私信沟通需求与时间  \n3) 安排 **见面评估**（性格/与现住狗狗匹配）  \n4) 确认行程与注意事项 → 准备行李 → 开心入住  \n*首次入住建议先做半日或1日适应。*",
                         EN:"1) Check **Members / Dogtopia** for real records  \n2) Message us with needs & dates  \n3) Arrange a **meet & greet** (temperament / compatibility)  \n4) Confirm plan & notes → pack → happy check-in  \n*For first stays, a half/one-day trial is recommended.*"},
    "dog_pack_h3":      {ZH:"打包清单（狗狗）",            EN:"Packing List (Dogs)"},
    "dog_pack_body":    {ZH:"• 粮食/零食（分装更佳）  \n• 日常药物/补充剂  \n• 牵引绳/胸背/身份牌  \n• 小床/毛毯/熟悉气味玩具  \n• 便袋/尿垫（如需）",
                         EN:"• Food/treats (pre-portioned preferred)  \n• Meds/supplements  \n• Leash/harness/ID tag  \n• Bed/blanket/familiar toy  \n• Waste bags/pee pads (if needed)"},
    "dog_require_h3":   {ZH:"入住要求",                    EN:"Requirements"},
    "dog_require_body": {ZH:"• 常规疫苗与驱虫  \n• 无传染病、可与人友好  \n• 如有护食/护玩具/分离焦虑，请提前告知。",
                         EN:"• Core vaccines & flea/tick control  \n• No contagious illness; friendly with people  \n• Tell us about resource guarding/separation anxiety, etc."},
    "dog_price_body":   {ZH:"• 日托：$XX–$XX / 天  \n• 过夜寄养：$XX–$XX / 晚  \n• 额外服务：喂药/清洁/额外运动等按需计价",
                         EN:"• Daycare: $XX–$XX / day  \n• Boarding: $XX–$XX / night  \n• Extras: medication/cleaning/exercise as needed"},
    "dog_faq1_q":       {ZH:"能与其他狗狗同住吗？",         EN:"Can my dog co-stay with others?"},
    "dog_faq1_a":       {ZH:"会先做性格评估与逐步引入；不适合群住会安排分区与错峰互动。",
                         EN:"We do a temperament check and gradual intro; if group stay isn’t suitable, we use separate zones and staggered play."},
    "dog_faq2_q":       {ZH:"可以看日常更新吗？",           EN:"Do you share daily updates?"},
    "dog_faq2_a":       {ZH:"会发照片/短视频合集，长住会有周报。", EN:"Yes—photos/short videos; weekly summaries for longer stays."},
    "dog_faq3_q":       {ZH:"幼犬能来吗？",                 EN:"Do you take puppies?"},
    "dog_faq3_a":       {ZH:"可以，但需要更密集如厕安排与看护；请提前沟通作息与训练节律。",
                         EN:"Yes, with tighter potty schedules and supervision; please share routines/training rhythm."},
    "dog_faq4_q":       {ZH:"特殊饮食/过敏怎么办？",         EN:"Special diet/allergies?"},
    "dog_faq4_a":       {ZH:"请提前列明禁忌与食谱；我们会严格按清单执行。",
                         EN:"Share allergies and diet in advance; we follow your checklist strictly."},

    # cat page
    "cat_intro":        {ZH:'欢迎来到 **Pawpaw Homestay**（🐱 猫猫服务）— 以下为服务、流程与小贴士。',
                         EN:'Welcome to **Pawpaw Homestay** (🐱 Cat Services) — details on services, process, and tips below.'},
    "cat_services_h3":  {ZH:"我们提供的服务（猫猫）",      EN:"Services We Provide (Cats)"},
    "cat_services_ul":  {ZH:"- 🏡 **过夜寄养 Boarding**：安静独立区，减压环境  \n- 🌞 **日托 Daycare**：短时看护与互动玩耍  \n- ✂️ **基础梳理**：温柔梳毛与清洁（按需）  \n- 🍽️ **投喂/加餐**：按既定食谱与时间  \n- 💊 **喂药**：按医嘱口服（需提前说明）",
                         EN:"- 🏡 **Boarding**: quiet private area, low-stress  \n- 🌞 **Daycare**: short-term care & play  \n- ✂️ **Basic grooming**: gentle brushing/cleaning (as needed)  \n- 🍽️ **Feeding**: per schedule/recipe  \n- 💊 **Medication**: oral per instruction (please inform in advance)"},
    "cat_skills_label": {ZH:"**擅长照护**：",              EN:"**Areas of Expertise**:"},
    "cat_skills_pills": {ZH:"<span class='pill'>新环境适应</span><span class='pill'>紧张/慢热猫</span><span class='pill'>老年猫关怀</span><span class='pill'>多猫分区管理</span>",
                         EN:"<span class='pill'>New-environment adaptation</span><span class='pill'>Shy/slow-to-warm cats</span><span class='pill'>Senior care</span><span class='pill'>Multi-cat zoning</span>"},
    "cat_flow_h3":      {ZH:"预定流程",                    EN:"Booking Flow"},
    "cat_flow_ol":      {ZH:"1) 在左侧 **Members / Catopia** 了解真实记录  \n2) 通过微信或私信沟通需求与时间  \n3) 安排 **见面评估**（性格/独立区匹配）  \n4) 确认行程与注意事项 → 准备行李 → 开心入住  \n*首次入住建议先做半日或1日适应。*",
                         EN:"1) Check **Members / Catopia** for real records  \n2) Message us with needs & dates  \n3) Arrange a **meet & greet** (temperament/private-area fit)  \n4) Confirm plan & notes → pack → happy check-in  \n*For first stays, a half/one-day trial is recommended.*"},
    "cat_pack_h3":      {ZH:"打包清单（猫猫）",            EN:"Packing List (Cats)"},
    "cat_pack_body":    {ZH:"• 粮食/零食（分装更佳）  \n• 日常药物/补充剂  \n• 便盆/猫砂（如需）  \n• 小床/毛毯/熟悉气味玩具  \n• 舒缓喷雾/费洛蒙（可选）",
                         EN:"• Food/treats (pre-portioned preferred)  \n• Meds/supplements  \n• Litter box/litter (if needed)  \n• Bed/blanket/familiar toy  \n• Calming spray/pheromones (optional)"},
    "cat_require_h3":   {ZH:"入住要求",                    EN:"Requirements"},
    "cat_require_body": {ZH:"• 常规疫苗与驱虫  \n• 无传染病、可被温柔操作  \n• 如有应激史/挑食/慢性病，请提前告知。",
                         EN:"• Core vaccines & flea/tick control  \n• No contagious illness; comfortable with gentle handling  \n• Share any stress history/picky eating/chronic issues."},
    "cat_price_body":   {ZH:"• 日托：$XX–$XX / 天  \n• 过夜寄养：$XX–$XX / 晚  \n• 额外服务：喂药/清洁/梳理等按需计价",
                         EN:"• Daycare: $XX–$XX / day  \n• Boarding: $XX–$XX / night  \n• Extras: medication/cleaning/grooming as needed"},
    "cat_faq1_q":       {ZH:"能与其他猫猫同住吗？",         EN:"Can my cat co-stay with others?"},
    "cat_faq1_a":       {ZH:"以分区为主，逐步引入；不适合群住则全程独立区。",
                         EN:"We prioritize separate zones with gradual intro; full private area if group stay isn’t suitable."},
    "cat_faq2_q":       {ZH:"可以看日常更新吗？",           EN:"Do you share daily updates?"},
    "cat_faq2_a":       {ZH:"会发照片/短视频合集，长住会有周报。", EN:"Yes—photos/short videos; weekly summaries for longer stays."},
    "cat_faq3_q":       {ZH:"挑食/敏感体质怎么办？",         EN:"Picky eater/sensitive?"},
    "cat_faq3_a":       {ZH:"严格按食谱与禁忌执行，可准备原味湿粮/冻干等过渡；过敏史请提前说明。",
                         EN:"We follow diet restrictions strictly; transitional plain wet/freeze-dried ok; please share allergy history."},
    "cat_faq4_q":       {ZH:"是否提供抓板/玩具？",           EN:"Do you provide scratchers/toys?"},
    "cat_faq4_a":       {ZH:"提供基础玩具和抓板，也欢迎自带熟悉的物品。",
                         EN:"We have basics; feel free to bring your cat’s favorites."},
}

# ---------------- CSS ----------------
def _shared_css():
    st.markdown("""
    <style>
      /* Scope to MAIN view so sidebar keeps default styles */
      [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"] div.stButton > button {
        background-color:#c8a18f !important;  /* brand warm brown */
        color:#fff !important;
        border:none !important;
        border-radius:10px !important;
        padding:8px 18px !important;
        font-weight:bold !important;
        font-size:15px !important;
        box-shadow:0 4px 6px rgba(0,0,0,0.2) !important;
        transition:all .2s ease-in-out;
      }
      [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"] div.stButton > button:hover{
        transform:translateY(-1px);
        box-shadow:0 6px 14px rgba(0,0,0,.25) !important;
      }
      [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"] div.stButton > button:disabled{
        opacity:1 !important;
        cursor:default !important;
      }

      /* subtle divider */
      .divider{ border:none; border-top:1px solid rgba(0,0,0,.06); margin:16px 0; }

      /* pills */
      .pill{
        display:inline-block; margin:4px 8px 0 0; padding:2px 8px; font-size:12px;
        background:rgba(200,161,143,.18); color:#5a3b2e; border-radius:12px;
      }
      .note{ color:#5a3b2e; font-size:12px; opacity:.9; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- Header (top-right lang toggle + dog/cat) ----------------
# ---------------- Header (top-right lang toggle + dog/cat) ----------------
def _header_with_toggle():
    # 标题（左） + 语言按钮（右）
    c_title, c_lang = st.columns([1, 0.18])
    with c_title:
        st.markdown(f"## {T('title')}")

    with c_lang:
        next_label = "English" if st.session_state.lang == ZH else "中文"
        st.button(
            next_label,
            key="btn_lang_toggle",
            on_click=_toggle_lang,   # 用回调，避免状态切换需要二次点击
        )

    st.write("")

    # Row 1: Dog / Cat nav (active one disabled, same color)
    left_sp, col_dog, center_gap, col_cat, right_sp = st.columns([2, 0.9, 0.05, 0.9, 2], gap="small")

    is_dog = st.session_state.svc_view == DOG
    is_cat = not is_dog

    with col_dog:
        st.button(
            T("dog_btn"),
            key="btn_dog",
            disabled=is_dog,
            on_click=_switch_to,
            args=(DOG,),
        )

    with center_gap:
        st.write("")

    with col_cat:
        st.button(
            T("cat_btn"),
            key="btn_cat",
            disabled=is_cat,
            on_click=_switch_to,
            args=(CAT,),
        )


# ---------------- Views ----------------
def _render_dog():
    st.write(T("dog_intro"))
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown(f"### {T('dog_services_h3')}")
        st.markdown(T("dog_services_ul"))
        st.markdown(T("dog_skills_label"), unsafe_allow_html=True)
        st.markdown(T("dog_skills_pills"), unsafe_allow_html=True)

        st.markdown(f"### {T('dog_flow_h3')}")
        st.markdown(T("dog_flow_ol"))

    with c2:
        st.markdown(f"### {T('hours_area_h3')}")
        st.write(T("hours_area_body"))
        st.markdown(f"### {T('dog_pack_h3')}")
        st.write(T("dog_pack_body"))
        st.markdown(f"### {T('dog_require_h3')}")
        st.write(T("dog_require_body"))

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"### {T('pricing_h3')}")
        st.write(T("dog_price_body"))
        st.markdown(f"<span class='note'>{T('pricing_note')}</span>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"### {T('cancel_h3')}")
        st.write(T("cancel_body"))

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    st.markdown(f"### {T('faq_h3')}")
    with st.expander(T("dog_faq1_q")):
        st.write(T("dog_faq1_a"))
    with st.expander(T("dog_faq2_q")):
        st.write(T("dog_faq2_a"))
    with st.expander(T("dog_faq3_q")):
        st.write(T("dog_faq3_a"))
    with st.expander(T("dog_faq4_q")):
        st.write(T("dog_faq4_a"))

def _render_cat():
    st.write(T("cat_intro"))
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown(f"### {T('cat_services_h3')}")
        st.markdown(T("cat_services_ul"))
        st.markdown(T("cat_skills_label"), unsafe_allow_html=True)
        st.markdown(T("cat_skills_pills"), unsafe_allow_html=True)

        st.markdown(f"### {T('cat_flow_h3')}")
        st.markdown(T("cat_flow_ol"))

    with c2:
        st.markdown(f"### {T('hours_area_h3')}")
        st.write(T("hours_area_body"))
        st.markdown(f"### {T('cat_pack_h3')}")
        st.write(T("cat_pack_body"))
        st.markdown(f"### {T('cat_require_h3')}")
        st.write(T("cat_require_body"))

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"### {T('pricing_h3')}")
        st.write(T("cat_price_body"))
        st.markdown(f"<span class='note'>{T('pricing_note')}</span>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"### {T('cancel_h3')}")
        st.write(T("cancel_body"))

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    st.markdown(f"### {T('faq_h3')}")
    with st.expander(T("cat_faq1_q")):
        st.write(T("cat_faq1_a"))
    with st.expander(T("cat_faq2_q")):
        st.write(T("cat_faq2_a"))
    with st.expander(T("cat_faq3_q")):
        st.write(T("cat_faq3_a"))
    with st.expander(T("cat_faq4_q")):
        st.write(T("cat_faq4_a"))

# ---------------- Main ----------------
def main():
    _init_state()
    _shared_css()
    _header_with_toggle()

    if st.session_state.svc_view == DOG:
        _render_dog()
    else:
        _render_cat()

if __name__ == "__main__":
    main()
