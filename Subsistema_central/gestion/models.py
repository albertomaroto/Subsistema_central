from django.db import models

# Create your models here.

class Nodo(models.Model):
	mac = models.CharField(max_length=30, primary_key=True)
	ip = models.CharField(max_length=30)
	tipo = models.CharField(max_length=30)
	nombre = models.CharField(max_length=30)
	activo = models.BooleanField(null=False)
	
	def __str__(self):
		return self.ip + " - " + self.nombre + " " + " (" + self.tipo + ")"
				
class Medida(models.Model):
	nodo = models.ForeignKey(Nodo, on_delete=models.CASCADE)
	parametro = models.CharField(max_length=30)
	valor = models.FloatField(null=True, blank=True, default=0.0)
	unidad = models.CharField(max_length=10)
	fecha_toma= models.DateTimeField('Fecha toma')
	
	def __str__(self):
		return self.parametro + ": " + str(self.valor) + self.unidad
	
class Nota(models.Model):
	nodo = models.ForeignKey(Nodo, on_delete=models.CASCADE)
	nota = models.CharField(max_length=300)
	
	def __str__(self):
		return self.nota
