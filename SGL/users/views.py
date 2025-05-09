from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from .models import User, UserActivity
from .forms import CustomUserCreationForm, CustomUserChangeForm

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'admin'

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:list')

    def test_func(self):
        return (self.request.user.is_superuser or
                self.request.user.role == 'admin' or
                self.request.user == self.get_object())

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = UserActivity.objects.filter(user=self.object).order_by('-timestamp')[:10]
        return context


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'admin'

    def delete(self, request, *args, **kwargs):
        messages.success(request, "User deleted successfully")
        return super().delete(request, *args, **kwargs)