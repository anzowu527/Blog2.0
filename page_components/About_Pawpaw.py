# About_Pawpaw.py
from __future__ import annotations
import os, re, random                                  # ★ add random

from pathlib import Path
from typing import List, Dict
import streamlit as st
from streamlit.components.v1 import html as components_html

from image_config import BASE_IMAGE_URL
from get_s3_images import get_index, _safe_join_url

BUCKET = "annablog"
ABOUT_ROOT1 = "images/info/about/"
ABOUT_ROOT2 = "images/info/about2/"

# ---------- utils ----------

def _cycle_classes(i: int) -> str:
    palette = ["slower", "faster", "vertical", "slower-down",
               "faster1", "fastest", "slower1", "slower2", "last"]
    return palette[i % len(palette)]

def _alt_from_key(key: str) -> str:
    base = Path(key).name
    return re.sub(r"\.(webp|jpe?g|png|gif|bmp)$", "", base, flags=re.I)\
             .replace("_", " ").replace("-", " ")

# ---------- parallax gallery ----------
def render_parallax_gallery(
    images: List[Dict[str, str]],
    title="",
    subtitle="",
    credit_html='Photos © Pawpaw Homestay',
    height=520,
    bg_color="transparent",
    tile_bg="transparent",
    show_shadow=True,
):
    items_html = []
    for item in images:
        src  = item.get("src", "")
        href = item.get("href", "#")
        klass = "img-wrapper " + item.get("class", "")
        alt  = item.get("alt", "")
        items_html.append(
            f'''<div class="{klass.strip()}">
                  <a href="{href}" target="_blank" rel="noopener">
                    <img src="{src}" alt="{alt}">
                  </a>
                </div>'''
        )
    items_html = "\n".join(items_html)
    box_shadow = "0 10px 50px #5f2f1182" if show_shadow else "none"

    html_code = f"""
<!doctype html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Hepta+Slab:wght@300;500;700&display=swap" rel="stylesheet">
<style>
html, body {{ margin:0; padding:0; height:100%; background:{bg_color}; }}
body {{ font-family:"Hepta Slab", sans-serif; font-weight:500; color:#5D4037; }}
* {{ box-sizing:border-box; }}
::-webkit-scrollbar {{ width:1px; height:1px; }}
.external {{ overflow:hidden; height:100vh; background:transparent; }}
.horizontal-scroll-wrapper {{
  display:flex; flex-direction:column; align-items:center; width:100vh;
  transform: rotate(-90deg) translate3d(0,-100vh,0); transform-origin:right top;
  overflow-y:auto; overflow-x:hidden; padding:0; height:100vw; perspective:1px;
  transform-style:preserve-3d; padding-bottom:10rem; background:transparent;
}}
.img-wrapper {{
  transform:rotate(90deg); display:flex; align-items:center; justify-content:center;
  min-height:40vh; transform-origin:50% 50%;
  transform: rotate(90deg) translateZ(.1px) scale(0.9) translateX(0px) translateY(-3vh);
  transition:1s;
}}
.img-wrapper:hover {{ min-height:65vh; }}
.slower     {{ transform: rotate(90deg) translateZ(-.2px)  scale(1.1) translateY(-10vh); }}
.faster     {{ transform: rotate(90deg) translateZ(.15px)  scale(0.8) translateY(14vh); }}
.fastest    {{ transform: rotate(90deg) translateZ(.22px)  scale(0.7) translateY(-15vh); }}
.vertical   {{ transform: rotate(90deg) translateZ(-.15px) scale(1.15); }}
.scroll-info, header {{ position:absolute; left:1rem; }}
header {{ bottom:1rem; }}
.scroll-info {{ top:1rem; display:flex; align-items:center; font-size:12px; }}
a {{ color:inherit; font-weight:500; }}
.img-wrapper a {{ overflow:hidden; display:block; padding:1vh; background:{tile_bg}; box-shadow:{box_shadow}; }}
img {{ max-width:45vh; max-height:50vh; transition:.5s; vertical-align:top; }}
.icon svg {{ width:20px; fill:currentcolor; }}
</style>
</head><body>
  <div class="external">
    <div class="horizontal-scroll-wrapper">
      {items_html}
    </div>
    <p class="scroll-info">
      <span class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
          <path d="M50,67.1c-0.6,0-1.2-0.2-1.8-0.7c-3.8-3.8-7.7-7.7-11.5-11.5c-2.3-2.3,1.2-5.8,3.5-3.5c2.5,2.5,4.9,4.9,7.4,7.4
          c0-13.7,0-27.4,0-41.2c0-0.6,0.2-1.2,0.5-1.5c0,0,0,0,0,0c0.4-0.6,1.1-1,2-0.9c13.7,0.3,26.4,7.2,33.5,19.1
          C96.5,55.9,84.7,85,60.2,91.6C35.5,98.2,11.6,79.1,11.1,54c-0.1-3.2,4.9-3.2,5,0c0.3,13.8,8.4,26.4,21.3,31.5
          c12.5,5,27.1,1.9,36.6-7.5c9.5-9.5,12.5-24.1,7.5-36.6c-4.8-12.1-16.3-20.1-29-21.2c0,12.8,0,25.5,0,38.3
          c2.5-2.5,4.9-4.9,7.4-7.4c2.3-2.3,5.8,1.3,3.5,3.5c-3.9,3.9-7.8,7.8-11.8,11.8C51.2,66.9,50.6,67.1,50,67.1z"/>
        </svg>
      </span>
      &nbsp;Try scrolling down
    </p>
    <header>
      <p>{subtitle}</p>
      <h1>{title}</h1>
      <p>{credit_html}</p>
    </header>
  </div>
</body></html>
"""
    components_html(html_code, height=height, scrolling=True)


# ---------- main ----------
def main():
    st.title("Welcome to Pawpaw Homestay!")

    # --- Fetch images from S3 ---
    idx = get_index(BUCKET, ABOUT_ROOT1)
    
    keys: List[str] = []
    if isinstance(idx, dict):
        for _, arr in idx.items():
            keys.extend(arr or [])
    elif isinstance(idx, (list, tuple)):
        keys = list(idx)

    keys = [k for k in keys if not Path(k).name.startswith("._") and not Path(k).name.startswith(".")]

    # accept many suffixes; skip HEIC (browser support varies)
    valid_ext = re.compile(r"\.(webp|avif|jpe?g|png|gif|bmp)$", re.I)   # ★
    keys = [k for k in keys if valid_ext.search(k)]

    # de-dup then shuffle randomly each run
    keys = list(dict.fromkeys(keys))                                     # ★ remove dups, keep order
    random.shuffle(keys)            

    if not keys:
        st.warning(f"No images found under s3://{BUCKET}/{ABOUT_ROOT1}")
        return

    items: List[Dict[str, str]] = []
    for i, key in enumerate(keys):
        url = _safe_join_url(BASE_IMAGE_URL, key)
        items.append({
            "src": url,
            "href": url,
            "class": _cycle_classes(i),
            "alt": _alt_from_key(key),
        })

    # --- Parallax gallery ---
    render_parallax_gallery(
        items,
        credit_html='Photos © Pawpaw Homestay',
        height=520,
        bg_color="transparent",
        tile_bg="transparent",
        show_shadow=True,
    )

    # --- Subtitle + caption ---
    st.subheader("About Pawpaw:")
    st.caption("Home-style care • Constant companionship • Lots of love")

    # --- Bilingual card ---
    card_html_1 = """
    <style>
    .ppw-card{
      position: relative;
      max-width: 900px; width: 90%;
      margin: 0 auto 32px auto;
      padding: 20px 26px 40px 26px;
      background: #fff6ef;
      border: 1px solid #c8a18f33;
      border-radius: 18px;
      box-shadow: 0 6px 18px rgba(95, 47, 17, 0.10);
      color: #5a3b2e; line-height: 1.75; font-size: 17px;
      font-family: 'Hepta Slab', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial;
      border-left: 6px solid #c8a18f66;
    }
    .translate-btn {
      position: absolute; right: 18px; bottom: 14px;
      background-color: #c8a18f; color: #fff; border: none;
      border-radius: 8px; padding: 4px 10px; font-size: 13px;
      cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
      transition: all 0.2s ease;
    }
    .translate-btn:hover { background-color: #b58c7c; }
    </style>

    <div class="ppw-card" id="pawpawCard">
      <div id="text-en">
        <p><strong>Pawpaw Homestay LLC.</strong> was founded in October 2025. Before that, the founder, Anqi, had over ten years of hands-on experience caring for pets — from 5-month-old playful puppies and mischievous adolescents to wise senior dogs of 15 years old. From tiny Maltese pups that fit in the palm of your hand to large, powerful German Shepherds, every guest at Pawpaw receives gentle and attentive care. Since opening, Pawpaw has NEVER had a single fight or escape incident — and we intend to keep it that way! Your pet’s safety will always be our top priority.</p>
        <p>The original residents of <strong>Pawpaw</strong> are two gentle cats, Jojo and Gogo. They have their own cozy spaces, separate from the boarding dogs and cats, so everyone can relax comfortably. Over the past year, Pawpaw also used sideyard as a foster space for about 36 dogs rescued from the San Bernardino Shelter — dogs who were once at risk of euthanasia ❤️ We’re overjoyed that each of them eventually found a loving foster or forever home!</p>
        <p><strong>Pawpaw</strong>’s core service is providing homestyle boarding for pets whose parents are away on vacation or business trips. You can rest assured that your little one will be in loving hands! Unlike hotel-style boarding, a home-style stay means your pets can truly treat this place as their second home 🏠 — filled with care, companionship, and warmth every single day. Since the host works from home, any unexpected situation can be noticed and handled immediately.</p>
      </div>

      <div id="text-zh" style="display:none;">
        <p><strong>Pawpaw Homestay LLC.</strong> 创立于2025年10月，在此之前创始人ANQI有10年养宠经验～她照顾过从5个月大的小宝宝，1岁多的青春期小朋友，到15岁老朋友；也带过从体型巴掌大的马尔济斯，到超大威猛的德牧，Pawpaw都能照顾的很好～目前Pawpaw从来没发生过小猫小狗打架或者小猫小狗出逃事件，将来也一定不会！我们永远都把小朋友们的安全放在第一位。</p>
        <p><strong>Pawpaw</strong>原住民是两只自己的温顺小猫Jojo和Gogo，平时他们会有自己的独立活动区域会和寄养的猫猫狗狗划分开。在此之前的的一年多里，Pawpaw作为中转家庭帮助了大概36只从San Bernadino Shelter里救助出来的即将被安乐死的狗狗❤️恭喜他们最后成功找到foster family和领养人！</p>
        <p><strong>Pawpaw</strong>的核心业务是为出游或者出差的宠物家长们提供寄养服务。家长们可以放心地把小朋友托付给我们！家庭式寄养和酒店式寄养的不同之处就是小朋友们可以把这里当作第二个家🏠每天都会有很多的关注很多的陪伴和很多的爱！因为主理人居家办公，所以如果有什么突发状况都能及时发现和解决～</p>
        <p><strong>Pawpaw</strong>的初心是希望所有小猫小狗在主人不在的时候都能体验到家的温暖！我们希望无论是第一次来的小客人，还是常常回家的老朋友，都能在这边开开心心的交到新朋友～</p>
      </div>

      <button class="translate-btn" id="ppw-toggle">中文 / EN</button>
    </div>

    <script>
    (function(){
      const en  = document.getElementById('text-en');
      const zh  = document.getElementById('text-zh');
      const btn = document.getElementById('ppw-toggle');
      btn.addEventListener('click', function(){
        const showEN = (en.style.display === 'none');
        en.style.display = showEN ? 'block' : 'none';
        zh.style.display = showEN ? 'none'  : 'block';
        btn.textContent  = showEN ? '中文 / EN' : 'EN / 中文';
      });
    })();
    </script>
    """

    components_html(card_html_1, height=580, scrolling=False)

    # --- Fetch images from S3 ---
    idx = get_index(BUCKET, ABOUT_ROOT2)
    
    keys: List[str] = []
    if isinstance(idx, dict):
        for _, arr in idx.items():
            keys.extend(arr or [])
    elif isinstance(idx, (list, tuple)):
        keys = list(idx)

    keys = [k for k in keys if not Path(k).name.startswith("._") and not Path(k).name.startswith(".")]

    # accept many suffixes; skip HEIC (browser support varies)
    valid_ext = re.compile(r"\.(webp|avif|jpe?g|png|gif|bmp)$", re.I)   # ★
    keys = [k for k in keys if valid_ext.search(k)]

    # de-dup then shuffle randomly each run
    keys = list(dict.fromkeys(keys))                                     # ★ remove dups, keep order
    random.shuffle(keys)            

    if not keys:
        st.warning(f"No images found under s3://{BUCKET}/{ABOUT_ROOT2}")
        return

    items: List[Dict[str, str]] = []
    for i, key in enumerate(keys):
        url = _safe_join_url(BASE_IMAGE_URL, key)
        items.append({
            "src": url,
            "href": url,
            "class": _cycle_classes(i),
            "alt": _alt_from_key(key),
        })

    # --- Parallax gallery ---
    render_parallax_gallery(
        items,
        credit_html='Photos © Pawpaw Homestay',
        height=520,
        bg_color="transparent",
        tile_bg="transparent",
        show_shadow=True,
    )

    # --- Subtitle + caption ---
    st.subheader("About the Founder:")
    st.caption("ANQI • Pet Lover • Master Chef")

    # --- Bilingual card ---
    card_html = """
    <style>
    .ppw-card{
      position: relative;
      max-width: 900px; width: 90%;
      margin: 0 auto 32px auto;
      padding: 20px 26px 40px 26px;
      background: #fff6ef;
      border: 1px solid #c8a18f33;
      border-radius: 18px;
      box-shadow: 0 6px 18px rgba(95, 47, 17, 0.10);
      color: #5a3b2e; line-height: 1.75; font-size: 17px;
      font-family: 'Hepta Slab', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial;
      border-left: 6px solid #c8a18f66;
    }
    .translate-btn {
      position: absolute; right: 18px; bottom: 14px;
      background-color: #c8a18f; color: #fff; border: none;
      border-radius: 8px; padding: 4px 10px; font-size: 13px;
      cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
      transition: all 0.2s ease;
    }
    .translate-btn:hover { background-color: #b58c7c; }
    </style>

    <div class="ppw-card" id="pawpawCard">
      <div id="text-en">
        <p><strong>ANQI</strong> completed her undergraduate studies at Occidental College, majoring in Mathematics and Computer Science. Later, she earned her graduate degree from Carnegie Mellon University, focusing on Data Science. She loves combining her technical skills with her personal passions to create meaningful and fun projects. For example, this Pawpaw website is one of them — it’s where she records the stories and photos of the pets she has cared for, and even analyzes the data collected during their stays.</p>

        <p><strong>ANQI</strong>’s biggest hobby outside of work is cooking — she loves making all kinds of beautiful meals! She also enjoys exploring new restaurants and cafés, and often tries to recreate her favorite dishes at home. The only thing she admits she’s hopeless at is desserts — somehow, every sweet she makes ends up a disaster 🤭. Savory food is definitely her strength!</p>

        <p><strong>ANQI</strong> has loved animals since she was a child — she always stops to admire every cat and dog she sees on the street, and her dream has long been to open a pet-related business someday! She still remembers spending her very first part-time paycheck in high school on a guinea pig from PetSmart. Whenever her friends or relatives traveled, she was the one who looked after their pets — hamsters, bunnies, cats, dogs — all of them!</p>
      </div>

      <div id="text-zh" style="display:none;">
        <p><strong>ANQI</strong> 本科就读于西方学院，主修数学和计算机科学。后来在卡耐基梅隆大学攻读研究生学位，专注于数据科学。她特别喜欢将学到的技术技能和她的兴趣爱好结合起来，创造有趣的项目。比如说这个Pawpaw网站，她就把曾经照顾过的小动物们的故事照片都记录下来，并对寄养期间收集来的数据做了分析。</p>
        <p><strong>ANQI</strong> 平时最大的兴趣爱好就是做饭，做各种漂亮饭！也喜欢探店，探各种美食店！在外头吃到的好吃的回到家就喜欢复刻出来。不过她是甜品白痴，在做甜品上是一点天赋都没有，做什么都翻车.....还是做咸口的技术会比较好一点。她特别喜欢吃鸭货，如果哪天家长带着小朋友和鸭货来寄养，说不定可以解锁折扣🤤</p>
        <p><strong>ANQI</strong> 从小就喜欢小动物，在路上见到小猫小狗都会停下来多看几眼，梦想就是开一家宠物（相关的）店！！还记得她高中parttime挣的第一桶金一发，直接高高兴兴地跑去petsmart买了一只天竺鼠回家。小时候帮亲戚朋友出游经常就是把小动物交给ANQI带，小仓鼠小兔子小猫小狗都照顾过～</p>
      </div>

      <button class="translate-btn" id="ppw-toggle">中文 / EN</button>
    </div>

    <script>
    (function(){
      const en  = document.getElementById('text-en');
      const zh  = document.getElementById('text-zh');
      const btn = document.getElementById('ppw-toggle');
      btn.addEventListener('click', function(){
        const showEN = (en.style.display === 'none');
        en.style.display = showEN ? 'block' : 'none';
        zh.style.display = showEN ? 'none'  : 'block';
        btn.textContent  = showEN ? '中文 / EN' : 'EN / 中文';
      });
    })();
    </script>
    """

    components_html(card_html, height=580, scrolling=False)
    

if __name__ == "__main__":
    main()
