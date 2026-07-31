from marshmallow import Schema, fields, validate


class ReviewCreateSchema(Schema):
    order_id = fields.Integer(required=True)
    goods_id = fields.Integer(required=True)
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    content = fields.String(required=False, allow_none=True)
