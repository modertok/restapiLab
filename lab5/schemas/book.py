from marshmallow import Schema, fields, validate, EXCLUDE


class BookCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    author = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(load_default=None, allow_none=True,
                             validate=validate.Length(max=1000))
    status = fields.Str(load_default="available",
                        validate=validate.OneOf(["available", "issued"]))
    year = fields.Int(required=True, validate=validate.Range(min=1000, max=2100))


class BookResponseSchema(Schema):
    id = fields.Str()
    title = fields.Str()
    author = fields.Str()
    description = fields.Str(allow_none=True)
    status = fields.Str()
    year = fields.Int()
