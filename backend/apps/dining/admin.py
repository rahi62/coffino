from django import forms
from django.contrib import admin

from apps.businesses.models import Branch, Business
from .models import Hall, Table, TableSession, TableTransferLog


class BusinessScopedSelect(forms.Select):
    """Annotate related choices so the admin can filter them in the browser."""

    def __init__(self, *args, business_id_getter, **kwargs):
        self.business_id_getter = business_id_getter
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, 'instance', None)
        if instance is not None:
            option['attrs']['data-business-id'] = str(self.business_id_getter(instance))
        return option


class HallAdminForm(forms.ModelForm):
    business = forms.ModelChoiceField(
        label='کسب‌وکار', queryset=Business.objects.order_by('name'), required=True,
        help_text='ابتدا کسب‌وکار، سپس شعبهٔ آن را انتخاب کنید.'
    )

    class Meta:
        model = Hall
        fields = ('business', 'branch', 'name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Branch.objects.select_related('business').order_by('business__name', 'name')
        branch_widget = BusinessScopedSelect(
            attrs={'data-business-scope': 'branch', 'data-business-field': 'business'},
            business_id_getter=lambda branch: branch.business_id,
        )
        branch_widget.choices = self.fields['branch'].choices
        self.fields['branch'].widget = branch_widget
        business_id = self.data.get('business') or self.initial.get('business')
        if not business_id and self.instance.pk:
            business_id = self.instance.branch.business_id
        if business_id:
            self.initial['business'] = business_id

    def clean(self):
        cleaned = super().clean()
        business, branch = cleaned.get('business'), cleaned.get('branch')
        if business and branch and branch.business_id != business.id:
            self.add_error('branch', 'شعبه باید متعلق به کسب‌وکار انتخاب‌شده باشد.')
        return cleaned

    class Media:
        js = ('dining/js/business_scope.js',)


class TableAdminForm(forms.ModelForm):
    business = forms.ModelChoiceField(
        label='کسب‌وکار', queryset=Business.objects.order_by('name'), required=True,
        help_text='ابتدا کسب‌وکار، سپس سالنِ همان کسب‌وکار را انتخاب کنید.'
    )

    class Meta:
        model = Table
        fields = ('business', 'hall', 'number', 'capacity', 'status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hall'].queryset = Hall.objects.select_related('branch__business').order_by(
            'branch__business__name', 'branch__name', 'name'
        )
        hall_widget = BusinessScopedSelect(
            attrs={'data-business-scope': 'hall', 'data-business-field': 'business'},
            business_id_getter=lambda hall: hall.branch.business_id,
        )
        hall_widget.choices = self.fields['hall'].choices
        self.fields['hall'].widget = hall_widget
        business_id = self.data.get('business') or self.initial.get('business')
        if not business_id and self.instance.pk:
            business_id = self.instance.hall.branch.business_id
        if business_id:
            self.initial['business'] = business_id

    def clean(self):
        cleaned = super().clean()
        business, hall = cleaned.get('business'), cleaned.get('hall')
        if business and hall and hall.branch.business_id != business.id:
            self.add_error('hall', 'سالن باید متعلق به کسب‌وکار انتخاب‌شده باشد.')
        return cleaned

    class Media:
        js = ('dining/js/business_scope.js',)


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    form = HallAdminForm
    list_display = ('name', 'branch', 'business_name')
    list_select_related = ('branch__business',)
    search_fields = ('name', 'branch__name', 'branch__business__name')

    @admin.display(description='کسب‌وکار', ordering='branch__business__name')
    def business_name(self, obj):
        return obj.branch.business.name


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    form = TableAdminForm
    list_display = ('number', 'hall', 'branch_name', 'business_name', 'capacity', 'status')
    list_select_related = ('hall__branch__business',)
    search_fields = ('number', 'hall__name', 'hall__branch__name', 'hall__branch__business__name')

    @admin.display(description='شعبه', ordering='hall__branch__name')
    def branch_name(self, obj):
        return obj.hall.branch.name

    @admin.display(description='کسب‌وکار', ordering='hall__branch__business__name')
    def business_name(self, obj):
        return obj.hall.branch.business.name


admin.site.register(TableSession)
admin.site.register(TableTransferLog)
