from marshmallow import Schema, fields, validate


class ChangePasswordSchema(Schema):
    old_password = fields.String(required=True, validate=validate.Length(min=1))
    new_password = fields.String(required=True, validate=validate.Length(min=6, max=128))
