from django.contrib import admin
from .models import Nodo, Medida, Nota

# Register your models here.

#admin.site.register(Nodo)
#admin.site.register(Medida)
#admin.site.register(Nota)

class MedidaAdmin(admin.ModelAdmin):
	
	list_filter = ['nodo','parametro']
	list_per_page = 300
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return [ 'nodo','parametro', 'valor', 'unidad', 'fecha_toma']
		else:
			return []

admin.site.register(Medida, MedidaAdmin)
			
class NotaInline(admin.StackedInline):
	model = Nota
	extra = 1
	
class MedidaInline(admin.TabularInline):
	model = Medida
	extra = 0
	fields = [('parametro', 'valor', 'unidad', 'fecha_toma')]
	empty_value_display = 'No hay medidas asociadas'
	list_filter = ['parametro']
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return ['parametro', 'valor', 'unidad', 'fecha_toma']
		else:
			return []
	
class NodoAdmin(admin.ModelAdmin):
	list_display = ('ip', 'nombre', 'tipo', 'mac', 'activo')
	list_filter = ('nombre', 'tipo')
	fieldsets = [
		(None,				{'fields': ['nombre','tipo']}),
		('Detalles', {'fields': ['ip','mac','activo'], 'classes': ['collapse']})
	]
	
	inlines = [MedidaInline, NotaInline]
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return ['ip','tipo','mac', 'activo']
		else:
			return []
			
	def get_formsets_with_inlines(self, request, obj=None):
		for inline in self.get_inline_instances(request, obj):
			if obj and obj.tipo == "SENSOR" and inline.__class__.__name__ == "MedidaInline":
				yield inline.get_formset(request, obj), inline
			elif obj and obj.tipo == "MARCADOR" and inline.__class__.__name__ == "NotaInline":
				yield inline.get_formset(request, obj), inline
	
admin.site.register(Nodo, NodoAdmin)
"""class MedidaInstanceAdmin(admin.ModelAdmin):
	model = Medida
	fields = [('parametro', 'valor', 'unidad')]"""