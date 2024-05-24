from enum import Enum

class CodeInfo:

    def __init__(self, id, time, code, type, region):
        self.id = id
        self.time = time
        self.code = code
        self.type = type
        self.region = region

    def __hash__(self) -> int:
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
            "region": self.region
        }

    @staticmethod
    def from_json(data):
        return CodeInfo(data["id"], float(data["time"]), data["code"], CodeType(int(data["type"])), data["region"])
    
    @staticmethod
    def count_type(code_list, type):
        return len(CodeInfo.get_in_type(code_list, type))
    
    @staticmethod
    def get_in_type(code_list, type):
        return [code for code in code_list if code.type == type]

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