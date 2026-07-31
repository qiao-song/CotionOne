from marshmallow import Schema, fields, validate


class CheckoutItemSchema(Schema):
    goods_id = fields.Integer(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1, max=99))


class CheckoutSchema(Schema):
    items = fields.List(fields.Nested(CheckoutItemSchema), required=True, validate=validate.Length(min=1))


class OrderStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(['received', 'returned']))
