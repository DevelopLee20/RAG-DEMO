import os

# 데이터베이스 파일은 이 스크립트와 같은 디렉토리에 생성됩니다.
DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "text_db.txt")


async def read_text_db() -> list[list[str]]:
    """
    텍스트 파일 데이터베이스를 읽습니다.

    각 항목은 'name,safe_name;' 형식입니다.

    Returns:
        각 내부 리스트가 [name, safe_name] 쌍인 리스트입니다.
        예: [['file1.pdf', 'safe_file1.pdf'], ['file2.txt', 'safe_file2.txt']]
    """
    if not os.path.exists(DB_FILE_PATH):
        return []

    try:
        with open(DB_FILE_PATH, encoding="utf-8") as f:
            content = f.read().strip()
    except OSError:
        return []

    if not content:
        return []

    # 항목은 ';'로 구분됩니다. 마지막 항목에 ';'가 있을 수 있습니다.
    entries = content.split(";")

    # 분할로 인해 발생할 수 있는 빈 문자열을 제거합니다.
    entries = [entry for entry in entries if entry]

    data = []
    for entry in entries:
        parts = entry.split(",")
        if len(parts) == 2:
            data.append([parts[0].strip(), parts[1].strip()])
    return data


async def write_text_db(name: str, safe_name: str) -> None:
    """
    텍스트 파일 데이터베이스에 이름/안전한 이름 쌍을 쓰거나 업데이트합니다.
    이름이 이미 있으면 safe_name을 덮어쓰고, 그렇지 않으면 새 쌍을 추가합니다.

    Args:
        name: 원본 이름입니다.
        safe_name: 저장할 안전한 이름입니다.
    """
    db_data = await read_text_db()
    data_dict = {entry[0]: entry[1] for entry in db_data}

    data_dict[name] = safe_name

    new_content = ";".join([f"{n},{s}" for n, s in data_dict.items()])
    if new_content:
        new_content += ";"

    with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


async def delete_text_db(name: str) -> bool:
    """
    텍스트 파일 데이터베이스에서 특정 이름을 삭제합니다.

    Args:
        name: 삭제할 원본 이름입니다.

    Returns:
        bool: 삭제 성공 여부
    """
    try:
        db_data = await read_text_db()
        # 삭제할 이름을 제외한 데이터만 유지
        filtered_data = [entry for entry in db_data if entry[0] != name]

        # 새로운 내용 생성
        new_content = ";".join([f"{n},{s}" for n, s in filtered_data])
        if new_content:
            new_content += ";"

        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"Error deleting from text db: {e}")
        return False


async def find_safe_name_by_name(name: str) -> str | None:
    """
    주어진 이름에 대한 안전한 이름을 찾습니다.

    Args:
        name: 검색할 원본 이름입니다.

    Returns:
        해당하는 안전한 이름 또는 찾지 못한 경우 None입니다.
    """
    db = await read_text_db()
    for entry in db:
        if entry[0] == name:
            return entry[1]
    return None


async def find_name_by_safe_name(safe_name: str) -> str | None:
    """
    주어진 안전한 이름에 대한 원본 이름을 찾습니다.

    Args:
        safe_name: 검색할 안전한 이름입니다.

    Returns:
        해당하는 원본 이름 또는 찾지 못한 경우 None입니다.
    """
    db = await read_text_db()
    for entry in db:
        if entry[1] == safe_name:
            return entry[0]
    return None
