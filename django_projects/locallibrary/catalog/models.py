from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _l
import uuid

class Genre(models.Model):
    name = models.CharField(max_length=200, help_text=_l('Nhập thể loại sách (ví dụ: Khoa học viễn tưởng)'))

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    summary = models.TextField(max_length=1000, help_text=_l('Nhập mô tả ngắn gọn về cuốn sách'))
    isbn = models.CharField('ISBN', max_length=13, unique=True,
                            help_text=_l('13 ký tự <a href="https://www.isbn-international.org/content/what-isbn">mã số ISBN</a>'))
    genre = models.ManyToManyField(Genre, help_text=_l('Chọn một thể loại cho cuốn sách này'))

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

class BookInstance(models.Model):
    """Mô hình đại diện cho một bản sao cụ thể của một cuốn sách (tức là có thể được mượn từ thư viện)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text=_l('ID duy nhất cho cuốn sách này trong toàn bộ thư viện'))
    book = models.ForeignKey('Book', on_delete=models.RESTRICT)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)

    LOAN_STATUS = (
        ('m', _l('Bảo trì')),
        ('o', _l('Đang mượn')),
        ('a', _l('Có sẵn')),
        ('r', _l('Đã đặt trước'))
    )

    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='m',
        help_text=_l('Tình trạng sách'),
    )

    class Meta:
        ordering = ['due_back']

    def __str__(self):
        """Chuỗi đại diện cho đối tượng Model"""
        return f'{self.id} ({self.book.title})'

class Author(models.Model):
    """Mô hình đại diện cho một tác giả."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('Mất', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        """Trả về URL để truy cập một tác giả cụ thể."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """Chuỗi đại diện cho đối tượng Model"""
        return f'{self.last_name}, {self.first_name}'
