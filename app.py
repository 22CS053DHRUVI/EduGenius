import streamlit as st
import EduGenius_Squad as squad
import tempfile
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import re

# --- PDF and Parsing Functions (same as before) ---
def save_exam_paper_to_pdf(questions, filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>CHAROTAR UNIVERSITY OF SCIENCE AND TECHNOLOGY</b>", styles['Title']))
    elements.append(Paragraph("DEPARTMENT OF COMPUTER ENGINEERING<br/>B.Tech (CE): 7th semester<br/>MACHINE LEARNING [CE473]", styles['Heading2']))
    elements.append(Paragraph("Marks: 70 &nbsp;&nbsp;&nbsp;&nbsp; Duration: 225 mins.", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Section 1
    elements.append(Paragraph("<b>Section - I</b>", styles['Heading2']))
    elements.append(Paragraph("Answer all the questions.", styles['Normal']))
    elements.append(Spacer(1, 8))

    for q in questions:
        # Draw question number in a box
        q_num = Table([[str(q['number'])]], colWidths=20, rowHeights=20)
        q_num.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        # Question text and marks
        q_text = Paragraph(f"{q['text']}", styles['Normal'])
        q_marks = Paragraph(f"({q['marks']})", styles['Normal'])
        # Layout: [number][question][marks]
        row = [q_num, q_text, q_marks]
        t = Table([row], colWidths=[25, 400, 40])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ]))
        elements.append(t)
        # MCQ options
        if q['type'] == 'mcq':
            opt_row = []
            for i, opt in enumerate(q['options']):
                opt_row.append(f"{i+1}) {opt}")
            opt_table = Table([opt_row], colWidths=[120]*len(opt_row))
            elements.append(opt_table)
        elements.append(Spacer(1, 8))

    doc.build(elements)

def parse_ai_exam_output(ai_output):
    questions = []
    blocks = re.split(r'\n(?=\d+\.)', ai_output.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if not lines or not re.match(r'\d+\.', lines[0]):
            continue
        number = int(lines[0].split('.')[0])
        text = lines[0][lines[0].find('.')+1:].strip()
        options = []
        marks = 1
        qtype = 'short'
        for line in lines[1:]:
            opt_match = re.match(r'\d+\)\s*(.+)', line)
            if opt_match:
                options.append(opt_match.group(1).strip())
            elif re.match(r'\(\d+\)', line.strip()):
                marks = int(re.findall(r'\d+', line)[0])
            else:
                text += ' ' + line.strip()
        if options:
            qtype = 'mcq'
        questions.append({
            'number': number,
            'text': text,
            'type': qtype,
            'options': options,
            'marks': marks
        })
    return questions

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Logo_of_Charotar_University_of_Science_and_Technology.png/320px-Logo_of_Charotar_University_of_Science_and_Technology.png", width=120)
    st.markdown("## EduGenius Squad")
    st.markdown("Generate academic content (notes, assignments, slides, practice papers) from PDFs or URLs using AI.")
    st.markdown("---")
    st.info("**Tip:** For best results, use clear, well-structured source material.")
    st.markdown("---")
    st.caption("Made with ❤️ by your team")

st.title("📚 EduGenius Squad - Academic Content Generator")

# Content type
content_type = st.selectbox(
    "What content would you like to generate?",
    ["Document", "Assignment", "PowerPoint", "Practice Paper"]
)

# Content source
with st.expander("Choose content source(s):", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
    with col2:
        url = st.text_input("Enter educational URL")

# For Practice Paper, select type
paper_type = None
if content_type == "Practice Paper":
    paper_type = st.radio("Paper type:", ["Internal (30 marks)", "External (70 marks)"], horizontal=True)

# Generate button
if st.button("🚀 Generate", use_container_width=True):
    with st.spinner("Generating, please wait..."):
        content = ""
        # Handle PDF
        if pdf_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_file.read())
                tmp_path = tmp.name
            content += squad.extract_text_from_pdf(tmp_path) + "\n"
            os.unlink(tmp_path)
        # Handle URL
        if url.strip():
            content += squad.fetch_text_from_url(url.strip()) + "\n"
        if not content.strip():
            st.error("❌ No valid content retrieved from selected sources.")
        else:
            try:
                if content_type == "Document":
                    prompt = squad.build_agent_prompt("study notes", content)
                    response = squad.doc_agent.run(prompt)
                    result = response.content.strip() if response and hasattr(response, "content") and response.content else ""
                    if result:
                        st.success("✅ Notes generated! Preview below:")
                        st.code(result[:1000] + ("..." if len(result) > 1000 else ""), language="markdown")
                        squad.save_text_to_pdf(result, "output.pdf")
                        with open("output.pdf", "rb") as f:
                            st.download_button("Download Notes PDF", f, file_name="output.pdf")
                    else:
                        st.error("❌ Failed to generate notes.")
                elif content_type == "Assignment":
                    prompt = squad.build_agent_prompt("assignment", content)
                    response = squad.assign_agent.run(prompt)
                    result = response.content.strip() if response and hasattr(response, "content") and response.content else ""
                    if result:
                        st.success("✅ Assignment generated! Preview below:")
                        st.code(result[:1000] + ("..." if len(result) > 1000 else ""), language="markdown")
                        squad.save_text_to_pdf(result, "Assignment.pdf")
                        with open("Assignment.pdf", "rb") as f:
                            st.download_button("Download Assignment PDF", f, file_name="Assignment.pdf")
                    else:
                        st.error("❌ Failed to generate assignment.")
                elif content_type == "PowerPoint":
                    prompt = squad.build_agent_prompt("ppt content", content)
                    response = squad.ppt_agent.run(prompt)
                    result = response.content.strip() if response and hasattr(response, "content") and response.content else ""
                    if result:
                        st.success("✅ Slides generated! Preview below:")
                        st.code(result[:1000] + ("..." if len(result) > 1000 else ""), language="markdown")
                        bullets = [line.strip("-• ") for line in result.split("\n") if line.strip()]
                        squad.create_ppt_from_bullets("Generated Slides", bullets, "output.pptx")
                        with open("output.pptx", "rb") as f:
                            st.download_button("Download PowerPoint", f, file_name="output.pptx")
                    else:
                        st.error("❌ Failed to generate slides.")
                elif content_type == "Practice Paper":
                    note = "Generate a 30 marks paper." if paper_type == "Internal (30 marks)" else "Generate a 70 marks paper."
                    prompt = f"{note}\n\n{squad.build_agent_prompt('practice paper', content)}"
                    response = squad.paper_agent.run(prompt)
                    result = response.content.strip() if response and hasattr(response, "content") and response.content else ""
                    if result:
                        questions = parse_ai_exam_output(result)
                        st.success("✅ Practice Paper generated! Preview below:")
                        for q in questions[:5]:
                            st.markdown(f"**Q{q['number']} ({q['marks']} marks):** {q['text']}")
                            if q['type'] == 'mcq':
                                st.markdown('  \n'.join([f"{i+1}) {opt}" for i, opt in enumerate(q['options'])]))
                        save_exam_paper_to_pdf(questions, "practice_paper.pdf")
                        with open("practice_paper.pdf", "rb") as f:
                            st.download_button("Download Practice Paper PDF", f, file_name="practice_paper.pdf")
                    else:
                        st.error("❌ Failed to generate paper.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.markdown("---")
st.caption("Made with ❤️ using Streamlit and EduGenius Squad")

