"""간호사 정보 + 마지막 스케줄 + 룰북을 로컬 JSON 파일에 저장/불러오기.
streamlit session_state는 브라우저 세션이 끝나면 사라지므로, 같은 폴더의
schedule_snapshots.json 파일에 실제로 디스크 저장해서 앱을 껐다 켜도 불러올 수 있게 함."""
import json
from datetime import datetime
from pathlib import Path

SNAPSHOT_FILE = Path(__file__).resolve().parent / "schedule_snapshots.json"


def _read_all():
    if not SNAPSHOT_FILE.exists():
        return {}
    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_all(data):
    try:
        with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def list_snapshots():
    """[(name, saved_at_str), ...] 최신순으로 반환."""
    data = _read_all()
    items = [(name, v.get("saved_at", "")) for name, v in data.items()]
    items.sort(key=lambda t: t[1], reverse=True)
    return items


def save_snapshot(name, nurses, rules, last_result=None, meta=None):
    if not name or not name.strip():
        return False, "이름을 입력해줘."
    data = _read_all()
    data[name.strip()] = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nurses": nurses,
        "rules": rules,
        "last_result": last_result,
        "meta": meta or {},
    }
    ok = _write_all(data)
    return ok, ("저장 완료" if ok else "저장 실패(파일 쓰기 오류)")


def load_snapshot(name):
    data = _read_all()
    return data.get(name)


def delete_snapshot(name):
    data = _read_all()
    if name in data:
        del data[name]
        return _write_all(data)
    return False
