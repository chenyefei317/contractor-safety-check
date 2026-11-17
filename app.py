import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import os
import json
import base64
import random
import urllib.request
from fpdf import FPDF
import qrcode

# ================= 页面基础配置 =================
st.set_page_config(
    page_title="慧瑞环保涂料 - 承包商入场安全培训系统",
    page_icon="🛡️",
    layout="wide"
)

# ================= 数据持久化存储（JSON文件读写） =================
RECORD_FILE = "training_records.json"

def load_records():
    if os.path.exists(RECORD_FILE):
        try:
            with open(RECORD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for rec in data:
                    if "签名Bytes列表_b64" in rec:
                        rec["签名Bytes列表"] = [base64.b64decode(b) for b in rec["签名Bytes列表_b64"]]
                    if "证照图片列表_b64" in rec:
                        rec["证照Bytes列表"] = [(name, base64.b64decode(b)) for name, b in rec["证照图片列表_b64"]]
                return data
        except Exception:
            return []
    return []

def save_records(records):
    serializable_records = []
    for rec in records:
        r_copy = rec.copy()
        if "签名Bytes列表" in r_copy:
            r_copy["签名Bytes列表_b64"] = [base64.b64encode(b).decode("utf-8") for b in r_copy["签名Bytes列表"] if isinstance(b, bytes)]
            r_copy.pop("签名Bytes列表", None)
        if "证照Bytes列表" in r_copy:
            r_copy["证照图片列表_b64"] = [(name, base64.b64encode(b).decode("utf-8")) for name, b in r_copy["证照Bytes列表"] if isinstance(b, bytes)]
            r_copy.pop("证照Bytes列表", None)
        r_copy.pop("证照图片列表", None)
        serializable_records.append(r_copy)
        
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable_records, f, ensure_ascii=False, indent=4)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "records" not in st.session_state:
    st.session_state.records = load_records()

# ================= 20道题库与随机抽题初始化 =================
QUESTION_BANK = [
    {
        "q": "在慧瑞厂区进行高处作业（≥2米）时，除基础PPE外，必须正确佩戴什么？",
        "options": ["普通单钩安全带", "双大钩安全带并高挂低用", "不需要安全带"],
        "answer": "双大钩安全带并高挂低用"
    },
    {
        "q": "施工现场产生的废油漆桶、废机油、含油抹布等应当如何处理？",
        "options": ["直接扔进生活垃圾桶", "作为危险废弃物分类收集并交由厂区指定危废点处理", "随意倾倒"],
        "answer": "作为危险废弃物分类收集并交由厂区指定危废点处理"
    },
    {
        "q": "涉及电工、登高、动火作业时，以下哪项做法是正确的？",
        "options": ["无证也能操作", "必须持有效特种作业证（人证合一），并提前向EHS部门申请《危险作业许可证》", "先施工再补办许可证"],
        "answer": "必须持有效特种作业证（人证合一），并提前向EHS部门申请《危险作业许可证》"
    },
    {
        "q": "根据《安全生产法》规定，特种作业人员必须经专门的安全作业培训，取得什么方可上岗？",
        "options": ["内部上岗证", "相应资格的特种作业操作证", "驾驶证"],
        "answer": "相应资格的特种作业操作证"
    },
    {
        "q": "厂区内（除指定吸烟区外）的吸烟规定是怎样的？",
        "options": ["随时随地可以吸烟", "严禁吸烟", "带好打火机可以吸烟"],
        "answer": "严禁吸烟"
    },
    {
        "q": "入场作业必须规范穿戴的基础劳动防护用品（PPE）包括哪些？",
        "options": ["反光背心、安全帽、安全鞋", "拖鞋、短裤", "西装革履"],
        "answer": "反光背心、安全帽、安全鞋"
    },
    {
        "q": "发包单位与承包商的关系中，以下说法正确的是？",
        "options": ["承包商可以不服从发包方安全管理", "必须服从统一协调管理并签订安全协议", "发包方不承担任何监督责任"],
        "answer": "必须服从统一协调管理并签订安全协议"
    },
    {
        "q": "从业人员在作业过程中发现直接危及人身安全的紧急情况时，有权采取什么行动？",
        "options": ["盲目坚持继续作业", "停止作业或者在采取可能的应急措施后撤离作业场所", "自行隐瞒"],
        "answer": "停止作业或者在采取可能的应急措施后撤离作业场所"
    },
    {
        "q": "IWAY 准则中关于用工的红线是什么？",
        "options": ["可以使用童工", "严禁使用童工，必须提供有效身份证件及工伤保险", "无所谓身份证件"],
        "answer": "严禁使用童工，必须提供有效身份证件及工伤保险"
    },
    {
        "q": "承包商/外包员工在厂区内每周工作时间达到或超过多少小时必须真实打卡？",
        "options": ["10小时", "18小时", "40小时"],
        "answer": "18小时"
    },
    {
        "q": "作业产生的废油漆桶属于哪类废弃物？",
        "options": ["一般生活垃圾", "危险废弃物（危废）", "建筑垃圾"],
        "answer": "危险废弃物（危废）"
    },
    {
        "q": "发生任何安全、环保事故（无论大小）或发现严重隐患，应当怎么做？",
        "options": ["隐瞒不报", "立即停止作业并第一时间向厂区现场负责人报告", "私下处理"],
        "answer": "立即停止作业并第一时间向厂区现场负责人报告"
    },
    {
        "q": "高处作业时，安全带的正确悬挂方式是？",
        "options": ["低挂高用", "高挂低用", "随意挂在脚手架上"],
        "answer": "高挂低用"
    },
    {
        "q": "引入厂区使用的新化学品，必须提前向 EHS 部门报备并附带什么文件？",
        "options": ["产品说明书广告", "最新的 SDS（安全数据表）", "发票"],
        "answer": "最新的 SDS（安全数据表）"
    },
    {
        "q": "承包商发放给现场作业人员的实际薪资（含加班费）不得低于什么标准？",
        "options": ["当地法定最低工资标准", "随意商定标准", "行业平均标准的一半"],
        "answer": "当地法定最低工资标准"
    },
    {
        "q": "动火作业前必须向 EHS 部门申请并取得什么许可？",
        "options": ["施工许可证", "危险作业许可证（动火证）", "出门证"],
        "answer": "危险作业许可证（动火证）"
    },
    {
        "q": "消防器材周围有什么明确要求？",
        "options": ["可以堆放杂物", "严禁遮挡、圈占消防器材", "可以当凳子坐"],
        "answer": "严禁遮挡、圈占消防器材"
    },
    {
        "q": "从业人员发现事故隐患或者其他不安全因素，应当向谁报告？",
        "options": ["现场安全生产管理人员或者本单位负责人", "不用理会", "发朋友圈"],
        "answer": "现场安全生产管理人员或者本单位负责人"
    },
    {
        "q": "低压电工或临时用电作业人员必须具备什么证件？",
        "options": ["电工特种作业操作证", "毕业证", "健康证"],
        "answer": "电工特种作业操作证"
    },
    {
        "q": "承包商员工是否可以私自将废弃物倒在厂区角落或混入生活垃圾？",
        "options": ["可以", "严禁私自倾倒或混入生活垃圾", "看情况"],
        "answer": "严禁私自倾倒或混入生活垃圾"
    }
]

if "random_questions" not in st.session_state:
    st.session_state.random_questions = random.sample(QUESTION_BANK, 3)

# ================= 辅助函数 =================
def image_to_base64(img_bytes):
    return base64.b64encode(img_bytes).decode("utf-8")

def canvas_to_bytes(image_data):
    if image_data is not None:
        try:
            img = Image.fromarray(image_data.astype("uint8"), "RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            buffered = io.BytesIO()
            bg.save(buffered, format="PNG")
            return buffered.getvalue()
        except Exception:
            return None
    return None

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

def get_font_path():
    font_filename = "NotoSansSC-Regular.ttf"
    if os.path.exists(font_filename):
        return font_filename
        
    possible_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\simhei.ttf"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    try:
        font_url = "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC-Regular.ttf"
        urllib.request.urlretrieve(font_url, font_filename)
        if os.path.exists(font_filename):
            return font_filename
    except Exception:
        pass
        
    return None

# ================= 核心模块：生成独立 PDF =================
def generate_viron_pdf(rec):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    
    font_path = get_font_path()
    if not font_path:
        return None 
            
    pdf.add_font("CustomChinese", "", font_path)
    pdf.set_font("CustomChinese", size=10)
    
    pdf.set_font("CustomChinese", size=16)
    pdf.cell(190, 8, "慧瑞环保涂料(上海)有限公司", ln=True, align="C")
    pdf.set_font("CustomChinese", size=18)
    pdf.cell(190, 10, "承包商EHS入厂培训记录", ln=True, align="C")
    pdf.set_font("CustomChinese", size=10)
    pdf.cell(190, 6, f"NO.: {rec['记录编号']}", ln=True, align="R")
    
    col_w = [30, 65, 30, 65]
    pdf.cell(col_w[0], 9, "培训主题", border=1, align="C")
    pdf.cell(col_w[1], 9, f"{rec['作业项目'][:14]}", border=1, align="C")
    pdf.cell(col_w[2], 9, "培训目的", border=1, align="C")
    pdf.cell(col_w[3], 9, "承包商安全培训，避免安全事故", border=1, ln=True, align="C")
    
    pdf.cell(col_w[0], 9, "培训时间", border=1, align="C")
    pdf.cell(col_w[1], 9, rec["培训日期"], border=1, align="C")
    pdf.cell(col_w[2], 9, "培训地点", border=1, align="C")
    pdf.cell(col_w[3], 9, rec["培训地点"], border=1, ln=True, align="C")
    
    pdf.cell(col_w[0], 9, "培训对象", border=1, align="C")
    pdf.cell(col_w[1], 9, rec["承包商公司"][:14], border=1, align="C")
    pdf.cell(col_w[2], 9, "主讲人", border=1, align="C")
    pdf.cell(col_w[3], 9, rec["主讲人"], border=1, ln=True, align="C")
    
    pdf.cell(col_w[0], 20, "参训人员信息", border=1, align="C")
    y_info = pdf.get_y()
    pdf.cell(160, 20, "", border=1, ln=True)
    pdf.set_xy(10 + col_w[0] + 3, y_info + 2)
    pdf.set_font("CustomChinese", size=8.5)
    pdf.cell(150, 4, f"参训人员：{rec['参训人员名单']}", ln=True)
    pdf.set_x(10 + col_w[0] + 3)
    pdf.cell(150, 4, f"身份证号：{rec['身份证号列表']}", ln=True)
    pdf.set_x(10 + col_w[0] + 3)
    pdf.cell(150, 4, f"负责人电话：{rec['施工负责人电话']} | 作业类别：{rec['作业类别']}", ln=True)
    pdf.set_x(10 + col_w[0] + 3)
    pdf.cell(150, 4, f"特种作业证号：{rec['特种作业证号']}", ln=True)
    
    pdf.set_font("CustomChinese", size=10)
    pdf.cell(30, 24, "参训人员签字", border=1, align="C")
    y_sign_box = pdf.get_y()
    pdf.cell(160, 24, "", border=1, ln=True)
    
    sigs = rec.get("签名Bytes列表", [])
    if not sigs and "签名Bytes列表_b64" in rec:
        sigs = [base64.b64decode(b) for b in rec["签名Bytes列表_b64"]]

    if sigs:
        sx = 43
        sy = y_sign_box + 2
        for i, sig_b in enumerate(sigs[:8]):
            try:
                sig_io = io.BytesIO(sig_b)
                if i == 4:
                    sx = 43
                    sy = y_sign_box + 13
                pdf.image(sig_io, x=sx, y=sy, w=35, h=10)
            except Exception:
                pass
            sx += 38
            
    pdf.set_font("CustomChinese", size=11)
    pdf.cell(190, 8, "培训内容记录", border=1, ln=True, align="C")
    
    pdf.set_font("CustomChinese", size=8)
    clauses = [
        "1. 【安全生产法法定要求】：严格执行《安全生产法》第30条（特种作业人员持证上岗）、第43条（危险作业现场安全管理与专人监护）、第49条（遵守安全管理协议与发包方统一协调管理）。从业人员依法享有知情权、紧急避险权、拒绝违章指挥权，必须履行隐患排查报告与遵章守纪义务。",
        "2. 【资质与用工红线 (IWAY G6.1 & G6.2)】：所有入场人员必须提供真实有效身份证件，严禁使用童工或违规借用证件。承包商必须为所有进场人员足额投保覆盖职业病及伤残/死亡的工伤保险或商业意外险，未办妥保险严禁入场施工作业。",
        "3. 【现场考勤红线 (IWAY G5.1) 与薪资合规 (G5.8)】：凡在厂区内每周工作时间累计达18小时以上的承包商/外包员工，必须按规定纳入本厂电子考勤系统进行真实考勤打卡，严禁瞒报、漏报工时；现场薪资与加班费发放不得低于当地法定最低工资标准。",
        "4. 【危险作业许可管理】：严禁无证、超期或假证进行动火、临时用电、高处（≥2米）及有限空间作业。涉及危险作业必须提前向厂区 EHS 部门申报并获批《危险作业许可证》，落实安全交底、气体检测及专人全过程监护。",
        "5. 【劳动防护用品 (PPE) 规范】：所有入场人员必须规范穿戴反光背心、安全帽、符合标准的安全鞋。高处作业必须正确系挂双大钩安全带（做到高挂低用），特种劳保用品严禁流于形式。",
        "6. 【消防安全与化学品管控】：厂区内全域严禁吸烟（除指定吸烟区外），严禁私自动用明火或遮挡、圈占消防器材。引入厂区使用的任何化学品必须提前报备并附带最新 SDS（安全数据表）, 落实防泄漏措施。",
        "7. 【危险废弃物合规处置】：施工作业中产生的废机油、废油漆桶、含油抹布、废化学品包装物等属于危险废弃物，必须分类收集并交由厂区指定的危废暂存点规范处置，严禁私自倾倒、掩埋或混入普通生活垃圾。",
        "8. 【事故应急与隐患报告机制】：发生任何安全、环境事故（无论大小）或发现严重安全隐患，现场人员必须立即停止作业，并在第一时间向慧瑞现场负责人及 EHS 部门报告，严禁瞒报、谎报或拖延不报。"
    ]
    combined_text = "\n".join(clauses)
    pdf.multi_cell(190, 4.5, combined_text, border=1, align="L")
    
    certs = rec.get("证照Bytes列表", [])
    if not certs and "证照图片列表_b64" in rec:
        certs = [(name, base64.b64decode(b)) for name, b in rec["证照图片列表_b64"]]

    if certs:
        y_cert = pdf.get_y()
        pdf.cell(190, 32, "", border=1, ln=True)
        pdf.set_xy(12, y_cert + 2)
        pdf.set_font("CustomChinese", size=9)
        pdf.cell(180, 5, "附：特种作业操作证照核验存档（人证合一）：", ln=True)
        x_offset = 14
        for _, cbytes in certs[:4]:
            try:
                cert_io = io.BytesIO(cbytes)
                pdf.image(cert_io, x=x_offset, y=y_cert + 8, h=20)
            except Exception:
                pass
            x_offset += 44
        pdf.set_y(y_cert + 32)
        
    pdf.set_font("CustomChinese", size=9.5)
    pdf.cell(30, 7, "考核方式", border=1, align="C")
    pdf.cell(160, 7, f"  [√] {rec['考核方式']}", border=1, ln=True)
    
    eval_text = (
        f"培训评估：[√] {rec['培训评估']}\n\n"
        f"                                              签署日期：{rec['签署日期']}          评价人：{rec['主讲人']}"
    )
    pdf.multi_cell(190, 6, eval_text, border=1)
    
    return bytes(pdf.output())

# ================= 1. 密码登录拦截 (密码: 8888) =================
try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_AVAILABLE = True
except ImportError:
    CANVAS_AVAILABLE = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center;'>🛡️ 慧瑞环保涂料(上海)有限公司<br>承包商入场安全培训系统</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; font-size: 13px;'>系统为内部合规平台，严禁商业用途 | 开发者：陈野菲</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            pwd = st.text_input("🔑 请输入系统访问密码", type="password", placeholder="输入密码进入系统")
            submitted = st.form_submit_button("登 录", use_container_width=True)
            if submitted:
                if pwd == "8888":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ 密码错误，请重新输入！")
    st.stop()

# ================= 顶部标题栏 =================
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("🛡️ 慧瑞环保涂料(上海)有限公司 - 承包商EHS入厂培训系统")
    st.caption("系统为内部合规平台，严禁商业用途 | 开发者：陈野菲")
with col_logout:
    if st.button("🔒 退出登录"):
        st.session_state.authenticated = False
        st.rerun()

# ================= 侧边栏：手机扫码填写端 =================
with st.sidebar:
    st.markdown("### 📱 手机扫码填写端")
    st.write("请让承包商员工扫描下方二维码，直接在手机上填写并手写签字：")
    
    default_url = "https://contractor-ehs-training.streamlit.app"
    target_url = st.text_input("输入手机访问的网址/局域网IP：", value=default_url, placeholder="例如: http://192.168.1.100:8501")
    
    if target_url:
        qr_bytes = generate_qr_code(target_url)
        st.image(qr_bytes, caption="微信/相机扫码直达填表", width=220)
    
    st.info("💡 **提示**：手机填表时，请确保手机和电脑连在同一个 Wi-Fi（局域网）下，并将 IP 改为您电脑的局域网 IP 地址。")

tab1, tab2 = st.tabs(["📝 入场培训、多人员信息、多重签名与随机抽题", "🗂️ 培训台账与独立 PDF 导出"])

# ================= TAB 1: 培训与签到主流程 =================
with tab1:
    st.subheader("一、 入场施工项目与多人员基本信息")
    c1, c2, c3 = st.columns(3)
    with c1:
        training_date = st.date_input("📅 培训/入场日期", datetime.today())
        contractor_company = st.text_input("🏢 承包商公司名称 *", placeholder="例如：上海XX机电安装工程有限公司")
        trainer = st.text_input("👨‍🏫 主讲人", value="陈野菲")
    with c2:
        project_name = st.text_input("🛠️ 作业项目名称 *", placeholder="例如：车间管道改造 / 1号厂房照明维保")
        work_location = st.selectbox(
            "📍 培训/作业地点 *", 
            ["1号厂房（仓库及办公区）", "生产车间", "研发实验室", "危废暂存间/化学品库", "厂区公共外围/配电房", "其他区域"]
        )
        worker_names = st.text_input("👷 参训施工人员姓名 *（多人填写，用逗号隔开）", placeholder="例如：张三, 李四, 王五")
    with c3:
        leader_phone = st.text_input("📱 施工负责人电话 *", max_chars=11, placeholder="请输入现场负责人手机号")
        ins_confirm = st.checkbox("✅ 已核验所有进场员工的工伤保险或商业意外险凭证")

    st.markdown("---")
    st.markdown("##### 🪪 参训人员身份证号登记（可根据人数点击增加选项）")
    if "id_count" not in st.session_state:
        st.session_state.id_count = 1

    col_btn1, _ = st.columns([1, 5])
    with col_btn1:
        if st.button("➕ 增加身份证框"):
            st.session_state.id_count += 1
            st.rerun()
        if st.session_state.id_count > 1 and st.button("➖ 减少一项"):
            st.session_state.id_count -= 1
            st.rerun()

    id_numbers = []
    id_cols = st.columns(min(st.session_state.id_count, 4))
    for i in range(st.session_state.id_count):
        col_idx = i % 4
        with id_cols[col_idx]:
            val = st.text_input(f"身份证号 {i+1} *", max_chars=18, key=f"id_{i}", placeholder=f"第 {i+1} 人身份证")
            if val:
                id_numbers.append(val)

    st.divider()

    st.subheader("二、 作业风险辨识与特种作业证照核验")
    st.info("💡 **法律与厂规要求**：特种作业人员必须经专门安全作业培训，取得相应资格（人证合一），方可上岗作业。")
    
    work_types = st.multiselect(
        "⚠️ 请选择本次施工涉及的作业类别（可多选）*：",
        ["常规一般作业", "⚡ 电工作业（临时用电/配电检修）", "🧗 登高/高处作业（≥2米）", "🔥 动火作业（焊接/切割/打磨等）", "🕳️ 有限空间作业", "🧪 涉及化学品使用"],
        default=["常规一般作业"]
    )

    need_electric = "⚡ 电工作业（临时用电/配电检修）" in work_types
    need_height = "🧗 登高/高处作业（≥2米）" in work_types
    need_hotwork = "🔥 动火作业（焊接/切割/打磨等）" in work_types
    is_special = need_electric or need_height or need_hotwork

    cert_number = "不涉及"
    cert_b64_list = []
    cert_bytes_list = []

    if is_special:
        st.warning("🚨 **检测到特种或危险作业！必须填写操作证编号并上传清晰证照图片。**")
        sc1, sc2 = st.columns([1, 2])
        with sc1:
            cert_number = st.text_input("📑 特种作业操作证编号 *", placeholder="请输入特种作业证号")
            permit_ack = st.checkbox("✅ 我已知晓：作业前必须单独办理《危险作业许可证》")
        with sc2:
            uploaded_certs = st.file_uploader(
                "📷 请上传特种作业操作证照片（可上传多张）*",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True
            )
            if uploaded_certs:
                cols_img = st.columns(len(uploaded_certs))
                for idx, file in enumerate(uploaded_certs):
                    bytes_data = file.getvalue()
                    cert_b64_list.append((file.name, image_to_base64(bytes_data)))
                    cert_bytes_list.append((file.name, bytes_data))
                    with cols_img[idx]:
                        st.image(bytes_data, caption=file.name, width=150)

    st.divider()

    st.subheader("三、 入场安全培训核心内容")
    with st.expander("📖 点击展开查看完整的 EHS 培训法律条文与厂区合规细则", expanded=True):
        st.markdown("""
        1. **安全生产法法定责任**：严格执行第30条（特种作业持证上岗）、第43条（危险作业现场专人管理）、第49条（遵守安全管理协议与发包方统一协调管理）。从业人员享有知情权、紧急避险权和拒绝违章指挥权，必须履行隐患排查报告与遵章守纪义务。
        2. **资质与用工红线 (IWAY G6.1 & G6.2)**：所有入场人员必须提供真实有效身份证件，严禁使用童工或违规借用证件。承包商必须为所有进场人员足额投保覆盖职业病及伤残/死亡的工伤保险或商业意外险，未办妥保险严禁入场施工作业。
        3. **现场考勤红线 (IWAY G5.1) 与薪资合规 (G5.8)**：凡在厂区内每周工作时间累计达18小时以上的承包商/外包员工，必须按规定纳入本厂电子考勤系统进行真实考勤打卡，严禁瞒报、漏报工时；现场薪资与加班费发放不得低于当地法定最低工资标准。
        4. **危险作业许可管理**：严禁无证、超期或假证进行动火、临时用电、高处（≥2米）及有限空间作业。涉及危险作业必须提前向厂区 EHS 部门申报并获批《危险作业许可证》，落实安全交底、气体检测及专人全过程监护。
        5. **劳动防护用品 (PPE) 规范**：所有入场人员必须规范穿戴反光背心、安全帽、符合标准的安全鞋。高处作业必须正确系挂双大钩安全带（做到高挂低用），特种劳保用品严禁流于形式。
        6. **消防安全与化学品管控**：厂区内全域严禁吸烟（除指定吸烟区外），严禁私自动用明火或遮挡、圈占消防器材。引入厂区使用的任何化学品必须提前报备并附带最新 SDS（安全数据表）, 落实防泄漏措施。
        7. **危险废弃物合规处置**：施工作业中产生的废机油、废油漆桶、含油抹布、废化学品包装物等属于危险废弃物，必须分类收集并交由厂区指定的危废暂存点规范处置，严禁私自倾倒、掩埋或混入普通生活垃圾。
        8. **事故应急与隐患报告机制**：发生任何安全、环境事故（无论大小）或发现严重安全隐患，现场人员必须立即停止作业，并在第一时间向慧瑞现场负责人及 EHS 部门报告，严禁瞒报、谎报或拖延不报。
        """)

    agree_terms = st.checkbox("☑️ 本人已完整阅读并理解上述 EHS 培训全部要求。")

    st.divider()

    st.subheader("四、 现场考核确认与多人数手写签名（支持最多 8 人）")
    
    st.markdown("##### 📝 现场随机考核（系统从 20 道题库中随机抽取 3 题，全部答对方可提交）")
    
    user_answers = []
    for idx, q_item in enumerate(st.session_state.random_questions):
        ans = st.radio(
            f"**第 {idx+1} 题**：{q_item['q']}",
            q_item['options'],
            index=None,
            key=f"rand_q_{idx}"
        )
        user_answers.append((ans, q_item['answer']))

    st.markdown("---")
    
    col_exam_extra, col_sign_area = st.columns([1, 1])
    with col_exam_extra:
        exam_methods = st.multiselect("考核方式记录", ["现场提问", "实际操作", "试卷", "其他"], default=["现场提问"])
        eval_result = st.radio(
            "培训评估结论：",
            [
                "通过培训考核，参训员工已理解本次培训内容，并按照相关要求来执行，已达到本次培训目的。",
                "通过培训考核，参训员工未完全理解本次培训内容，应继续加强培训，才能达到本次培训目的。"
            ]
        )
        sign_date = st.date_input("📅 签署日期", datetime.today())
        
        if st.button("🔄 刷新随机考题"):
            st.session_state.random_questions = random.sample(QUESTION_BANK, 3)
            st.rerun()

    with col_sign_area:
        st.markdown("##### ✍️ 参训人员手写签名")
        
        sig_tabs = st.tabs([f"签字 {i}" for i in range(1, 9)])
        canvases = []
        for i, tab in enumerate(sig_tabs):
            with tab:
                st.caption(f"第 {i+1} 位施工人员签字：")
                cv = st_canvas(
                    fill_color="rgba(255, 255, 255, 1)", 
                    stroke_width=3, 
                    stroke_color="#000000", 
                    background_color="#FFFFFF", 
                    height=110, 
                    width=320, 
                    drawing_mode="freedraw", 
                    key=f"sig_{i+1}", 
                    return_image_data=True
                )
                canvases.append(cv)

    st.divider()

    if st.button("✅ 提交安全培训记录", type="primary", use_container_width=True):
        all_correct = True
        for u_ans, correct_ans in user_answers:
            if u_ans != correct_ans:
                all_correct = False
                break

        if not contractor_company or not project_name or not worker_names or not leader_phone:
            st.error("❌ 请完整填写【第一部分】中的所有必填项！")
        elif len(id_numbers) == 0:
            st.error("❌ 请至少填写一个参训人员的身份证号！")
        elif not ins_confirm:
            st.error("❌ 必须核验工伤或商业保险后方可入场！")
        elif is_special and (not cert_number or len(cert_bytes_list) == 0):
            st.error("❌ 特种作业必须填写证号并上传证照！")
        elif not agree_terms:
            st.error("❌ 请先勾选确认已阅读并理解要求！")
        elif not all_correct:
            st.error("❌ 随机考核题目回答有误，请核对后重新答题！（提示：可点击刷新考题或仔细核对题目选项）")
        elif CANVAS_AVAILABLE and (canvases[0].image_data is None or len(canvases[0].json_data.get("objects", [])) == 0):
            st.error("❌ 至少需要【签字 1】完成首位人员的手写签名！")
        else:
            sig_bytes_list = []
            if CANVAS_AVAILABLE:
                for cv in canvases:
                    if cv.image_data is not None and len(cv.json_data.get("objects", [])) > 0:
                        b = canvas_to_bytes(cv.image_data)
                        if b:
                            sig_bytes_list.append(b)
            
            first_sig_b = sig_bytes_list[0] if sig_bytes_list else None
            first_sig_b64 = image_to_base64(first_sig_b) if first_sig_b else ""

            record = {
                "记录编号": f"TR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "培训日期": training_date.strftime("%Y年%m月%d日"),
                "签署日期": sign_date.strftime("%Y年%m月%d日"),
                "培训地点": work_location,
                "承包商公司": contractor_company,
                "作业项目": project_name,
                "主讲人": trainer,
                "参训人员名单": worker_names,
                "身份证号列表": "、".join(id_numbers),
                "施工负责人电话": leader_phone,
                "作业类别": "、".join(work_types),
                "特种作业证号": cert_number,
                "证照数量": len(cert_bytes_list),
                "证照图片列表": cert_b64_list,
                "证照Bytes列表": cert_bytes_list,
                "签名Bytes列表": sig_bytes_list,
                "签名图片B64": first_sig_b64,
                "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.session_state.records.append(record)
            save_records(st.session_state.records)
            
            st.session_state.random_questions = random.sample(QUESTION_BANK, 3)
            st.success("🎉 培训记录提交成功！数据已持久化保存至后台并可在台账与 PDF 中查看。")

# ================= TAB 2: 台账与 PDF =================
with tab2:
    st.subheader("🗂️ 已完成培训人员台账记录")
    
    st.session_state.records = load_records()
    
    # 显眼的管理操作：清空台账按钮（直接平铺显示在表格上方）
    if len(st.session_state.records) > 0:
        st.markdown("---")
        col_c1, col_c2 = st.columns([2, 5])
        with col_c1:
            if st.button("🗑️ 清空所有历史台账记录（归0）", type="primary", use_container_width=True):
                st.session_state.records = []
                save_records([])
                st.success("✅ 所有台账记录已成功清空并归零！")
                st.rerun()
        with col_c2:
            st.warning("⚠️ 提示：点击左侧按钮将永久清空后台所有历史台账数据，建议清空前先点下方按钮导出 Excel 备份！")
        st.markdown("---")

    if len(st.session_state.records) == 0:
        st.info("暂无签到记录，请先在第一个标签页完成提交。")
    else:
        df_display = pd.DataFrame([
            {k: v for k, v in r.items() if k not in ["证照图片列表", "证照Bytes列表", "签名图片B64", "签名Bytes列表", "证照图片列表_b64", "签名Bytes列表_b64"]}
            for r in st.session_state.records
        ])
        st.dataframe(df_display, use_container_width=True)

        csv_data = df_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 导出培训台账 (Excel CSV)",
            data=csv_data,
            file_name=f"慧瑞承包商安全培训台账_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        st.divider()
        st.subheader("📄 导出独立 PDF 档案")
        
        selected_idx = st.selectbox(
            "选择要导出 PDF 的记录：",
            range(len(st.session_state.records)),
            format_func=lambda i: f"{st.session_state.records[i]['记录编号']} - {st.session_state.records[i]['承包商公司']} - {st.session_state.records[i]['参训人员名单']}"
        )
        
        rec = st.session_state.records[selected_idx]

        pdf_bytes = generate_viron_pdf(rec)
        if pdf_bytes:
            st.download_button(
                label="📄 一键下载独立 PDF 签到表（含多人手写签名与证照）",
                data=pdf_bytes,
                file_name=f"TrainingRecord_{rec['承包商公司']}_{rec['记录编号']}.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("⚠️ 未能加载系统字体，PDF 下载暂不可用。")
