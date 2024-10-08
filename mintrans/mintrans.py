import httpx
from pydantic import ValidationError
import re
import time
import random
from typing import Optional
from urllib.parse import quote
from pathlib import Path

from tools import google_text_response_formatter, google_file_response_formatter
from constants import user_agents
from exceptions import RateLimitException
from models import TranslationRequest, TranslationResponse, DetectedLanguageResponse, FileRequest, FileResponse

class BaseTranslator:
    def __init__(self):
        self.client: Optional[httpx.Client] = None

    def _create_client(self):
        """Initializes the HTTPX client."""
        if not self.client:
            self.client = httpx.Client()

    def close(self):
        """Closes the client."""
        if self.client:
            self.client.close()
            self.client = None

    def __enter__(self):
        self._create_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_headers(self):
        return {"user-agent": random.choice(user_agents)}

class BingTranslator(BaseTranslator):
    def __init__(self):
        super().__init__()
        self.session = None

    def _get_session(self):
        self._create_client()
        session = self.client
        headers = self.get_headers()
        headers.update({
            "Referer": "https://www.bing.com/translator"
        })
        session.headers.update(headers)
        response = session.get("https://www.bing.com/translator")
        content = response.text
        params_pattern = re.compile(r"params_AbusePreventionHelper\s*=\s*(\[.*?\]);", re.DOTALL)
        match = params_pattern.search(content)
        if match:
            params = match.group(1)
            key, token, time = [p.strip("\"").replace("[", "").replace("]", "") for p in params.split(",")]
            session.headers.update({"key": key, "token": token})
        match = re.search(r'IG:"(\w+)"', content)
        if match:
            ig_value = match.group(1)
            session.headers.update({"IG": ig_value})
        return session

    def translate_text(self, text: str, target_language: str, source_language: str = "auto-detect"):
        if not self.session:
            self.session = self._get_session()

        try:
            translation_request = TranslationRequest(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e}")
        
        url = f"https://www.bing.com/ttranslatev3?isVertical=1&&IG={self.session.headers.get('IG')}&IID=translator.{random.randint(5019, 5026)}.{random.randint(1, 3)}"
        data = {
            "": "",
            "fromLang": source_language,
            "text": text,
            "to": target_language,
            "token": self.session.headers.get("token"),
            "key": self.session.headers.get("key")
        }
        response = self.session.post(url, data=data).json()
        if isinstance(response, dict):
            if "ShowCaptcha" in response.keys():
                self.session = self._get_session()
                return self.translate_text(
                    translation_request.text,
                    translation_request.source_language,
                    translation_request.target_language,
                )
            elif "statusCode" in response.keys():
                if response["statusCode"] == 400:
                    response["errorMessage"] = f"1000 characters limit! You send {len(text)} characters."
        else:
            response = response[0]
            return TranslationResponse(
                text=response["translations"][0]["text"],
                source_language=response["detectedLanguage"]["language"],
                target_language=response["translations"][0]["to"],
            )

        return response

    def detect_language(self, text: str):
        return DetectedLanguageResponse(language=self.translate_text(text=text, source_language="auto-detect", target_language="tr").source_language)


class DeepLTranslator(BaseTranslator):
    def __init__(self) -> None:
        super().__init__()
        self.client = self._create_client()

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
    ) -> TranslationResponse:
        try:
            translation_request = TranslationRequest(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e}")

        json = {
            "jsonrpc": "2.0",
            "method": "LMT_handle_jobs",
            "params": {
                "jobs": [
                    {
                        "kind": "default",
                        "sentences": [
                            {"text": translation_request.text, "id": 1, "prefix": ""}
                        ],
                        "preferred_num_beams": 1,  # translation_request.num_beams,
                    }
                ],
                "lang": {
                    "target_lang": translation_request.target_language,
                    "preference": {"weight": {}},
                },
                "timestamp": round(time.time() * 1.5),
            },
        }

        if translation_request.source_language != "auto":
            json["params"]["lang"][
                "source_lang_computed"
            ] = translation_request.source_language

        params = {"method": "LMT_handle_jobs"}

        headers = self.get_headers()
        headers.update({"content-type": "application/json"})

        response = self.client.post(
            "https://www2.deepl.com/jsonrpc", json=json, params=params, headers=headers
        ).json()

        try:
            return TranslationResponse(
                text=response["result"]["translations"][0]["beams"][0]["sentences"][0][
                    "text"
                ],
                source_language=response["result"]["source_lang"],
                target_language=response["result"]["target_lang"],
            )
        except KeyError:
            raise RateLimitException("Rate limit error!")

    def close(self):
        self.client.close()

    def detect_language(self, text: str) -> str:
        return DetectedLanguageResponse(
            language=self.translate_text(
                text, source_language="auto", target_language="tr"
            ).source_language
        )


class GoogleTranslator(BaseTranslator):
    def __init__(self):
        super().__init__()
        self.client = self._create_client()

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",) -> TranslationResponse:
        try:
            translation_request = TranslationRequest(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e}")

        url = "https://translate.google.com/_/TranslateWebserverUi/data/batchexecute"

        params = {"rpcids": "MkEWBc"}

        payload = "f.req=" + quote(
            f'[[["MkEWBc","[[\\"{translation_request.text}\\",\\"{translation_request.source_language}\\",\\"{translation_request.target_language}\\",true],[]]",null,"generic"]]]'
        )

        headers = self.get_headers()
        headers.update({
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        })

        response = self.client.post(url, params=params, data=payload, headers=headers)
        # print(response.text)

        response = google_text_response_formatter(response.text)

        try:
            return TranslationResponse(
                text=response["text"],
                source_language=response["source_language"],
                target_language=response["target_language"],
            )
        except KeyError:
            raise RateLimitException("Rate limit error!")

    def translate_image(
        self,
        image_path: Path,
        target_language: str,
        source_language: str = "auto",) -> FileResponse:
        raise NotImplementedError("Image translation is not implemented yet!")
        try:
            file_request = FileRequest(
                file_path=image_path,
                source_language=source_language,
                target_language=target_language,
            )
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e}")

        url = "https://translate.google.com/_/TranslateWebserverUi/data/batchexecute"

        params = {"rpcids": "WqWDPb"}

        f_req_data = f'[[["WqWDPb", "[[\\"{file_request.file_data_encoded}\\",\\"image/jpeg\\"],\\"{file_request.source_language}\\",\\"{file_request.target_language}\\"]", null, "generic"]]]'

        payload = {
            'f.req': f_req_data,
        }

        headers = self.get_headers()
        headers.update({
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            # "X-Goog-BatchExecute-Bgr": '[";zNK40orQAAYE3UGHJN1fI9NznCOeFGUmADQBEArZ1C5Mchj3qFijBIVo1JYBSjJDNxZAxhreKoF_Dd4dHOBFVjaLRC75KBOAjZZkvjZwHwAAAfdPAAAAHHUBB2MAQLQLssYzf3Wu0yWZ7Y2P0SmQTnn-x_zhnRfraTk9luQz_kA_2SRKOm2IpB3VlPVXlYE1KHpljaD3yKvzpZC5LIwXAGJbP6dVZiy-MX_Rb5yofs1OVKmxaP174zaEqZwyMo6fia6nrCruTQ4bL0342KMBsb5Er9yr5VxPwkGf_dZwIvkeljFYrDT7mw4OZxv0QvXJoyVxYKmkrjo4j4ujrfgvh0F8JIQCxJF-8EE3IZAwDwNlDSj-fiNR1iPXU_JMNapRSEf9FPf7zv-MMO0e56F49yG4OEYWSCPUh-Sg1tZSh4aOGBmZa7gCPc_-ZTZbnMXqTrhqTUBs4e-tvbq2N-XFA-ocAZHz8pKD0KyTyFUMX8xoajJ_gU48zjg3b3pYGT80_8ZqlY6TVNAQXOyEpwvcIu6FhzD3_ZlzJA9C_hi6zprjQQ0rXKMIraXAH0e5dnts3TN0E3qr1rtLG5c68JKgptcFMvsh-HXrsYSpmLeWsyizkFO0AODYladyCzEnD-_Zrx5Lkkr9ovw7vMIO0P6BnTj_RguubxnH5gWgrNu8ALrcy00yylOjBYyjWZpnYNk4X_OYh0jnMPQHA2z_vggxLb0xZhWjV8hZfBldyojlSUZQMix3c3ibKuoa9nAXF0G42thaWlFJOuT3WCw4NkZ_odHlTvzHSwlid4vGtyjM6HjPcYrTOzN21Z_7I0gwCdjSPFJ_vSbB20wmZXc9VKn8E_QG3XPsCYBEIMVKjZun0orn0jLM6-rdc84LfGA7l-HGAg3E6IL630hMTer6donE5YJ7nNVWYuErqjS35egpG4fiDT-bIsJbfRNSS2JhHu3lREXZjE-LFjacktOCMkvEMp8qNmR3qk3aeOeJOeOxlE_hmB-HqzqM3RZ_CbyafmkTJqRXMtb2Rr76AjAYAMsiO1PS_jnOw3xuTdXgl66Y8rpHN-GlPQcbire7m_xDI85aa1pLSUcQ0cq1_jiYPZxHI3fzzxlwHw_mlMv9dnekVgVyzIijh5jSh9YgS0yKp6hq_0TZr2jJnsrx8TapHQOa43Y3uMRewh1S8IkS2Ht7zxwwqhtL0yb7spSt11kaO800G9FoxAFZLQXwAKy-eW5LBvl-DnN14B1Rci6_e0EFDevbnrq-905L_kclsdWen7OIHo5DlrsrZCPBvQ",null,null,1148,38,null,null,0,"2"]'
            })

        response = self.client.post(url, params=params, data=payload, headers=headers)

        # response = google_file_response_formatter(response.text)

        print(response)

    def translate_document(
        self,
        document: str,
        target_language: str,
        source_language: str = "auto",) -> TranslationResponse:
        raise NotImplementedError("Document translation is not implemented yet!")

    def translate_text_legacy(
        self,
        text,
        source_language,
        target_language,) -> TranslationResponse:
        try:
            translation_request = TranslationRequest(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e}")

        url = "https://translate.googleapis.com/translate_a/single"

        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": translation_request.target_language,
            "hl": translation_request.source_language,
            "dt": ["t", "bd"],
            "dj": "1",
            "source": "popup5",
            "q": translation_request.text,
        }

        response = self.client.get(url, params=params).json()

        try:
            return TranslationResponse(
                text=response["sentences"][0]["trans"],
                source_language=response["src"],
                target_language=translation_request.target_language,
            )
        except KeyError:
            raise RateLimitException("Rate limit error!")

    def detect_language(self, text: str) -> str:
        return DetectedLanguageResponse(
            language=self.translate_text(
                text, source_language="auto", target_language="tr"
            ).source_language
        )

    def close(self):
        self.client.close()


if __name__ == "__main__":
    with GoogleTranslator() as t:
        t.translate_image("image.jpg", "tr")
        # print(t.detect_language("Merhaba Kanka Naber!").json())
        # print(t.translate_text("Hello Brother!", target_language="tr", source_language="auto-detect").json())
