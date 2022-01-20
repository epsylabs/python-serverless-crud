from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

serializer = TypeSerializer()


class KeyDeserialization(Exception):
    pass


class Deserializer(TypeDeserializer):
    def _deserialize_time(self, value):
        return value

    def _deserialize_key(self, value):
        raise KeyDeserialization()

    def _deserialize__typename(self, value):
        return value["S"]

    def deserialize(self, obj):
        output = {}
        if isinstance(obj, dict):
            output = {}
            for k, v in obj.items():
                try:
                    dv = super().deserialize(v)
                    dv if not isinstance(dv, list) else self.deserialize(dv)
                    output[k] = dv
                except KeyDeserialization:
                    pass
        elif isinstance(obj, list):
            output = []
            for i in obj:
                try:
                    dv = i if isinstance(i, str) else super().deserialize(i)
                    output.append(dv if not isinstance(dv, list) else self.deserialize(dv))
                except KeyDeserialization:
                    pass

        return output


deserializer = Deserializer()
