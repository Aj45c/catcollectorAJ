from subprocess import CompletedProcess
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from psycopg2 import DatabaseError
from .models import Cat, Toy, Photo
from .forms import FeedingForm

import uuid
import boto3

S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'catcollectaj'



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

def cats_index(request):
  cats = Cat.objects.all(user=request.user)
  return render(request, 'cats/index.html', { 'cats': cats })

def cats_detail(request, cat_id):
  cat = Cat.objects.get(id=cat_id)
  feeding_form = FeedingForm()
  toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
  return render(request, 'cats/detail.html', {
    # include the cat and feeding_form in the context
    'cat': cat, 'feeding_form': feeding_form,
    'toys': toys_cat_doesnt_have
  })

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

def assoc_toy(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.add(toy_id)
  return redirect('detail', cat_id=cat_id)

def assoc_toy_delete(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.remove(toy_id)
  return redirect('detail', cat_id=cat_id)

def add_photo(request, cat_id):
  # attempt to collect the photo file data
  photo_file = request.FILES.get('photo-file', None)
  # use conditional logic to determine if file is present
  if photo_file:
  # if it's present, we will create a reference the the boto3 client
    s3 = boto3.client('s3')
    # create a unique id for each photo file
    key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
    # funny_cat.png = jdbw7f.png
    # upload the photo file to aws s3
    try:
    # if successful
      s3.upload_fileobj(photo_file, BUCKET, key)
      # take the exchanged url and save it to the database
      url = f"{S3_BASE_URL}{BUCKET}/{key}"
      # 1) create photo instance with photo model and provide cat_id as foreign key val
      photo = Photo(url=url, cat_id=cat_id)
      # 2) save the photo instance to the database
      photo.save()
    except Exception as error:
      print("Error uploading photo: ", error)
      return redirect('detail', cat_id=cat_id)
    # print an error message
  return redirect('detail', cat_id=cat_id)
  # redirect the user to the origin 

def signup(request):
  # check if the request method is POST
  # we need to create a new user because form was submmited

  # 1} use the form data from the request to create a form/model instance from the model forma
  # 2}validate the form to ensure it was Completed
  # 3)saving the user object to the Database
  # $)log in the user(creates a sesson for the logged in user)
  error_message = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid Info - Please Try Again'
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html' , context)


class CatCreate(CreateView):
  model = Cat
  fields = ['name', 'breed', 'description', 'age']
  success_url = '/cats/'
  def form_valid(self, form):
    # Assign the logged in user (self.request.user)
    form.instance.user = self.request.user  # form.instance is the cat
    # Let the CreateView do its job as usual
    return super().form_valid(form)

class CatUpdate(UpdateView):
  model = Cat
  # Let's disallow the renaming of a cat by excluding the name field!
  fields = [ 'breed', 'description', 'age']

class CatDelete(DeleteView):
  model = Cat
  success_url = '/cats/'

class ToyList(ListView):
  model = Toy
  template_name = 'toys/index.html'

class ToyDetail(DetailView):
  model = Toy
  template_name = 'toys/detail.html'

class ToyCreate(CreateView):
    model = Toy
    fields = ['name', 'color']


class ToyUpdate(UpdateView):
    model = Toy
    fields = ['name', 'color']


class ToyDelete(DeleteView):
    model = Toy
    success_url = '/toys/'
