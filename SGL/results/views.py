from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from .models import Result
from .forms import ResultForm


class ResultListView(ListView):
    model = Result
    template_name = 'results/result_list.html'
    context_object_name = 'results'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Result.STATUS_CHOICES
        return context

    def get_status_choices(self):
        return Result.STATUS_CHOICES
class ResultCreateView(CreateView):
    model = Result
    form_class = ResultForm
    template_name = 'results/result_form.html'
    success_url = reverse_lazy('results:list')


class ResultDetailView(DetailView):
    model = Result
    template_name = 'results/result_detail.html'
    context_object_name = 'result'


class ResultUpdateView(UpdateView):
    model = Result
    form_class = ResultForm
    template_name = 'results/result_form.html'
    context_object_name = 'result'

    def get_success_url(self):
        return reverse_lazy('results:detail', kwargs={'pk': self.object.pk})