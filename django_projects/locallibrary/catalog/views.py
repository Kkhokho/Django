from django.shortcuts import render
from django.views import generic
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# Create your views here.
from catalog.models import Book, Author, BookInstance, Genre
from typing import Any
from django.shortcuts import render
from catalog.models import Book, Author, BookInstance, Genre
from django.views import View, generic
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
import datetime 
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from catalog.forms import RenewBookForm
def index(request):
    """View function for home page of site."""
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    # The 'all()' is implied by default.
    num_authors = Author.objects.count()
    num_authors = Author.objects.count() # The 'all()' is implied by default.# Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1
    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits
    }
    return render(request, 'index.html', context=context)
class BookListView(generic.ListView):
    model = Book
    context_object_name = 'my_book_list'
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