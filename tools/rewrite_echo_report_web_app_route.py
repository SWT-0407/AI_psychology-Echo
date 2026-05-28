from pathlib import Path

from docx import Document


SRC = Path(r"E:\Users\醨\PycharmProjects\PythonProject6\reports\心语Echo项目报告_技术创新强化版.docx")
OUT = Path(r"E:\Users\醨\PycharmProjects\PythonProject6\reports\心语Echo项目报告_Web技术路线版.docx")


def replace_paragraph(doc: Document, old: str, new: str) -> None:
    for paragraph in doc.paragraphs:
        if paragraph.text.strip() == old:
            paragraph.text = new
            return
    raise ValueError(f"Paragraph not found: {old[:80]}")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document(SRC)
    replacements = {
        "项目目前以 Streamlit 为主入口，已经形成心理评测、AI 树洞、虚拟角色陪伴、个人画像、历史记录、可选云同步、本地微调模型和可信心理智能体等模块。系统的核心不是某一个页面，而是“画像中枢”：评测负责识别状态，树洞负责承接真实表达，未完成对话模块负责判断是否应该完成现实沟通，角色陪伴负责延续关系记忆，RAG 负责补充可靠知识，安全模块负责约束边界，所有结果最终都沉淀为可回看、可解释、可更新的动态用户画像。":
        "项目目前已经形成一套浏览器端网页应用，包含心理评测、AI 树洞、虚拟角色陪伴、个人画像、历史记录、可选云同步、本地微调模型和可信心理智能体等模块。系统的核心不是某一个页面，而是“画像中枢”：评测负责识别状态，树洞负责承接真实表达，未完成对话模块负责判断是否应该完成现实沟通，角色陪伴负责延续关系记忆，RAG 负责补充可靠知识，安全模块负责约束边界，所有结果最终都沉淀为可回看、可解释、可更新的动态用户画像。",

        "（一）页面层：以 Streamlit 组织核心功能":
        "（一）Web 应用层：自研网页端交互工作台",

        "项目入口是 main.py。页面路由主要包括首页、心理评测日记、AI 树洞、虚拟角色陪伴和个人画像。首页负责展示用户状态和功能入口；心理评测页负责日记化评估与报告；树洞页负责轻量倾诉；陪伴页负责角色聊天；画像页则让用户查看和管理系统推断出的长期信号。":
        "系统前端采用网页端交互工作台形式组织核心功能，主要包括首页、心理评测日记、AI 树洞、未完成对话、虚拟角色陪伴和个人画像等页面。首页负责展示用户状态和功能入口；心理评测页负责日记化评估与报告；树洞页负责轻量倾诉和未完成表达收集；陪伴页负责角色聊天与关系记忆延续；画像页则让用户查看、确认和管理系统推断出的长期信号。",
    }
    for old, new in replacements.items():
        replace_paragraph(doc, old, new)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
