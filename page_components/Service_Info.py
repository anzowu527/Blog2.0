# page_components/Service_Info.py
import streamlit as st

DOG = "dog"
CAT = "cat"

def _init_state():
    if "svc_view" not in st.session_state:
        st.session_state.svc_view = DOG  # default tab

def _switch_to(tab: str):
    st.session_state.svc_view = tab

def _shared_css():
    st.markdown("""
    <style>
      /* round, on-brand, uniform height */
      .svc-pill .stButton>button{
        display:inline-flex; align-items:center; justify-content:center;
        height:44px; padding:0 18px; min-width:160px;
        border:none; border-radius:9999px;
        background:#c8a18f; color:#fff; font-weight:700; font-size:15px; line-height:1;
        box-shadow:0 4px 10px rgba(200,161,143,.35);
        transition:transform .08s ease, background .2s ease, box-shadow .2s ease;
        width:auto;               /* do not span column */
      }
      .svc-pill .stButton{ margin:0 !important; }  /* kill extra vertical spacing */
      .svc-pill .stButton>button:hover{
        background:#b58c7c; transform:translateY(-1px);
        box-shadow:0 6px 14px rgba(200,161,143,.42);
      }
      /* active/inactive */
      .svc-active .stButton>button{ background:#5a3b2e !important; color:#fff; }
      .svc-inactive .stButton>button{ background:#c8a18f; color:#fff; }
    </style>
    """, unsafe_allow_html=True)

def _header_with_toggle():
    st.markdown("## 🛎️ Service & Info")

    # Row: [ left spacer | DOG | center gap | CAT | right spacer ]
    left_sp, col_dog, center_gap, col_cat, right_sp = st.columns([1, 0.7, 0.01, 0.7, 1], gap="small")

    with col_dog:
        cls = "svc-active" if st.session_state.svc_view == "dog" else "svc-inactive"
        st.markdown(f'<div class="svc-pill {cls}">', unsafe_allow_html=True)
        if st.button("🐶 Dog Services", key="btn_dog"):   # no use_container_width -> stays compact
            _switch_to("dog")
        st.markdown("</div>", unsafe_allow_html=True)

    # center_gap is just empty column to keep the midpoint between the two buttons
    with center_gap:
        st.write("")  # keeps layout stable

    with col_cat:
        cls = "svc-active" if st.session_state.svc_view == "cat" else "svc-inactive"
        st.markdown(f'<div class="svc-pill {cls}">', unsafe_allow_html=True)
        if st.button("🐱 Cat Services", key="btn_cat"):
            _switch_to("cat")
        st.markdown("</div>", unsafe_allow_html=True)



def _render_dog():
    st.write("欢迎来到 **Pawpaw Homestay**（🐶 Dog Services）— 针对狗狗的服务、流程与小贴士如下。")
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("### 我们提供的服务（狗狗）")
        st.markdown(
            """
            - 🏡 **过夜寄养 Boarding**：家庭环境，规律作息与互动  
            - 🌞 **日托 Daycare**：白天寄托，固定散步与后院放风  
            - 🚶 **遛狗 Walks**：能量释放与嗅闻散步  
            - 🍽️ **投喂/加餐**：按既定食谱与时间  
            - 💊 **喂药**：按医嘱口服（需提前说明）  
            """)
        st.markdown("**擅长照护**：", unsafe_allow_html=True)
        st.markdown(
            "<span class='pill'>幼犬社交与如厕节律</span>"
            "<span class='pill'>分离焦虑舒缓</span>"
            "<span class='pill'>基础礼仪巩固</span>"
            "<span class='pill'>老年犬关怀</span>", unsafe_allow_html=True
        )

        st.markdown("### 预定流程")
        st.markdown(
            """
            1) 在左侧 **Members / Dogtopia** 了解真实记录  
            2) 通过微信或私信沟通需求与时间  
            3) 安排 **见面评估**（性格/与现住狗狗匹配）  
            4) 确认行程与注意事项 → 准备行李 → 开心入住  
            """)
        st.markdown("<span class='note'>*首次入住建议先做半日或1日适应。</span>", unsafe_allow_html=True)

    with c2:
        st.markdown("### 营业时间 & 区域")
        st.write("• 一般 8:00–20:00（可协商弹性）  \n• 大洛杉矶周边")
        st.markdown("### 打包清单（狗狗）")
        st.write("• 粮食/零食（分装更佳）  \n• 日常药物/补充剂  \n• 牵引绳/胸背/身份牌  \n• 小床/毛毯/熟悉气味玩具  \n• 便袋/尿垫（如需）")
        st.markdown("### 入住要求")
        st.write("• 常规疫苗与驱虫  \n• 无传染病、可与人友好  \n• 如有护食/护玩具/分离焦虑，请提前告知。")

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("### 价格区间（参考）")
        st.write("• 日托：$XX–$XX / 天  \n• 过夜寄养：$XX–$XX / 晚  \n• 额外服务：喂药/清洁/额外运动等按需计价")
        st.markdown("<span class='note'>*价格基于体型、年龄、性格、日程与照护强度评估。</span>", unsafe_allow_html=True)
    with c4:
        st.markdown("### 取消/改期（简要）")
        st.write("• 48小时以上：全额退  \n• 24–48小时：收取部分费用  \n• 24小时内：按当天规则计费")
        st.markdown("<span class='note'>*节假日或热门时段可能有不同规则。</span>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    st.markdown("### 常见问题（FAQ）")
    with st.expander("能与其他狗狗同住吗？"):
        st.write("会先做性格评估与逐步引入；不适合群住会安排分区与错峰互动。")
    with st.expander("可以看日常更新吗？"):
        st.write("会发照片/短视频合集，长住会有周报。")
    with st.expander("幼犬能来吗？"):
        st.write("可以，但需要更密集如厕安排与看护；请提前沟通作息与训练节律。")
    with st.expander("特殊饮食/过敏怎么办？"):
        st.write("请提前列明禁忌与食谱；我们会严格按清单执行。")

    st.markdown(
        "<a class='cta' href='?page=members' target='_self'>🧑‍🤝‍🧑 查看成员与故事</a>  "
        "<a class='cta' href='?page=kingdom_stats' target='_self'>📈 查看数据与口碑</a>  "
        "<a class='cta' href='?page=dogtopia' target='_self'>🐶 Dogtopia</a>",
        unsafe_allow_html=True
    )

def _render_cat():
    st.write("欢迎来到 **Pawpaw Homestay**（🐱 Cat Services）— 针对猫猫的服务、流程与小贴士如下。")
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("### 我们提供的服务（猫猫）")
        st.markdown(
            """
            - 🏡 **过夜寄养 Boarding**：安静独立区，减压环境  
            - 🌞 **日托 Daycare**：短时看护与互动玩耍  
            - ✂️ **基础梳理**：温柔梳毛与清洁（按需）  
            - 🍽️ **投喂/加餐**：按既定食谱与时间  
            - 💊 **喂药**：按医嘱口服（需提前说明）  
            """)
        st.markdown("**擅长照护**：", unsafe_allow_html=True)
        st.markdown(
            "<span class='pill'>新环境适应</span>"
            "<span class='pill'>紧张/慢热猫</span>"
            "<span class='pill'>老年猫关怀</span>"
            "<span class='pill'>多猫分区管理</span>", unsafe_allow_html=True
        )

        st.markdown("### 预定流程")
        st.markdown(
            """
            1) 在左侧 **Members / Catopia** 了解真实记录  
            2) 通过微信或私信沟通需求与时间  
            3) 安排 **见面评估**（性格/独立区匹配）  
            4) 确认行程与注意事项 → 准备行李 → 开心入住  
            """)
        st.markdown("<span class='note'>*首次入住建议先做半日或1日适应。</span>", unsafe_allow_html=True)

    with c2:
        st.markdown("### 营业时间 & 区域")
        st.write("• 一般 8:00–20:00（可协商弹性）  \n• 大洛杉矶周边")
        st.markdown("### 打包清单（猫猫）")
        st.write("• 粮食/零食（分装更佳）  \n• 日常药物/补充剂  \n• 便盆/猫砂（如需）  \n• 小床/毛毯/熟悉气味玩具  \n• 舒缓喷雾/费洛蒙（可选）")
        st.markdown("### 入住要求")
        st.write("• 常规疫苗与驱虫  \n• 无传染病、可被温柔操作  \n• 如有应激史/挑食/慢性病，请提前告知。")

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("### 价格区间（参考）")
        st.write("• 日托：$XX–$XX / 天  \n• 过夜寄养：$XX–$XX / 晚  \n• 额外服务：喂药/清洁/梳理等按需计价")
        st.markdown("<span class='note'>*价格基于年龄、性格、健康状况与照护强度评估。</span>", unsafe_allow_html=True)
    with c4:
        st.markdown("### 取消/改期（简要）")
        st.write("• 48小时以上：全额退  \n• 24–48小时：收取部分费用  \n• 24小时内：按当天规则计费")
        st.markdown("<span class='note'>*节假日或热门时段可能有不同规则。</span>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    st.markdown("### 常见问题（FAQ）")
    with st.expander("能与其他猫猫同住吗？"):
        st.write("以分区为主，逐步引入；不适合群住则全程独立区。")
    with st.expander("可以看日常更新吗？"):
        st.write("会发照片/短视频合集，长住会有周报。")
    with st.expander("挑食/敏感体质怎么办？"):
        st.write("严格按食谱与禁忌执行，可准备原味湿粮/冻干等过渡；过敏史请提前说明。")
    with st.expander("是否提供抓板/玩具？"):
        st.write("提供基础玩具和抓板，也欢迎自带熟悉的物品。")



def main():
    _init_state()
    _shared_css()
    _header_with_toggle()

    # Render the selected view
    if st.session_state.svc_view == DOG:
        _render_dog()
    else:
        _render_cat()

if __name__ == "__main__":
    main()
