from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.urls import reverse_lazy
from .models import Sample
from .forms import SampleForm


class SampleTrackView(TemplateView):
    template_name = 'samples/sample_track.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all samples ordered by collection date (newest first)
        context['samples'] = Sample.objects.all().order_by('-collection_date')
        return context


class SampleListView(ListView):
    model = Sample
    template_name = 'samples/sample_list.html'
    context_object_name = 'samples'
    paginate_by = 20


class SampleCreateView(CreateView):
    model = Sample
    form_class = SampleForm
    template_name = 'samples/sample_form.html'
    success_url = reverse_lazy('samples:list')

    def form_valid(self, form):
        form.instance.barcode = f"SMP-{Sample.objects.count() + 1000}"
        return super().form_valid(form)


class SampleDetailView(DetailView):
    model = Sample
    template_name = 'samples/sample_detail.html'
    context_object_name = 'sample'


class SampleUpdateView(UpdateView):
    model = Sample
    form_class = SampleForm
    template_name = 'samples/sample_form.html'
    context_object_name = 'sample'

    def get_success_url(self):
        return reverse_lazy('samples:detail', kwargs={'pk': self.object.pk})