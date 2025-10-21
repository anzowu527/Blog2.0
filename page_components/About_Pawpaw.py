# page_components/About_Pawpaw.py
import streamlit as st

def main():
    st.markdown(
        """
        <style>
        .about-wrap { 
          background: #ffeada; 
          padding: 18px; 
        }
        .about-card {
          background: #ffffffcc;
          border: 2px solid #f4cbba;
          border-radius: 16px;
          padding: 24px;
          box-shadow: 0 6px 10px rgba(200,161,143,.35);
        }
        h1, h2, h3 { font-family: 'American Typewriter', serif; color:#5a3b2e; }
        p, li      { color:#523a2e; font-size: 16px; line-height:1.6; }
        .pill {
          display:inline-block; margin:6px 8px 0 0; padding:6px 10px;
          background:#c8a18f; color:#fff; border-radius:999px; font-size:13px;
        }
        .cta {
          margin-top: 14px;
          padding: 12px 16px;
          background: #c8a18f;
          color: #fff; 
          border-radius: 10px;
          display:inline-block;
          font-weight: 700;
          text-decoration:none;
        }
        .cta:hover { background:#a27763; }
        .muted { color:#a27763; font-size: 13px; }
        </style>
        """, unsafe_allow_html=True
    )

    st.markdown('<div class="about-wrap"><div class="about-card">', unsafe_allow_html=True)

    st.markdown("## 📖 About Pawpaw Homestay")
    st.write(
        "Pawpaw Homestay 是一个 **家庭式寄养** 与 **陪伴看护** 的小天地。"
        "我们注重安全、干净、规律与耐心互动：让每一只到访的毛孩子，都像在自己家里一样放松与开心。"
    )

    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("### 我们的特色")
        st.markdown(
            """
            - 🐾 **个性化照护**：按作息与饮食习惯定制看护方案  
            - 🏡 **家庭环境**：每日固定散步与后院放风  
            - 🧼 **干净与消毒**：入住前后与每日清洁  
            - 📸 **照片/视频更新**：让家长随时安心了解动态  
            """
        )
        st.markdown("**擅长照护**：<span class='pill'>幼犬/幼猫</span><span class='pill'>分离焦虑</span><span class='pill'>慢热性格</span><span class='pill'>老年宠物</span>", unsafe_allow_html=True)

    with c2:
        st.markdown("### 服务与区域")
        st.write("• 日托 / 过夜寄养  \n• 简单基础训练  \n• 覆盖大洛杉矶周边")
        st.markdown("<span class='muted'>*更详细的价目与统计可在左侧各页面查看。</span>", unsafe_allow_html=True)

    st.markdown("### 联系方式")
    st.write("欢迎通过左侧导航进入 **Dogtopia / Catopia / Members** 了解更多真实记录。")
    st.markdown(
        "<a class='cta' href='?page=members' target='_self'>🧑‍🤝‍🧑 查看成员与故事</a>  "
        "<a class='cta' href='?page=kingdom_stats' target='_self'>📈 查看数据与口碑</a>",
        unsafe_allow_html=True
    )

    st.markdown("</div></div>", unsafe_allow_html=True)
