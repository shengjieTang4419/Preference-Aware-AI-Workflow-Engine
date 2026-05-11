"""
生成 Topic 事件
"""

from crewai_web.core.event import BusinessEvent, EventContext
from crewai_web.core.ai.client import AIClient
from crewai_web.web.services.document_service import get_document_service


class GenerateTopicEvent(BusinessEvent):
    """步骤 1: 生成项目主题"""

    name = "生成项目主题"
    step = 1
    total = 7

    async def do_execute(self, ctx: EventContext) -> None:
        ai_client = AIClient.get_default()

        # 读取上传的文档内容
        doc_context = ""
        if ctx.doc_filenames:
            doc_service = get_document_service()
            doc_contents = []
            for filename in ctx.doc_filenames:
                doc_data = doc_service.read_document(filename)
                if doc_data:
                    doc_contents.append(f"## 文档：{filename}\n\n{doc_data['content']}")

            if doc_contents:
                doc_context = "\n\n---\n\n".join(doc_contents)
                doc_context = f"\n\n## 参考文档\n\n{doc_context}\n\n---\n\n"

        # 组装 prompt（将文档内容注入到 scenario 中）
        scenario_with_docs = ctx.scenario
        if doc_context:
            scenario_with_docs = f"{ctx.scenario}\n\n{doc_context}"

        prompt = ai_client.load_prompt("generator/topic.prompt", scenario=scenario_with_docs)

        topic = await ai_client.call(prompt, role=self.role)
        ctx.topic = topic.strip()
