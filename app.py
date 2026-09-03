import streamlit as st
import pandas as pd
import datetime
import io
import zipfile
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="承包商入场安全校验", layout="centered")

# 侧边栏：手机端/网页端扫码填报支持
with st.sidebar:
    st.header("📱 扫码/网页端填报")
    st.write("承包商可通过手机扫描二维码或直接打开链接进行填报与资料上传。")
    
    app_url = st.text_input("本应用公网链接 (URL):", value="https://contractor-safety-check.streamlit.app/")
    
    if app_url:
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={app_url}"
        st.image(qr_api_url, caption="手机相机/支付宝/浏览器扫码", width=200)

st.title("👷 承包商入场及高危作业安全校验与承诺书")
st.write("依据《安全生产法》及 **宜家供应商IWAY6.0合规风险与管控要求**，请在入场前逐项核实、上传证明并签字。内部管理工具，严禁商业用途")

# 1. 前置检查项 (已按最新需求修改)
st.subheader("1. 承包商资信与资质审核 (入场必选)")
q1_1 = st.checkbox("1）企业资质类资料--基础证照：有效的营业执照")
q1_2 = st.checkbox("2）提交承包商安全协议（甲乙双方盖章）")
q1_3 = st.checkbox("3）保险证明：施工人员工伤保险缴纳证明，或商业保险证明")

# 2. 现场人员资质与基础保障 (已按最新需求修改)
st.subheader("2. 现场人员资质与基础保障 (入场必选)")
q2_1 = st.checkbox("1）【培训】提供承包商员工入厂安全培训记录（注：需在现场完成并确认）。")
q2_2 = st.checkbox("2）提供承包商施工人员工伤保险缴纳证明或意外伤害保险缴纳证明。")
q2_3 = st.checkbox("3）作业人员的身份证复印件。")

st.subheader("3. 特种/高危作业特批 (按需填写，无则留空)")
q3_1 = st.checkbox("【动火作业】如涉及动火或切割产生明火作业，申请报备。")
id_3_1 = st.text_input("备选特种作业人员 (动火) 身份证号：", key="id_fire")

q3_2 = st.checkbox("【电工作业】如涉及电工 (低压作业), 申请报备。")
id_3_2 = st.text_input("备选特种作业人员 (电工) 身份证号：", key="id_elec")

q3_3 = st.checkbox("【登高作业】如涉及登高作业，申请报备。")
id_3_3 = st.text_input("备选特种作业人员 (登高) 身份证号：", key="id_high")

# 4. 文件/证件上传区域 (保持不变)
st.subheader("4. 相关证明材料上传")
st.write("请上传营业执照、工伤保险证明、特种作业操作证等相关证件照片或扫描件（支持多选）。")
uploaded_files = st.file_uploader(
    "上传凭证/证件文件", 
    type=["png", "jpg", "jpeg", "pdf"], 
    accept_multiple_files=True
)

st.subheader("5. 自我承诺与声明")
st.info("本人郑重承诺：以上勾选的核验项及上传的资料均真实有效，绝无弄虚作假。若因未落实安全防范措施而导致相关事故，愿承担相应的管理责任。")

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

# 提交并生成最终统一报告
if st.button("📁 确认无误，生成完整校验报告并打包下载"):
    # 加入了 q2_3 身份证复印件的必选校验
    base_passed = q1_1 and q1_2 and q1_3 and q2_1 and q2_2 and q2_3
    
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
        
        # 更新了后台生成的 CSV 表格字段，使其与最新的题目匹配
        data = {
            "安全核验管控项目": [
                "企业资质 - 有效的营业执照", 
                "企业资质 - 承包商安全协议", 
                "企业资质 - 保险缴纳证明", 
                "人员资质 - 入厂安全培训记录", 
                "人员资质 - 施工人员保险证明", 
                "人员资质 - 身份证复印件",
                "特种作业报备：动火作业", 
                "特种作业报备：电工作业", 
                "特种作业报备：登高作业"
            ],
            "现场确认结果": [
                "合格 / 已提供", 
                "合格 / 已签订", 
                "合格 / 已提供", 
                "合格 / 现场已确认", 
                "合格 / 已提供", 
                "合格 / 已提供",
                status_3_1, 
                status_3_2, 
                status_3_3
            ]
        }
        
        df = pd.DataFrame(data)
        
        # === 页面展示区 ===
        st.markdown("### 📋 承包商入场安全核验清单汇总")
        st.table(df)
        
        if uploaded_files:
            st.markdown(f"**📎 已上传证明文件数量：** {len(uploaded_files)} 个")
        
        st.markdown("---")
        st.markdown(f"**📝 声明承诺人：** {checker_name}")
        st.markdown(f"**📅 承诺生效日期：** {commit_date}")
        st.markdown("**✍️ 现场手写签名确认：**")
        
        signature_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        st.image(signature_img, width=400, caption=f"承诺人：{checker_name}")
        
        # === 内存中动态打包 ZIP ===
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. 写入 CSV 表格数据
            csv_bytes = df.to_csv(index=False).encode('utf-8-sig')
            csv_filename = f"承包商入场核验_{checker_name}_{commit_date}.csv"
            zip_file.writestr(csv_filename, csv_bytes)
            
            # 2. 写入手写签名图片
            img_byte_arr = io.BytesIO()
            signature_img.save(img_byte_arr, format='PNG')
            img_filename = f"签名_{checker_name}_{commit_date}.png"
            zip_file.writestr(img_filename, img_byte_arr.getvalue())
            
            # 3. 写入承包商上传的证明文件
            if uploaded_files:
                for idx, uploaded_file in enumerate(uploaded_files):
                    file_ext = uploaded_file.name.split('.')[-1]
                    safe_file_name = f"证明文件_{idx+1}_{checker_name}_{commit_date}.{file_ext}"
                    zip_file.writestr(safe_file_name, uploaded_file.getvalue())
            
        zip_buffer.seek(0)
        
        st.balloons() 
        st.success("🎉 合规档案与证件已全部打包完毕！点击下方按钮即可一键下载：")
        
        zip_filename = f"承包商安全合规档案及证件_{checker_name}_{commit_date}.zip"
        st.download_button(
            label="📥 下载本场完整合规档案 (含清单、签名与上传证件)",
            data=zip_buffer,
            file_name=zip_filename,
            mime="application/zip"
        )
