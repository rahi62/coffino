from django.db import migrations, models
import uuid


def create_categories_from_legacy_values(apps,schema_editor):
    Category=apps.get_model('inventory','IngredientCategory')
    Item=apps.get_model('inventory','InventoryItem')
    cache={}
    for item in Item.objects.exclude(category='').iterator():
        name=item.category.strip()
        if not name:continue
        key=(item.branch_id,name.casefold())
        category=cache.get(key)
        if category is None:
            category=Category.objects.filter(branch_id=item.branch_id,name__iexact=name).first()
            if category is None:category=Category.objects.create(branch_id=item.branch_id,name=name)
            cache[key]=category
        Item.objects.filter(pk=item.pk).update(material_category_id=category.id)


class Migration(migrations.Migration):
    dependencies=[('inventory','0004_inventoryitem_material_management')]

    operations=[
        migrations.CreateModel(
            name='IngredientCategory',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('uuid',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
                ('name',models.CharField(max_length=80)),
                ('sort_order',models.PositiveIntegerField(default=0)),
                ('is_active',models.BooleanField(default=True)),
                ('branch',models.ForeignKey(on_delete=models.deletion.CASCADE,related_name='ingredient_categories',to='businesses.branch')),
            ],
            options={'ordering':['sort_order','name','id'],'unique_together':{('branch','name')}},
        ),
        migrations.AddField(
            model_name='inventoryitem',name='material_category',
            field=models.ForeignKey(blank=True,null=True,on_delete=models.deletion.SET_NULL,related_name='materials',to='inventory.ingredientcategory'),
        ),
        migrations.RunPython(create_categories_from_legacy_values,migrations.RunPython.noop),
    ]
