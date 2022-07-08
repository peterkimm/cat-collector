from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Cat, Toy, Photo
from .forms import FeedingForm

import uuid
import boto3

S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'catcollector-avatar-24'

# Create your views here.

# def home(request):
#     '''
#     this is where we return a response
#     in most cases we  would render a template
#     and we'll need some data for that template
#     '''
#     return HttpResponse('<h1> Hello World </h1>')

def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

@login_required
def cats_index(request):
  cats = Cat.objects.filter(user=request.user)
  return render(request, 'cats/index.html', { 'cats': cats })

@login_required
def cats_detail(request, cat_id):
  cat = Cat.objects.get(id=cat_id)
  feeding_form = FeedingForm()
  toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
  return render(request, 'cats/detail.html', {
    # include the cat and feeding_form in the context
    'cat': cat, 'feeding_form': feeding_form,
    'toys': toys_cat_doesnt_have
  })

@login_required
def add_feeding(request, cat_id):
  # create the ModelForm using the data in request.POST
  form = FeedingForm(request.POST)
  # validate the form
  if form.is_valid():
    # don't save the form to the db until it
    # has the cat_id assigned
    new_feeding = form.save(commit=False)
    new_feeding.cat_id = cat_id
    new_feeding.save()
  return redirect('detail', cat_id=cat_id)

@login_required
def assoc_toy(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.add(toy_id)
  return redirect('detail', cat_id=cat_id)

@login_required
def assoc_toy_delete(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.remove(toy_id)
  return redirect('detail', cat_id=cat_id)

@login_required
def add_photo(request, cat_id):
    # attempt to collect the photo file data
    photo_file = request.FILES.get('photo-file', None)
    # use conditional logic to determin if file is present
    if photo_file:
    # if it's present, we will create a reference the boto3 client
        s3 = boto3.client('s3')
        # create a unique id for each photo file
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # upload the photo file to aws s3
        try:
        # if successful
            s3.upload_fileobj(photo_file, BUCKET, key)
        # take the exchange url and save it to the database
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            # 1) create photo instance with photo model and provide cat_id as foreign key value
            photo = Photo(url=url, cat_id=cat_id)
            # 2) save the photo instance to the database
            photo.save()
        except Exception as error:
            print("Error uploading photo: ", error)
            return redirect('detail', cat_id=cat_id)
        # print an error message
    return redirect('detail', cat_id=cat_id)
    # redirect the user to the origin page
        

# def signup(request):
  # check if the request method is POST = we need to create a new user because form was submitted

  # 1) use the form data from the request to create a form/model instance from the model form
  # 2) validate the form to ensure it was complete
  # 2.2) if form not valid - redirect the user to the signup page with an error message
  # 3) saving the user object to the database
  # 4) login the user (create a session for the logged in user in the database)
  # 5) redirect the user to the cats index page

  # else the request is GET = the user clicked on the signup link
  # 1) create a blank instance of the model form
  # 2) provide that form instance to a registration template
  # 3) render the template so the user can fill out the form

def signup(request):
  error_messages = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('index')
    else:
      error_messages = 'Invalid Info - Please Try Again'
  form = UserCreationForm()
  context = {'form': form, 'error_messages': error_messages}
  return render(request, 'registration/signup.html', context)
    






class CatCreate(LoginRequiredMixin, CreateView):
  model = Cat
  fields = ['name', 'breed', 'description', 'age']
  success_url = '/cats/'

  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

class CatUpdate(LoginRequiredMixin, UpdateView):
  model = Cat
  # Let's disallow the renaming of a cat by excluding the name field!
  fields = [ 'breed', 'description', 'age']

class CatDelete(LoginRequiredMixin, DeleteView):
  model = Cat
  success_url = '/cats/'

class ToyList(LoginRequiredMixin, ListView):
  model = Toy
  template_name = 'toys/index.html'

class ToyDetail(LoginRequiredMixin, DetailView):
  model = Toy
  template_name = 'toys/detail.html'

class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = ['name', 'color']


class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    fields = ['name', 'color']


class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'
