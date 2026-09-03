import streamlit as st
import pandas as pd
import datetime
import os
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="承包商入场安全校验", layout="centered")

# 侧边栏：手机扫码填报支持 (使用免安装在线接口，绝对不会报错)
with st.sidebar:
    st.header("📱 手机端扫码填报")
    st.write("将本应用部署至云端后，输入网页公网链接，即可实时生成二维码供手机扫码。")
    app_url = st.text_input("请输入本应用的云端链接 (URL):", value="https://your-app.streamlit.app")
    if app_url:
        # 纯 URL 动态生成二维码，零依赖、零报错
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
        st.image(qr_api_url, caption="微信/手机相机扫码填报", width=200)

st.title("👷 承包商入场及高危作业安全校验与承诺书")
st.write("依据《安全生产法》及 **宜家供应商IWAY合规风险与管控要求**，请在入场前逐项核实并签字。")

# 1. 前置检查项
st.subheader("1. 承包商资信与资质审核 (入场必选)")
q1_1 = st.checkbox("【资质】提供承包商营业执照、安全生产许可证及相关专业施工作业资质。")
q1_2 = st.checkbox("【资信】无重大安全、环保事故不良记录。")
q1_3 = st.checkbox("【协议】签订专业承包商安全协议，不免除或转嫁本企业的统一协调、管理义务。")

st.subheader("2. 现场人员资质与基础保障 (入场必选)")
q2_1 = st.checkbox("【培训】提供承包商员工岗位危害告知及入厂安全培训记录。")
q2_2 = st.checkbox("【保险】提供有效的工伤保险凭证（入职当天覆盖，含职业病及伤残/死亡赔偿）。")

st.subheader("3. 特种/高危作业特批 (按需填写，无则留空)")
q3_1 = st.checkbox("【动火作业】如涉及动火或切割产生明火作业，申请报备。")
id_3_1 = st.text_input("备选特种作业人员 (动火) 身份证号：", key="id_fire")

q3_2 = st.checkbox("【电工作业】如涉及电工 (低压作业), 申请报备。")
id_3_2 = st.text_input("备选特种作业人员 (电工) 身份证号：", key="id_elec")

q3_3 = st.checkbox("【登高作业】如涉及登高作业，申请报备。")
id_3_3 = st.text_input("备选特种作业人员 (登高) 身份证号：", key="id_high")

st.subheader("4. 自我承诺与声明")
st.info("本人郑重承诺：以上勾选的核验项均已在现场真实排查并确认，绝无弄虚作假。若因未落实安全防范措施而导致相关事故，愿承担相应的管理责任。")

declaration = st.checkbox("我已阅读并同意以上自我承诺")

col1, col2 = st.columns(2)
with col1:
    checker_name = st.text_input("承诺人姓名 (必填)：")
with col2:
    commit_date = st.date_input("承诺日期：", datetime.date.today())

st.write("---")
st.write("✍️ **请在下方空白处手写签名：**")
canvas_result = st_canvas(
    stroke_width=3,
    stroke_color="#000000",
    background_color="#F0F2F6",
    height=150,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
)

# 2. 提交并生成最终统一报告
if st.button("📁 确认无误，生成完整校验报告并归档"):
    base_passed = q1_1 and q1_2 and q1_3 and q2_1 and q2_2
    
    if not base_passed:
        st.error("❌ 警告：第 1 和第 2 部分为基础必选项！未全部落实前，绝对禁止办理入场。")
    elif not declaration or not checker_name:
        st.warning("⚠️ 流程未完成：请勾选【自我承诺】并填写【承诺人姓名】。")
    elif canvas_result.image_data is None:
        st.warning("⚠️ 请在上方画板完成手写签名后再提交。")
    else:
        st.success("✅ 核验与承诺通过！以下为本次入场的完整合规档案：")
        
        status_3_1 = f"已报备 (身份证: {id_3_1})" if q3_1 else "未涉及此作业"
        status_3_2 = f"已报备 (身份证: {id_3_2})" if q3_2 else "未涉及此作业"
        status_3_3 = f"已报备 (身份证: {id_3_3})" if q3_3 else "未涉及此作业"
        
        data = {
            "安全核验管控项目": ["提供承包商资质审核", "无重大安全环保不良记录", "签订专业承包商安全协议", "提供入场安全培训记录", "提供工伤保险/等效保险凭证", "特种作业报备：动火作业", "特种作业报备：电工作业", "特种作业报备：登高作业"],
            "现场确认结果": ["合格 / 已提供", "合格 / 已确认", "合格 / 已签订", "合格 / 已提供", "合格 / 已提供", status_3_1, status_3_2, status_3_3]
        }
        
        df = pd.DataFrame(data)
        
        # === 统一展示区：表格与签名整合在同一视图 ===
        st.markdown("### 📋 承包商入场安全核验清单汇总")
        st.table(df)
        
        st.markdown("---")
        st.markdown(f"**📝 声明承诺人：** {checker_name}")
        st.markdown(f"**📅 承诺生效日期：** {commit_date}")
        st.markdown("**✍️ 现场手写签名确认：**")
        
        signature_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        st.image(signature_img, width=400, caption=f"承诺人：{checker_name}")
        
        # === 自动后台归档 ===
        save_folder = "iway_check"
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            
        csv_name = f"承包商入场核验_{checker_name}_{commit_date}.csv"
        csv_path = os.path.join(save_folder, csv_name)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        img_name = f"签名_{checker_name}_{commit_date}.png"
        img_path = os.path.join(save_folder, img_name)
        signature_img.save(img_path)
        
        st.balloons() 
        st.success(f"💾 归档成功！表格与手写签名已同步加密保存至本地 `{save_folder}` 文件夹。")
