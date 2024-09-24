import httpx
import re
import time
import random
from typing import Optional
from urllib.parse import quote

from tools import google_response_formatter
from constants import user_agent
from exceptions import RateLimitException
from models import TranslationRequest, TranslationResponse


class BingTranslator:
    def __init__(self):
        self.client = self._get_client()

    def _get_client(self):
        client = httpx.Client()

        headers = {
            "User-Agent": user_agent,
            "Referer": "https://www.bing.com/translator",
        }

        client.headers.update(headers)

        response = client.get("https://www.bing.com/translator")

        content = response.text
        # Some regex magic happens here
        params_pattern = re.compile(
            r"params_AbusePreventionHelper\s*=\s*(\[.*?\]);", re.DOTALL
        )

        match = params_pattern.search(content)
        if match:
            params = match.group(1)
            key, token, time = [
                p.strip('"').replace("[", "").replace("]", "")
                for p in params.split(",")
            ]
            client.headers.update({"key": key, "token": token})

        match = re.search(r'IG:"(\w+)"', content)
        if match:
            ig_value = match.group(1)
            client.headers.update({"IG": ig_value})

        return client

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        auto_close: bool = False,
    ) -> TranslationResponse:
        try:
            translation_request = TranslationRequest(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e}")

        url = f"https://www.bing.com/ttranslatev3?isVertical=1&&IG={self.client.headers.get('IG')}&IID=translator.{random.randint(5019, 5026)}.{random.randint(1, 3)}"

        data = {
            "": "",
            "fromLang": translation_request.source_language,
            "text": translation_request.text,
            "to": translation_request.target_language,
            "token": self.client.headers.get("token"),
            "key": self.client.headers.get("key"),
        }

        response = self.client.post(url, data=data).json()

        if auto_close:
            self.client.close()

        if type(response) is dict:
            if "ShowCaptcha" in response.keys():
                self.client = self._get_client()
                return self.translate_text(
                    translation_request.text,
                    translation_request.source_language,
                    translation_request.target_language,
                )
            elif "statusCode" in response.keys():
                if response["statusCode"] == 400:
                    response[
                        "errorMessage"
                    ] = f"1000 characters limit! You send {len(text)} characters."
        else:
            response = response[0]
            return TranslationResponse(
                text=response["translations"][0]["text"],
                source_language=response["detectedLanguage"]["language"],
                target_language=response["translations"][0]["to"],
            )
        return response

    def close(self):
        self.client.close()


class DeepLTranslator:
    def __init__(self) -> None:
        self.client = httpx.Client()

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        auto_close: bool = False,
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
                        "preferred_num_beams": translation_request.num_beams,
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

        headers = {"content-type": "application/json"}

        response = self.client.post(
            "https://www2.deepl.com/jsonrpc", json=json, params=params, headers=headers
        ).json()

        if auto_close:
            self.client.close()

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


class GoogleTranslator:
    def __init__(self):
        self.client = httpx.Client()

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        auto_close: bool = False,
    ) -> TranslationResponse:
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

        headers = {
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        }

        response = self.client.post(url, params=params, data=payload, headers=headers)

        if auto_close:
            self.client.close()

        response = google_response_formatter(response.text)

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
        image: bytes,
        target_language: str,
        source_language: str = "auto",
        auto_close: bool = False,
    ) -> TranslationResponse:
        raise NotImplementedError("Image translation is not implemented yet!")

    def translate_document(
        self,
        document: bytes,
        target_language: str,
        source_language: str = "auto",
        auto_close: bool = False,
    ) -> TranslationResponse:
        raise NotImplementedError("Document translation is not implemented yet!")

    def translate_text_legacy(
        self, text, source_language, target_language, auto_close: bool = False
    ) -> TranslationResponse:
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

        if auto_close:
            self.client.close()

        try:
            return TranslationResponse(
                text=response["sentences"][0]["trans"],
                source_language=response["src"],
                target_language=translation_request.target_language,
            )
        except KeyError:
            raise RateLimitException("Rate limit error!")

    def detect_language(self, text: str, auto_close: bool = False) -> str:
        return self.translate_text(
            text, source_language="auto", target_language="tr", auto_close=auto_close
        ).source_language

    def close(self):
        self.client.close()


if __name__ == "__main__":
    t = GoogleTranslator()
    print(t.detect_language("Hello Brother!", auto_close=True))
