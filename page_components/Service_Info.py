# page_components/Service_Info.py
import streamlit as st

def main():
    st.markdown(
        """
        <style>
        .svc-wrap { background:#ffeada; padding: 8px 12px; }
        .svc-card {
          background:#ffffffcc; border:2px solid #f4cbba; border-radius:16px;
          padding:22px; box-shadow:0 6px 10px rgba(200,161,143,.32);
        }
        h1,h2,h3 { font-family:'American Typewriter', serif; color:#5a3b2e; }
        p,li { color:#523a2e; font-size:16px; line-height:1.6; }
        .pill { display:inline-block; margin:6px 8px 0 0; padding:6px 10px;
                background:#c8a18f; color:#fff; border-radius:999px; font-size:13px; }
        .note { color:#a27763; font-size:13px; }
        .cta { display:inline-block; margin-top:12px; padding:10px 14px;
               background:#c8a18f; color:#fff; border-radius:10px; font-weight:700; text-decoration:none; }
        .cta:hover { background:#a27763; }
        .divider { height:2px; background:#f4cbba; border:0; margin:14px 0 8px; }
        </style>
        """, unsafe_allow_html=True
    )


    st.markdown("## 🛎️ Service & Info")
    st.write("欢迎来到 **Pawpaw Homestay**！下面是常用服务、流程与小贴士，帮助你快速了解并预定。")

    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("### 我们提供的服务")
        st.markdown(
            """
            - 🏡 **过夜寄养 Boarding**：家庭环境，规律作息与互动  
            - 🌞 **日托 Daycare**：白天寄托，固定散步与后院放风  
            - 🚶 **遛狗 Walks**：短途舒展或能量释放  
            - 🍽️ **投喂/加餐**：按既定食谱与时间  
            - 💊 **喂药**：按医嘱口服（需提前说明）  
            """)
        st.markdown("**擅长照护**：", unsafe_allow_html=True)
        st.markdown(
            "<span class='pill'>幼犬/幼猫</span>"
            "<span class='pill'>慢热/分离焦虑</span>"
            "<span class='pill'>基础礼仪巩固</span>"
            "<span class='pill'>老年宠物</span>", unsafe_allow_html=True
        )

        st.markdown("### 预定流程")
        st.markdown(
            """
            1) 在左侧 **Members / Dogtopia / Catopia** 了解真实记录  
            2) 通过微信或私信沟通需求与时间  
            3) 安排 **见面评估**（性格/合住匹配）  
            4) 确认行程与注意事项 → 准备行李 → 开心入住  
            """)
        st.markdown("<span class='note'>*首次入住建议先做半日或1日适应。</span>", unsafe_allow_html=True)

    with c2:
        st.markdown("### 营业时间 & 区域")
        st.write("• 一般 8:00–20:00（可协商弹性）  \n• 大洛杉矶周边")
        st.markdown("### 打包清单")
        st.write("• 粮食/零食（分装更佳）  \n• 日常药物/补充剂  \n• 牵引绳/胸背  \n• 小床/毛毯/熟悉气味玩具  \n• 便盆/猫砂（如需）")

        st.markdown("### 入住要求")
        st.write("• 常规疫苗（按时）与驱虫  \n• 无传染病、可与人友好  \n• 幼宠/特殊情况请提前说明")
        st.markdown("<span class='note'>*如有分离焦虑/护食/护玩具等行为，也请如实告知便于照护。</span>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("### 价格区间（参考）")
        st.write(
            "• 日托：$XX–$XX / 天  \n"
            "• 过夜寄养：$XX–$XX / 晚  \n"
            "• 额外服务：喂药/清洁/额外运动等按需计价"
        )
        st.markdown("<span class='note'>*价格会基于体型、年龄、性格、日程与照护强度做个性化评估。</span>", unsafe_allow_html=True)

    with c4:
        st.markdown("### 取消/改期（简要）")
        st.write(
            "• 48小时以上：全额退  \n"
            "• 24–48小时：收取部分费用  \n"
            "• 24小时内：按当天规则计费"
        )
        st.markdown("<span class='note'>*节假日或热门时段可能有不同规则。</span>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)

    st.markdown("### 常见问题（FAQ）")
    with st.expander("能与其他宠物同住吗？"):
        st.write("会先做性格评估与逐步引入。若不适合群住，将安排分区与错峰互动。")
    with st.expander("可以看实时照片/视频吗？"):
        st.write("日常会发照片/短视频合集，长住也会有周报式更新。")
    with st.expander("幼犬能来吗？"):
        st.write("可以，但需要更密集如厕安排与看护；请提前沟通作息。")
    with st.expander("特殊饮食/过敏怎么办？"):
        st.write("请提前列明禁忌与食谱；我们会严格按清单执行。")

    st.markdown(
        "<a class='cta' href='?page=members' target='_self'>🧑‍🤝‍🧑 查看成员与故事</a>  "
        "<a class='cta' href='?page=kingdom_stats' target='_self'>📈 查看数据与口碑</a>  "
        "<a class='cta' href='?page=dogtopia' target='_self'>🐶 Dogtopia</a>  "
        "<a class='cta' href='?page=catopia' target='_self'>🐱 Catopia</a>",
        unsafe_allow_html=True
    )

    st.markdown("</div></div>", unsafe_allow_html=True)
