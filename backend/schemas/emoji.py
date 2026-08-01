from marshmallow import Schema, fields, validate


class EmojiCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=50))
