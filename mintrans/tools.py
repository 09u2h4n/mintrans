from urllib.parse import unquote
import json


def google_response_formatter(data: str) -> dict[str, str]:
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


if __name__ == "__main__":
    # print(response_formatter(html_text1))
    # for index, i in enumerate(response_formatter(html_text1)):
    #     print(f"{index}) {i}")

    print(google_response_formatter(html_text1))
