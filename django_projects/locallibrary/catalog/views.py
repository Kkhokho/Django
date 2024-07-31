from django.shortcuts import render
from catalog.models import Book, Author, BookInstance, Genre
from django.views import View, generic
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.urls import reverse, reverse_lazy
from catalog.forms import RenewBookForm
import datetime
from django.views.generic.edit import CreateView, UpdateView, DeleteView

def index(request):
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    context_object_name = 'book_list'
    queryset = Book.objects.filter(title__icontains='')[:5]
    template_name = 'catalog/book_list.html'
    paginate_by = 1

    def get_context_data(self, **kwargs):
        context = super(BookListView, self).get_context_data(**kwargs)
        return context
    
class BookDetailView(generic.DetailView):
    model = Book

    def book_detail_view(request, primary_key):
        book = get_object_or_404(Book, pk=primary_key)
        return render(request, 'catalog/book_detail.html', context={'book': book})
    
class AuthorListView(generic.ListView):
    model = Author
    context_object_name = 'author_list'
    queryset = Author.objects.all()
    template_name = 'catalog/author_list.html'

    def get_context_data(self, **kwargs):
        context = super(AuthorListView, self).get_context_data(**kwargs)
        return context

class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'catalog/author_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AuthorDetailView, self).get_context_data(**kwargs)
        context['books'] = Book.objects.filter(author=self.object)
        return context
    

class LoanedBooksByUserListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    context_object_name = 'bookinstance_list'
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

    def get_context_data(self, **kwargs):
        context = super(LoanedBooksByUserListView, self).get_context_data(**kwargs)
        return context
    
class LoanedBooksAllListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    context_object_name = 'bookinstance_list'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    permission_required = 'catalog.catalog.change_bookinstance'

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

    def get_context_data(self, **kwargs):
        context = super(LoanedBooksAllListView, self).get_context_data(**kwargs)
        return context

@login_required
@permission_required('catalog.can_mark_returned')
@require_POST
def return_book(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)
    
    if book_instance.borrower != request.user:
        return HttpResponseForbidden("You do not have permission to return this book.")
    
    book_instance.status = 'a'  
    book_instance.borrower = None
    book_instance.save()
    
    return redirect('my-borrowed')

@login_required
@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)
    
    if request.method == 'POST':
        form = RenewBookForm(request.POST)
        
        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed'))
    
        else:
            proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
            form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2021'}

class AuthorUpdate(UpdateView):
    model = Author
    fields = '__all__'

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')