from typing import Any, List, Optional, Tuple, Dict, Union

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    pass

class ColumnRef(ASTNode):
    def __init__(self, column_name: str, table_name: Optional[str] = None):
        self.column_name = column_name
        self.table_name = table_name

    def full_name(self) -> str:
        if self.table_name:
            return f"{self.table_name}.{self.column_name}"
        return self.column_name

    def __repr__(self) -> str:
        return f"<ColumnRef {self.full_name()}>"

class Literal(ASTNode):
    def __init__(self, value: Any):
        self.value = value

    def __repr__(self) -> str:
        return f"<Literal {self.value!r}>"

class BinaryOp(ASTNode):
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self) -> str:
        return f"<BinaryOp ({self.left} {self.op} {self.right})>"

class SelectQuery(ASTNode):
    def __init__(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        wheres: Optional[List[BinaryOp]] = None,
        joins: Optional[List[Tuple[str, str, str]]] = None,
        order_bys: Optional[List[Tuple[str, str]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        self.table_name = table_name
        self.columns = columns or []
        self.wheres = wheres or []
        self.joins = joins or []
        self.order_bys = order_bys or []
        self.limit = limit
        self.offset = offset
