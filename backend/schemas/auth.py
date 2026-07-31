from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class SendCodeSchema(Schema):
    phone = fields.String(required=True, validate=validate.Regexp(r'^1\d{10}$', error='手机号格式不正确'))


class RegisterSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=2, max=50))
    phone = fields.String(required=True, validate=validate.Regexp(r'^1\d{10}$', error='手机号格式不正确'))
    password = fields.String(required=True, validate=validate.Length(min=6, max=128))


class LoginSchema(Schema):
    username = fields.String(required=False)
    phone = fields.String(required=False)
    password = fields.String(required=False)
    code = fields.String(required=False)

    @validates_schema
    def validate_login_method(self, data, **kwargs):
        has_identity = bool(data.get('username') or data.get('phone'))
        has_credential = bool(data.get('password') or data.get('code'))
        if not has_identity:
            raise ValidationError('请输入用户名或手机号')
        if not has_credential:
            raise ValidationError('请输入密码或验证码')
