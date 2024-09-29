from urllib.parse import unquote
import json
import base64

def google_text_response_formatter(data: str) -> dict[str, str]:
    cleaned_data = json.loads(unquote(data)[5:].strip())
    cleaned_data = json.loads(cleaned_data[0][2])[1]
    # Some magic happens here for extracting the data we need
    source_language = cleaned_data[3]
    target_language = cleaned_data[1]
    translated_text = cleaned_data[0][0][5][0][0]

    return {
        "text": translated_text,
        "target_language": target_language,
        "source_language": source_language,
    }

def google_file_response_formatter(data: str) -> dict[str, str]:
    cleaned_data = json.loads(unquote(data)[5:].strip().replace('"[["', '[["').replace('"]]"', '"]]'))
    cleaned_data = cleaned_data[0]
    return cleaned_data

def data2base64(data: bytes) -> str:
    """Binary veriyi base64 url-safe olarak encode eder."""
    return base64.b64encode(data).decode("utf-8")

def base642data(data: str) -> bytes:
    """base64 url-safe olarak encode edilmiş veriyi binary veriye decode eder."""
    return base64.b64decode(data.encode("utf-8"))

if __name__ == "__main__":
    from constants import data_encoded, response_image_text
    # print(response_formatter(html_text1))
    for index, i in enumerate(google_file_response_formatter(response_image_text)):
        print(f"{index}) {i}")

    # print(google_file_response_formatter(response_image_text))
    # with open("image.png", "wb") as f:
    #     f.write(base642data(data=data_encoded))
    
    # with open("image.png", "rb") as f:
    #     data = data2base64(f.read())
    #     print(data == data_encoded)
    
    # with open("image2.png", "wb") as f:
    #     f.write(base642data(data=data))

