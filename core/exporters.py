from __future__ import annotations

from io import BytesIO

from .schemas import DesignPackage, ImplementationPromptPack


def to_confluence_wiki(
    task: str, package: DesignPackage, prompt_pack: ImplementationPromptPack | None = None
) -> str:
    design = package.design
    lines = [
        "h1. SystemDesign-GPT Output",
        "h2. Design Problem",
        task,
        "h2. Quality Score",
        f"* Total Score: {package.quality_report.total_score}/100",
        "h2. High-Level Architecture",
        design.high_level_architecture,
        "h2. Components",
    ]
    for component in design.components:
        lines.append(f"* *{component.name}* ({component.type}): {component.description}")
    lines.append("h2. Tradeoffs")
    for tradeoff in design.tradeoffs:
        lines.append(f"* {tradeoff}")
    if prompt_pack and prompt_pack.prompts:
        lines.append("h2. Implementation Prompts")
        for prompt in prompt_pack.prompts:
            lines.append(f"* *{prompt.title}*: {prompt.objective}")
    return "\n".join(lines)


def to_github_pr_comment(task: str, package: DesignPackage) -> str:
    design = package.design
    lines = [
        "## System Design Summary",
        f"**Task:** {task}",
        "",
        f"**Quality Score:** {package.quality_report.total_score}/100",
        f"**Recommended Option:** {package.recommended_option or 'N/A'}",
        "",
        "### Architecture",
        design.high_level_architecture,
        "",
        "### Key Components",
    ]
    for component in design.components[:8]:
        lines.append(f"- `{component.name}` ({component.type}): {component.description}")
    lines.append("")
    lines.append("### Risks / Tradeoffs")
    for item in (design.bottlenecks + design.tradeoffs)[:8]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def to_pdf_bytes(task: str, package: DesignPackage) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    buff = BytesIO()
    c = canvas.Canvas(buff, pagesize=letter)
    y = 760
    lines = [
        "SystemDesign-GPT",
        f"Task: {task}",
        f"Quality Score: {package.quality_report.total_score}/100",
        "Architecture:",
        package.design.high_level_architecture,
        "Tradeoffs:",
    ]
    lines.extend(package.design.tradeoffs[:6])
    for line in lines:
        c.drawString(40, y, line[:105])
        y -= 18
        if y < 60:
            c.showPage()
            y = 760
    c.save()
    return buff.getvalue()
