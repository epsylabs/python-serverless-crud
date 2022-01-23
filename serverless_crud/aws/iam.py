class PolicyBuilder:
    def __init__(self, statements=None):
        statements = statements or []
        if isinstance(statements, dict):
            statements = list(statements)

        self.statements = {statement.get("Sid"): statement for statement in statements}

    def get_statement(self, sid):
        return self.statements.get(sid)

    def add_statement(self, statement: dict):
        self.statements[statement.get("Sid")] = statement

    def all(self):
        return [
            statement for statement in self.statements.values() if statement.get("Action") and statement.get("Resource")
        ]
