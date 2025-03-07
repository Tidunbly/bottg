import json
import os


def json_maker(mainpath, json_file_path):
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                documents = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении {json_file_path}: {e}")
            documents = []
    else:
        documents = []

    existing_files = {doc["title"] for doc in documents}

    file_id = len(documents)

    for filename in os.listdir(mainpath):
        if filename.endswith(".txt") and filename not in existing_files:
            file_path = os.path.join(mainpath, filename)

            file_id += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()

                documents.append({
                    "id": file_id,
                    "title": filename,
                    "text": text
                })

                existing_files.add(filename)

            except (IOError, UnicodeDecodeError) as e:
                print(f"Ошибка при чтении файла {filename}: {e}")

    try:
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(documents, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Ошибка при записи в файл {json_file_path}: {e}")
