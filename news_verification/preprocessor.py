


# import cv2
# from PIL import Image
# import whisper
# import tldextract
# from newspaper import Article
# from serpapi import GoogleSearch
# import google.generativeai as genai
# import os


# class Description:
#     def __init__(self):
#         GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#         GROQ_API_KEY = os.getenv("GROQ_API_KEY")
#         TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
#         API_KEY=os.getenv("API_KEY")

#     # ===============================
#     # 🖼️ IMAGE DESCRIPTION (Gemini)
#     # ===============================
#     def _extract_image_description(self, image_path: str) -> str:
#         genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#         model = genai.GenerativeModel("gemini-2.5-flash-lite")

#         image = Image.open(image_path)
#         response = model.generate_content(["Describe this image in detail.", image])
#         return response.text

#     # ===============================
#     # 🎥 VIDEO DESCRIPTION (Gemini Vision)
#     # ===============================
#     def _extract_video_description_vision(self, video_path: str, frame_count: int = 3) -> dict:
#         genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#         vision_model = genai.GenerativeModel("gemini-1.5-pro")
#         text_model = genai.GenerativeModel("gemini-1.5-pro")

#         cap = cv2.VideoCapture(video_path)
#         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         interval = max(total_frames // frame_count, 1)

#         descriptions = []
#         for i in range(frame_count):
#             cap.set(cv2.CAP_PROP_POS_FRAMES, i * interval)
#             ret, frame = cap.read()
#             if not ret:
#                 continue

#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             pil_image = Image.fromarray(frame_rgb)

#             response = vision_model.generate_content(["Describe this frame in detail:", pil_image])
#             if response.text:
#                 descriptions.append(response.text.strip())

#         cap.release()
#         combined_description = "\n".join(descriptions)

#         # Summarize combined frame descriptions
#         try:
#             summary_prompt = (
#                 "Summarize the following visual descriptions into 3–4 sentences. "
#                 "Focus on the main scene, activity, people, and mood:\n\n"
#                 + combined_description
#             )
#             summary_response = text_model.generate_content(summary_prompt)
#             summary_text = summary_response.text.strip()
#         except Exception as e:
#             print(f"[ERROR: Gemini summarization failed] {e}")
#             summary_text = combined_description[:300] + "..."

#         return {"combined_description": combined_description, "summary": summary_text}

#     # ===============================
#     # 🔊 AUDIO DESCRIPTION (Whisper)
#     # ===============================
#     def _extract_audio_description(self, audio_path: str) -> str:
#         model = whisper.load_model("base")
#         result = model.transcribe(audio_path)
#         return result["text"]

#     # ===============================
#     # 🔎 IMAGE → SIMILAR URLs (Google Lens API)
#     # ===============================
#     def _extract_urls_from_image(self, url, api_key=None, hl="en", country="in"):
#         if api_key is None:
#             api_key = self.API_KEY

#         params = {
#             "api_key": api_key,
#             "engine": "google_lens",
#             "url": url,
#             "country": country,
#             "hl": hl,
#         }

#         search = GoogleSearch(params)
#         results = search.get_dict()
#         return [item["link"] for item in results.get("visual_matches", [])]

#     # ===============================
#     # 🌐 URL CONTENT EXTRACTION
#     # ===============================
#     def _extract_content_from_url(self, url: str, source=None, is_text=False, is_image=False):
#         article = Article(url)
#         article.download()
#         article.parse()

#         extracted = tldextract.extract(url)
#         source = f"{extracted.domain}.{extracted.suffix}"

#         info = {
#             "url": url,
#             "source": source,
#             "title": article.title,
#             "authors": article.authors,
#             "publish_date": article.publish_date,
#             "top_image": article.top_image,
#             "text": article.text,
#         }

#         if is_image:
#             info["media_type"] = "image"
#         if is_text:
#             info["media_type"] = "text"

#         return info

#     # ===============================
#     # 🚀 MAIN PROCESS METHOD
#     # ===============================
#     def process(self, input_dict: dict) -> dict:
#         """
#         Takes an input dictionary with optional keys:
#         text, image, video, audio, url — and extracts semantic descriptions.
#         """
#         print(input_dict)
#         responses = {}

#         for key, value in input_dict.items():
#             if value in [None, "null", "None"]:
#                 continue

#             print(f"{key}: {value}")

#             try:
#                 if key == "text":
#                     responses[key] = value

#                 elif key == "image":
#                     responses[key] = self._extract_image_description(value)
#                     print("✅ Image description extracted")

#                 elif key == "video":
#                     video_result = self._extract_video_description_vision(value)
#                     responses[key] = video_result["summary"]
#                     print("✅ Video description extracted")

#                 elif key == "audio":
#                     responses[key] = self._extract_audio_description(value)
#                     print("✅ Audio description extracted")

#                 elif key == "url":
#                     content = self._extract_content_from_url(value)
#                     responses[key] = content["text"]
#                     print("✅ URL content extracted")

#                 else:
#                     raise ValueError(f"Unsupported input type: {key}")

#             except Exception as e:
#                 print(f"[ERROR processing {key}]: {e}")

#         print("🟢 Final responses:", responses)
#         return responses


import cv2
from PIL import Image
import whisper
import tldextract
from newspaper import Article
from serpapi import GoogleSearch
import google.generativeai as genai
import os
from pathlib import Path

# Import the FakeImageDetector class
from deepfake import FakeImageDetector


class Description:
    def __init__(self):
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        API_KEY=os.getenv("API_KEY")
        
        # Instantiate the FakeImageDetector
        self.fake_image_detector = FakeImageDetector(fast=True)

    # ===============================
    # 🖼️ IMAGE DESCRIPTION (Gemini)
    # ===============================
    def _extract_image_description(self, image_path: str) -> str:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")

        image = Image.open(image_path)
        response = model.generate_content(["Describe this image in detail.", image])
        return response.text

    # ===============================
    # 🎥 VIDEO DESCRIPTION (Gemini Vision)
    # ===============================
    def _extract_video_description_vision(self, video_path: str, frame_count: int = 3) -> dict:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        vision_model = genai.GenerativeModel("gemini-1.5-pro")
        text_model = genai.GenerativeModel("gemini-1.5-pro")

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(total_frames // frame_count, 1)

        descriptions = []
        for i in range(frame_count):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * interval)
            ret, frame = cap.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            response = vision_model.generate_content(["Describe this frame in detail:", pil_image])
            if response.text:
                descriptions.append(response.text.strip())

        cap.release()
        combined_description = "\n".join(descriptions)

        # Summarize combined frame descriptions
        try:
            summary_prompt = (
                "Summarize the following visual descriptions into 3–4 sentences. "
                "Focus on the main scene, activity, people, and mood:\n\n"
                + combined_description
            )
            summary_response = text_model.generate_content(summary_prompt)
            summary_text = summary_response.text.strip()
        except Exception as e:
            print(f"[ERROR: Gemini summarization failed] {e}")
            summary_text = combined_description[:300] + "..."

        return {"combined_description": combined_description, "summary": summary_text}

    # ===============================
    # 🔊 AUDIO DESCRIPTION (Whisper)
    # ===============================
    def _extract_audio_description(self, audio_path: str) -> str:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]

    # ===============================
    # 🔎 IMAGE → SIMILAR URLs (Google Lens API)
    # ===============================
    def _extract_urls_from_image(self, url, api_key=None, hl="en", country="in"):
        if api_key is None:
            api_key = self.API_KEY

        params = {
            "api_key": api_key,
            "engine": "google_lens",
            "url": url,
            "country": country,
            "hl": hl,
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        return [item["link"] for item in results.get("visual_matches", [])]

    # ===============================
    # 🌐 URL CONTENT EXTRACTION
    # ===============================
    def _extract_content_from_url(self, url: str, source=None, is_text=False, is_image=False):
        article = Article(url)
        article.download()
        article.parse()

        extracted = tldextract.extract(url)
        source = f"{extracted.domain}.{extracted.suffix}"

        info = {
            "url": url,
            "source": source,
            "title": article.title,
            "authors": article.authors,
            "publish_date": article.publish_date,
            "top_image": article.top_image,
            "text": article.text,
        }

        if is_image:
            info["media_type"] = "image"
        if is_text:
            info["media_type"] = "text"

        return info

    # ===============================
    # 🚀 MAIN PROCESS METHOD
    # ===============================
    def process(self, input_dict: dict) -> dict:
        """
        Takes an input dictionary with optional keys:
        text, image, video, audio, url — and extracts semantic descriptions.
        """
        print(input_dict)
        responses = {}

        for key, value in input_dict.items():
            if value in [None, "null", "None"]:
                continue

            print(f"{key}: {value}")

            try:
                if key == "text":
                    responses[key] = value

                elif key == "image":
                    # Extract image description
                    responses[key] = self._extract_image_description(value)
                    print("✅ Image description extracted")

                    # Call deepfake detector
                    fake_results = self.fake_image_detector.predict(value)
                    image_name = Path(value).name
                    if image_name in fake_results:
                        responses['fake_probability'] = fake_results[image_name]
                        print(f"✅ Deepfake detection for {image_name} completed.")

                elif key == "video":
                    video_result = self._extract_video_description_vision(value)
                    responses[key] = video_result["summary"]
                    print("✅ Video description extracted")

                elif key == "audio":
                    responses[key] = self._extract_audio_description(value)
                    print("✅ Audio description extracted")

                elif key == "url":
                    content = self._extract_content_from_url(value)
                    responses[key] = content["text"]
                    print("✅ URL content extracted")

                else:
                    raise ValueError(f"Unsupported input type: {key}")

            except Exception as e:
                print(f"[ERROR processing {key}]: {e}")

        print("🟢 Final responses:", responses)
        return responses