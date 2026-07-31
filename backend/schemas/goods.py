from marshmallow import Schema, fields, validate


class GoodsCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    price = fields.Decimal(required=True, places=2)
    description = fields.String(required=False, allow_none=True)


class GoodsUpdateSchema(Schema):
    title = fields.String(required=False, validate=validate.Length(min=1, max=200))
    price = fields.Decimal(required=False, places=2)
    description = fields.String(required=False, allow_none=True)
