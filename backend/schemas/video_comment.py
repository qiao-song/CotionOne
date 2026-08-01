from marshmallow import Schema, fields, validate


class VideoCommentCreateSchema(Schema):
    goods_id = fields.Integer(required=True)
    content = fields.String(required=True, validate=validate.Length(min=1, max=500))
