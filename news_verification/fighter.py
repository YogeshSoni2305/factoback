from system_prompts import *
import models
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init
from tavily_search import tavily_search
from preprocessor import Description
import warnings
import asyncio
import json

warnings.filterwarnings("ignore")
init()


class ClaimFighter:
    def __init__(self):
        load_dotenv("api.key")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.tavily_key = os.getenv("TAVILY_API_KEY")

        if not self.groq_key or not self.gemini_key or not self.tavily_key:
            raise ValueError("Missing API Keys.")
        print("✅ All API keys are loaded successfully!")

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Initialize models
        self.llama = models.LlamaChat(api_key=self.groq_key, system_prompt=LLAMA_SYSTEM_PROMPT)
        self.deepseek = models.DeepseekChat(api_key=self.groq_key, system_prompt=DEEPSEEK_SYSTEM_PROMPT)
        self.gemini_chat = models.GeminiChat(api_key=self.gemini_key, system_prompt=GEMINI_EXTRACTOR_SYSTEM_PROMPT)
        self.gemini_arbitrator = models.GeminiIntermediate(api_key=self.gemini_key, system_prompt=GEMINI_INTERMEDIATE_SYSTEM_PROMPT)
        self.output = {}

    def extract_claims(self, message: dict) -> dict:
        """Extract factual claims and questions from the input"""
        chat_session = models.GeminiChat(api_key=self.gemini_key, system_prompt=GEMINI_EXTRACTOR_SYSTEM_PROMPT)
        response = chat_session.send_message(str(message))
        print(f"{Fore.MAGENTA}RESPONSE FROM CLAIM EXTRACTOR (GEMINI):{Style.RESET_ALL}")
        print(response)
        return response

    def save_to_markdown(self, content, filename="./static/claim_fighter_results.md", mode="a"):
        """Save content to markdown"""
        with open(filename, mode, encoding="utf-8") as md_file:
            md_file.write(content)

    def fetch_tavily_sources(self, claim_text: str):
        """Fetch 5–6 fact-check sources related to a claim"""
        print(f"🔍 Fetching Tavily sources for: {claim_text}")
        try:
            tavily_resp = tavily_search(
                query=claim_text,
                max_results=6,
                topic="news",
                search_depth="advanced",
                TAVILY_API_KEY=self.tavily_key
            )
            results = tavily_resp.get("results", [])
            formatted = [
                {"title": r.get("title", "Untitled"), "url": r.get("url", "#")}
                for r in results
            ]
            return formatted
        except Exception as e:
            print(f"[TAVILY ERROR] {e}")
            return []

    def fight(self, response):
        """Run one-round debate with reasoning + fact-check sources"""
        markdown_content = "## Debate Results (Single Round)\n\n"

        for idx, claim in enumerate(response[0]["claims"][:3]):
            print(f"\n{Fore.YELLOW}=== CLAIM ({claim}) ==={Style.RESET_ALL}")
            markdown_content += f"### Claim: {claim}\n\n"

            claim_key = f"claim{idx}"
            self.output[claim_key] = {"claim": claim}

            # === DeepSeek turn ===
            _, deepseek_response = self.deepseek.send_message(claim)
            deepseek_response = deepseek_response or "No response or token limit exceeded."
            markdown_content += f"**DeepSeek Response:**\n\n```\n{deepseek_response}\n```\n\n"

            # === LLaMA turn ===
            llama_response = self.llama.send_message(f"Claim: {claim}\nOpponent: {deepseek_response}")
            markdown_content += f"**LLaMA Response:**\n\n```\n{llama_response}\n```\n\n"

            # === Gemini Arbitrator (Final Verdict) ===
            gemini_response = self.gemini_arbitrator.send_message(
                claim=claim,
                llama_response=llama_response,
                deepseek_response=deepseek_response
            )
            markdown_content += f"**Gemini Arbitrator Verdict:**\n\n```\n{json.dumps(gemini_response, indent=2)}\n```\n\n"

            # === Tavily fact-check sources ===
            tavily_sources = self.fetch_tavily_sources(claim)
            markdown_content += "**Fact-Check Sources:**\n\n"
            if tavily_sources:
                for src in tavily_sources:
                    markdown_content += f"- [{src['title']}]({src['url']})\n"
            else:
                markdown_content += "_No reliable sources found._\n"
            markdown_content += "\n"

            # === Combine final reasoning and confidence ===
            final_reasoning = gemini_response.get("reasoning", "No reasoning provided.")
            confidence = gemini_response.get("confidence", "Unknown")
            conclusion = gemini_response.get("conclusion", "No conclusion generated.")

            markdown_content += f"**Final Verdict:**\n\n{conclusion}\n\n"
            markdown_content += f"**Reasoning:** {final_reasoning}\n\n"
            markdown_content += f"**Confidence:** {confidence}\n\n"
            markdown_content += "---\n\n"

            # Save to structured output
            self.output[claim_key].update({
                "deepseek_response": deepseek_response,
                "llama_response": llama_response,
                "gemini_response": gemini_response,
                "tavily_sources": tavily_sources,
                "final_conclusion": conclusion,
                "confidence": confidence
            })

        # Save results
        self.save_to_markdown(markdown_content)
        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(self.output, f, ensure_ascii=False, indent=4)
        print("✅ Output saved to output.json and claim_fighter_results.md")

    def run(self, inputs: dict):
        try:
            # Markdown header
            markdown_header = "# ClaimFighter Results\n\n## User Inputs\n\n"
            for key, value in inputs.items():
                if value:
                    markdown_header += f"- **{key.upper()}**: {value}\n"
            markdown_header += "\n---\n\n"
            self.save_to_markdown(markdown_header, mode="w")

            # Preprocessing
            desc = Description()
            results = desc.process(inputs)
            self.output["inputs"] = inputs
            self.output["descr"] = results
            print("✅ Preprocessing completed.")

            preprocessed_md = "## Preprocessed Content\n\n"
            for key, value in results.items():
                preprocessed_md += f"### {key.upper()} Content\n\n```\n{value}\n```\n\n"
            preprocessed_md += "---\n\n"
            self.save_to_markdown(preprocessed_md)

            # Claim extraction
            claims = self.extract_claims(results)
            claims_md = "## Extracted Claims\n\n```\n" + str(claims) + "\n```\n\n"
            self.save_to_markdown(claims_md)

            # Fight one round
            self.fight(claims)
            print(f"\n{Fore.GREEN}Results successfully saved ✅{Style.RESET_ALL}")

        except Exception as e:
            print(f"[ERROR] {e}")
            self.save_to_markdown(f"\n\n## Error\n\n```\n{str(e)}\n```\n")


if __name__ == "__main__":
    fighter = ClaimFighter()
    input_data = {
        "text": "Donald Trump has increased tariffs to demonstrate his power over other countries.",
        "image": r"/workspaces/fantom_code/backend/data/donald.jpg",
        "video": None,
        "audio": r"/workspaces/fantom_code/backend/data/donaltrump(1) (mp3cut.net) (1).mp3",
        "url": "https://www.firstpost.com/explainers/donald-trump-liberation-day-tariff-90-day-pause-explained-13878689.html"
    }
    fighter.run(input_data)
