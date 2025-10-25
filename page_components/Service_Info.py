# page_components/Service_Info.py
from __future__ import annotations
import streamlit as st
from datetime import date
from topia_common import render_topia_title


# ---------------- Constants ----------------
DOG = "dog"
CAT = "cat"
ZH  = "zh"
EN  = "en"

# ---------------- State ----------------

import math

def _charge_days(drop_date, drop_slot, pick_date, pick_slot):
    """
    使用 3 段=1天 计价：
      - 同日早→中/晚 = 1天
      - 早→次日早 = 1天
      - 一般情况：ceil(diff_slots / 3)
      - 最少 1 天
    """
    day_gap = (pick_date - drop_date).days
    diff_slots = day_gap * 3 + (pick_slot - drop_slot)

    if diff_slots <= 0:
        return 1

    return max(1, math.ceil(diff_slots / 3))

def _init_state():
    # 默认值
    if "svc_view" not in st.session_state:
        st.session_state.svc_view = DOG
    if "lang" not in st.session_state:
        st.session_state.lang = ZH

    # 允许通过 ?lang=zh 或 ?lang=en 强制切换
    try:
        qp_lang = st.query_params.get("lang")
        if isinstance(qp_lang, list):
            qp_lang = qp_lang[0] if qp_lang else None
    except Exception:
        qp_lang = None

    if qp_lang:
        qp_lang = qp_lang.lower()
        if qp_lang in (ZH, EN):
            st.session_state.lang = qp_lang
        # 允许通过 ?view=dog 或 ?view=cat 强制切换
    try:
        qp_view = st.query_params.get("view")
        if isinstance(qp_view, list):
            qp_view = qp_view[0] if qp_view else None
    except Exception:
        qp_view = None

    if qp_view:
        qp_view = qp_view.lower()
        if qp_view in (DOG, CAT):
            st.session_state.svc_view = qp_view

def render_view_toggle_button_same_page():
    """Same-tab DOG↔CAT toggle: updates ?view= in parent URL and reloads."""
    cur_view  = st.session_state.get("svc_view", DOG)
    cur_lang  = st.session_state.get("lang", ZH)
    next_view = CAT if cur_view == DOG else DOG

    # Label in the current language
    if cur_lang == ZH:
        label = "转至猫猫服务" if cur_view == DOG else "转至狗狗服务"
    else:
        label = "Switch to Cat Services" if cur_view == DOG else "Switch to Dog Services"

    components_html(f"""
    <style>
      .translate-like-btn {{
        background-color:#c8a18f;color:#fff;border:none;border-radius:8px;
        padding:6px 14px;font-size:14px;font-weight:700;white-space:nowrap;
        box-shadow:0 2px 6px rgba(0,0,0,.15);transition:all .2s ease;cursor:pointer;
      }}
      .translate-like-btn:hover {{ background-color:#b58c7c; }}
      .translate-like-wrap {{ display:flex;justify-content:center;align-items:center;margin:6px 0 10px; }}
    </style>
    <div class="translate-like-wrap">
      <button class="translate-like-btn" id="ppw-view-toggle">{label}</button>
    </div>
    <script>
      (function(){{
        const btn = document.getElementById('ppw-view-toggle');
        btn.addEventListener('click', function(){{
          const P = window.parent || window;
          const url = new URL(P.location.href);
          // preserve existing params (like lang), just flip view
          const cur = (url.searchParams.get('view') || '{cur_view}').toLowerCase();
          const next = (cur === 'dog') ? 'cat' : 'dog';
          url.searchParams.set('view', next);
          // keep hash (if any)
          url.hash = P.location.hash;
          P.history.replaceState(null, '', url.toString());
          P.location.reload();
        }});
      }})();
    </script>
    """, height=56, scrolling=False)


from streamlit.components.v1 import html as components_html

def render_translate_toggle_button_same_page():
    """Same-tab language toggle: updates ?lang= in parent URL and reloads."""
    cur_lang  = st.session_state.get("lang", "zh")
    next_lang = "en" if cur_lang == "zh" else "zh"
    label     = "中文 / EN" if cur_lang == "en" else "EN / 中文"

    components_html(f"""
    <style>
      .translate-btn {{
        background-color:#c8a18f;color:#fff;border:none;border-radius:8px;
        padding:6px 14px;font-size:14px;font-weight:700;white-space:nowrap;
        box-shadow:0 2px 6px rgba(0,0,0,.15);transition:all .2s ease;cursor:pointer;
      }}
      .translate-btn:hover {{ background-color:#b58c7c; }}
      .translate-btn-wrap {{ display:flex;justify-content:center;align-items:center;margin:6px 0 10px; }}
    </style>
    <div class="translate-btn-wrap">
      <button class="translate-btn" id="ppw-toggle">{label}</button>
    </div>
    <script>
      (function(){{
        const btn = document.getElementById('ppw-toggle');
        btn.addEventListener('click', function(){{
          const P = window.parent || window;            // <-- use parent, not iframe
          const url = new URL(P.location.href);
          const cur = (url.searchParams.get('lang') || '{cur_lang}').toLowerCase();
          const next = (cur === 'en') ? 'zh' : 'en';
          url.searchParams.set('lang', next);

          // Stay on the SAME tab:
          // 1) update address bar without opening a new page
          P.history.replaceState(null, '', url.toString());
          // 2) hard reload so Streamlit reads new query params and reruns
          P.location.reload();
        }});
      }})();
    </script>
    """, height=56, scrolling=False)  # <-- no `key` here


# ---------------- i18n ----------------
def T(key: str) -> str:
    lang = st.session_state.lang
    return _STRINGS[key][lang]

_STRINGS = {

    # shared mini facts (top right cards)
    "hours_area_h3":    {
        ZH:"营业时间 & 接送Policy",            
        EN:"Hours & Area"},
    "hours_area_body":  {
        ZH:"• <b>主人上门接送宠物：</b> 9:00–20:00（可协商）<br>• <b>Pawpaw接送宠物：</b>晚上19:00之后（不塞车时段）<br>• <b>可接送范围：</b>距离Rancho Cucamonga 1个小时左右以内都可以（西至DTLA, 南至IRVINE, 东至RIVERSIDE）。如果比一个小时远可以折中至一个小时内的地方交接～ <br>• <b> 价格: </b> 20🔪一程（来回都要接送就是40🔪） <br>• 🐶🐶寄养一个星期以上/🐱🐱寄养一个月以上可以免费接送！！",
        EN: "• <b>Owner drop-off:</b> 9:00–20:00 (flexible)<br>"
            "• <b>Pawpaw pick-up/drop-off:</b> after 19:00 (non-rush hour)<br>"
            "• <b>Service area:</b> within about 1 hour from Rancho Cucamonga "
            "(west to DTLA, south to Irvine, east to Riverside). "
            "If farther, we can meet halfway within a 1-hour range.<br>"
            "• <b>Price:</b> $20 per trip (round-trip = $40)<br>"
            "• Boarding stays of one week or longer include <b>free pick-up & drop-off!</b>"},
    "cancel_h3": {
        ZH: "定金/预定/结寄养费",
        EN: "Deposit / Booking / Payment"
    },

    "cancel_body": {
        ZH: "• 确定预约需要付20%定金留位置哦～  <br>"
            "• 如果寄养时间有改动，定金可顺延至下次使用💛 <br>"
            "• 剩余的寄养费希望可以在小朋友们走当天或着走之前结清👍",
        EN: "• A 20% deposit is required to secure your booking.<br>"
            "• If your stay dates change, the deposit can be carried over to the next booking 💛<br>"
            "• The remaining balance should be settled on or before the pet’s departure day 🐾"
    },

    "faq_h3":           {ZH:"《常见问题》",             EN:"《Frequently Asked Questions (FAQ)》"},

    # ---------- DOG ----------
    "dog_services_h3":  {ZH:"《Pawpaw提供🐩的服务》",      
                     EN:"《Pawpaw 🐩 Services》"},

    "dog_services_ul":  {ZH:"-  **【🦮遛狗】** 每天早晚至少出门大遛两次，每次30min+。让🐶🐶能有足够的嗅闻散步+能量释放。 \n-  **【🍚喂食】** 可以按既定食谱与时间；接受鲜食，预热熟食等；只会给小狗喂食主人准备的食物+零食，除非主人说小狗可以吃别的零食。\n-  **【💤睡觉】** 🐶🐶如果需要和人睡也没问题～Pawpaw允许狗狗上床上沙发，而且非常喜欢抱着小狗睡觉！如果不是很粘人的小狗也可以独自在大厅睡觉；如果晚上有进笼子/playpen睡觉的习惯希望可以提前告知。\n-  **【🪥护理】** 小狗需要刷牙，梳毛，耳道清洁等需要自备工具哦（避免交叉感染）\n-  **【💊喂药】** 如果有吃药需求会按医嘱口服（请提前说明）",
                        EN:"- **【🦮 Walks】**: At least two long walks every morning and evening (30+ min each) — plenty of sniffing and energy release time!  \n- **【🍚Feeding】**: Meals follow your dog’s usual schedule and recipe; fresh or warmed food is fine. Only owner-provided food and treats are given unless otherwise approved.  \n- **【💤 Sleeping】**: Dogs are welcome to sleep on the bed or sofa! Pawpaw loves cuddling. Independent sleepers can rest in the living room; please let us know if your pup sleeps in a crate/playpen at night.  \n- **【🪥 Care】**: Please bring your own toothbrush, comb, and ear-cleaning tools (for hygiene and no cross-use).  \n- **【💊 Medication】**: Oral meds given as instructed—please let us know in advance."},

    "dog_env_badges_h3":{ZH:"《环境亮点》",                    
                        EN:"《Environment Highlights》"},

    "dog_env_badges_ul":{ZH:"- **【封闭后院】** 小狗随时可以去院子玩耍，玩抛接球，跑酷！院子是完全封闭的，不用担心狗狗会出逃。  \n- **【随意活动】** 不笼养！狗狗有更多的活动空间，更像在自己家❤️  \n- **【可上沙发】** 不怕弄脏！我们的沙发都有做防水/保护措施，🛋️都是可以随时清洗的。  \n- **【足够陪伴】** 因为家里24小时都会有人，狗狗会有足够的陪伴！如果有什么突发状况可以马上得知，并且可以立刻采取措施。",
                        EN:"- **【Fully fenced backyard】** — safe and fun space for fetch, running, and play!  \n- **【Free Roaming】** — no cages, dogs roam freely just like home ❤️  \n- **【Sofa-friendly】** — waterproof covers and washable furniture, no worries about messes 🛋️  \n- **【Constant company】** — someone is always home 24/7, ensuring safety and companionship."},

    "dog_skills_label": {ZH:"**Pawpaw擅长**：",              
                        EN:"**Pawpaw’s Expertise:**"},

    "dog_skills_pills": {ZH:"<span class='pill'>狗狗喂药</span><span class='pill'>分离焦虑舒缓</span><span class='pill'>基础礼仪巩固</span><span class='pill'>老年犬照顾</span><span class='pill'>处理公狗Marking</span><span class='pill'>补被啃的墙角</span><span class='pill'>了解vet流程</span><span class='pill'>小狗礼貌社交</span><span class='pill'>错误行为纠正</span>",
                        EN:"<span class='pill'>Medication handling</span><span class='pill'>Easing separation anxiety</span><span class='pill'>Basic manners reinforcement</span><span class='pill'>Senior dog care</span><span class='pill'>Managing male dog marking</span><span class='pill'>Repairing chewed corners</span><span class='pill'>Understanding vet procedures</span><span class='pill'>Puppy socialization & etiquette</span><span class='pill'>Correcting unwanted behavior</span>"},

   # ---------- CAT ----------
    "cat_services_h3":  {ZH:"《Pawpaw提供🐈的服务》",      
                     EN:"《Pawpaw 🐈 Services》"},

    "cat_services_ul":  {ZH:"- **【🏠住宿】**：猫咪不混养！同一家猫咪会拥有安静独立房间，来之前房间会打扫干净，用紫外线灯消毒好，喷上Feliway。保证猫猫们环境的干净和预防应激。  \n-  **【🪀玩耍】**：胆子大（且家长允许）的猫咪每天下午会有2-3小时的放风时间可以探索房间以外的地方，不会在房间无聊～房间内也有足够的家具让猫猫攀爬玩耍。  \n-  **【🛀护理】**：平时会给猫猫梳掉浮毛；长毛猫如果打结会在家长和猫咪的同意下剃掉。会给猫咪剪指甲如果猫咪不抗拒。  \n-  **【🍽️饮食】**：可以自助餐也可以定时定量，以猫咪平时的习惯而定。  \n-  **【💊吃药】**：按医嘱口服药物（请提前说明）",
                        EN:"- **【🏠Boarding】**: Each cat stays in a quiet, private, disinfected room (UV sanitized + Feliway-sprayed) to ensure cleanliness and reduce stress.  \n- **【🪀Playtime】**: Confident cats (with owner’s approval) enjoy 2–3 hours of supervised free-roam daily; rooms are furnished for climbing and play.  \n- **【🛀Cares】**: Regular brushing to remove loose fur; gentle shaving of knots (with consent). Nail trimming if your cat is comfortable.  \n- **【🍽️Feeding】**: Free-feeding or scheduled meals — adjusted to your cat’s usual routine.  \n- **【💊Medication】**: Oral medicine given as prescribed — please notify us in advance."},

    "cat_env_badges_h3":{ZH:"《环境亮点》",                    
                        EN:"《Environment Highlights》"},

    "cat_env_badges_ul":{ZH:"- **【独立房间】** 猫咪们都是单间寄养，家里有个别房间是专门给猫猫的。这样猫咪会有自己的安全舒适区，在新环境更容易适应。 \n- **【猫狗隔离】** 猫猫和狗狗是彻底分开的，以防猫咪挠伤狗狗或者狗狗吓到猫咪。  \n- **【用具齐全】** 提供消毒猫砂盆/猫砂/玩具/罐头/小零食（也欢迎自带熟悉的玩具）；也有备猫咪基本生病用药  \n- **【经验丰富】** 不会强迫紧张内向的小猫社交；有处理猫咪尿闭的经验（家里有备应对尿闭的药）；对小猫的异常行为有所了解（呕吐/掉毛/长黑头等）能马上辨别病因。",
                        EN:"- **【Private rooms】** — each cat has its own clean, quiet space for comfort and easy adaptation.  \n- **【Cat-dog separation】** — cats and dogs are kept completely apart to ensure calm and safety.  \n- **【Fully equipped】** — sanitized litter boxes, litter, toys, treats, canned food, and basic medicines are provided (you’re welcome to bring familiar items).  \n- **【Experienced care】** — patient with shy or anxious cats, familiar with urinary blockage and other common feline issues; can quickly spot abnormal behaviors (vomiting, shedding, blackheads, etc.)."},

    "cat_skills_label": {ZH:"**Pawpaw擅长**：",              
                        EN:"**Pawpaw’s Expertise:**"},

    "cat_skills_pills": {ZH:"<span class='pill'>新环境适应</span><span class='pill'>紧张/慢热猫</span><span class='pill'>老年猫关怀</span><span class='pill'>多猫分区管理</span><span class='pill'>治疗尿闭</span><span class='pill'>社交性训练</span>",
                        EN:"<span class='pill'>Adjusting to new environments</span><span class='pill'>Shy / slow-to-warm cats</span><span class='pill'>Senior cat care</span><span class='pill'>Multi-cat zone management</span><span class='pill'>Handling urinary blockage</span><span class='pill'>Gentle socialization training</span>"},
    }
# ---------------- Policy i18n (separated & nested) ----------------
_POLICY = {
    "dog": {
        "policy_h3":        {ZH:"《寄养🐶🐶须知》‼️重要‼️", 
                            EN:"《Boarding Guidelines》 (‼️Important — Please read carefully!)"},

        "policy_health_h4": {ZH:"【健康要求】", 
                            EN:"【Health Requirements】"},
        "policy_health":    {ZH:"• 疫苗一定要打好才能保证狗狗们的健康！  \n• 入住前确认无传染性疾病与寄生虫（如跳蚤/蜱虫），并做好驱虫🐛  \n• 若有慢性病或特殊药物，请提前告知并附注意事项⚠️",
                            EN:"• All vaccines must be up to date to ensure everyone’s safety  \n• Pets should be free of contagious diseases and parasites (like fleas/ticks) before boarding 🐛  \n• Please let us know about any chronic conditions or medications in advance, with instructions attached🏥"},

        "policy_behavior_h4":{ZH:"【性格与行为】", 
                            EN:"【Temperament & Behavior】"},
        "policy_behavior":  {ZH:"• 如有攻击前科/护食/其他行为问题务必如实告知❌  \n• 说明是否适合与其他宠物同住/错峰接触",
                            EN:"• Please be honest about any aggression, resource guarding, or behavioral issues  \n• Let us know whether your pet is comfortable co-staying or prefers separate time/space"},

        "policy_pack_h4":   {ZH:"【物品准备】", 
                            EN:"【What to Bring】"},
        "policy_pack":      {ZH:"• 平时吃的主食与零食（长期寄养如果饭吃完了Pawpaw会提前联系，可以随时寄过来～）  \n• 玩具/小床/毛毯等熟悉物品（让狗狗更安心，更快适应！）  \n• 需吃药的请备好药品并附详细喂药说明🩵",
                            EN:"• Bring your pet’s usual food and treats (for long stays, we’ll contact you if supplies run low — you can always ship more!)  \n• Familiar items like toys, bed, or blanket help your pet feel safe and settle in faster 🩵  \n• If medication is needed, please include clear written instructions"},

        "policy_pay_h4":    {ZH:"【费用与支付】", 
                            EN:"【Fees & Payment】"},
        "policy_pay":       {ZH:"• 支持 Zelle / Cash 至 Pawpaw Homestay 账户，我们都是合法报税的！  \n• 具体价格💰请参考下一个板块",
                            EN:"• Payments can be made via Zelle or cash to Pawpaw Homestay — all taxes are properly handled ✅  \n• Please refer to the next section for detailed pricing 💰"},

        "policy_time_h4":   {ZH:"【接送时间】", 
                            EN:"【Drop-off / Pick-up】"},
        "policy_time":      {ZH:"• 请提前确认时间并尽量准时✨  \n• 如果要赶飞机请一定要提前再提前交接好小朋友，不然有可能因为交通原因出现意外✈️",
                            EN:"• Please confirm your drop-off and pick-up times in advance and try to be on time ✨  \n• If you have a flight, plan for extra time — LA traffic can be unpredictable!"},

        "policy_emerg_h4":  {ZH:"【突发情况处理】", 
                            EN:"【Emergencies】"},
        "policy_emerg":     {ZH:"• 如果需要延长寄养时间请尽早告知📢  \n• 如果有突发状况Pawpaw会及时与家长沟通，做所有决策之前都会告知家长并且征求同意。",
                            EN:"• If you need to extend your pet’s stay, please let us know as early as possible 📢  \n• In any unexpected situation, Pawpaw will contact you right away — no decisions are made without your consent"},

        "policy_liab_h4":   {ZH:"【责任与免责】", 
                            EN:"【Safety & Responsibility】"},
        "policy_liab":      {ZH:"• ⚠️我们永远会把小动物们的安全放在第1️⃣位！   \n•目前Pawpaw没有任何的狗狗玩耍咬伤或者狗狗出逃的历史👍但宠物的突发疾病（癫痫等），非人为受伤（玩耍中拉伤，蚊虫叮咬等）不可完全避免～不过如果发现会及时沟通并采取行动。Pawpaw都会有备处理基本疾病的药（红霉素软膏/复方酮康唑软膏/碘伏/体外驱虫喷雾等）  \n• 如果宠物寄养逾期且联系不上主人14天，Pawpaw有权处理宠物（交至收容所或者发帖寻求领养）",
                            EN:"• Pawpaw always puts your pet’s safety first ❤️  \n• We’re proud to say there’s never been a case of injury or escape 👍  \n• However, rare incidents like sudden illness (e.g. seizures) or minor play-related strains can sometimes happen — if so, we’ll act quickly and keep you fully informed"}

        },

    "cat": {
       "policy_h3":        {ZH:"《寄养🐱🐱须知》‼️重要‼️", 
                            EN:"《Cat Boarding Guidelines》 (‼️Important — Please read carefully!)"},

        "policy_health_h4": {ZH:"【健康要求】", 
                            EN:"【Health Requirements】"},
        "policy_health":    {ZH:"• 疫苗一定要打好才能保证猫主子们的健康！  \n• 若有慢性病或特殊药物，请提前告知并附注意事项⚠️",
                            EN:"• All vaccines must be up to date to keep everyone healthy and safe 🐾  \n• If your cat has chronic conditions or takes medication, please inform us in advance and include any special notes or care instructions ⚠️"},

        "policy_behavior_h4":{ZH:"【性格与行为】", 
                            EN:"【Temperament & Behavior】"},
        "policy_behavior":  {ZH:"• 如有攻击前科/其他行为问题务必如实告知  \n• 说明是否希望和别的猫猫社交🧑‍🤝‍🧑",
                            EN:"• Please be honest about any aggression or other behavioral issues  \n• Let us know whether your cat enjoys socializing with other cats or prefers to stay private 🧑‍🤝‍🧑"},

        "policy_pack_h4":   {ZH:"【物品准备】", 
                            EN:"【What to Bring】"},
        "policy_pack":      {ZH:"• 平时吃的主食与零食（长期寄养如果饭吃完了Pawpaw会提前联系，可以随时寄过来～）  \n• 玩具/有主人气味的物品（让🐱🐱更安心，更快适应！）  \n• 需吃药的请备好药品并附详细喂药说明🩵",
                            EN:"• Bring your cat’s regular food and treats (for long stays, we’ll let you know if supplies run low — you can always ship more!)  \n• Familiar items with your scent, like toys, blankets, or small bedding, help your cat feel safe and settle in faster 🩵  \n• If medication is needed, please include the medicine and clear written instructions"},

        "policy_pay_h4":    {ZH:"【费用与支付】", 
                            EN:"【Fees & Payment】"},
        "policy_pay":       {ZH:"• 支持 Zelle / Cash 至 Pawpaw Homestay 账户，我们都是合法报税的！  \n• 具体价格💰请参考下一个板块",
                            EN:"• Payments can be made via Zelle or cash to Pawpaw Homestay — we are fully tax-compliant ✅  \n• Please refer to the next section for detailed pricing 💰"},

        "policy_time_h4":   {ZH:"【接送时间】", 
                            EN:"【Drop-off / Pick-up】"},
        "policy_time":      {ZH:"• 请提前确认时间并尽量准时✨  \n• 如果要赶飞机请一定要提前再提前交接好小朋友，不然有可能因为交通原因出现意外～",
                            EN:"• Please confirm drop-off and pick-up times in advance and arrive on time ✨  \n• If you’re catching a flight, plan extra time for the handover — LA traffic can be unpredictable!"},

        "policy_emerg_h4":  {ZH:"【突发情况处理】", 
                            EN:"【Emergencies】"},
        "policy_emerg":     {ZH:"• 如果需要延长寄养时间请尽早告知🎺  \n• 如果有突发状况Pawpaw会及时与家长沟通，做所有决策之前都会告知家长并且征求同意。",
                            EN:"• Please inform us as early as possible if you need to extend your cat’s stay 🎺  \n• In case of any emergency or unexpected situation, Pawpaw will contact you right away — no decisions will be made without your consent"},

        "policy_liab_h4":   {ZH:"【责任与免责】", 
                            EN:"【Safety & Responsibility】"},
        "policy_liab":      {ZH:"• ⚠️我们永远会把小动物们的安全放在第1️⃣位！   \n• 目前Pawpaw没有任何的猫猫玩耍咬伤或者猫猫出逃的历史👍但宠物的突发疾病（癫痫，应激性猫藓，尿闭等）不可完全避免～不过如果发现会及时沟通并采取行动。Pawpaw都会有备处理基本疾病的药（红霉素软膏/复方酮康唑软膏/碘伏/尿闭罐头等）。  \n• 如果宠物寄养逾期且联系不上主人14天，Pawpaw有权处理宠物（交至收容所或者发帖寻求领养）",
                            EN:"• Pawpaw always puts your cat’s safety and well-being first ❤️  \n• We’ve never had a case of injury or escape 👍  \n• However, sudden illnesses (such as seizures, stress-related ringworm, or urinary blockage) can occur and are sometimes unavoidable. If anything happens, we’ll contact you immediately and take prompt action.  \n• Pawpaw also keeps basic veterinary supplies on hand — such as erythromycin ointment, antifungal cream, iodine solution, and urinary-support wet food — to provide quick initial care if needed."}


        }
}
_STRINGS.update({
    # ---- Shared pricing section titles ----
    "price_h3_dog": {ZH:"💰 价格（狗狗）", EN:"💰 Pricing (Dogs)"},
    "price_h3_cat": {ZH:"💰 价格（猫猫）", EN:"💰 Pricing (Cats)"},

    # ---- Dog table headers/rows ----
    "th_size":      {ZH:"体型",     EN:"Size"},
    "th_std":       {ZH:"普通价格/天", EN:"Standard / day"},
    "th_1v1":       {ZH:"1v1/天",    EN:"1-on-1 / day"},
    "sz_xs":        {ZH:"超小型犬（<8lb:兔体马尔济斯/茶杯犬）",  EN:"Toy / XS"},
    "sz_s":         {ZH:"小型犬（<15lb:博美/比熊/泰迪）",    EN:"Small"},
    "sz_m":         {ZH:"中型犬（<35lb：柴犬/柯基/法斗）",    EN:"Medium"},
    "sz_l":         {ZH:"大型犬（>35lb：边牧/博恩山/澳牧）",    EN:"Large"},

    # ---- Cat table headers/rows ----
    "th_day":       {ZH:"一天",     EN:"Per Day"},
    "th_week":      {ZH:"一周",     EN:"Per Week"},
    "th_month":     {ZH:"一个月",   EN:"Per Month"},
    "row_1":        {ZH:"一只猫",     EN:"1 cat"},
    "row_2":        {ZH:"双猫家庭",     EN:"2 cats"},
    "row_3":        {ZH:"三猫家庭",     EN:"3 cats"},
})
_STRINGS.update({
    "checkin_slot":  {ZH:"入住时段", EN:"Check-in window"},
    "checkout_slot": {ZH:"离店时段", EN:"Pick-up window"},
    "slot_morning":  {ZH:"早上 8–12", EN:"Morning 8–12"},
    "slot_afternoon":{ZH:"下午 1–4",  EN:"Afternoon 1–4"},
    "slot_evening":  {ZH:"晚上 5–8",  EN:"Evening 5–8"},
})
def _html_table(title: str, headers: list[str], rows: list[list[str]], caption: str = ""):
    thead = "".join(f"<th>{h}</th>" for h in headers)
    tbody = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    num_cols = len(headers)
    caption_html = f"<div class='price-caption'>{caption}</div>" if caption else ""

    st.markdown(
        f"<div class='card-box'>"
        f"<div class='price-title'>{title}</div>"
        f"<table class='price-table col{num_cols}'>"
        f"<colgroup>{''.join('<col>' for _ in range(num_cols))}</colgroup>"
        f"<thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>"
        f"{caption_html}"  # ✅ caption below the table
        f"</div>",
        unsafe_allow_html=True
    )

def _pricing_tables(kind: str):
    if kind == DOG:
        _html_table(
            title=T("price_h3_dog"),
            headers=[T("th_size"), T("th_std"), T("th_1v1")],
            rows=[
                [T("sz_xs"), "$30", "$55"],
                [T("sz_s"),  "$35", "$55"],
                [T("sz_m"),  "$45", "$70"],
                [T("sz_l"),  "$65", "$90"],
            ],
            caption=(
                "❌ Pawpaw cannot accept dogs that are **aggressive**, **intact males over 45 lb**, "
                "or **high-anxiety pups prone to destruction or excessive barking**.<br>"
                "All guests must be friendly, non-aggressive, and potty-trained 💛<br>"
                "⚠️ If a female dog goes into heat during boarding, there’s a $5/day add-on."
                if st.session_state.lang == EN else
                "⚠️ Pawpaw不接待：<b>有攻击性、超大型犬、未Potty Trained、拆家或有严重分离焦虑的狗狗。</b><br>"
                "⚠️ <b>如果寄养期间小狗生理期，来的每天+5🔪</b><br>"
                "⚠️ <b>多宠家庭或者长期寄养价格可议❤️</b><br>"

            )
        )
    else:  # CAT
        _html_table(
            title=T("price_h3_cat"),
            headers=["", T("th_day"), T("th_week"), T("th_month")],
            rows=[
                [T("row_1"), "$25", "$170", "$550"],
                [T("row_2"), "$45", "$310", "$900"],
                [T("row_3"), "$60", "$410", "$1300"],
            ],
            caption=(
                "❌ Pawpaw doesn’t board **unneutered male cat**.<br>"
                if st.session_state.lang == EN else
                "⚠️ Pawpaw不接待：<b>未绝育的公猫</b><br>"
                "⚠️ <b>多宠家庭或者长期寄养价格可议❤️</b><br>"
            )
        )

def _price_calculator(kind: str):
    

    today = date.today()

    # 一行 7 列：入住日｜离店日｜入住时段｜离店时段｜体重/只数｜护理/占位｜接送
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1.15, 1.15, 1.0, 1.0, 1.05, 1.05, 1.4])

    # 日期
    with c1:
        dropoff = st.date_input(
            "📅 入住日期" if st.session_state.lang==ZH else "📅 Drop-off",
            value=today, key=f"{kind}_drop"
        )
    with c2:
        pickup = st.date_input(
            "📅 离店日期" if st.session_state.lang==ZH else "📅 Pick-up",
            value=today, key=f"{kind}_pick"
        )

    # 时段选项与索引
    slot_labels = [T("slot_morning"), T("slot_afternoon"), T("slot_evening")]
    with c3:
        drop_slot_label = st.selectbox(T("checkin_slot"), slot_labels, index=0, key=f"{kind}_drop_slot")
    with c4:
        pick_slot_label = st.selectbox(T("checkout_slot"), slot_labels, index=0, key=f"{kind}_pick_slot")

    slot_index = {slot_labels[0]: 0, slot_labels[1]: 1, slot_labels[2]: 2}
    drop_slot = slot_index[drop_slot_label]
    pick_slot  = slot_index[pick_slot_label]

    # 计价天数（按时段规则）
    charge_days = _charge_days(dropoff, drop_slot, pickup, pick_slot)

    per_trip_fee = 20  # $20/趟

    if kind == DOG:
        # 体重 + 护理 + 接送
        with c5:
            weight = st.number_input(
                "🐶 体重(lb)" if st.session_state.lang==ZH else "🐶 Weight (lb)",
                min_value=1.0, max_value=200.0, value=15.0, step=1.0, key=f"{kind}_w"
            )
        with c6:
            care = st.selectbox(
                "护理类型" if st.session_state.lang==ZH else "Care type",
                ["普通寄养", "1v1"] if st.session_state.lang==ZH else ["Standard", "1-on-1"],
                key=f"{kind}_care"
            )
        with c7:
            transport_choice = st.selectbox(
                "🚗 接送？" if st.session_state.lang==ZH else "🚗 Transport?",
                ["主人接送", "Pawpaw接宠", "Pawpaw送回", "Pawpaw接+送"]
                if st.session_state.lang==ZH
                else ["Owner drop-off & pick-up", "Pick-up only", "Drop-off only", "Pick-up & drop-off"],
                index=0, key=f"{kind}_transport"
            )

        # 接送趟数映射（你指定的规则）
        trips = ({"主人接送": 0, "Pawpaw接宠": 1, "Pawpaw送回": 1, "Pawpaw接+送": 2}
                 if st.session_state.lang==ZH else
                 {"Owner drop-off & pick-up": 0, "Pick-up only": 1, "Drop-off only": 1, "Pick-up & drop-off": 2}
                )[transport_choice]

        # 住满 7 晚（按计费天数）接送免费
        transport_cost = 0 if charge_days >= 7 else per_trip_fee * trips

        # 体型分档
        if weight < 8: size_key = "超小型犬" if st.session_state.lang==ZH else "XS"
        elif weight < 15: size_key = "小型犬" if st.session_state.lang==ZH else "S"
        elif weight < 35: size_key = "中型犬" if st.session_state.lang==ZH else "M"
        else: size_key = "大型犬" if st.session_state.lang==ZH else "L"

        std_rates = {"XS": 30, "S": 35, "M": 45, "L": 65}
        one_rates = {"XS": 55, "S": 55, "M": 70, "L": 90}
        # 用英文字母键来取价
        size_key_en = ("XS" if weight < 8 else "S" if weight < 15 else "M" if weight < 35 else "L")
        day_rate = one_rates[size_key_en] if ("1v1" in care or "1-on-1" in care) else std_rates[size_key_en]

        subtotal = day_rate * charge_days
        total = subtotal + transport_cost

        # 接送短语（按你的要求显示哪种接送）
        if st.session_state.lang==ZH:
            transport_phrase = (
                "不需要接送" if trips==0 else
                "需要接"   if transport_choice=="Pawpaw接宠" else
                "需要送"   if transport_choice=="Pawpaw送回" else
                "需要接送"
            )
            care_label = "1v1" if "1v1" in care else "普通寄养"
            st.markdown(
                f"""
                <div class='calc-box'>
                <div class='calc-line'>
                    [{size_key}｜{charge_days}晚｜{care_label}｜${day_rate}/天｜{transport_phrase}] 
                    = {charge_days} × ${day_rate} + ${transport_cost} = <b>${total}</b>
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            transport_phrase = (
                "Owner drop-off & pick-up" if trips==0 else
                "Pick-up only" if trips==1 and "Pick-up" in transport_choice else
                "Drop-off only" if trips==1 else
                "Pick-up & drop-off"
            )
            care_label = "1-on-1" if "1-on-1" in care else "Standard"
            st.markdown(
                f"""
                <div class='calc-box'>
                <div class='calc-line'>
                    [{size_key_en}｜{charge_days}night(s)｜{care_label}｜${day_rate}/day｜{transport_phrase}] 
                    = {charge_days} × ${day_rate} + ${transport_cost} = <b>${total}</b>
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        # --- CAT calculator (新规则) ---
        with c5:
            n_cats = st.selectbox(
                "🐱 猫咪只数" if st.session_state.lang==ZH else "🐱 Cats",
                [1,2,3], index=0, key=f"{kind}_cats"
            )
        with c6:
            transport_choice = st.selectbox(
                "🚗 接送？" if st.session_state.lang==ZH else "🚗 Transport?",
                ["主人接送", "Pawpaw接宠", "Pawpaw送回", "Pawpaw接+送"] 
                if st.session_state.lang==ZH 
                else ["Owner drop-off & pick-up", "Pick-up only", "Drop-off only", "Pick-up & drop-off"],
                index=0,
                key=f"{kind}_transport"
            )
        with c7:
            st.write("")  # 占位对齐

        # 接送趟数（0/1/2）
        if st.session_state.lang == ZH:
            trips = {"主人接送": 0, "Pawpaw接宠": 1, "Pawpaw送回": 1, "Pawpaw接+送": 2}[transport_choice]
        else:
            trips = {"Owner drop-off & pick-up": 0, "Pick-up only": 1, "Drop-off only": 1, "Pick-up & drop-off": 2}[transport_choice]

        # -------------------------
        # 计价参数（猫）
        # -------------------------
        per_trip_fee = 20
        # 原始日价
        day_rates = {1:25, 2:45, 3:60}
        # 周价
        week_rates = {1:170, 2:310, 3:410}
        # 月价（整月）
        month_rates = {1:550, 2:900, 3:1300}
        # 未满月时：按“原日价 - 5”
        day_discounted = {k: v - 5 for k, v in day_rates.items()}
        # 大于一个月时：超出整月的“天数”按以下特价计
        month_extra_day = {1:15, 2:30, 3:45}

        # 住宿晚数（你已用 nights；若已实现时段算法，用 charge_days 覆盖）
        # 若你已有 _charge_days(drop_date, drop_slot, pick_date, pick_slot)，请用它的返回值替换 nights

        # 接送费用（满 30 晚免费）
        transport_cost = 0 if charge_days >= 30 else per_trip_fee * trips

        # 计算小计
        # -------------------------
        if charge_days >= 30:
            months   = charge_days // 30
            rem_days = charge_days % 30
            subtotal = months * month_rates[n_cats] + rem_days * month_extra_day[n_cats]
            per_day_display = month_extra_day[n_cats]  # 超月部分按特价/天
            parts = []
            if months:
                parts.append(f"{months}×月(${month_rates[n_cats]})")
            if rem_days:
                parts.append(f"{rem_days}×天×${month_extra_day[n_cats]}")
            breakdown = " + ".join(parts) if parts else f"0×天"

        else:
            weeks     = charge_days // 7
            rem_days  = charge_days % 7

            if weeks == 0:
                # ✅ 未满一周：全部按原始日价
                subtotal = rem_days * day_rates[n_cats]
                per_day_display = day_rates[n_cats]
                breakdown = f"{rem_days}×天×${day_rates[n_cats]}" if rem_days else "0×天"
            else:
                # ✅ 有整周：整周按周价；余数天数按“原日价 - 5”
                subtotal = weeks * week_rates[n_cats] + rem_days * day_discounted[n_cats]
                per_day_display = day_discounted[n_cats]  # 括号里展示余数天的单价
                parts = []
                if weeks:
                    parts.append(f"{weeks}×周(${week_rates[n_cats]})")
                if rem_days:
                    parts.append(f"{rem_days}×天×${day_discounted[n_cats]}")
                breakdown = " + ".join(parts) if parts else f"0×天"


        total = subtotal + transport_cost

        # 家庭标签
        fam_label = {1: T("row_1"), 2: T("row_2"), 3: T("row_3")}[n_cats]

        # 接送短语（保持你喜欢的输出格式）
        if st.session_state.lang==ZH:
            transport_phrase = (
                "不需要接送" if trips==0 else
                "需要接"   if transport_choice=="Pawpaw接宠" else
                "需要送"   if transport_choice=="Pawpaw送回" else
                "需要接送"
            )
            st.markdown(
                f"<div class='calc-box'>"
                f"<div class='calc-line'>"
                f"[{fam_label}｜{charge_days}晚｜${per_day_display}/天｜{transport_phrase}] "
                f"= {breakdown} + ${transport_cost} = <b>${total}</b>"
                f"</div></div>",
                unsafe_allow_html=True
            )
        else:
            transport_phrase = (
                "Owner drop-off & pick-up" if trips==0 else
                "Pick-up only" if trips==1 and "Pick-up" in transport_choice else
                "Drop-off only" if trips==1 else
                "Pick-up & drop-off"
            )
            fam_label_en = {1:"1 cat", 2:"2 cats", 3:"3 cats"}[n_cats]
            st.markdown(
                f"<div class='calc-box'>"
                f"<div class='calc-line'>"
                f"[{fam_label_en} | {charge_days} night(s) | ${per_day_display}/day | {transport_phrase}] "
                f"= {breakdown} + ${transport_cost} = <b>${total}</b>"
                f"</div></div>",
                unsafe_allow_html=True
            )

    st.caption(
        "＊价格为预估，最终以实际情况为准；不足一天按时段规则计费（见上）。"
        if st.session_state.lang==ZH else
        "*This is an estimate; final charges may vary. Partial days follow the time-window rules above.*"
    )



STRICT = False  # set True while developing to catch missing keys

def PT(key: str, species: str) -> str:
    """Lookup policy text for species only (dog/cat). No generic fallback."""
    lang = st.session_state.lang
    try:
        return _POLICY[species][key][lang]
    except KeyError as e:
        if STRICT:
            raise KeyError(f"Missing policy text: species='{species}', key='{key}', lang='{lang}'") from e
        return ""  # fail soft in production


# ---------------- CSS ----------------
def _shared_css():
    st.markdown(f"""
    <style>
      /* Header buttons (global style baseline) */
      [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"] div.stButton > button{{
        background-color:#c8a18f !important; color:#fff !important; border:none !important;
        border-radius:10px !important; padding:8px 18px !important; font-weight:600 !important;
        box-shadow:0 4px 6px rgba(0,0,0,.2) !important; transition:all .2s ease-in-out;
      }}
      [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"] div.stButton > button:hover{{
        transform:translateY(-1px); box-shadow:0 6px 14px rgba(0,0,0,.25) !important;
      }}
      [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"] div.stButton > button:disabled{{
        opacity:1 !important; cursor:default !important;
      }}

      /* Divider + pills */
      .divider{{ border:none; border-top:1px solid rgba(0,0,0,.06); margin:16px 0; }}
      .pill{{ display:inline-block; margin:4px 8px 0 0; padding:2px 8px; font-size:12px;
             background:rgba(200,161,143,.18); color:#5a3b2e; border-radius:12px; }}
      .note{{ color:#5a3b2e; font-size:12px; opacity:.9; }}

      /* --- Card box (base style) --- */
      .sticky-wrap{{ position: sticky; top: 12px; }}
      @media (max-width: 900px){{ .sticky-wrap{{ position: static; }} }}

      .card-box{{
        position:relative;
        border-radius:14px;
        padding:16px 18px;
        margin-bottom:14px;
        background:linear-gradient(160deg,#c8a18f 0%,#b58b79 100%);
        border:1px solid rgba(255,255,255,.22);
        box-shadow:0 18px 36px -14px rgba(90,59,46,.40),0 8px 18px rgba(0,0,0,.10),
                   inset 0 1px 0 rgba(255,255,255,.28), inset 0 -1px 0 rgba(0,0,0,.06);
        color:#fff3e7;
        backdrop-filter:saturate(110%) contrast(102%);
        transition:transform .18s ease, box-shadow .18s ease, background .18s ease;
      }}
      .card-box:hover{{ transform:translateY(-2px); }}
      .card-box h4{{ margin:0 0 10px 0; color:#fff !important; letter-spacing:.2px; }}
      .card-box p, .card-box li, .card-box div, .card-box span {{ color:#fff3e7 !important; }}
      .card-box ul{{ margin:8px 0 0 18px; }} .card-box li{{ margin:4px 0; }}

      /* --- Pricing tables inside card-box --- */
      .card-box .price-title{{
        margin:0 0 8px 0;
        font-weight:700;
        color:#fff;
        letter-spacing:.2px;
      }}

      .card-box .price-table{{
        width:100%;
        border-collapse:separate;
        border-spacing:0;
        font-size:14px;
        border-radius:10px;
        overflow:hidden;
        background:linear-gradient(180deg,#fffaf4 0%,#fff3e7 100%);
        box-shadow:inset 0 1px 0 rgba(255,255,255,.25),
                   0 2px 8px rgba(0,0,0,.08);
      }}

      .card-box .price-table th, 
      .card-box .price-table td{{
        color:#3a251c !important;
        padding: 16px 14px;
        line-height:1.5;   
        text-align:left;
        vertical-align:middle;
        border-bottom:1px solid rgba(90,59,46,.1);
      }}

      .card-box .price-table th{{ font-weight:700; background:rgba(255,234,218,.6); }}
      .card-box .price-table tr:last-child td{{ border-bottom:none; }}
      .card-box .price-table td:first-child{{ font-weight:600; }}

      /* --- Control table column widths --- */
      .card-box .price-table{{ table-layout: fixed; }}

      /* 🐶 狗狗表：3列（左列略宽） */
      .card-box .price-table.col3 col:first-child{{ width:38%; }}
      .card-box .price-table.col3 col:nth-child(2),
      .card-box .price-table.col3 col:nth-child(3){{ width:29%; }}

      /* 🐱 猫猫表：4列（左列略宽，其余均分） */
      .card-box .price-table.col4 col:first-child{{ width:38%; }}
      .card-box .price-table.col4 col:nth-child(2),
      .card-box .price-table.col4 col:nth-child(3),
      .card-box .price-table.col4 col:nth-child(4){{ width:20.6%; }}
                
      .card-box .price-caption{{
          margin-top:10px; font-size:13px; line-height:1.5; color:#fff3e7; opacity:0.95;
      }}

      /* --- Price calculator result box --- */
      .calc-box{{
        margin-top:8px; margin-bottom:10px; border-radius:12px; padding:10px 14px;
        background:linear-gradient(160deg,#c8a18f 0%,#b58b79 100%);
        border:1px solid rgba(255,255,255,.22);
        box-shadow:0 10px 22px -12px rgba(90,59,46,.35), 0 4px 10px rgba(0,0,0,.08),
                    inset 0 1px 0 rgba(255,255,255,.25);
        color:#fff3e7;
      }}
      .calc-box .calc-line{{
        text-align:center; font-size:20px !important; font-weight:700 !important;
        line-height:1.7 !important; letter-spacing:.2px; word-break:break-word;
      }}

      

    /* 极窄屏避免字距撑开 */
    @media (max-width: 380px){{
        .navpill.control.rect{{ letter-spacing:0; }}
    }}

    /* 你原有的导航 pills 行：保持居中可换行 */
    .nav-row{{ display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:8px; }}
      /* Nav pills */
      a.navpill{{
        display:inline-block; padding:10px 14px; margin:6px 6px 0 0; border-radius:9999px;
        text-decoration:none !important; background:#c8a18f; color:#fff !important; font-weight:600;
        box-shadow:0 4px 8px rgba(0,0,0,.15);
        transition:transform .08s ease, box-shadow .15s ease, background .2s ease; white-space:nowrap;
      }}
      a.navpill:hover{{ transform:translateY(-1px); box-shadow:0 6px 14px rgba(0,0,0,.18); }}
      a.navpill.alt{{ background:#e8d7cf; color:#3a251c !important; }}

      /* Keep nav pills tidy on phones */
      .nav-row{{ display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:8px; }}
      @media (max-width: 640px){{
        .content-box{{ padding:8px 10px; }}
        a.navpill{{ padding:8px 12px; font-size:13px; }}
        .content-box .stButton>button{{ height:36px; padding:0 12px; font-size:13px; }}
      }}

      /* Anchor offset */
      .anchor-target{{ scroll-margin-top: 90px; }}

      /* Content box spacing & cleanup */
      .content-box{{ margin:12px auto 12px auto; }}
      .content-box [data-testid="column"] > div:empty{{ display:none; }}
      @media (max-width: 640px){{
        .btn-center .stButton>button{{ display:block !important; margin-left:auto !important; margin-right:auto !important; }}
      }}
    </style>

    <script>
      /* Smooth scroll for in-page nav pills */
      document.addEventListener('click', function(e){{
        const a = e.target.closest('a[href^="#"]');
        if(!a) return;
        const id = a.getAttribute('href').slice(1);
        const el = document.getElementById(id);
        if(el){{
          e.preventDefault();
          el.scrollIntoView({{behavior:'smooth', block:'start'}});
          history.replaceState(null, '', '#' + id);
        }}
      }}, {{passive:false}});
    </script>
    """, unsafe_allow_html=True)

# === NEW: anchor helper ===
def _anchor_here(anchor_id: str):
    """Drop a zero-height anchor div with a class that sets scroll-margin-top."""
    st.markdown(f"<div id='{anchor_id}' class='anchor-target'></div>", unsafe_allow_html=True)


from streamlit.components.v1 import html as components_html

def render_top_controls_same_page():
    """Centered row: [ Translate ]  [ Dog/Cat Toggle ] — both same-tab updates."""
    cur_lang = st.session_state.get("lang", "zh")
    cur_view = st.session_state.get("svc_view", "dog")

    # labels
    translate_label = "中文 / EN" if cur_lang == "en" else "EN / 中文"
    if cur_lang == "zh":
        view_label = "转至猫猫服务" if cur_view == "dog" else "转至狗狗服务"
    else:
        view_label = "Switch to 🐱 Services" if cur_view == "dog" else "Switch to 🐶 Services"

    components_html(f"""
    <style>
      .ppw-btn-row {{
        display:flex; justify-content:center; align-items:center; gap:12px;
        margin:6px 0 10px;
        flex-wrap:wrap;   /* small screens wrap nicely */
      }}
      .ppw-btn {{
        background-color:#c8a18f; color:#fff; border:none; border-radius:8px;
        padding:6px 14px; font-size:14px; font-weight:700; white-space:nowrap;
        box-shadow:0 2px 6px rgba(0,0,0,.15); transition:all .2s ease; cursor:pointer;
      }}
      .ppw-btn:hover {{ background-color:#b58c7c; }}
    </style>

    <div class="ppw-btn-row">
      <button class="ppw-btn" id="ppw-translate">{translate_label}</button>
      <button class="ppw-btn" id="ppw-view">{view_label}</button>
    </div>

    <script>
      (function(){{
        const P = window.parent || window;

        // translate toggle — flip ?lang=
        const tBtn = document.getElementById('ppw-translate');
        if (tBtn) {{
          tBtn.addEventListener('click', function(){{
            const url = new URL(P.location.href);
            const cur = (url.searchParams.get('lang') || '{cur_lang}').toLowerCase();
            const next = (cur === 'en') ? 'zh' : 'en';
            url.searchParams.set('lang', next);
            url.hash = P.location.hash;            // keep hash
            P.history.replaceState(null, '', url.toString());
            P.location.reload();
          }});
        }}

        // view toggle — flip ?view=
        const vBtn = document.getElementById('ppw-view');
        if (vBtn) {{
          vBtn.addEventListener('click', function(){{
            const url = new URL(P.location.href);
            const cur = (url.searchParams.get('view') || '{cur_view}').toLowerCase();
            const next = (cur === 'dog') ? 'cat' : 'dog';
            url.searchParams.set('view', next);
            url.hash = P.location.hash;            // keep hash
            P.history.replaceState(null, '', url.toString());
            P.location.reload();
          }});
        }}
      }})();
    </script>
    """, height=60, scrolling=False)

# === NEW: content box under the title ===
def content_box_under_title():
    render_top_controls_same_page()

    # —— Row 2: 导航 pills（原样保留） ——
    zh = (st.session_state.lang == "zh")
    pills = [
        ("#service-info", "服务信息" if zh else "Service Info"),
        ("#hours",        "营业时间" if zh else "Hours"),
        ("#payment",      "支付与定金" if zh else "Payment"),
        ("#environment",  "环境" if zh else "Environment"),
        ("#policy",       "寄养须知" if zh else "Boarding Policy"),
        ("#faq",          "常见问题" if zh else "FAQ"),
    ]
    pills_html = "<div class='nav-row'>" + "".join(
        f"<a class='navpill{' alt' if i==len(pills)-1 else ''}' href='{href}'>{label}</a>"
        for i, (href, label) in enumerate(pills)
    ) + "</div>"
    st.markdown(pills_html, unsafe_allow_html=True)


# ---------------- Sidebar (cards) ----------------
def _sidebar_cards(kind: str):
    st.markdown("<div class='sticky-wrap'>", unsafe_allow_html=True)

    # NEW: anchors for Hours and Payment cards
    _anchor_here("hours")
    st.markdown(f"<div class='card-box'><h4>{T('hours_area_h3')}</h4><div>{T('hours_area_body')}</div></div>", unsafe_allow_html=True)

    _anchor_here("payment")
    st.markdown(f"<div class='card-box'><h4>{T('cancel_h3')}</h4><div>{T('cancel_body')}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- Shared policy block ----------------
def _policy_block(kind: str):
    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    st.markdown(f"### {PT('policy_h3', kind)}")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{PT('policy_health_h4', kind)}**")
        st.markdown(PT("policy_health", kind))
        st.markdown(f"**{PT('policy_behavior_h4', kind)}**")
        st.markdown(PT("policy_behavior", kind))
        st.markdown(f"**{PT('policy_pack_h4', kind)}**")
        st.markdown(PT("policy_pack", kind))
        st.markdown(f"**{PT('policy_pay_h4', kind)}**")
        st.markdown(PT("policy_pay", kind))

    with col2:
        
        st.markdown(f"**{PT('policy_time_h4', kind)}**")
        st.markdown(PT("policy_time", kind))
        st.markdown(f"**{PT('policy_emerg_h4', kind)}**")
        st.markdown(PT("policy_emerg", kind))
        st.markdown(f"**{PT('policy_liab_h4', kind)}**")
        st.markdown(PT("policy_liab", kind))
    
    st.markdown("----")
    title = "《价格计算机》" if st.session_state.lang == ZH else "🧮 Price Calculator"
    st.markdown(f"### {title}")
    _pricing_tables(kind)
    st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)

    _price_calculator(kind)

# ---------------- Views ----------------
def _render_dog():
    c_main, c_side = st.columns([1.8, 1], gap="large")
    with c_main:
        _anchor_here("dog-services")      
        st.markdown(f"### {T('dog_services_h3')}")
        st.markdown(T("dog_services_ul"))
        st.markdown("---")

        _anchor_here("environment") 
        st.markdown(f"### {T('dog_env_badges_h3')}")
        st.markdown(T("dog_env_badges_ul"))
        st.markdown(T("dog_skills_label"), unsafe_allow_html=True)
        st.markdown(T("dog_skills_pills"), unsafe_allow_html=True)

    with c_side:
        _sidebar_cards(DOG)

    # full-width species-specific policy
    _anchor_here("policy") 
    _policy_block(DOG)
    st.markdown("---")
    _anchor_here("faq")    
    st.markdown(f"### {T('faq_h3')}")

    with st.expander("Will dogs meet the cats?" if st.session_state.lang==EN else "狗狗会见到猫猫吗？"):
        st.write(
            "Nope — they’re completely separated. If a cat is out, dogs stay in their room. "
            "Even if your pup is cat-friendly, we still keep species apart for everyone’s safety. "
            "Better safe than sorry — safety comes first." 
            if st.session_state.lang==EN else
            "Nonononoooo!!他们是完全隔离开的，如果猫猫在外面狗狗就需要在房间。即便狗狗是cat friendly，为了双方的安全着想我们也不会让他们见面的。不怕一万就怕万一，毛孩子们的安全是第一位。"
        )
    with st.expander("What if my dog damages furniture or marks indoors?" if st.session_state.lang==EN else "小狗如果寄养期间咬坏家具/乱尿怎么办？"):
        st.write(
            "If that happens, we’ll stop it immediately and take gentle measures to prevent further damage. "
            "If a male dog starts marking indoors, Pawpaw will provide diapers until the marking stops. "
            "Owners don’t need to pay any extra fees — we just want everyone to stay comfortable 💛"
            if st.session_state.lang==EN else
            "如果有发现我们会马上阻止，如果后续还有持续损坏家具行为需要采取限制小狗行动范围的措施。公狗如果有Marking的行为，Pawpaw会准备尿布直到Marking结束。主人不需要支付任何的额外费用～"
        )

    with st.expander("Do you share daily updates?" if st.session_state.lang==EN else "可以看日常更新吗？"):
        st.write(
            "Yes! Short stays get spontaneous photo/video updates throughout the day. "
            "For longer stays, we send a daily bundle of fresh photos and clips. 📷"
            if st.session_state.lang==EN else
            "当然会！短期寄养的宝贝每天都有不定时的照片/视频放送。长期寄养的宝贝就是每天发放一次当天新鲜拍的视频/照片📷"
        )

    with st.expander("Can you board a female dog in heat?" if st.session_state.lang==EN else "生理期小狗能来寄养吗？"):
        st.write(
            "Sorry, we generally don’t accept dogs currently in heat. "
            "If heat starts during the stay, owners provide diapers and there’s a +$5/day surcharge."
            if st.session_state.lang==EN else
            "不可以，我们一般不接正在来姨妈的小狗。如果狗狗是在寄养期间突然来了，需要主人自费尿布 & 然后生理期的每天+5🔪。"
        )
    with st.expander("Can unneutered dogs stay here?" if st.session_state.lang==EN else "没有绝育能来寄养吗？"):
        st.write(
            "Yes, they can! We just ask owners to book early so we can schedule carefully — "
            "during your pup’s stay, we won’t accept unneutered dogs of the opposite sex at the same time."
            if st.session_state.lang==EN else
            "可以的！没绝育希望可以尽早预约，到时候同时间段就不会接没绝育的异性啦。"
        )

    with st.expander("How many dogs are usually boarding at the same time?" if st.session_state.lang==EN else "同一时间段会有几只小狗？"):
        st.write(
            "Typically, Pawpaw hosts around 3 dogs from different families at a time — roughly 3 pups total. "
            "In special cases (like extended stays or two dogs from the same family), there might be up to 4."
            if st.session_state.lang==EN else
            "Pawpaw一般情况只会带3家小狗 ≈ 3只。特殊情况会有4只（寄养突然延期或者同一家有两只狗狗等）"
        )

    with st.expander("What does a typical day look like?" if st.session_state.lang==EN else "狗狗的一天是怎么样的呢？"):
        st.write(
            "8:00–9:00 🦮 Morning walk  \n"
            "9:00–10:00 🍚 Breakfast (can align to your set time)  \n"
            "10:00–12:00 Backyard play if it isn’t too hot  \n"
            "12:00–18:00 Indoor free time (toys/nap/treats)  \n"
            "18:00–19:00 🦮 Evening walk  \n"
            "19:00–20:00 🍚 Dinner (flexible)  \n"
            "20:00–22:00 Extra yard play + free roam if they still have zoomies  \n"
            "23:00 Bedtime 🛏️"
            if st.session_state.lang==EN else
            "8:00-9:00 🦮出门遛弯儿  \n"
            "9:00-10:00 🍚吃饭（如果有固定吃饭时间可以协调）  \n"
            "10:00-12:00 不是很热的话可以去选择去院子玩耍  \n"
            "12:00-18:00 在室内自由活动（玩玩具/睡大觉/吃零食）  \n"
            "18:00-19:00 🦮晚上遛弯儿  \n"
            "19:00-20:00 🍚吃晚饭（可协调）  \n"
            "20:00-22:00 没玩够的宝可以去院子里继续玩+自由活动  \n"
            "23:00 准备睡觉🛏️"
        )


def _render_cat():
    c_main, c_side = st.columns([1.8, 1], gap="large")
    with c_main:
        _anchor_here("cat-services")
        st.markdown(f"### {T('cat_services_h3')}")
        st.markdown(T("cat_services_ul"))
        st.markdown("---")

        _anchor_here("environment")
        st.markdown(f"### {T('cat_env_badges_h3')}")
        st.markdown(T("cat_env_badges_ul"))
        st.markdown(T("cat_skills_label"), unsafe_allow_html=True)
        st.markdown(T("cat_skills_pills"), unsafe_allow_html=True)

    with c_side:
        _sidebar_cards(CAT)

    # full-width species-specific policy
    _anchor_here("policy") 
    _policy_block(CAT)
    st.markdown("---")

    _anchor_here("faq") 
    st.markdown(f"### {T('faq_h3')}")
    with st.expander("Will my cat see dogs?" if st.session_state.lang==EN else "猫猫会见到狗狗吗？"):
        st.write(
            "Nonononoooo!! They’re completely separated. If cats are out, dogs must stay in their rooms. "
            "Even if a dog is cat-friendly, we never let them meet — safety always comes first. "
            "Better safe than sorry — we’d never take that risk for our fur babies!"
            if st.session_state.lang==EN else
            "Nonononoooo!!他们是完全隔离开的，如果猫猫在外面狗狗就需要在房间。即便狗狗是cat friendly，为了双方的安全着想我们也不会让他们见面的。不怕一万就怕万一，毛孩子们的安全是第一位。"
        )

    with st.expander("Is my cat always inside the room?" if st.session_state.lang==EN else "猫猫是一直在房间里面吗？"):
        st.write(
            "Cats get 2–3 hours of supervised free-roam time every afternoon! "
            "If your cat is shy, you can request to keep them fully private instead. "
            "Many owners worry their cats might accidentally escape, but rest assured — "
            "that’s never once happened at Pawpaw."
            if st.session_state.lang==EN else
            "猫猫每天下午有2-3小时的放风时间是可以出来的，如果胆子小的可以申请不出房间～主人一般都比较担心自己的小猫会不小心溜出门跑走，在Pawpaw就从来没发生过这种情况。"
        )

    with st.expander("Can unneutered cats stay?" if st.session_state.lang==EN else "猫咪没绝育可以来寄养吗？"):
        st.write(
            "Unspayed females are welcome, but we don’t accept unneutered males. "
            "Even if a male cat doesn’t usually mark at home, the new environment and other cat scents can trigger it. "
            "Since rooms have beds and cat pee odor is very hard to remove, we don’t take unneutered males to keep everyone comfy and clean."
            if st.session_state.lang==EN else
            "女孩儿没有绝育可以来，男孩儿就不接受没有绝育的。因为公猫未绝育有几率会尿床，即便在家里没有尿床的习惯，在Pawpaw毕竟多多少少会有别的小猫的气味，然后房间里有床且猫尿特别难去味道所以未绝育的公猫这边不接。"
        )

# ---------------- Main ----------------
def main():
    _init_state()
    _shared_css()

    # Title (wrapped for precise CSS control)
    st.markdown("<div class='app-title'>", unsafe_allow_html=True)
    render_topia_title("svc-title", "🐾 Pawpaw Services 🐾")
    
    st.markdown("</div>", unsafe_allow_html=True)
    _anchor_here("service-info")
    content_box_under_title()

    

    if st.session_state.svc_view == DOG:
        _render_dog()
    else:
        _render_cat()


if __name__ == "__main__":
    main()
