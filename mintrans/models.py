from typing import Optional
import json


class TranslationRequest:
    def __init__(
        self,
        text: str,
        source_language: str = "auto",
        target_language: str = "en",
        # num_beams: Optional[int] = 1,
    ):
        if len(text) > 1500:
            raise ValueError("Text must not exceed 1500 characters")
        self.text = text
        self.source_language = source_language
        self.target_language = target_language
        # self.num_beams = num_beams

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Text must be a string")
        # Maybe this part is a bit buggy
        # httpx could raise another error like status code 400
        # if text is too long or something like that
        if len(value) > 1500:
            raise ValueError("Text must not exceed 1500 characters")
        self._text = value

    @property
    def source_language(self) -> str:
        return self._source_language

    @source_language.setter
    def source_language(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Source language must be a string")
        self._source_language = value

    @property
    def target_language(self) -> str:
        return self._target_language

    @target_language.setter
    def target_language(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Target language must be a string")
        self._target_language = value

    # Maybe in next updates i can add num beams for DeepL
    # @property
    # def num_beams(self) -> Optional[int]:
    #     return self._num_beams

    # @num_beams.setter
    # def num_beams(self, value: Optional[int]):
    #     if value is not None and not isinstance(value, int):
    #         raise TypeError("Number of beams must be an integer or None")
    #     self._num_beams = value


class TranslationResponse:
    def __init__(self, text: str, source_language: str, target_language: str):
        self.text = text
        self.source_language = source_language
        self.target_language = target_language
        # self.alternative_texts = alternative_texts

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Translated text must be a string")
        self._text = value

    @property
    def source_language(self) -> str:
        return self._source_language

    @source_language.setter
    def source_language(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Source language must be a string")
        self._source_language = value.lower()

    @property
    def target_language(self) -> str:
        return self._target_language

    @target_language.setter
    def target_language(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Target language must be a string")
        self._target_language = value.lower()

    # In the next updates maybe i optionally add for Google
    # @property
    # def alternative_texts(self) -> list:
    #     return self._alternative_texts

    # @alternative_texts.setter
    # def alternative_texts(self, value: list):
    #     if not isinstance(value, list):
    #         raise TypeError("Alternative texts must be a list")
    #     self._alternative_texts = value

    def json(self):
        return json.dumps(
            {
                "text": self.text,
                "source_language": self.source_language,
                "target_language": self.target_language,
            }
        )


if __name__ == "__main__":
    t = TranslationRequest("hello", "en", "tr")
    print(t)
