from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.urls import reverse_lazy
from .models import Sample
from .forms import SampleForm
from django.shortcuts import render, redirect
from patients.models import Patient
from django.views.generic import DeleteView
from django.http import HttpResponse
from .utils import generate_bill_pdf, save_bill_pdf
from .models import Bill




class SampleTrackView(TemplateView):
    template_name = 'samples/sample_track.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        response = super().form_valid(form)

        if form.cleaned_data.get('paid', False):
            # Create bill
            bill = Bill.objects.create(
                sample=self.object,
                paid=True,
                amount=100.00  # Set your default amount or get from form
            )

            # Generate PDF
            context = {
                'sample': self.object,
                'bill': bill
            }
            pdf_content = generate_bill_pdf(context)

            if pdf_content:
                save_bill_pdf(bill, pdf_content)

                # Add to context for template
                self.object.bill_pdf_url = bill.pdf_file.url

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'object') and hasattr(self.object, 'bill_pdf_url'):
            context['bill_pdf_url'] = self.object.bill_pdf_url
        return context
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


def create_sample(request):
    if request.method == 'POST':
        form = SampleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('samples:list')
    else:
        form = SampleForm()

    # Get patients for the template dropdown
    patients = Patient.objects.all().order_by('last_name')

    return render(request, 'samples/sample_form.html', {
        'form': form,
        'patients': patients
    })

class SampleDeleteView(DeleteView):
    model = Sample
    template_name = 'samples/sample_confirm_delete.html'
    success_url = reverse_lazy('samples:list')