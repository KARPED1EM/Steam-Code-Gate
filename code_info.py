from enum import Enum

class CodeInfo:
    def __init__(self, uid, time, code, code_type, region):
        self.id = uid
        self.time = time
        self.code = code
        self.type = code_type
        self.region = region

    def __hash__(self) -> int:
        # de-dup by time to preserve existing semantics
        return hash(self.time)

    def __eq__(self, other) -> bool:
        if isinstance(other, CodeInfo):
            return self.time == other.time
        return False

    def to_json(self):
        return {
            "id": self.id,
            "time": self.time,
            "code": self.code,
            "type": self.type.value,
            "region": self.region,
        }

    @staticmethod
    def from_json(data):
        return CodeInfo(
            data["id"],
            float(data["time"]),
            data["code"],
            CodeType(int(data["type"])),
            data["region"],
        )

    @staticmethod
    def count_type(code_list, code_type):
        return len(CodeInfo.get_in_type(code_list, code_type))

    @staticmethod
    def get_in_type(code_list, code_type):
        return [code for code in code_list if code.type == code_type]

class CodeType(Enum):
    UNKNOWN = 0
    LOGIN = 1
    RECOVERY = 2
    GAME_PURCHASE = 3
    MARKET_PURCHASE = 4
    MARKET_SOLD = 5
    SUPPORT = 6
    REFUND_REQUEST = 7
    REFUNDED = 8