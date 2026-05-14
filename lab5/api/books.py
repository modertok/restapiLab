from flask import request, make_response
from flask_restful import Resource
from marshmallow import ValidationError

from schemas.book import BookCreateSchema, BookResponseSchema
from services import book_service

_create_schema = BookCreateSchema()
_response_schema = BookResponseSchema()


class BookListResource(Resource):
    def get(self):
        """
        Get all books with optional filtering, sorting and pagination.
        ---
        tags:
          - books
        parameters:
          - name: status
            in: query
            type: string
            enum: [available, issued]
            description: Filter by book status
          - name: author
            in: query
            type: string
            description: Filter by author name (partial, case-insensitive)
          - name: sort_by
            in: query
            type: string
            enum: [title, year]
            description: Sort field
          - name: limit
            in: query
            type: integer
            default: 10
            minimum: 1
            maximum: 100
            description: Number of items per page
          - name: offset
            in: query
            type: integer
            default: 0
            minimum: 0
            description: Number of items to skip
        responses:
          200:
            description: Paginated list of books
            schema:
              $ref: '#/definitions/BookListResponse'
          422:
            description: Invalid query parameters
            schema:
              $ref: '#/definitions/ValidationError'
        """
        status = request.args.get("status")
        author = request.args.get("author")
        sort_by = request.args.get("sort_by")

        if status is not None and status not in ("available", "issued"):
            return {"errors": {"status": ["Must be one of: available, issued"]}}, 422

        if sort_by is not None and sort_by not in ("title", "year"):
            return {"errors": {"sort_by": ["Must be one of: title, year"]}}, 422

        try:
            limit = int(request.args.get("limit", 10))
            offset = int(request.args.get("offset", 0))
        except (ValueError, TypeError):
            return {"errors": {"limit/offset": ["Must be integers"]}}, 422

        if not (1 <= limit <= 100):
            return {"errors": {"limit": ["Must be between 1 and 100"]}}, 422
        if offset < 0:
            return {"errors": {"offset": ["Must be >= 0"]}}, 422

        books, total = book_service.get_books(
            status=status, author=author, sort_by=sort_by,
            limit=limit, offset=offset,
        )
        return {
            "items": [_response_schema.dump(b) for b in books],
            "total": total,
            "limit": limit,
            "offset": offset,
        }, 200

    def post(self):
        """
        Create a new book.
        ---
        tags:
          - books
        consumes:
          - application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              $ref: '#/definitions/BookCreate'
        responses:
          201:
            description: Book created successfully
            schema:
              $ref: '#/definitions/Book'
          422:
            description: Validation error
            schema:
              $ref: '#/definitions/ValidationError'
        """
        payload = request.get_json(silent=True) or {}
        try:
            data = _create_schema.load(payload)
        except ValidationError as exc:
            return {"errors": exc.messages}, 422

        book = book_service.add_book(data)
        return _response_schema.dump(book), 201


class BookResource(Resource):
    def get(self, book_id):
        """
        Get a single book by its UUID.
        ---
        tags:
          - books
        parameters:
          - name: book_id
            in: path
            type: string
            required: true
            description: Book UUID
        responses:
          200:
            description: Book found
            schema:
              $ref: '#/definitions/Book'
          404:
            description: Book not found
            schema:
              $ref: '#/definitions/NotFound'
        """
        book = book_service.get_book(book_id)
        if book is None:
            return {"detail": "Book not found"}, 404
        return _response_schema.dump(book), 200

    def delete(self, book_id):
        """
        Delete a book by its UUID (idempotent).
        ---
        tags:
          - books
        parameters:
          - name: book_id
            in: path
            type: string
            required: true
            description: Book UUID
        responses:
          204:
            description: Book deleted (or did not exist — idempotent)
        """
        book_service.remove_book(book_id)
        return make_response("", 204)
