from pydantic import BaseModel, Field, field_validator
import json
from pathlib import Path
from tools import base642data, data2base64

class TranslationRequest(BaseModel):
    text: str = Field(..., max_length=1500)
    source_language: str = "auto"
    target_language: str = "en"

    @field_validator("text")
    def check_text_length(cls, value):
        if len(value) > 1500:
            raise ValueError("Text must not exceed 1500 characters")
        return value

    @field_validator("source_language", "target_language")
    def validate_language(cls, value):
        if not isinstance(value, str):
            raise TypeError("Language must be a string")
        return value.lower()


class TranslationResponse(BaseModel):
    text: str
    source_language: str
    target_language: str

    @field_validator("text", "source_language", "target_language")
    def validate_fields(cls, value):
        if not isinstance(value, str):
            raise TypeError("Field must be a string")
        return value.lower()

    def json(self):
        return json.dumps(
            {
                "text": self.text,
                "source_language": self.source_language,
                "target_language": self.target_language,
            }
        )


class DetectedLanguageResponse(BaseModel):
    language: str

    @field_validator("language")
    def validate_language(cls, value):
        if not isinstance(value, str):
            raise TypeError("Language must be a string")
        return value.lower()

    def json(self):
        return json.dumps({"language": self.language})


class FileRequest(TranslationRequest):
    text: str = ""
    file_path: Path
    
    @field_validator("file_path")
    def validate_file_path(cls, value):
        if not isinstance(value, Path):
            raise TypeError("File path must be a Path")
        return value

    @property
    def file_data_encoded(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
    
        with self.file_path.open("rb") as f:
            file_data = f.read()

        encoded_data = data2base64(file_data)
        return encoded_data

class FileResponse(BaseModel):
    file: bytes
    source_language: str
    target_language: str

    @field_validator("file")
    def validate_file(cls, value):
        if not isinstance(value, bytes):
            raise TypeError("File must be a bytes object")
        return value
    
    @field_validator("source_language", "target_language")
    def validate_language(cls, value):
        if not isinstance(value, str):
            raise TypeError("Language must be a string")
        return value.lower()

    def json(self):
        return json.dumps(
            {
                "file": self.file.decode("utf-8"),
                "source_language": self.source_language,
                "target_language": self.target_language,
            }
        )

    def save(self):
        print("saving")

if __name__ == "__main__":
    t = FileRequest(file_path="./mintrans/mintrans.py", source_language="en", target_language="tr")
    print(t)

